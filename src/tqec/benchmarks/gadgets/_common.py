"""Helpers shared by the gadget family modules."""

from collections.abc import Mapping, Sequence

from tqec.computation.block_graph import BlockGraph
from tqec.utils.position import Position3D

READY: Mapping[str, str] = {"fixed_bulk": "ready"}
"""``fixed_bulk`` compiles the gadget on ``main``."""

COMPILE_FAILED: Mapping[str, str] = {"fixed_bulk": "compile_failed"}
"""``fixed_bulk`` does not compile the gadget on ``main``."""


def flip_basis(kind: str) -> str:
    """Swap ``X`` and ``Z`` in a cube kind string."""
    return "".join("X" if letter == "Z" else "Z" for letter in kind)


def pos(x: int, y: int, z: int) -> Position3D:
    """Shorthand for :py:class:`~tqec.utils.position.Position3D`."""
    return Position3D(x, y, z)


def build(
    name: str,
    cubes: Sequence[tuple[Position3D, str]],
    pipes: Sequence[tuple[Position3D, Position3D]],
) -> BlockGraph:
    """Build a graph from ``(position, kind)`` cubes and the listed ``(source, sink)`` pipes.

    Pipe kinds are inferred from the cubes at their ends.
    """
    graph = BlockGraph(name)
    for position, kind in cubes:
        graph.add_cube(position, kind)
    for source, sink in pipes:
        graph.add_pipe(source, sink)
    return graph
