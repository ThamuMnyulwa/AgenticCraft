"""The eval questions as an MLflow evaluation dataset, so they show on the "Datasets" page."""

import mlflow
from mlflow.genai.datasets import EvaluationDataset, create_dataset, search_datasets

from part1_mlflow.agent import EXPERIMENT
from shared.eval_data import EVAL_DATA

DATASET_NAME = "devfest-travel-questions"


def get_or_create_dataset() -> EvaluationDataset:
    """Find the dataset (or create it) and sync it with shared/eval_data.py.

    eval_data.py stays the source of truth. merge_records() matches rows by their
    inputs, so running this again does not add duplicates.
    """
    experiment_id = mlflow.get_experiment_by_name(EXPERIMENT).experiment_id
    found = [d for d in search_datasets(experiment_ids=[experiment_id]) if d.name == DATASET_NAME]
    dataset = found[0] if found else create_dataset(name=DATASET_NAME, experiment_id=experiment_id)
    dataset.merge_records(EVAL_DATA)
    return dataset
