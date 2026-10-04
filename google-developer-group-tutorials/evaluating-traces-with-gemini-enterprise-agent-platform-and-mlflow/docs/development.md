# Development

## Layout rules

- Run every Python entry point as a module from this folder, for example `uv run python -m part1_mlflow.evaluate`, so `shared` is importable. `demo.sh` does this for you.
- Change the model only in `shared/config.py`.
- Change the evaluation questions only in `shared/eval_data.py`. Both parts use them.
- Keep exactly one deliberately failing row. The CI quality gate assumes it.
- No em-dashes in code, comments, docs or output text.

## Formatting and linting

The same rules apply everywhere. They come from `ruff.toml` at the AgenticCraft root: line length 110, rules `E F I UP B`.

| When | What runs | Where it is configured |
|---|---|---|
| On save | ruff fix, organise imports, format; `terraform fmt` | `.vscode/settings.json` at the repo root (VS Code and Antigravity). Install the recommended extensions. |
| On commit | `ruff check --fix`, `ruff format`, `terraform_fmt`, plus the hooks below | `.pre-commit-config.yaml` at the repo root |
| On demand | `./demo.sh lint` | `demo.sh` |
| In CI | every pre-commit hook on all files | `.github/workflows/ci.yml` |

Ruff is pinned to the same version (0.16.10) in the `dev` group and in pre-commit, so local, commit and CI results match.

## Pre-commit hooks (whole AgenticCraft repo)

- **Secrets:** gitleaks, detect-private-key, and a local hook that blocks `.env` and `.env.*` (but allows `.env.example`).
- **Python:** ruff check with `--fix`, then ruff format. This covers `.py` files only; notebooks are excluded.
- **Notebooks:** nbstripout with `--keep-id`. It skips `outputs/` folders, which hold executed notebooks on purpose.
- **Shell:** shellcheck.
- **Terraform:** `terraform_fmt`.
- **Hygiene:**
  - large files (over 1 MB)
  - merge conflict markers
  - YAML, TOML and JSON syntax
  - end-of-file newline and trailing whitespace
  - line endings
  - shebangs and executable bits

Fixers never touch `.ipynb` outputs, `.html` and `.pptx` slides, images, lock files or databases.

## Tests

`./demo.sh test` runs the offline tests in `tests/` with no network and no keys:

- `test_tools.py`: fixed weather data, calculator results, and that the calculator rejects code.
- `test_right_tool.py`: the Part 2 custom metric finds tool calls in an eval case.
- `test_quality_gate.py`: pass-rate maths, and that one deliberate failure still passes the gate.

## CI/CD (GitHub Actions)

| Workflow | Trigger | Jobs |
|---|---|---|
| `ci.yml` | every push and PR | `secrets`: gitleaks over the full history. `pre-commit`: all hooks on all files. |
| `gdg-evaluating-traces.yml` | changes to this folder, nightly at 05:00 UTC, manual | `tests`: `uv sync --locked` and pytest. `terraform`: fmt and validate for both stacks. `evals`: Part 1 evaluation with `--gate`, uploads `mlflow.db` as an artifact. |

- The `evals` job signs in with Workload Identity Federation and is skipped until the `GCP_*` repository variables exist (see [setup.md](setup.md)). PRs from forks are skipped because they cannot get an identity token.
- To inspect a CI evaluation: download the artifact, then run `uv run mlflow server --backend-store-uri sqlite:///mlflow.db`.
- The nightly run exists to catch model drift. A provider-side model change can break the gate with no code change.

## Dependency updates

- `.github/dependabot.yml` opens weekly grouped PRs for GitHub Actions, uv packages, and the Terraform provider in both stacks.
- Pre-commit hook versions update separately with `pre-commit autoupdate`.
- After a uv bump, check that `google-genai` is still in the range MLflow's Gemini autolog supports (see [decisions.md](decisions.md)).

## Adding a dependency

- **Runs locally only** (Part 1, eval tooling): `uv add <pkg>`.
- **Needed by the deployed agent:** `uv add --group agent-runtime <pkg>`. Only this group is shipped to Agent Runtime.
- **Dev tooling:** `uv add --dev <pkg>`.
