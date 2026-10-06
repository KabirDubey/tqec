"""Gadgets wrapping the graphs of :mod:`tqec.gallery`, closed per basis and with open ports."""

from collections.abc import Callable
from functools import partial

from tqec.benchmarks.gadgets._common import COMPILE_FAILED, READY
from tqec.benchmarks.gadgets.spec import GadgetSpec, register
from tqec.computation.block_graph import BlockGraph
from tqec.gallery.cnot import cnot
from tqec.gallery.cz import cz
from tqec.gallery.move_rotation import move_rotation
from tqec.gallery.steane_encoding import steane_encoding
from tqec.gallery.three_cnots import three_cnots
from tqec.utils.enums import Basis

_BASES = {"z": Basis.Z, "x": Basis.X}
_MERGE = {"z": "zx", "x": "xz"}


def _named(
    name: str, factory: Callable[[Basis | None], BlockGraph], basis: Basis | None
) -> BlockGraph:
    graph = factory(basis)
    graph.name = name
    return graph


def _named_cz(name: str) -> BlockGraph:
    graph = cz()
    graph.name = name
    return graph


for _b, _basis in _BASES.items():
    register(
        GadgetSpec(
            id=f"cnot_{_b}",
            build=partial(_named, f"cnot_{_b}", cnot, _basis),
            family="gallery",
            mechanisms=frozenset({f"space:merge_split:{_MERGE[_b]}"}),
            expected=READY,
        )
    )
    register(
        GadgetSpec(
            id=f"move_rotation_{_b}",
            build=partial(_named, f"move_rotation_{_b}", move_rotation, _basis),
            family="gallery",
            mechanisms=frozenset({f"space:rotation:move:{_b}"}),
            expected=READY,
        )
    )
    register(
        GadgetSpec(
            id=f"three_cnots_{_b}",
            build=partial(_named, f"three_cnots_{_b}", three_cnots, _basis),
            family="gallery",
            mechanisms=frozenset({f"space:merge_split:{_MERGE[_b]}"}),
            expected=READY,
        )
    )
    register(
        GadgetSpec(
            id=f"steane_{_b}",
            build=partial(_named, f"steane_{_b}", steane_encoding, _basis),
            family="gallery",
            mechanisms=frozenset({f"space:merge_split:{_MERGE[_b]}"}),
            expected=READY,
        )
    )

# Open-port variants: ``prepare_batch`` fills the ports; the registry only expects that the
# filled graphs compile, so the status is that of the filled graphs.
for _id, _factory in (
    ("cnot_open", cnot),
    ("move_rotation_open", move_rotation),
    ("three_cnots_open", three_cnots),
    ("steane_open", steane_encoding),
):
    register(
        GadgetSpec(
            id=_id,
            build=partial(_named, _id, _factory, None),
            family="gallery_open",
            mechanisms=frozenset({"port:fill"}),
            expected=READY,
            notes="Open ports: the batch fills them (one unit per filling scheme).",
        )
    )

register(
    GadgetSpec(
        id="cz_open",
        build=partial(_named_cz, "cz_open"),
        family="gallery_open",
        mechanisms=frozenset({"port:fill"}),
        expected=COMPILE_FAILED,
        blocked_by=("https://github.com/tqec/tqec/issues/838",),
        notes=(
            "Open ports. Both fillings raise NotImplementedError: the OZXH pipe is an x-direction "
            "spatial Hadamard on a spatial cube, which the fixed bulk convention does not "
            "implement yet (_get_left_right_spatial_hadamard_cube_arm_plaquettes)."
        ),
    )
)
