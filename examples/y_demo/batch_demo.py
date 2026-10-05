"""Batch processing demo for Y gadgets: placement, observables, fault distance, sinter.

Builds four block graphs (Y memory, S gate X, S gate Z and a multi-component graph holding all
three, placed apart), runs them through ``tqec.orchestration`` in its default mode (one circuit
per input, relative placement kept), prints what the manifest recorded, confirms the fault
distance of every circuit and samples logical error rates with sinter. Finally it shows that two
components placed on the same spacetime cell are rejected.

Run: ``python examples/y_demo/batch_demo.py --ks 1 --shots 500`` (see README.md).
"""

from __future__ import annotations

import argparse
import os
import tempfile
from pathlib import Path

# Use a fresh detector database for the demo: a shared default database may hold detectors that
# an older tqecd computed (before PR #74), which would hide the fix. Set before importing tqec.
os.environ.setdefault(
    "TQEC_DETECTOR_DATABASE_PATH", str(Path(tempfile.mkdtemp(prefix="y_demo_db_")) / "db.pkl")
)

import numpy as np
import pymatching
import stim

from tqec.computation.block_graph import BlockGraph
from tqec.gallery import memory, s_gate_teleportation
from tqec.orchestration import BatchConfig, prepare_batch, simulate_batch
from tqec.utils.enums import PauliBasis
from tqec.utils.exceptions import TQECError
from tqec.utils.noise_model import NoiseModel
from tqec.utils.position import Position3D


def place(target: BlockGraph, part: BlockGraph, dx: int, dy: int, dz: int) -> None:
    """Copy ``part`` shifted by ``(dx, dy, dz)`` into ``target``.

    Raises:
        TQECError: If a cube of ``part`` lands on an occupied cell of ``target``.

    """
    shifted = part.shift_by(dx, dy, dz)
    for cube in shifted.cubes:
        target.add_cube(cube.position, cube.kind, cube.label, cube.condition)
    for pipe in shifted.pipes:
        target.add_pipe(pipe.u.position, pipe.v.position, pipe.kind)


def multi_component_graph() -> BlockGraph:
    """Y memory, S gate X and S gate Z, disjoint, offset in x and (for the last) in time."""
    g = BlockGraph("multi")
    place(g, memory(PauliBasis.Y), 0, 0, 0)
    place(g, s_gate_teleportation(PauliBasis.X), 4, 0, 0)
    place(g, s_gate_teleportation(PauliBasis.Z), 8, 0, 3)
    return g


def fault_distance(circuit: stim.Circuit, p: float = 1e-3) -> int:
    """Length of the shortest graphlike logical error, counting every error mechanism."""
    noisy = NoiseModel.uniform_depolarizing(p).noisy_circuit(circuit)
    error = noisy.shortest_graphlike_error(
        ignore_ungraphlike_errors=False, canonicalize_circuit_errors=True
    )
    return len(error)


def per_observable_rates(circuit: stim.Circuit, p: float, shots: int, seed: int = 0) -> list[float]:
    """Logical error rate of each observable on its own (pymatching, same noise as sinter)."""
    noisy = NoiseModel.uniform_depolarizing(p).noisy_circuit(circuit)
    matching = pymatching.Matching.from_detector_error_model(noisy.detector_error_model())
    sampler = noisy.compile_detector_sampler(seed=seed)
    detections, actual = sampler.sample(shots, separate_observables=True)
    predicted = matching.decode_batch(detections)
    return list(np.mean(predicted != actual, axis=0))


def main() -> None:
    """Run the demo."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ks", default="1,2", help="comma-separated k values")
    parser.add_argument("--ps", default="1e-3,3e-3", help="comma-separated physical error rates")
    parser.add_argument("--shots", type=int, default=2000, help="max shots per circuit")
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--out", type=Path, default=None, help="run directory (default: temp)")
    args = parser.parse_args()
    ks = tuple(int(k) for k in args.ks.split(","))
    ps = tuple(float(p) for p in args.ps.split(","))
    run_dir = args.out or Path(tempfile.mkdtemp(prefix="y_demo_batch_"))

    graphs = [
        memory(PauliBasis.Y),
        s_gate_teleportation(PauliBasis.X),
        s_gate_teleportation(PauliBasis.Z),
        multi_component_graph(),
    ]
    for graph, name in zip(graphs, ["y_memory", "s_gate_x", "s_gate_z", "multi"]):
        graph.name = name
    # Default BatchConfig.split_components=False: one circuit per input, placement kept.
    config = BatchConfig(ks=ks, ps=ps, max_shots=args.shots, max_errors=None)
    manifest = prepare_batch(graphs, config, run_dir)

    print(f"\n== Placement and observables (run dir {run_dir})")
    for unit in manifest.units:
        print(f"{unit.gadget_id}: status={unit.status} observables={unit.observables}")
        print(f"  device frame (lattice, inclusive): {unit.device_frame}")
        for comp in unit.components:
            print(f"  component {comp['component_id']}: {comp['minimum']} .. {comp['maximum']}")
        for i, (cid, lo) in enumerate(zip(unit.observable_components, unit.logical_observables)):
            print(
                f"  observable {i}: component {cid}, external stabilizer {lo.external_stabilizer}"
            )

    print("\n== Fault distance (shortest graphlike error at p=1e-3, expected 2k+1)")
    for unit in manifest.units:
        for k, rel in sorted(unit.circuits.items()):
            circuit = stim.Circuit.from_file(run_dir / rel)
            d = fault_distance(circuit)
            verdict = "OK" if d == 2 * k + 1 else "MISMATCH"
            print(f"{unit.gadget_id} k={k}: distance {d} vs {2 * k + 1}  {verdict}")

    print("\n== Sinter (uniform depolarizing, pymatching)")
    result = simulate_batch(run_dir, num_workers=args.workers)
    print(f"aggregate: {result.aggregate}")
    for row in sorted(result.results, key=lambda r: (r.gadget_id, r.k, r.p)):
        print(
            f"{row.gadget_id} k={row.k} p={row.p:g}: {row.errors}/{row.shots} errors "
            f"(rate {row.errors / max(row.shots, 1):.4f}; any observable wrong counts as one error)"
        )

    print("\n== Multi-component graph: per-observable error rate (pymatching on the same circuit)")
    multi = next(u for u in manifest.units if u.name == "multi")
    for k, rel in sorted(multi.circuits.items()):
        circuit = stim.Circuit.from_file(run_dir / rel)
        for p in ps:
            rates = per_observable_rates(circuit, p, args.shots)
            labelled = ", ".join(
                f"obs{i}[{cid}]={rate:.4f}"
                for i, (cid, rate) in enumerate(zip(multi.observable_components, rates))
            )
            print(f"k={k} p={p:g}: {labelled}")

    print("\n== Two components on the same spacetime cell must be rejected")
    clash = BlockGraph("clash")
    place(clash, memory(PauliBasis.Y), 0, 0, 0)
    try:
        place(clash, s_gate_teleportation(PauliBasis.X), 0, 0, 0)
    except TQECError as error:
        print(f"TQECError (expected): {error}")
    else:
        raise SystemExit("ERROR: overlapping components were accepted")
    assert Position3D(0, 0, 0) in clash


if __name__ == "__main__":
    main()
