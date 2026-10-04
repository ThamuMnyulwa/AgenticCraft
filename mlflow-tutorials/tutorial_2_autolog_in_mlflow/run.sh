#!/usr/bin/env bash
set -uo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR" || exit 1

PAPERMILL="${PAPERMILL:-.venv/bin/papermill}"
JUPYTER="${JUPYTER:-.venv/bin/jupyter}"
KERNEL="${KERNEL:-python3}"

export MPLCONFIGDIR="${MPLCONFIGDIR:-$ROOT_DIR/.matplotlib-cache}"
mkdir -p "$MPLCONFIGDIR"

rm -rf outputs
mkdir -p outputs

status=0
notebooks=(
  notebooks/01_sklearn_autolog.ipynb
  notebooks/02_pytorch_autolog.ipynb
  notebooks/03_genai_tracing.ipynb
)

for notebook in "${notebooks[@]}"; do
  output="outputs/$(basename "$notebook")"
  echo "Running $notebook -> $output"

  if ! "$PAPERMILL" "$notebook" "$output" --kernel "$KERNEL"; then
    status=1
  fi

  if [[ -f "$output" ]]; then
    echo "Exporting $output -> outputs/*.md"
    if ! "$JUPYTER" nbconvert --to markdown "$output" --output-dir outputs; then
      status=1
    fi
  fi
done

exit "$status"
