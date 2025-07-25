"""Tests for Y Half Cube implementation."""

import pytest
from tqec.computation.block_graph import BlockGraph
from tqec.computation.cube import YHalfCube
from tqec.computation.pipe import PipeKind
from tqec.utils.position import Position3D
from tqec.compile.specs.library.y_half_cube import (
    determine_y_half_cube_mode,
    _parse_initialization_flag,
    create_y_half_cube_block,
)
from tqec.compile.specs.base import CubeSpec
from tqec.utils.exceptions import TQECError


def test_parse_initialization_flag_string():
    """Test parsing initialization flag with string values."""
    # Initialization variants
    assert _parse_initialization_flag("initialization") is True
    assert _parse_initialization_flag("initialisation") is True
    assert _parse_initialization_flag("init") is True
    assert _parse_initialization_flag("INIT") is True
    assert _parse_initialization_flag("  Init  ") is True

    # Measurement variants
    assert _parse_initialization_flag("measurement") is False
    assert _parse_initialization_flag("measure") is False
    assert _parse_initialization_flag("meas") is False
    assert _parse_initialization_flag("MEAS") is False
    assert _parse_initialization_flag("  Measure  ") is False


def test_parse_initialization_flag_invalid():
    """Test parsing initialization flag with invalid values."""
    with pytest.raises(ValueError, match="Unrecognized initialization flag"):
        _parse_initialization_flag("invalid")

    with pytest.raises(TypeError, match="Flag must be bool or str"):
        _parse_initialization_flag(123)


def test_y_memory_block_graph_creation():
    """Test creating a Y memory block graph as shown in the notebook."""
    # Create a Y memory experiment manually - BlockGraph with a Y half cube
    graph = BlockGraph()

    y_init = graph.add_cube(Position3D(0, 0, 0), YHalfCube())
    y_meas = graph.add_cube(Position3D(0, 0, 1), YHalfCube())

    # Connect them with a timelike pipe (Z direction)
    kind = PipeKind.from_str("zxo")
    pipe = graph.add_pipe(y_init, y_meas, kind)

    # Verify the graph structure
    assert len(graph.cubes) == 2
    assert isinstance(graph.cubes[0].kind, YHalfCube)
    assert isinstance(graph.cubes[1].kind, YHalfCube)
    assert len(graph.pipes) == 1

    # Validate the graph - this should pass
    graph.validate()


def test_determine_y_half_cube_mode():
    """Test determining Y half cube mode based on pipe direction."""
    # Create Y memory block graph
    graph = BlockGraph()
    y_init = graph.add_cube(Position3D(0, 0, 0), YHalfCube())
    y_meas = graph.add_cube(Position3D(0, 0, 1), YHalfCube())
    kind = PipeKind.from_str("zxo")
    pipe = graph.add_pipe(y_init, y_meas, kind)

    # Get the actual cube objects
    y_init_cube = None
    y_meas_cube = None
    for cube in graph.cubes:
        if cube.position == Position3D(0, 0, 0):
            y_init_cube = cube
        elif cube.position == Position3D(0, 0, 1):
            y_meas_cube = cube

    assert y_init_cube is not None
    assert y_meas_cube is not None

    # Test the pipe direction detection
    init_mode = determine_y_half_cube_mode(y_init_cube, graph)
    meas_mode = determine_y_half_cube_mode(y_meas_cube, graph)

    # Y init cube should be initialization (True)
    assert init_mode is True
    # Y meas cube should be measurement (False)
    assert meas_mode is False


def test_determine_y_half_cube_mode_no_temporal_pipes():
    """Test error when Y half cube has no temporal pipes."""
    graph = BlockGraph()
    y_cube = graph.add_cube(Position3D(0, 0, 0), YHalfCube())

    # Get the cube object
    cube_obj = None
    for cube in graph.cubes:
        if cube.position == Position3D(0, 0, 0):
            cube_obj = cube
            break

    assert cube_obj is not None

    with pytest.raises(TQECError, match="must have exactly one temporal pipe"):
        determine_y_half_cube_mode(cube_obj, graph)


def test_create_y_half_cube_block_not_implemented():
    """Test that Y half cube block creation raises NotImplementedError."""
    # Create a minimal spec for testing
    spec = CubeSpec(kind=YHalfCube())

    # Should raise NotImplementedError since the implementation is incomplete
    with pytest.raises(NotImplementedError, match="Y final layer creation not implemented yet"):
        create_y_half_cube_block(spec, True)

    with pytest.raises(NotImplementedError, match="Y final layer creation not implemented yet"):
        create_y_half_cube_block(spec, False)

    with pytest.raises(NotImplementedError, match="Y final layer creation not implemented yet"):
        create_y_half_cube_block(spec, "init")

    with pytest.raises(NotImplementedError, match="Y final layer creation not implemented yet"):
        create_y_half_cube_block(spec, "meas")


def test_create_y_half_cube_block_invalid_spec():
    """Test that Y half cube block creation fails with non-Y cube spec."""
    from tqec.computation.cube import ZXCube
    from tqec.utils.enums import Basis

    # Create a spec that's not a Y half cube
    spec = CubeSpec(kind=ZXCube(x=Basis.X, y=Basis.Z, z=Basis.X))

    with pytest.raises(AssertionError):
        create_y_half_cube_block(spec, True)


def test_y_memory_cube_types():
    """Test that Y memory cubes have correct types."""
    graph = BlockGraph()
    y_init = graph.add_cube(Position3D(0, 0, 0), YHalfCube())
    y_meas = graph.add_cube(Position3D(0, 0, 1), YHalfCube())

    # Verify cube kinds
    for cube in graph.cubes:
        assert isinstance(cube.kind, YHalfCube)
        assert str(cube.kind) == "Y"
        assert type(cube.kind).__name__ == "YHalfCube"
