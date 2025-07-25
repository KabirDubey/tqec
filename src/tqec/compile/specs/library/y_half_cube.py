"""Y Half Cube implementation for the fixed bulk convention.

This module implements Y half cube blocks using raw circuit layers,
based on the approach from Gidney 2024.
"""

import stim
from typing import Union
from tqec.compile.blocks.block import Block
from tqec.compile.blocks.layers.atomic.raw import RawCircuitLayer
from tqec.compile.blocks.layers.composed.repeated import RepeatedLayer
from tqec.compile.specs.base import CubeSpec
from tqec.circuit.schedule.circuit import ScheduledCircuit
from tqec.computation.cube import YHalfCube
from tqec.computation.block_graph import BlockGraph
from tqec.utils.scale import LinearFunction, PhysicalQubitScalable2D
from tqec.utils.position import Direction3D
from tqec.utils.exceptions import TQECError


def _parse_initialization_flag(flag: Union[str, bool]) -> bool:
    """Parse initialization flag accepting multiple spellings.

    Args:
        flag: Can be boolean or string with various spellings:
            - True/False
            - "initialization"/"initialisation"/"init" -> True
            - "measurement"/"measure"/"meas" -> False

    Returns:
        Boolean indicating if this is initialization (True) or measurement (False)

    Raises:
        ValueError: if string flag is not recognized
    """
    if isinstance(flag, bool):
        return flag

    if isinstance(flag, str):
        flag_lower = flag.lower().strip()

        # Initialization variants
        init_variants = {
            "initialization", "initialisation", "init",
        }

        # Measurement variants
        measure_variants = {
            "measurement", "measure", "meas",
        }

        if flag_lower in init_variants:
            return True
        elif flag_lower in measure_variants:
            return False
        else:
            raise ValueError(f"Unrecognized initialization flag: {flag}. "
                           f"Use one of {init_variants | measure_variants}")

    raise TypeError(f"Flag must be bool or str, got {type(flag)}")


def determine_y_half_cube_mode(cube, graph: BlockGraph) -> bool:
    """Determine if Y half cube should be initialization or measurement based on pipe direction.

    Args:
        cube: The Y half cube from the block graph
        graph: The block graph containing the cube

    Returns:
        True if initialization (has pipe in +Z direction)
        False if measurement (has pipe in -Z direction)

    Raises:
        TQECError: if cube doesn't have exactly one temporal pipe or has wrong pipe direction
    """
    assert isinstance(cube.kind, YHalfCube)

    # Get all pipes connected to this cube
    connected_pipes = list(graph.pipes_at(cube.position))

    # Filter for temporal pipes (Z direction)
    temporal_pipes = [pipe for pipe in connected_pipes if pipe.direction == Direction3D.Z]

    if len(temporal_pipes) != 1:
        raise TQECError(f"Y Half Cube at {cube.position} must have exactly one temporal pipe, "
                       f"found {len(temporal_pipes)} temporal pipes")

    pipe = temporal_pipes[0]

    # Determine direction: if this cube is the "u" (source) of the pipe,
    # it's initialization (pipe goes +Z direction from this cube)
    # if this cube is the "v" (target) of the pipe,
    # it's measurement (pipe comes from -Z direction to this cube)

    if pipe.u == cube:
        # This cube is the source, so pipe goes +Z -> initialization
        return True
    elif pipe.v == cube:
        # This cube is the target, so pipe comes from -Z -> measurement
        return False
    else:
        raise TQECError(f"Y Half Cube at {cube.position} is not connected to temporal pipe {pipe}")


def create_y_half_cube_block(spec: CubeSpec, mode: Union[str, bool]) -> Block:
    """Create a Y half cube block using raw circuit layers.

    Args:
        spec: specification of the Y half cube
        mode: initialization/measurement mode. Accepts:
            - True/False
            - "initialization"/"initialisation"/"init" -> initialization mode
            - "measurement"/"measure"/"final" -> measurement mode

    Returns:
        Block implementing the Y half cube with SequencedLayers

    Raises:
        AssertionError: if spec does not represent a Y half cube
        ValueError: if mode string is not recognized
    """
    assert isinstance(spec.kind, YHalfCube)
    is_initialization = _parse_initialization_flag(mode)

    # Create the three types of layers following Gidney's approach
    y_final_layer = _create_y_final_layer(spec)
    y_padding_layer = _create_y_padding_layer(spec)
    y_switch_layer = _create_y_switch_layer(spec)

    if is_initialization:
        # Initialization order: y_final_layer.inverted(), y_padding_layer.inverted(), y_switch_layer.inverted()
        layers = [
            _invert_layer(y_final_layer),
            _invert_layer(y_padding_layer),
            _invert_layer(y_switch_layer)
        ]
    else:
        # Measurement order: y_switch_layer, y_padding_layer, y_final_layer
        layers = [
            y_switch_layer,
            y_padding_layer,
            y_final_layer
        ]

    return Block(layers)


def _create_y_final_layer(spec: CubeSpec):
    """Create the Y final layer (measurement/reset layer).

    This corresponds to the final_round in Gidney's Y memory implementation.
    """
    raise NotImplementedError("Y final layer creation not implemented yet")


def _create_y_padding_layer(spec: CubeSpec):
    """Create the Y padding layer (boundary rounds for stabilization).

    This corresponds to the boundary_round in Gidney's Y memory implementation
    with repetitions for d/2 boundary rounds.
    """
    raise NotImplementedError("Y padding layer creation not implemented yet")


def _create_y_switch_layer(spec: CubeSpec):
    """Create the Y switch/transition layer (Y basis ↔ Z basis transition).

    This corresponds to the qubit_to_boundary_round in Gidney's Y memory implementation
    for the single transition round between Y and Z bases.
    """
    raise NotImplementedError("Y switch layer creation not implemented yet")


def _invert_layer(layer):
    """Invert a layer using Gidney's time-reversal approach.

    This should convert measurement operations to initialization operations
    and vice versa, following the .inverted() pattern from Gidney's chunks.
    """
    raise NotImplementedError("Layer inversion not implemented yet")
