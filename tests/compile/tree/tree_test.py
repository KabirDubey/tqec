from pathlib import Path

import pytest

from tqec.compile.compile import compile_block_graph
from tqec.compile.convention import FIXED_BULK_CONVENTION
from tqec.compile.detectors.database import DetectorDatabase
from tqec.computation.block_graph import BlockGraph
from tqec.utils.exceptions import TQECError
from tqec.utils.position import Position3D


def test_generate_circuit_rejects_database_from_other_tqecd(tmp_path: Path) -> None:
    g = BlockGraph("Memory Experiment")
    g.add_cube(Position3D(0, 0, 0), "ZXZ")
    layer_tree = compile_block_graph(g, FIXED_BULK_CONVENTION).to_layer_tree()

    database = DetectorDatabase()
    database.tqecd_version = "0.0.0-other"
    database_path = tmp_path / "database.pkl"
    database.to_file(database_path)

    with pytest.raises(TQECError, match=r"tqecd 0\.0\.0-other"):
        layer_tree.generate_circuit(1, database_path=database_path)
