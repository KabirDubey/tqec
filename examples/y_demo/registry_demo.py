"""Registry to batch: select gadgets from the registry, vend them, run the batch, report.

The user picks gadgets with ``tqec.benchmarks.gadgets.iter_gadgets`` (family, tags), ``vend`` turns
them into ``prepare_batch`` inputs, and ``prepare_batch`` / ``simulate_batch`` run them in the
fixed bulk convention. For every unit the script prints the status the batch observed on this
branch, the circuit-level distance against ``2k+1`` and the sinter errors.

Run: ``python examples/y_demo/registry_demo.py --ks 1,2 --shots 500`` (see README.md).
"""

from __future__ import annotations

import argparse
import os
import tempfile
from pathlib import Path

# Fresh detector database (a database made before tqecd PR #74 hides the Y fix); set before tqec.
os.environ.setdefault(
    "TQEC_DETECTOR_DATABASE_PATH", str(Path(tempfile.mkdtemp(prefix="y_demo_db_")) / "db.pkl")
)

import stim
from batch_demo import fault_distance

from tqec.benchmarks.gadgets import iter_gadgets, vend
from tqec.orchestration import BatchConfig, prepare_batch, simulate_batch

CONVENTION = "fixed_bulk"


def main() -> None:
    """Run the demo."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ks", default="1,2", help="comma-separated k values")
    parser.add_argument("--p", type=float, default=1e-3, help="physical error rate")
    parser.add_argument("--shots", type=int, default=500, help="shots per circuit")
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--out", type=Path, default=None, help="run directory (default: temp)")
    args = parser.parse_args()
    ks = tuple(int(k) for k in args.ks.split(","))
    run_dir = args.out or Path(tempfile.mkdtemp(prefix="y_registry_demo_"))

    # 1. Select: every Y gadget, plus a few memory and junction gadgets chosen by tag.
    specs = [
        *iter_gadgets(family="y_half_cube"),
        *iter_gadgets(family="memory", mechanisms=["time:memory:x"]),
        *iter_gadgets(family="junction", mechanisms=["time:stability:x"]),
    ]
    print(f"selected {len(specs)} gadgets: {', '.join(spec.id for spec in specs)}")

    # 2. Vend and batch, fixed bulk only.
    config = BatchConfig(
        conventions=(CONVENTION,), ks=ks, ps=(args.p,), max_shots=args.shots, max_errors=None
    )
    manifest = prepare_batch(vend(specs), config, run_dir)
    result = simulate_batch(run_dir, num_workers=args.workers)
    errors = {(r.gadget_id, r.k): f"{r.errors}/{r.shots}" for r in result.results}

    # 3. Report what the batch observed on this branch.
    print(f"\nrun dir {run_dir}; p={args.p:g}; distance = circuit-level, expected 2k+1")
    print(f"{'gadget':26} {'status':15} k  {'dist':>4} {'2k+1':>4}  errors")
    for unit in manifest.units:
        # unit.name is the registry id; gadget_id has an s00_ prefix
        if not unit.circuits:
            print(f"{unit.name:26} {unit.status:15} -")
            continue
        for k, rel in sorted(unit.circuits.items()):
            d = fault_distance(stim.Circuit.from_file(run_dir / rel), args.p)
            err = errors.get((unit.gadget_id, k), "-")
            print(f"{unit.name:26} {unit.status:15} {k}  {d:>4} {2 * k + 1:>4}  {err}")


if __name__ == "__main__":
    main()
