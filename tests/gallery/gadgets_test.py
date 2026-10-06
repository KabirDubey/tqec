import json
from pathlib import Path
from typing import Any

import pytest

from tqec.computation.block_graph import BlockGraph
from tqec.gallery.gadgets import (
    CONVENTIONS,
    MECHANISMS,
    PENDING,
    STATUSES,
    GadgetSpec,
    build_graph,
    get,
    iter_gadgets,
    register,
    vend,
)
from tqec.gallery.gadgets.__main__ import main
from tqec.gallery.gadgets.y_half_cube import DATA_DIR
from tqec.utils.exceptions import TQECError

ALL_SPECS = iter_gadgets()


def _spec(**overrides: Any) -> GadgetSpec:
    fields: dict[str, Any] = {
        "id": "x_test",
        "build": lambda: BlockGraph("x"),
        "family": "test",
        "mechanisms": frozenset({"time:memory:z"}),
        "expected": {"fixed_bulk": "ready"},
    }
    fields.update(overrides)
    return GadgetSpec(**fields)


def test_registry_is_not_empty_and_ids_are_unique() -> None:
    ids = [spec.id for spec in ALL_SPECS]
    assert len(ids) > 60
    assert len(ids) == len(set(ids))


def test_vocabularies() -> None:
    assert CONVENTIONS == ("fixed_bulk",)
    assert {"ready", "compile_failed", "invalid_graph", "import_failed", "skipped"} <= STATUSES
    assert {"observable_failed", "circuit_failed", "completed", "simulation_failed"} <= STATUSES


def test_every_mechanism_tag_has_a_spec() -> None:
    covered = set().union(*(spec.mechanisms for spec in ALL_SPECS))
    assert covered <= MECHANISMS
    assert MECHANISMS - covered == set(PENDING)


@pytest.mark.parametrize(
    "bad",
    [
        {"id": "Bad-Id"},
        {"id": "a" * 41},
        {"mechanisms": frozenset({"time:unknown"})},
        {"expected": {"fixed_bulk": "bogus"}},
        {"expected": {"fixed_boundary": "ready"}},
        {"expected_distance": "k"},
    ],
)
def test_invalid_specs_are_rejected(bad: dict[str, object]) -> None:
    with pytest.raises(TQECError):
        _spec(**bad)


def test_duplicate_registration_is_rejected() -> None:
    with pytest.raises(TQECError):
        register(_spec(id=ALL_SPECS[0].id))


def test_distance_formula() -> None:
    assert _spec().distance(2) == 5
    assert _spec(expected_distance="2*k").distance(2) == 4


def test_filters() -> None:
    assert {s.family for s in iter_gadgets(family="memory")} == {"memory"}
    tagged = iter_gadgets(mechanisms=["time:memory:z", "space:regular:xchain"])
    assert {s.id for s in tagged} == {"memory_xzz", "memory_zxz"}
    ready = iter_gadgets(convention="fixed_bulk", status="ready")
    assert ready and all(s.expected["fixed_bulk"] == "ready" for s in ready)
    assert [s.id for s in iter_gadgets(ids=["memory_zxz"])] == ["memory_zxz"]
    with pytest.raises(ValueError, match="requires `convention`"):
        iter_gadgets(status="ready")
    with pytest.raises(ValueError):
        iter_gadgets(convention="fixed_boundary")
    with pytest.raises(ValueError):
        iter_gadgets(mechanisms=["nope"])


def test_get_unknown_id() -> None:
    with pytest.raises(TQECError):
        get("no_such_gadget")


@pytest.mark.parametrize("spec", ALL_SPECS, ids=lambda s: s.id)
def test_every_spec_builds_a_valid_graph(spec: GadgetSpec) -> None:
    graph = build_graph(spec)
    assert isinstance(graph, BlockGraph)
    graph.validate()
    if spec.expected["fixed_bulk"] != "ready" or spec.family == "y_half_cube":
        assert spec.blocked_by or spec.expected["fixed_bulk"] != "ready"


def test_non_ready_specs_state_what_blocks_them() -> None:
    for spec in iter_gadgets(family="y_half_cube"):
        assert spec.blocked_by


def test_y_files_exist_and_g05_is_not_registered() -> None:
    y_specs = iter_gadgets(family="y_half_cube")
    assert len(y_specs) == 24
    for spec in y_specs:
        assert (DATA_DIR / f"{spec.id}.bgraph").is_file()
    assert "y_half_cube_g05" not in {s.id for s in y_specs}


def test_vend_names_graphs_after_ids_and_passes_paths_through() -> None:
    inputs = vend(["memory_zxz", get("y_half_cube_g01")])
    graph, path = inputs
    assert isinstance(graph, BlockGraph)
    assert graph.name == "memory_zxz"
    assert isinstance(path, Path)
    assert path.name == "y_half_cube_g01.bgraph"


def test_cli_list_and_json(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--family", "memory"]) == 0
    assert "memory_zxz" in capsys.readouterr().out
    assert main(["--json", "--mechanism", "time:memory:x"]) == 0
    rows = json.loads(capsys.readouterr().out)
    assert {row["id"] for row in rows} == {"memory_xzx", "memory_zxx"}
    assert main(["--status", "ready"]) == 2
    assert main(["--mechanism", "nope"]) == 2


def test_cli_export(tmp_path: Path) -> None:
    assert main(["--family", "pair", "--export", str(tmp_path)]) == 0
    files = sorted(p.name for p in tmp_path.glob("*.bgraph"))
    assert "pair_time_zxz.bgraph" in files
    graph = BlockGraph.from_bgraph(tmp_path / "pair_time_zxz.bgraph")
    assert len(graph.cubes) == 2


def test_pending_tags_are_valid_and_point_to_issues() -> None:
    assert PENDING
    assert set(PENDING) <= MECHANISMS
    assert all(url.startswith("https://github.com/tqec/tqec/issues/") for url in PENDING.values())
    assert any(tag.startswith("space:patch_rotation:") for tag in PENDING)


def test_spec_can_use_a_pending_tag_without_central_edits() -> None:
    tag = next(iter(PENDING))
    assert _spec(mechanisms=frozenset({tag})).mechanisms == {tag}


def test_expected_is_immutable_and_not_shared() -> None:
    spec = ALL_SPECS[0]
    with pytest.raises(TypeError):
        mutable: Any = spec.expected
        mutable["fixed_bulk"] = "ready"
    shared = {"fixed_bulk": "ready"}
    first, second = _spec(expected=shared), _spec(expected=shared)
    shared["fixed_bulk"] = "compile_failed"
    assert first.expected["fixed_bulk"] == "ready"
    assert first.expected is not second.expected


def test_iter_gadgets_rejects_unknown_ids_and_family() -> None:
    with pytest.raises(ValueError, match="Unknown gadget ids"):
        iter_gadgets(ids=["memory_zxz", "nope"])
    with pytest.raises(ValueError, match="Unknown gadget family"):
        iter_gadgets(family="nope")
