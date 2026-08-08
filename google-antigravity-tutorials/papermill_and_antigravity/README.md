# From one notebook to an automated pipeline

Demo repo for a talk: taking a Titanic survival model from **a single hand-run
Jupyter notebook** to **four single-purpose notebooks automated with
[papermill](https://papermill.readthedocs.io/) and packaged in one Docker
container**.

Both halves are independent [uv](https://docs.astral.sh/uv/) projects with their
own lockfiles — deliberately separate environments.

| | `before/` (step ①) | `after/` (step ④) |
|---|---|---|
| Code | one notebook does everything | `fs_train → train → fs_score → score` |
| Execution | a human clicks Run | `run_pipeline.sh` + papermill |
| Environment | local uv venv | Docker image (built with uv) |
| Run record | whatever is in your head | executed notebooks in `output/` |

## before/ — one notebook, run by hand

```bash
cd before
uv sync
uv run jupyter lab titanic_model.ipynb
```

Run the cells top to bottom. Talking points:

- Feature engineering, training and scoring live in one file — you can't rerun
  scoring without rerunning (or carefully skipping) everything else.
- Hidden state: run cells out of order and you get different results.
- "Works on my machine": the environment is whatever your local venv happens to
  contain, and there is no record of what actually ran.

## after/ — four notebooks driven by papermill

The same model, split along the seams of the diagram. Feature engineering and
modelling are separate notebooks, `model.pkl` is the hand-off, and — the part
that makes it automatable — **every notebook declares its inputs and outputs in
a cell tagged `parameters`**, which papermill overrides at run time:

```python
# Parameters (papermill overrides these at run time)
input_path = "data/train.csv"
features_path = "output/train_features.csv"
```

`run_pipeline.sh` is then just four papermill calls in order:

```bash
papermill notebooks/fs_train.ipynb output/fs_train_run.ipynb --log-output \
  -p input_path data/train.csv \
  -p features_path output/train_features.csv
```

### Run it in Docker (the headline demo)

```bash
cd after
docker build -t titanic-pipeline .
docker run --rm -v "$PWD/output:/app/output" titanic-pipeline
```

> **Don't forget `-v`.** Without the volume mount the pipeline still runs and
> still prints a successful-looking log, but every artifact dies with the
> container. Paste this command; don't retype it live.

### Run it locally (no Docker)

```bash
cd after
uv sync
uv run ./run_pipeline.sh
```

Either way, `after/output/` then contains:

- `predictions.csv` — one row per passenger in `data/score.csv` (178 of them)
- `model.pkl`, `train_features.csv`, `score_features.csv` — the hand-off
  artifacts between pipeline steps
- `fs_train_run.ipynb`, `train_run.ipynb`, `fs_score_run.ipynb`,
  `score_run.ipynb` — the executed notebooks, i.e. **run logs you can open in
  Jupyter**

## What to point at during the talk

**1. Parameters are injected, not edited.** Open any run-log notebook in
`output/` and you'll find a cell papermill inserted that the source notebook
never had:

```python
# Parameters
features_path = "output/train_features.csv"
model_path = "output/model.pkl"
```

The notebook on disk is untouched. The record of what ran is separate from the
thing that ran.

**2. The same notebooks run against different inputs, with no edits.** Every
path is a parameter, so you can redirect a whole run:

```bash
OUTPUT_DIR=output/experiment uv run ./run_pipeline.sh          # local
docker run --rm -v "$PWD/output:/app/output" \
  -e OUTPUT_DIR=output/experiment titanic-pipeline             # containerized
```

Or drive a single notebook ad hoc, without the script — here, engineering
features from the *training* file using the scoring notebook:

```bash
mkdir -p output   # papermill won't create the output directory for you
uv run papermill notebooks/fs_score.ipynb output/adhoc_run.ipynb --log-output \
  -p input_path data/train.csv \
  -p features_path output/adhoc_features.csv
```

**3. Failures are inspectable, not lost.** Point a step at a file that doesn't
exist:

```bash
TRAIN_DATA=data/nope.csv uv run ./run_pipeline.sh; echo "exit=$?"
```

The run stops at stage 1 with `exit=1` (`set -euo pipefail`), later stages never
run, and `output/fs_train_run.ipynb` is left behind with the traceback saved in
the failing cell and `metadata.papermill.exception = true`. You debug a failed
production run by opening the notebook, exactly as if you'd been sitting there.

**4. The environment is part of the code.** `uv.lock` plus the Dockerfile mean
the pipeline runs the same anywhere Docker runs. `jupyterlab` is a dev-only
dependency, so `uv sync --frozen --no-dev` keeps it out of the image.

## Repo tour

- `before/` — step ①: single notebook, own uv project (no papermill installed).
- `after/` — step ④: pipeline notebooks, papermill runner, Dockerfile, own uv
  project.
- `tools/` — authoring utilities, not part of the demo flow: `split_data.py`
  produced `after/data/{train,score}.csv` from the vendored
  `before/data/titanic.csv`; `build_notebooks.py` regenerates all five notebooks
  (edit the generator, not the `.ipynb` files).
- `docs/superpowers/` — design spec and implementation plan for this repo.

## Notes

- Running the container on native Linux (rather than Docker Desktop) leaves the
  files in `output/` owned by root. Add `--user "$(id -u):$(id -g)"` to the
  `docker run` command if that bites.
- Each papermill invocation prints an ipykernel `Kernel is running over TCP
  without encryption` warning. It is harmless boilerplate.
