# Y batch demo

Shows how `tqec.orchestration` (batch processing) handles Y gadgets in its default mode: one circuit per
input, relative placement kept, each connected component with its own observables.

It builds a Y memory, the S gate (X and Z) and a multi-component graph holding all three placed apart. It prints
each component's bounding box and observables, checks the circuit-level fault distance of every circuit against `2k+1` (the minimum graphlike logical distance over
all observables, and per observable by keeping only that observable), runs a small sinter batch, and shows that
`BlockGraph` construction rejects overlapping cubes (`TQECError`) before batching.

Setup (branch `kd/y-demo`; it needs tqecd PR #74 with the Y fragment flow, which is not in a release yet), from the
repository root:

    uv sync
    uv pip install --python .venv/bin/python -e <path to a tqecd checkout of KabirDubey/tqecd feat/yfragmentflow>

To get that checkout:

    git clone -b feat/yfragmentflow https://github.com/KabirDubey/tqecd.git <path>
    # or, in an existing clone: git fetch origin feat/yfragmentflow && git checkout feat/yfragmentflow

(or `export PYTHONPATH=<tqecd checkout>/src`). The script uses a fresh detector database, since a database made
by tqecd 0.2.1 hides the fix.

Commands, from the repository root:

    .venv/bin/python examples/y_demo/batch_demo.py --ks 1 --shots 300 --ps 1e-3   # quick check, about 1 min
    .venv/bin/python examples/y_demo/batch_demo.py                                # k=1,2, p=1e-3,3e-3, 2000 shots

Options: `--ks`, `--ps`, `--shots`, `--workers`, `--out DIR` (keep the run directory with `manifest.json`,
`results.json` and the `.stim` circuits).

## Registry to batch

`examples/y_demo/registry_demo.py` shows the gadget registry feeding the batch interface: pick gadgets with
`tqec.benchmarks.gadgets.iter_gadgets(...)` (here every `y_half_cube` gadget, plus the `memory` and `junction` gadgets
with chosen tags), write them out with `vend(...)`, run `prepare_batch` and `simulate_batch` in the fixed bulk
convention, and print per unit: the status the registry expects, the status the batch observed, the circuit-level
distance against `2k+1` and the sinter error count. A row marked `<- differs` is a gadget whose registry
expectation no longer matches (the registry on `main` lists the Y gadgets as `compile_failed`; with the Y branches
merged they compile).

    .venv/bin/python examples/y_demo/registry_demo.py --ks 1 --shots 200      # small check
    .venv/bin/python examples/y_demo/registry_demo.py                          # k=1,2, p=1e-3, 500 shots

Options: `--ks`, `--p`, `--shots`, `--workers`, `--out DIR`. The setup is the one above (tqecd with the Y fragment
flow, fresh detector database).
