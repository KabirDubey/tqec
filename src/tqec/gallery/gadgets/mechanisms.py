"""Closed vocabularies of the gadget registry: error-mechanism tags and unit statuses.

A *mechanism* is a minimum-weight fault path through one kind of block configuration. Every
:class:`~tqec.gallery.gadgets.spec.GadgetSpec` names the mechanisms it is meant to cover with
tags from :data:`MECHANISMS`. A tag outside the set is rejected when the spec is built, so
the vocabulary cannot drift silently.

Tags (``{a,b}`` stands for one tag per alternative):

- ``space:regular:{xchain,zchain}``: chain across a regular cube between same-basis walls
- ``space:spatial_cube:{z,x}``: chain across a spatial cube between arms
- ``space:junction3:spatial_endpoints:{z,x}``: 3-arm junction, spatial-cube arms, horizontal surface
- ``space:junction3:regular_endpoints:{z,x}``: 3-arm junction, regular-cube arms, vertical surfaces
- ``space:junction_h:{stability,regular}:{z,x}``: H and I-shaped six-cube junctions
- ``space:pipe:{x,y}``: chain across the merged patch of a spatial pipe
- ``space:hadamard:{x,y}:vertical``: spatial Hadamard wall, memory-type surface
- ``space:hadamard:{x,y}:horizontal:{z,x}``: spatial Hadamard wall, stability-type surface
- ``space:corner:spacetime:{z,x}``: space pipe followed by a time pipe
- ``space:rotation:move:{z,x}``: boundary rotation by movement
- ``space:merge_split:{zx,xz}``: lattice-surgery merge and split
- ``space:y:top:{x,z}``: Y cubes on a temporal pipe with X or Z along y (patch orientation)
- ``space:y:twist``: chain through the Y half cube diagonal wall
- ``time:memory:{x,z}``: timelike chain through a regular memory cube
- ``time:stability:{z,x}``: measurement chain through a stability patch
- ``time:pipe:{z,x}``: chain through the joining round of a temporal pipe
- ``time:hadamard:{z,x}``: chain through a temporal Hadamard transition
- ``time:junction:time_pipe``: temporal pipe at a spatial cube with spatial pipes
- ``time:boundary:{init,meas}:{x,z}``: faults in the first and last rounds
- ``time:y:{init,meas}``: Y half cube below (init) or above (meas)
- ``time:y:hadamard_pipe:{zxoh,xzoh}``: Y through a Hadamard temporal pipe
- ``time:y:above:{xzx,zxx}``: Y on each regular wall layout
- ``time:y:{junction_arm,after_pipes}``: Y on a junction arm, Y on a cube with pipes
- ``time:conditional:{zx,y}``: conditional measurement branches
- ``port:fill``: not a fault path: port filling of an open graph

- ``space:patch_rotation:{temporal,spatial}:{z,x}``: patch rotation block, temporally or
  spatially aligned (pending, see :data:`PENDING`)

Tags of blocks tqec cannot compile yet are predeclared and listed in :data:`PENDING` with the
issue that blocks them, so a family module can use them without editing this file.
"""

from collections.abc import Mapping
from itertools import product
from types import MappingProxyType

_BASES = ("x", "z")


PENDING: Mapping[str, str] = MappingProxyType(
    {
        f"space:patch_rotation:{alignment}:{b}": "https://github.com/tqec/tqec/issues/1012"
        for alignment, b in product(("temporal", "spatial"), ("z", "x"))
    }
)
"""Tags no registered gadget needs to cover yet, mapped to the issue that blocks them.

The coverage test requires a spec for every tag in :data:`MECHANISMS` except these.
"""


def _expand() -> frozenset[str]:
    tags: set[str] = set()
    tags.update(f"space:regular:{b}chain" for b in _BASES)
    tags.update(f"space:spatial_cube:{b}" for b in _BASES)
    tags.update(
        f"space:junction3:{e}_endpoints:{b}" for e, b in product(("spatial", "regular"), _BASES)
    )
    tags.update(
        f"space:junction_h:{kind}:{b}" for kind, b in product(("stability", "regular"), _BASES)
    )
    tags.update(f"space:pipe:{d}" for d in ("x", "y"))
    tags.update(f"space:hadamard:{d}:vertical" for d in ("x", "y"))
    tags.update(f"space:hadamard:{d}:horizontal:{b}" for d, b in product(("x", "y"), ("z", "x")))
    tags.update(f"space:corner:spacetime:{b}" for b in ("z", "x"))
    tags.update(f"space:rotation:move:{b}" for b in ("z", "x"))
    tags.update(f"space:merge_split:{k}" for k in ("zx", "xz"))
    tags.add("space:y:twist")
    tags.update(f"space:y:top:{b}" for b in ("x", "z"))
    tags.update(f"time:memory:{b}" for b in _BASES)
    tags.update(f"time:stability:{b}" for b in ("z", "x"))
    tags.update(f"time:pipe:{b}" for b in ("z", "x"))
    tags.update(f"time:hadamard:{b}" for b in ("z", "x"))
    tags.add("time:junction:time_pipe")
    tags.update(f"time:boundary:{w}:{b}" for w, b in product(("init", "meas"), _BASES))
    tags.update(("time:y:init", "time:y:meas"))
    tags.update(f"time:y:hadamard_pipe:{k}" for k in ("zxoh", "xzoh"))
    tags.update(f"time:y:above:{k}" for k in ("xzx", "zxx"))
    tags.update(("time:y:junction_arm", "time:y:after_pipes"))
    tags.update(("time:conditional:zx", "time:conditional:y"))
    tags.add("port:fill")
    tags.update(PENDING)
    return frozenset(tags)


MECHANISMS: frozenset[str] = _expand()
"""The closed set of error-mechanism tags a gadget may carry."""

STATUSES: frozenset[str] = frozenset(
    {
        "import_failed",
        "invalid_graph",
        "observable_failed",
        "compile_failed",
        "circuit_failed",
        "ready",
        "completed",
        "simulation_failed",
        "skipped",
    }
)
"""Unit statuses, spelled as the ``tqec.orchestration`` ``UnitStatus`` values.

The registry is independent of the orchestration package, so it repeats the literals. A registry
spec only expects the statuses a gadget can reach before simulation; ``completed`` and
``simulation_failed`` are run outcomes, accepted here so a run manifest compares by string.
"""

CONVENTIONS: tuple[str, ...] = ("fixed_bulk",)
"""Names of the conventions a spec states expectations for.

Only ``fixed_bulk`` is in scope, by owner decision on Oct0526; ``fixed_boundary`` is not covered."""
