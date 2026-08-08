#!/usr/bin/env bash
# Run the whole pipeline: four notebooks executed in order via papermill.
# Locally:      uv run ./run_pipeline.sh   (from after/)
# In Docker:    the image ENTRYPOINT runs this directly.
set -euo pipefail
cd "$(dirname "$0")"

TRAIN_DATA="${TRAIN_DATA:-data/train.csv}"
SCORE_DATA="${SCORE_DATA:-data/score.csv}"
OUTPUT_DIR="${OUTPUT_DIR:-output}"

mkdir -p "$OUTPUT_DIR"

echo
echo "==> [1/4] FS_TRAIN: engineering training features"
papermill notebooks/fs_train.ipynb "$OUTPUT_DIR/fs_train_run.ipynb" --log-output \
  -p input_path "$TRAIN_DATA" \
  -p features_path "$OUTPUT_DIR/train_features.csv"

echo
echo "==> [2/4] TRAIN: fitting the model"
papermill notebooks/train.ipynb "$OUTPUT_DIR/train_run.ipynb" --log-output \
  -p features_path "$OUTPUT_DIR/train_features.csv" \
  -p model_path "$OUTPUT_DIR/model.pkl"

echo
echo "==> [3/4] FS_SCORE: engineering scoring features"
papermill notebooks/fs_score.ipynb "$OUTPUT_DIR/fs_score_run.ipynb" --log-output \
  -p input_path "$SCORE_DATA" \
  -p features_path "$OUTPUT_DIR/score_features.csv"

echo
echo "==> [4/4] SCORE: predicting"
papermill notebooks/score.ipynb "$OUTPUT_DIR/score_run.ipynb" --log-output \
  -p features_path "$OUTPUT_DIR/score_features.csv" \
  -p model_path "$OUTPUT_DIR/model.pkl" \
  -p predictions_path "$OUTPUT_DIR/predictions.csv"

echo
echo "==> Done. Predictions at $OUTPUT_DIR/predictions.csv — executed notebooks in $OUTPUT_DIR/ are the run logs."
