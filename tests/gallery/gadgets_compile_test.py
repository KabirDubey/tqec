"""Compile every registered gadget under the fixed bulk convention and check its facts.

Slow: run with ``pytest -m slow tests/gallery/gadgets_compile_test.py``.
"""

import pytest

from tqec.compile.compile import compile_block_graph
from tqec.compile.convention import FIXED_BULK_CONVENTION
from tqec.computation.block_graph import BlockGraph
from tqec.gallery.gadgets import GadgetSpec, build_graph, iter_gadgets
from tqec.utils.noise_model import NoiseModel

K = 1
_CONVENTION = "fixed_bulk"


def _observed(graph: BlockGraph, k: int) -> tuple[str, int | None]:
    """Return the status string and the shortest graphlike error length for ``graph``."""
    try:
        surfaces = graph.find_correlation_surfaces()
    except NotImplementedError:
        return "observable_failed", None
    if not surfaces:
        return "observable_failed", None
    try:
        compiled = compile_block_graph(graph, FIXED_BULK_CONVENTION, surfaces)
    except Exception:
        return "compile_failed", None
    try:
        circuit = compiled.to_layer_tree().generate_circuit(k)
        noisy = NoiseModel.uniform_depolarizing(0.001).noisy_circuit(circuit)
        error = noisy.shortest_graphlike_error(
            ignore_ungraphlike_errors=False, canonicalize_circuit_errors=True
        )
    except Exception:
        return "circuit_failed", None
    return "ready", len(error)


@pytest.mark.slow
@pytest.mark.timeout(1800)
@pytest.mark.parametrize("spec", iter_gadgets(), ids=lambda s: s.id)
def test_gadget_status_and_distance_fixed_bulk(spec: GadgetSpec) -> None:
    graph = build_graph(spec)
    graphs = [graph]
    if graph.num_ports > 0:
        graphs = [filled.graph for filled in graph.fill_ports_for_minimal_simulation()]
    results = [_observed(g, K) for g in graphs]
    status = next((s for s, _ in results if s != "ready"), "ready")
    assert status == spec.expected[_CONVENTION]
    if status == "ready":
        assert all(d == spec.distance(K) for _, d in results)
