"""Command line listing and export of the gadget registry.

Run ``python -m tqec.benchmarks.gadgets --help``.
"""

import argparse
import json
import sys
from pathlib import Path

from tqec.benchmarks.gadgets import CONVENTIONS, MECHANISMS, build_graph, iter_gadgets


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m tqec.benchmarks.gadgets", description="List or export registered gadgets."
    )
    parser.add_argument("--list", action="store_true", help="print one line per gadget (default)")
    parser.add_argument("--family", help="keep one family")
    parser.add_argument(
        "--mechanism", action="append", default=[], help="keep gadgets with this tag (repeatable)"
    )
    parser.add_argument("--convention", choices=CONVENTIONS, help="convention for --status")
    parser.add_argument("--status", help="keep gadgets with this expected status")
    parser.add_argument("--json", action="store_true", help="print JSON instead of text")
    parser.add_argument("--export", type=Path, metavar="DIR", help="write each gadget into DIR")
    parser.add_argument("--format", choices=("bgraph", "dae"), default="bgraph")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the command line; return the exit code."""
    args = _parser().parse_args(argv)
    unknown = set(args.mechanism) - MECHANISMS
    if unknown:
        print(f"Unknown mechanism tags: {sorted(unknown)}", file=sys.stderr)
        return 2
    try:
        specs = iter_gadgets(
            family=args.family,
            mechanisms=args.mechanism,
            convention=args.convention,
            status=args.status,
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if args.export is not None:
        args.export.mkdir(parents=True, exist_ok=True)
        for spec in specs:
            graph = build_graph(spec)
            graph.name = spec.id
            target = args.export / f"{spec.id}.{args.format}"
            if args.format == "bgraph":
                graph.to_bgraph(target, graph_name=spec.id)
            else:
                graph.to_dae_file(target)
        print(f"Wrote {len(specs)} gadgets to {args.export}")
        return 0
    if args.json:
        rows = [
            {
                "id": s.id,
                "family": s.family,
                "expected": dict(s.expected),
                "mechanisms": sorted(s.mechanisms),
                "blocked_by": list(s.blocked_by),
                "expected_distance": s.expected_distance,
                "notes": s.notes,
            }
            for s in specs
        ]
        print(json.dumps(rows, indent=2))
        return 0
    for s in specs:
        expected = ",".join(f"{c}={s.expected[c]}" for c in CONVENTIONS)
        print(
            f"{s.id}\t{s.family}\t{expected}\t{' '.join(sorted(s.mechanisms))}"
            f"\t{' '.join(s.blocked_by)}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
