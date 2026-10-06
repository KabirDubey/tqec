"""Junction gadgets: spatial cubes with several arms and the multi-cube H and I shapes.

The graphs are those of ``tests/compile/compile_test.py:326-760``. The four three-arm shapes
are named after the side the arms leave from: ``left`` is ``⊣`` (arms ``+y``, ``-y``, ``-x``),
``up`` is ``T`` (``+y``, ``-x``, ``+x``), ``down`` is ``⊥`` (``-y``, ``-x``, ``+x``) and
``right`` is ``⊢`` (``+y``, ``-y``, ``+x``). The six-cube shapes are ``h`` (two parallel rows
joined along ``x``) and ``ii`` (the ``工`` shape).
"""

from functools import partial

from tqec.benchmarks.gadgets._common import READY, build, flip_basis, pos
from tqec.benchmarks.gadgets.spec import GadgetSpec, register
from tqec.computation.block_graph import BlockGraph
from tqec.utils.position import Position3D

_ARMS: dict[str, tuple[tuple[int, int], ...]] = {
    "left": ((0, 1), (0, -1), (-1, 0)),
    "up": ((0, 1), (-1, 0), (1, 0)),
    "down": ((0, -1), (-1, 0), (1, 0)),
    "right": ((0, 1), (0, -1), (1, 0)),
}


def _maybe_flip(kind: str, basis: str) -> str:
    return flip_basis(kind) if basis == "x" else kind


def _l_junction(name: str, basis: str, time_pipe: int) -> BlockGraph:
    kinds = [_maybe_flip(k, basis) for k in ("ZXX", "ZZX", "XZX")]
    cubes = [
        (pos(0, 0, 0), kinds[0]),
        (pos(0, 1, 0), kinds[1]),
        (pos(1, 1, 0), kinds[2]),
    ]
    pipes = [(pos(0, 0, 0), pos(0, 1, 0)), (pos(0, 1, 0), pos(1, 1, 0))]
    if time_pipe:
        cubes.append((pos(1, 1, time_pipe), kinds[2]))
        pipes.append((pos(1, 1, 0), pos(1, 1, time_pipe)))
    return build(name, cubes, pipes)


def _junction3(name: str, shape: str, endpoints: str, basis: str) -> BlockGraph:
    if endpoints == "spatial":
        centre_kind = "ZZX" if basis == "z" else "XXZ"
        arm_kinds = (centre_kind, centre_kind)
    else:
        centre_kind = _maybe_flip("ZZX", basis)
        arm_kinds = (_maybe_flip("ZXX", basis), _maybe_flip("XZX", basis))
    cubes = [(pos(0, 0, 0), centre_kind)]
    for dx, dy in _ARMS[shape]:
        cubes.append((pos(dx, dy, 0), arm_kinds[0] if dx == 0 else arm_kinds[1]))
    return build(name, cubes, [(pos(0, 0, 0), cube[0]) for cube in cubes[1:]])


def _six_cubes(name: str, shape: str, centre_kind: str, endpoint_kind: str) -> BlockGraph:
    """Build the H or 工 shape: two spatial cubes with three neighbours each, joined by one pipe."""
    if shape == "h":
        layout = [
            (pos(0, 0, 0), centre_kind),
            (pos(0, 1, 0), endpoint_kind),
            (pos(0, -1, 0), endpoint_kind),
            (pos(1, 0, 0), centre_kind),
            (pos(1, -1, 0), endpoint_kind),
            (pos(1, 1, 0), endpoint_kind),
        ]
    else:
        layout = [
            (pos(0, 0, 0), centre_kind),
            (pos(-1, 0, 0), endpoint_kind),
            (pos(1, 0, 0), endpoint_kind),
            (pos(0, 1, 0), centre_kind),
            (pos(-1, 1, 0), endpoint_kind),
            (pos(1, 1, 0), endpoint_kind),
        ]
    nodes: list[Position3D] = [p for p, _ in layout]
    edges = [(0, 1), (0, 2), (0, 3), (3, 4), (3, 5)]
    return build(name, layout, [(nodes[a], nodes[b]) for a, b in edges])


def _six_stability(name: str, shape: str, kind: str) -> BlockGraph:
    return _six_cubes(name, shape, kind, kind)


def _six_regular(name: str, shape: str, basis: str) -> BlockGraph:
    endpoint = _maybe_flip("ZXX" if shape == "h" else "XZX", basis)
    return _six_cubes(name, shape, _maybe_flip("ZZX", basis), endpoint)


def _stability_i3(name: str, kind: str, axis: str) -> BlockGraph:
    step = (1, 0, 0) if axis == "x" else (0, 1, 0)
    cubes = [(pos(i * step[0], i * step[1], 0), kind) for i in range(3)]
    return build(name, cubes, [(cubes[0][0], cubes[1][0]), (cubes[1][0], cubes[2][0])])


# --- L junction (compile_test.py:326-340, 365-385) -------------------------------------------
for _basis in ("z", "x"):
    register(
        GadgetSpec(
            id=f"junction_l_{'zzx' if _basis == 'z' else 'xxz'}",
            build=partial(
                _l_junction, f"junction_l_{'zzx' if _basis == 'z' else 'xxz'}", _basis, 0
            ),
            family="junction",
            mechanisms=frozenset({f"space:spatial_cube:{_basis}"}),
            expected=READY,
            notes=(
                "The X-type mirror has no compile test on main; the status and distance were "
                "observed on brainlab (job Oct0526-032923-gadgets-registry-slow2)."
                if _basis == "x"
                else ""
            ),
        )
    )

for _name, _step in (("future", 1), ("past", -1)):
    register(
        GadgetSpec(
            id=f"junction_l_timepipe_{_name}",
            build=partial(_l_junction, f"junction_l_timepipe_{_name}", "z", _step),
            family="junction",
            mechanisms=frozenset({"time:junction:time_pipe", "space:spatial_cube:z"}),
            expected=READY,
        )
    )

# --- three-arm junctions (compile_test.py:551-637) -------------------------------------------
for _shape in _ARMS:
    for _endpoints in ("spatial", "regular"):
        for _basis in ("z", "x"):
            _id = f"junction3_{_shape}_{_endpoints}_{_basis}"
            register(
                GadgetSpec(
                    id=_id,
                    build=partial(_junction3, _id, _shape, _endpoints, _basis),
                    family="junction",
                    mechanisms=frozenset({f"space:junction3:{_endpoints}_endpoints:{_basis}"}),
                    expected=READY,
                )
            )

# --- six-cube shapes (compile_test.py:660-763) -----------------------------------------------
for _shape in ("h", "ii"):
    for _kind in ("zzx", "xxz"):
        _id = f"junction_{_shape}_stability_{_kind}"
        register(
            GadgetSpec(
                id=_id,
                build=partial(_six_stability, _id, _shape, _kind.upper()),
                family="junction",
                mechanisms=frozenset(
                    {f"space:junction_h:stability:{_kind[0]}", f"time:stability:{_kind[0]}"}
                ),
                expected=READY,
            )
        )
    for _basis in ("z", "x"):
        _id = f"junction_{_shape}_regular_{_basis}"
        _h_boundary = _shape == "h"
        register(
            GadgetSpec(
                id=_id,
                build=partial(_six_regular, _id, _shape, _basis),
                family="junction",
                mechanisms=frozenset({f"space:junction_h:regular:{_basis}"}),
                expected=READY,
            )
        )

# --- I-shape stability (compile_test.py:639-657) ---------------------------------------------
for _axis in ("x", "y"):
    for _kind in ("zzx", "xxz"):
        _id = f"stability_i3_{_axis}_{_kind}"
        register(
            GadgetSpec(
                id=_id,
                build=partial(_stability_i3, _id, _kind.upper(), _axis),
                family="junction",
                mechanisms=frozenset({f"time:stability:{_kind[0]}"}),
                expected=READY,
            )
        )
