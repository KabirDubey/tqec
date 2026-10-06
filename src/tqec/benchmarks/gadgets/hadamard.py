"""Gadgets with a Hadamard pipe, in space or in time."""

from functools import partial

from tqec.benchmarks.gadgets._common import COMPILE_FAILED, READY, build, pos
from tqec.benchmarks.gadgets.spec import GadgetSpec, register
from tqec.computation.block_graph import BlockGraph
from tqec.utils.position import Direction3D

# The Hadamard pipe is inferred from the face-basis mismatch of its two cubes
# (``compile_test.py:391-401, 469-497, 505-545``).
_VERTICAL_KINDS = {"x": ("ZXZ", "XZX"), "y": ("XZZ", "ZXX")}
_HORIZONTAL_KINDS = {"z": ("ZZX", "XXZ"), "x": ("XXZ", "ZZX")}
_TIME_KINDS = {"z": ("XZZ", "ZXX"), "x": ("XZX", "ZXZ")}


def _pair(name: str, kinds: tuple[str, str], axis: str, sign: int = 1) -> BlockGraph:
    direction = {"x": Direction3D.X, "y": Direction3D.Y, "z": Direction3D.Z}[axis]
    first = pos(0, 0, 0)
    second = first.shift_in_direction(direction, sign)
    return build(name, [(first, kinds[0]), (second, kinds[1])], [(first, second)])


def _bell(name: str, top_basis: str) -> BlockGraph:
    flipped = "x" if top_basis == "z" else "z"
    return build(
        name,
        [
            (pos(0, 0, 0), "XZZ"),
            (pos(0, 1, 0), "XZZ"),
            (pos(0, 0, 1), "ZX" + top_basis.upper()),
            (pos(0, 1, 1), "XZ" + flipped.upper()),
        ],
        [
            (pos(0, 0, 0), pos(0, 1, 0)),
            (pos(0, 0, 0), pos(0, 0, 1)),
            (pos(0, 1, 0), pos(0, 1, 1)),
        ],
    )


for _axis, _kinds in _VERTICAL_KINDS.items():
    register(
        GadgetSpec(
            id=f"hadamard_space_{_axis}_vertical",
            build=partial(_pair, f"hadamard_space_{_axis}_vertical", _kinds, _axis),
            family="hadamard",
            mechanisms=frozenset({f"space:hadamard:{_axis}:vertical"}),
            # fixed_bulk raises NotImplementedError (compile_test.py:481-490); see #1058, #1057.
            expected=COMPILE_FAILED,
        )
    )

for _axis in ("x", "y"):
    for _basis, _kinds in _HORIZONTAL_KINDS.items():
        register(
            GadgetSpec(
                id=f"hadamard_space_{_axis}_horizontal_{_basis}",
                build=partial(_pair, f"hadamard_space_{_axis}_horizontal_{_basis}", _kinds, _axis),
                family="hadamard",
                mechanisms=frozenset({f"space:hadamard:{_axis}:horizontal:{_basis}"}),
                # fixed_bulk raises along x (compile_test.py:521-547).
                expected={"fixed_bulk": "ready" if _axis == "y" else "compile_failed"},
            )
        )

for _basis, _kinds in _TIME_KINDS.items():
    register(
        GadgetSpec(
            id=f"hadamard_time_{_basis}",
            build=partial(_pair, f"hadamard_time_{_basis}", _kinds, "z"),
            family="hadamard",
            mechanisms=frozenset({f"time:hadamard:{_basis}"}),
            expected=READY,
        )
    )
    register(
        GadgetSpec(
            id=f"hadamard_time_{_basis}_neg",
            build=partial(_pair, f"hadamard_time_{_basis}_neg", _kinds, "z", -1),
            family="hadamard",
            mechanisms=frozenset({f"time:hadamard:{_basis}"}),
            expected=READY,
            notes="Mirror of the same gadget with the Hadamard pipe pointing down in time.",
        )
    )
    register(
        GadgetSpec(
            id=f"bell_hadamard_{_basis}",
            build=partial(_bell, f"bell_hadamard_{_basis}", _basis),
            family="hadamard",
            mechanisms=frozenset({f"time:hadamard:{_basis}"}),
            expected=READY,
        )
    )
