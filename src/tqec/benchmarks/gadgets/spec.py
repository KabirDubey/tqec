"""Gadget specification and the registry that stores it."""

import re
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType

from tqec.benchmarks.gadgets.mechanisms import CONVENTIONS, MECHANISMS, STATUSES
from tqec.computation.block_graph import BlockGraph
from tqec.utils.exceptions import TQECError

_ID_RE = re.compile(r"[a-z0-9_]{1,40}")
_DISTANCE_RE = re.compile(r"(?P<mul>\d+)\*k(?P<add>[+-]\d+)?")


@dataclass(frozen=True)
class GadgetSpec:
    """A named block graph with the facts needed to benchmark and test it.

    Attributes:
        id: Lowercase ``[a-z0-9_]``, at most 40 characters, prefixed by the family.
        build: Zero-argument callable returning a
            :py:class:`~tqec.computation.block_graph.BlockGraph`, or the path of a ``.bgraph`` or
            ``.dae`` file.
        family: Group the gadget belongs to (``memory``, ``y_half_cube``, ...).
        mechanisms: Tags of :data:`~tqec.benchmarks.gadgets.mechanisms.MECHANISMS` the gadget
            covers.
        expected: Status per convention name, with the strings of ``UnitStatus``.
        blocked_by: Issues, pull requests or branches that must land before ``expected`` changes.
        expected_distance: Expected ``shortest_graphlike_error`` length as a formula in ``k``
            (``"2*k+1"``), measured over all observables of the graph jointly.
        notes: Free text for gaps and caveats.

    """

    id: str
    build: Callable[[], BlockGraph | Path]
    family: str
    mechanisms: frozenset[str]
    expected: Mapping[str, str]
    blocked_by: tuple[str, ...] = ()
    expected_distance: str = "2*k+1"
    notes: str = ""

    def __post_init__(self) -> None:
        if not _ID_RE.fullmatch(self.id):
            raise TQECError(f"Invalid gadget id {self.id!r}: expected [a-z0-9_]{{1,40}}.")
        object.__setattr__(self, "mechanisms", frozenset(self.mechanisms))
        unknown = self.mechanisms - MECHANISMS
        if unknown:
            raise TQECError(f"Gadget {self.id!r} has unknown mechanism tags {sorted(unknown)}.")
        object.__setattr__(self, "expected", MappingProxyType(dict(self.expected)))
        if set(self.expected) != set(CONVENTIONS):
            raise TQECError(f"Gadget {self.id!r} must state `expected` for {CONVENTIONS}.")
        bad_status = set(self.expected.values()) - STATUSES
        if bad_status:
            raise TQECError(f"Gadget {self.id!r} has unknown statuses {sorted(bad_status)}.")
        if _DISTANCE_RE.fullmatch(self.expected_distance) is None:
            raise TQECError(f"Gadget {self.id!r}: bad distance formula {self.expected_distance!r}.")

    def distance(self, k: int) -> int:
        """Return the expected ``shortest_graphlike_error`` length at scale ``k``."""
        match = _DISTANCE_RE.fullmatch(self.expected_distance)
        assert match is not None
        return int(match["mul"]) * k + int(match["add"] or 0)


_REGISTRY: dict[str, GadgetSpec] = {}


def register(spec: GadgetSpec) -> GadgetSpec:
    """Add ``spec`` to the registry and return it.

    Raises:
        TQECError: If a spec with the same id is already registered.

    """
    if spec.id in _REGISTRY:
        raise TQECError(f"Gadget {spec.id!r} is already registered.")
    _REGISTRY[spec.id] = spec
    return spec


def get(gadget_id: str) -> GadgetSpec:
    """Return the spec registered under ``gadget_id``.

    Raises:
        TQECError: If there is none.

    """
    try:
        return _REGISTRY[gadget_id]
    except KeyError:
        raise TQECError(f"Unknown gadget id {gadget_id!r}.") from None


def iter_gadgets(
    *,
    family: str | None = None,
    mechanisms: Iterable[str] | None = None,
    convention: str | None = None,
    status: str | None = None,
    ids: Iterable[str] | None = None,
) -> list[GadgetSpec]:
    """Return the registered specs that match every given filter, sorted by id.

    Args:
        family: Keep the specs of this family.
        mechanisms: Keep the specs that carry all of these tags.
        convention: Keep the specs that state an expectation for this convention. Required with
            ``status``.
        status: Keep the specs whose expected status for ``convention`` equals this.
        ids: Keep the specs with these ids.

    Raises:
        ValueError: If ``status`` is given without ``convention``, or a filter value is unknown
            (convention, status, tag, id or family).

    """
    if status is not None and convention is None:
        raise ValueError("Filtering by `status` requires `convention`.")
    if convention is not None and convention not in CONVENTIONS:
        raise ValueError(f"Unknown convention {convention!r}.")
    if status is not None and status not in STATUSES:
        raise ValueError(f"Unknown status {status!r}.")
    wanted_tags = frozenset(mechanisms) if mechanisms is not None else frozenset()
    unknown = wanted_tags - MECHANISMS
    if unknown:
        raise ValueError(f"Unknown mechanism tags {sorted(unknown)}.")
    wanted_ids = frozenset(ids) if ids is not None else None
    if wanted_ids is not None and wanted_ids - _REGISTRY.keys():
        raise ValueError(f"Unknown gadget ids {sorted(wanted_ids - _REGISTRY.keys())}.")
    if family is not None and family not in {s.family for s in _REGISTRY.values()}:
        raise ValueError(f"Unknown gadget family {family!r}.")
    result = []
    for spec in sorted(_REGISTRY.values(), key=lambda s: s.id):
        if family is not None and spec.family != family:
            continue
        if not wanted_tags <= spec.mechanisms:
            continue
        if wanted_ids is not None and spec.id not in wanted_ids:
            continue
        if status is not None and convention is not None and spec.expected[convention] != status:
            continue
        result.append(spec)
    return result


def build_graph(spec: GadgetSpec) -> BlockGraph:
    """Build the block graph of ``spec``, reading it from file when the spec is file-backed."""
    built = spec.build()
    if isinstance(built, BlockGraph):
        return built
    if built.suffix == ".bgraph":
        return BlockGraph.from_bgraph(built, graph_name=spec.id)
    return BlockGraph.from_dae_file(built, graph_name=spec.id)


def vend(specs_or_ids: Iterable[GadgetSpec | str]) -> list[BlockGraph | Path]:
    """Return the inputs for ``tqec.orchestration.prepare_batch``, one per spec.

    A built graph is returned with ``name`` set to the spec id, so the batch derives its gadget id
    from it without loss. A file-backed spec is returned as its path, which ``prepare_batch``
    reads itself; the file is named ``<id>.bgraph``.

    Args:
        specs_or_ids: Specs or registered ids, in the order the gadgets are wanted.

    """
    inputs: list[BlockGraph | Path] = []
    for item in specs_or_ids:
        spec = get(item) if isinstance(item, str) else item
        built = spec.build()
        if isinstance(built, BlockGraph):
            graph = built.clone()
            graph.name = spec.id
            inputs.append(graph)
        else:
            inputs.append(built)
    return inputs
