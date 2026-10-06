"""Gadgets with a conditional measurement cube (issue #829)."""

from functools import partial

from tqec.benchmarks.gadgets._common import build, pos
from tqec.benchmarks.gadgets.spec import GadgetSpec, register
from tqec.computation.block_graph import BlockGraph
from tqec.computation.correlation import CorrelationSurface, ZXEdge, ZXNode
from tqec.utils.enums import Basis

# ``find_correlation_surfaces`` raises NotImplementedError for a conditional cube
# (``interop/pyzx/utils.py:71``), so the observables of these gadgets cannot be enumerated yet.
_EXPECTED = {"fixed_bulk": "observable_failed"}


def _conditional_column(name: str, base: str, final_kind: str) -> BlockGraph:
    """Build a memory column with a merged ancilla, measured in a basis chosen by the merge outcome.

    The condition is the parity of the first-round stabiliser measurements in the merged region.
    """
    a0, a1, b1, c = pos(0, 0, 0), pos(0, 0, 1), pos(1, 0, 1), pos(1, 0, 2)
    graph = build(
        name,
        [(a0, base), (a1, base), (b1, base)],
        [(a0, a1), (a1, b1)],
    )
    condition = CorrelationSurface(frozenset({ZXEdge(ZXNode(a1, Basis.X), ZXNode(b1, Basis.X))}))
    graph.add_cube(c, final_kind, condition=condition)
    graph.add_pipe(b1, c)
    return graph


register(
    GadgetSpec(
        id="cond_meas_zxz_zxx",
        build=partial(_conditional_column, "cond_meas_zxz_zxx", "ZXZ", "ZXZ_ZXX"),
        family="conditional",
        mechanisms=frozenset({"time:conditional:zx"}),
        expected=_EXPECTED,
        notes=(
            "The ConditionalCubeKind docstring says ZX-branch conditionals compile, but the "
            "observables cannot be enumerated yet (interop/pyzx/utils.py:71)."
        ),
    )
)
register(
    GadgetSpec(
        id="cond_meas_xzx_y",
        build=partial(_conditional_column, "cond_meas_xzx_y", "XZX", "XZX_Y"),
        family="conditional",
        mechanisms=frozenset({"time:conditional:y"}),
        expected=_EXPECTED,
        blocked_by=("https://github.com/tqec/tqec/pull/719",),
    )
)
