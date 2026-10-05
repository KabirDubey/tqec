"""Y half cube gadgets, shipped as ``.bgraph`` files.

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

_NOTES = {
    "g04": "Also the graph of the earlier g05 (same cubes and pipes).",
    "s_gate_y": (
        "The generator on kd/y-half-cube-gen refuses a Y-input S gate; this file compiled there "
        "with tqecd #74 (UNVERIFIED on main)."
    ),
}

for _name, _tags in _TAGS.items():
    register(
        GadgetSpec(
            id=f"y_half_cube_{_name}",
            build=lambda _name=_name: DATA_DIR / f"y_half_cube_{_name}.bgraph",
            family="y_half_cube",
            mechanisms=_tags | {"space:y:twist"},
            # Y raises NotImplementedError on main (fixed_bulk.py:88-90).
            expected=COMPILE_FAILED,
            blocked_by=_BLOCKED_BY,
            notes=_NOTES.get(_name, ""),
        )
    )
