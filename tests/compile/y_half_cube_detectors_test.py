"""Detectors that the native detector path finds for the fixed-bulk Y half cube.

The Y half cube is built from a transition (SWITCH) round, ``REPEAT``ed padding (PAD) rounds and
a readout (FINAL) round. The detectors of a ``REPEAT`` body are those of its first iteration, so
the first PAD round must not be part of the repetition. This only shows from ``k = 2``.
"""

import pytest

from tqec.compile.blocks.layers.composed.repeated import RepeatedLayer
from tqec.compile.blocks.layers.composed.sequenced import SequencedLayers
from tqec.compile.compile import compile_block_graph
from tqec.compile.convention import FIXED_BULK_CONVENTION
from tqec.compile.specs.base import YHalfCubeSpec
from tqec.compile.specs.library.generators.y_basis_fixed_bulk import get_y_half_cube_block
from tqec.computation.block_graph import BlockGraph
from tqec.gallery.memory import memory
from tqec.gallery.s_gate_teleportation import s_gate_teleportation
from tqec.utils.enums import Basis, PauliBasis
from tqec.utils.noise_model import NoiseModel
from tqec.utils.position import Position3D
from tqec.utils.scale import LinearFunction


def _y_memory() -> BlockGraph:
    return memory(PauliBasis.Y)


def _y_above_two_cubes() -> BlockGraph:
    """Two ``XZX`` cubes joined in space, each with a Y half cube on top."""
    g = BlockGraph("Y half cubes above two joined cubes")
    bottom = [g.add_cube(Position3D(x, 0, 0), "XZX") for x in range(2)]
    top = [g.add_cube(Position3D(x, 0, 1), "Y") for x in range(2)]
    g.add_pipe(bottom[0], bottom[1], "OZX")
    for b, t in zip(bottom, top):
        g.add_pipe(b, t, "XZO")
    return g


def _s_gate(basis: PauliBasis) -> BlockGraph:
    return s_gate_teleportation(basis)


GRAPHS = {
    "y_memory": _y_memory,
    "s_gate_x": lambda: _s_gate(PauliBasis.X),
    "s_gate_z": lambda: _s_gate(PauliBasis.Z),
    "y_above_two_cubes": _y_above_two_cubes,
}
# Where a Y half cube is joined to an ``XZO`` pipe, tqecd 0.2.1 misses the weight-3 detectors on
# the SWITCH round's domain wall, which leaves a weight-1 logical error at every k. tqecd PR #74
# (https://github.com/tqec/tqecd/pull/74) finds them and gives full distance; until tqec requires
# a tqecd release with it, only determinism is asserted for these gadgets.
FULL_DISTANCE = {"y_memory", "s_gate_z"}


def test_measurement_half_cube_emits_first_pad_round_outside_the_repetition() -> None:
    spec = YHalfCubeSpec(
        horizontal_boundary_basis=Basis.Z,
        initialization=False,
    )
    block = get_y_half_cube_block(spec, pad_repetitions=LinearFunction(2, -1))
    _, pad, _ = block.layer_sequence
    assert isinstance(pad, SequencedLayers)
    _, repeated_pad = pad.layer_sequence
    assert isinstance(repeated_pad, RepeatedLayer)
    assert repeated_pad.repetitions == LinearFunction(2, -2)
    # The temporal schedule is the one of an ordinary cube, so that blocks can be merged.
    assert [layer.scalable_timesteps for layer in block.layer_sequence] == [
        LinearFunction(0, 1),
        LinearFunction(2, -1),
        LinearFunction(0, 1),
    ]


def test_constant_pad_repetitions_below_one_are_rejected() -> None:
    spec = YHalfCubeSpec(horizontal_boundary_basis=Basis.Z, initialization=False)
    with pytest.raises(ValueError, match="at least one PAD round"):
        get_y_half_cube_block(spec, pad_repetitions=LinearFunction(0, 0))


@pytest.mark.slow
@pytest.mark.timeout(0)
@pytest.mark.parametrize("k", [2])
@pytest.mark.parametrize("name", list(GRAPHS))
def test_native_detectors_are_deterministic_with_full_distance(name: str, k: int) -> None:
    graph = GRAPHS[name]()
    compiled = compile_block_graph(graph, FIXED_BULK_CONVENTION)
    circuit = compiled.generate_stim_circuit(k, database_path=None)
    # Raises a ValueError if any detector is non-deterministic.
    circuit.detector_error_model()

    if name not in FULL_DISTANCE:
        return
    noisy = NoiseModel.uniform_depolarizing(1e-3).noisy_circuit(circuit)
    error = noisy.shortest_graphlike_error(
        ignore_ungraphlike_errors=False, canonicalize_circuit_errors=True
    )
    assert len(error) == 2 * k + 1
