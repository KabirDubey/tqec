"""Y half cube gadgets, shipped as ``.bgraph`` files.

Every gadget carries ``space:y:top:x`` and/or ``space:y:top:z``: the basis along y of the temporal
pipe that touches its Y cubes ("X top" is a ``ZXO`` pipe, "Z top" an ``XZO`` pipe). Gadgets whose
Y cubes used one orientation have a twin, the same graph rotated 90 degrees about z (x and y
swapped, first two letters of each kind swapped), with id suffix ``_xtop`` or ``_ztop`` (the new
orientation). The twins are new files; the originals are untouched.

The files are the evidence set of the Y half cube work (a 48/48 compile and distance run).
They stay byte-identical; Python builders can replace them later with a test that a builder
equals its file. ``g05`` of that set holds the same cubes and pipes as ``g04`` (same
coordinates, different order), so it is registered once, as ``y_half_cube_g04``.
"""

from pathlib import Path

from tqec.gallery.gadgets._common import COMPILE_FAILED
from tqec.gallery.gadgets.spec import GadgetSpec, register

DATA_DIR = Path(__file__).resolve().parent / "data" / "y_half_cube"
"""Directory of the ``.bgraph`` files."""

_BLOCKED_BY = ("https://github.com/tqec/tqec/pull/719", "kd/y-half-cube-gen")
_TQECD_74 = "https://github.com/tqec/tqecd/pull/74"
_NEEDS_TQECD_74 = frozenset(
    {
        "g01",
        "g02",
        "g04",
        "g06",
        "g08",
        "g09",
        "g10",
        "g11_ztop",
        "g12_ztop",
        "s_gate_x",
        "s_gate_y",
        "ymem_ztop",
    }
)
"""Gadgets (by name after ``y_half_cube_``) with distance 1 at k=1 and k=2 under tqecd 0.2.1.

tqecd 0.2.1 merges anticommuting flows with a non-minimal commuting cover, which drops detectors
of the Y SWITCH round; tqecd PR #74 returns the minimal cover. On ``kd/y-half-cube-gen``
(5f86d3039) all 24 Y gadgets reach 2k+1 at k=1 and k=2 with #74; these 12 are 1 with 0.2.1.
"""
_TQECD_74_NOTE = "Distance 1 with tqecd 0.2.1 (non-minimal commuting cover); 2k+1 with tqecd #74."

_TAGS: dict[str, frozenset[str]] = {
    "g01": frozenset({"time:y:meas", "time:y:hadamard_pipe:zxoh", "time:y:junction_arm"}),
    "g02": frozenset({"time:y:meas", "time:y:junction_arm"}),
    "g03": frozenset({"time:y:meas", "time:y:junction_arm"}),
    "g04": frozenset({"time:y:init", "time:y:meas", "time:y:junction_arm"}),
    "g06": frozenset({"time:y:meas", "time:y:hadamard_pipe:xzoh", "time:y:junction_arm"}),
    "g07": frozenset({"time:y:meas", "time:y:hadamard_pipe:xzoh", "time:y:junction_arm"}),
    "g08": frozenset(
        {
            "time:y:meas",
            "time:y:hadamard_pipe:zxoh",
            "time:y:hadamard_pipe:xzoh",
            "time:y:junction_arm",
        }
    ),
    "g09": frozenset({"time:y:meas"}),
    "g10": frozenset({"time:y:meas", "time:y:above:xzx"}),
    "g11": frozenset({"time:y:meas", "time:y:above:zxx"}),
    "g12": frozenset({"time:y:meas"}),
    "s_gate_x": frozenset({"time:y:meas", "time:y:after_pipes"}),
    "s_gate_y": frozenset({"time:y:init", "time:y:meas"}),
    "s_gate_z": frozenset({"time:y:meas", "time:y:after_pipes"}),
    "ymem": frozenset({"time:y:init", "time:y:meas"}),
}

_TOP_X = frozenset({"ymem", "g03", "g11", "g12"})
_TOP_Z = frozenset({"g09", "g10", "s_gate_x", "s_gate_y", "s_gate_z"})
_TOP_BOTH = frozenset({"g01", "g02", "g04", "g06", "g07", "g08"})
assert _TOP_X | _TOP_Z | _TOP_BOTH == set(_TAGS)

_TWINS: dict[str, str] = {name: "z" for name in _TOP_X} | {name: "x" for name in _TOP_Z}
"""Gadget name -> orientation of its rotated twin."""

_NOTES = {
    "g04": "Also the graph of the earlier g05 (same cubes and pipes).",
    "s_gate_y": (
        "The generator on kd/y-half-cube-gen refuses a Y-input S gate; this file compiled there "
        "with tqecd #74 (UNVERIFIED on main)."
    ),
}


def _top_tags(top: frozenset[str]) -> frozenset[str]:
    return frozenset(f"space:y:top:{t}" for t in top)


def _register(gadget_id: str, file_name: str, tags: frozenset[str], notes: str) -> None:
    name = gadget_id.removeprefix("y_half_cube_")
    blocked_by = _BLOCKED_BY
    if name in _NEEDS_TQECD_74:
        blocked_by += (_TQECD_74,)
        notes = f"{notes} {_TQECD_74_NOTE}".strip()
    register(
        GadgetSpec(
            id=gadget_id,
            build=lambda: DATA_DIR / file_name,
            family="y_half_cube",
            mechanisms=tags | {"space:y:twist"},
            # Y raises NotImplementedError on main (fixed_bulk.py:88-90).
            expected=COMPILE_FAILED,
            blocked_by=blocked_by,
            notes=notes,
        )
    )


for _name, _tags in _TAGS.items():
    _orientation = {"x", "z"} if _name in _TOP_BOTH else {"x"} if _name in _TOP_X else {"z"}
    _register(
        f"y_half_cube_{_name}",
        f"y_half_cube_{_name}.bgraph",
        _tags | _top_tags(frozenset(_orientation)),
        _NOTES.get(_name, ""),
    )
    if _name in _TWINS:
        _t = _TWINS[_name]
        _register(
            f"y_half_cube_{_name}_{_t}top",
            f"y_half_cube_{_name}_{_t}top.bgraph",
            _tags | _top_tags(frozenset({_t})),
            f"Rotated twin of y_half_cube_{_name} (x and y swapped).",
        )
