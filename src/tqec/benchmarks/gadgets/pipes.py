"""Gadgets made of two or three cubes joined by pipes in time, in space, or in both."""

from functools import partial

from tqec.benchmarks.gadgets._common import READY, build, pos
from tqec.benchmarks.gadgets.spec import GadgetSpec, register
from tqec.computation.block_graph import BlockGraph
from tqec.computation.pipe import PipeKind
from tqec.utils.position import Position3D

# Cube kind and spatial pipe kind of the compile tests (``compile_test.py:215-283``); the pipe
# kind has its ``O`` along the direction in which the second cube sits.
_SPACE_PIPES = {"zxz": "OXZ", "zxx": "ZOX", "xzx": "OZX", "xzz": "XOZ"}


def _pair_time(name: str, kind: str) -> BlockGraph:
    return build(
        name,
        [(pos(0, 0, 0), kind.upper()), (pos(0, 0, 1), kind.upper())],
        [(pos(0, 0, 0), pos(0, 0, 1))],
    )


def _space_shift(pipe_kind: str) -> list[int]:
    shift = [0, 0, 0]
    shift[PipeKind.from_str(pipe_kind).direction.value] = 1
    return shift


def _pair_space(name: str, kind: str) -> BlockGraph:
    pipe_kind = _SPACE_PIPES[kind]
    first = pos(-1, 0, 0)
    second = first.shift_by(*_space_shift(pipe_kind))
    return build(name, [(first, kind.upper()), (second, kind.upper())], [(first, second)])


def _corner(name: str, kind: str) -> BlockGraph:
    pipe_kind = _SPACE_PIPES[kind]
    first = pos(1, 2, 0)
    second: Position3D = first.shift_by(*_space_shift(pipe_kind))
    third = second.shift_by(dz=1)
    graph = build(
        name,
        [(first, kind.upper()), (second, kind.upper()), (third, kind.upper())],
        [],
    )
    graph.add_pipe(first, second, pipe_kind)
    graph.add_pipe(second, third, kind[:2].upper() + "O")
    return graph


for _kind in _SPACE_PIPES:
    _basis = _kind[2]
    _axis = "xy"[_SPACE_PIPES[_kind].index("O")]
    register(
        GadgetSpec(
            id=f"pair_time_{_kind}",
            build=partial(_pair_time, f"pair_time_{_kind}", _kind),
            family="pair",
            mechanisms=frozenset({f"time:pipe:{_basis}"}),
            expected=READY,
        )
    )
    register(
        GadgetSpec(
            id=f"pair_space_{_axis}_{_kind}",
            build=partial(_pair_space, f"pair_space_{_axis}_{_kind}", _kind),
            family="pair",
            mechanisms=frozenset({f"space:pipe:{_axis}"}),
            expected=READY,
        )
    )
    register(
        GadgetSpec(
            id=f"corner_spacetime_{_kind}",
            build=partial(_corner, f"corner_spacetime_{_kind}", _kind),
            family="corner",
            mechanisms=frozenset({f"space:corner:spacetime:{_basis}"}),
            expected=READY,
        )
    )
