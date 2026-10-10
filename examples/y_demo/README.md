# Y gadgets through the batch pipeline

One sequence of shell commands that takes gadgets from the gadget registry (`tqec.benchmarks.gadgets`) through
every stage of batch processing (`tqec.orchestration`): select and export the gadgets, write the batch
configuration, generate the circuits (`prepare_batch`, writing `manifest.json`), run sinter over the whole batch
(`simulate_batch`, writing `results.json`), and read both back with the circuit-level distance of every circuit.

The gadgets are every Y half cube gadget in the registry, plus the X memory gadgets as a control.

## Setup

You need git and [uv](https://docs.astral.sh/uv/). The Y gadgets need tqecd PR #74 (the Y fragment flow), which is
not in a release yet; the released tqecd 0.2.1 gives them distance 1.

    git clone -b kd/y-demo https://github.com/KabirDubey/tqec.git tqec
    git clone -b feat/yfragmentflow https://github.com/KabirDubey/tqecd.git tqecd
    cd tqec
    uv sync
    uv pip install --python .venv/bin/python -e ../tqecd

Check that Python loads tqecd from the checkout (the path ends in `tqecd/src/tqecd/__init__.py`):

    .venv/bin/python -c "import tqecd; print(tqecd.__file__)"

Run everything with `.venv/bin/python`, not `uv run`: `uv run` syncs the environment back to the lockfile and
reinstalls tqecd 0.2.1.

## Commands

Run these from the repository root, in one shell. Everything is written under `y_demo_run/`.

1. Use a fresh detector database (a database made by tqecd 0.2.1 hides the Y fix):

       mkdir -p y_demo_run
       export TQEC_DETECTOR_DATABASE_PATH=$PWD/y_demo_run/detector_db.pkl

2. List the gadgets from the registry (id, family, expected status per convention, tags):

       .venv/bin/python -m tqec.benchmarks.gadgets --family y_half_cube
       .venv/bin/python -m tqec.benchmarks.gadgets --family memory --mechanism time:memory:x

3. Export them as `.bgraph` files, the batch's input:

       .venv/bin/python -m tqec.benchmarks.gadgets --family y_half_cube --export y_demo_run/gadgets
       .venv/bin/python -m tqec.benchmarks.gadgets --family memory --mechanism time:memory:x --export y_demo_run/gadgets

4. Write the batch configuration. These are `BatchConfig` fields; the ones left out keep their defaults. `ks` and
   `conventions` drive circuit generation; `ps`, `noise_models`, `decoders` and `max_shots` drive sinter.

       cat > y_demo_run/config.json <<'EOF'
       {"conventions": ["fixed_bulk"], "ks": [1, 2], "ps": [0.001, 0.003],
        "noise_models": ["uniform_depolarizing"], "decoders": ["pymatching"],
        "max_shots": 2000, "max_errors": null}
       EOF

5. Generate the circuits. `prepare_batch` compiles every gadget at every k into a noiseless circuit under
   `y_demo_run/batch/circuits` and writes `y_demo_run/batch/manifest.json`, which records the configuration, so the
   next stage needs only the run directory:

       .venv/bin/python - <<'EOF'
       import json
       from pathlib import Path
       from tqec.orchestration import BatchConfig, prepare_batch

       config = BatchConfig.from_dict(json.loads(Path("y_demo_run/config.json").read_text()))
       gadgets = sorted(Path("y_demo_run/gadgets").glob("*.bgraph"))
       manifest = prepare_batch(gadgets, config, "y_demo_run/batch")
       for unit in manifest.units:
           print(f"{unit.name:26} {unit.status:15} k={sorted(unit.circuits)}")
       EOF

6. Run sinter. `simulate_batch` applies the noise model to every prepared circuit, runs one `sinter.collect` over
   the whole batch and writes `y_demo_run/batch/results.json`:

       .venv/bin/python - <<'EOF'
       from tqec.orchestration import simulate_batch

       result = simulate_batch("y_demo_run/batch")
       print(result.aggregate, len(result.results), "results,", len(result.failures), "failures")
       EOF

7. Report, from the two files: the status each gadget reached, the circuit-level distance of each circuit against
   `2k+1` (minimum graphlike logical error, all observables) and the sinter error count at each p.

       .venv/bin/python - <<'EOF'
       import stim
       from tqec.orchestration import BatchManifest, BatchResult
       from tqec.utils.noise_model import NoiseModel

       run = "y_demo_run/batch"
       manifest = BatchManifest.read(run)
       errors = {(r.gadget_id, r.k, r.p): f"{r.errors}/{r.shots}" for r in BatchResult.read(run).results}
       print(f"{'gadget':26} {'status':8} k  dist 2k+1  p      errors")
       for unit in manifest.units:
           if not unit.circuits:
               print(f"{unit.name:26} {unit.status}")
           for k, rel in sorted(unit.circuits.items()):
               circuit = stim.Circuit.from_file(manifest.run_dir / rel)
               noisy = NoiseModel.uniform_depolarizing(1e-3).noisy_circuit(circuit)
               error = noisy.shortest_graphlike_error(
                   ignore_ungraphlike_errors=False, canonicalize_circuit_errors=True
               )
               for p in manifest.config.ps:
                   count = errors.get((unit.gadget_id, k, p), "-")
                   print(f"{unit.name:26} {unit.status:8} {k}  {len(error):>4} {2 * k + 1:>4}  {p:<6g} {count}")
       EOF

## What to expect

Every gadget reaches `ready`, with distance 3 at k=1 and 5 at k=2. The statuses and distances are the same on every
run. The sinter error counts are statistical (sinter is not seeded), so they change from run to run within shot
noise; at p=0.001 they fall from k=1 to k=2.
