# Titanic before/after papermill demo — design

**Date:** 2026-08-08
**Status:** Approved

## Purpose

A live-demo repo for a developer-group talk showing the journey from step ① of the
slides (a simple model living in one Jupyter notebook, run by hand) to step ④
(the same model split into single-purpose notebooks, automated with papermill via a
bash script, and packaged in a single Docker container). The Titanic dataset keeps
the ML trivially small so the pipeline structure is the star.

## Decisions (from brainstorming)

- **"After" scope:** step 4 from the slides — split notebooks + papermill runner
  containerized in one Docker image. (The bash script also runs locally as a
  no-Docker fallback for the live demo.)
- **Environments:** `uv` for both halves — each of `before/` and `after/` is its own
  uv project with its own `pyproject.toml` + `uv.lock`. No `requirements.txt`.
  `before` does not have papermill installed; `after`'s canonical environment is the
  Docker image, which installs dependencies with `uv sync --frozen`.
- **Pipeline split:** four notebooks matching the diagram —
  `fs_train → train → fs_score → score`, with `model.pkl` passed between them.

## Repo layout

```
papermill_and_antigravity/
├── README.md                  # talk narrative + copy-paste demo commands
├── before/                    # ① single notebook, run by hand
│   ├── pyproject.toml         # uv project: pandas, scikit-learn, jupyterlab
│   ├── uv.lock
│   ├── data/titanic.csv       # full classic Titanic dataset (~891 rows, vendored)
│   └── titanic_model.ipynb    # load → feature eng → train → score → predictions
└── after/                     # ④ split notebooks + papermill, in one Docker container
    ├── pyproject.toml         # uv project: pandas, scikit-learn, papermill, ipykernel
    ├── uv.lock
    ├── Dockerfile             # uv-based image, uv sync --frozen, entrypoint = run_pipeline.sh
    ├── run_pipeline.sh        # bash: papermill each notebook in order with -p parameters
    ├── .dockerignore
    ├── data/
    │   ├── train.csv          # with Survived label
    │   └── score.csv          # Survived dropped — simulates unseen passengers
    ├── notebooks/
    │   ├── fs_train.ipynb     # data/train.csv → output/train_features.csv
    │   ├── train.ipynb        # output/train_features.csv → output/model.pkl
    │   ├── fs_score.ipynb     # data/score.csv → output/score_features.csv
    │   └── score.ipynb        # model.pkl + score_features.csv → output/predictions.csv
    └── output/                # executed notebooks + artifacts (gitignored, volume-mounted)
```

## Data

The classic Titanic passenger CSV (~891 rows), vendored into the repo so the demo
works offline:

- `before/data/titanic.csv` — the full dataset; the notebook does its own
  train/test split inline.
- `after/data/train.csv` — ~80% of rows, including the `Survived` label.
- `after/data/score.csv` — the remaining ~20% with `Survived` dropped, playing the
  role of new, unseen passengers to score.

The split is done once while authoring the repo (deterministic seed, throwaway
script) and the resulting CSVs are committed — no runtime download or split step.

## Model & feature engineering

scikit-learn `LogisticRegression`. Feature engineering is deliberately simple and
identical in both halves: impute `Age`/`Fare` with medians, encode `Sex` as 0/1,
one-hot `Embarked`, keep `Pclass`, `SibSp`, `Parch`. In `after`, FE lives in the
`fs_*` notebooks which write engineered CSVs; `train`/`score` only consume them.

## Papermill mechanics (after)

- Every notebook has a cell tagged `parameters` declaring its input/output paths
  with sensible defaults (so notebooks also run interactively in Jupyter).
- `run_pipeline.sh` runs the four notebooks in order:
  `papermill notebooks/<name>.ipynb output/<name>_run.ipynb -p <param> <value> …`
  (via `uv run papermill …` locally; plain `papermill` inside the container where
  the venv is on PATH).
- Executed notebooks land in `output/` as inspectable run logs — a key talking
  point. `set -euo pipefail` so a failing notebook fails the pipeline run.

## Docker (after)

- Base image: `ghcr.io/astral-sh/uv:python3.12-bookworm-slim`.
- Layers: copy `pyproject.toml` + `uv.lock`, `uv sync --frozen --no-dev`, then copy
  `notebooks/`, `data/`, `run_pipeline.sh`.
- `ENTRYPOINT ["./run_pipeline.sh"]`; run with
  `docker run --rm -v "$PWD/output:/app/output" titanic-pipeline` so predictions and
  run-log notebooks land on the host.

## Demo flow (captured in README)

1. **Before:** `cd before && uv sync && uv run jupyter lab` — run cells by hand;
   point out fragility (hidden state, manual re-runs, "works on my machine" env).
2. **After:** `cd after && docker build -t titanic-pipeline . && docker run --rm
   -v "$PWD/output:/app/output" titanic-pipeline` — one command, reproducible,
   parameterized, logged. Local fallback: `uv run ./run_pipeline.sh`.

## Error handling

- `run_pipeline.sh` uses `set -euo pipefail`; papermill propagates notebook cell
  errors as non-zero exits, so a broken step halts the pipeline with the failing
  executed notebook left in `output/` for inspection.
- Notebooks read inputs via their parameters; missing files fail fast with a clear
  pandas error inside the run-log notebook.

## Verification

- Execute `before/titanic_model.ipynb` headless once (`uv run jupyter execute`) to
  prove it runs end-to-end.
- Run the after pipeline locally (`uv run ./run_pipeline.sh`) and in Docker; assert
  `output/predictions.csv` exists with one row per score.csv passenger and a
  prediction column.

## Out of scope

- Intermediate slide steps ② and ③ as standalone demos (the after/ folder covers
  step ④, which subsumes step ③'s bash + papermill runner), orchestrators
  (Airflow, cron), CI, tests beyond the verification runs, model quality tuning,
  and multi-container setups.
