# MLflow Autologging with scikit-learn

**Notebook 1 of 3** · Demo for the "MLflow: Autologging & Zero-Config" talk

This notebook shows *true* zero-config tracking. You add one line, `mlflow.autolog()`, and MLflow records every parameter, metric, and the trained model for you.

**What you'll do**
1. Train a model the normal way (nothing recorded).
2. Turn on autologging and retrain (everything recorded).
3. Open the MLflow UI and compare two runs.

Find more at [thamu.dev](https://thamu.dev/).

## Setup

Using `uv` for package management (falls back to pip). Run this once.


```python
# Install dependencies. In a fresh environment, uncomment the line you need.
# uv:   !uv pip install "mlflow>=3.1" scikit-learn
# pip:  !pip install "mlflow>=3.1" scikit-learn

import mlflow
import sklearn
print("mlflow  :", mlflow.__version__)
print("sklearn :", sklearn.__version__)
```

    mlflow  : 3.14.0
    sklearn : 1.9.0


## Step 1 — Baseline: train with no tracking

This is ordinary scikit-learn. When the kernel restarts, the result is gone. Nothing is recorded.


```python
from sklearn.ensemble import RandomForestClassifier
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split

X, y = load_iris(return_X_y=True)
X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42)

clf = RandomForestClassifier(n_estimators=100, max_depth=6, random_state=42)
clf.fit(X_tr, y_tr)

print("accuracy:", clf.score(X_te, y_te))
# A single number. Where did it come from? What settings produced it? Unrecorded.
```

    accuracy: 1.0


## Step 2 — Turn on autologging

One call. `mlflow.autolog()` hooks into scikit-learn and records params, metrics, the model, and its signature automatically. We also name the experiment so runs are easy to find.


```python
# MLflow 3.x deprecated the plain-file backend, so point at a local SQLite DB.
mlflow.set_tracking_uri("sqlite:///mlflow.db")
mlflow.set_experiment("sklearn-autolog-demo")
mlflow.autolog()   # <- the only MLflow line you add

clf = RandomForestClassifier(n_estimators=100, max_depth=6, random_state=42)
clf.fit(X_tr, y_tr)   # same fit() as before — but now it's all captured

print("accuracy:", clf.score(X_te, y_te))
```

    2026/07/20 23:52:59 INFO mlflow.store.db.utils: Creating initial MLflow database tables...


    2026/07/20 23:52:59 INFO mlflow.store.db.utils: Updating database tables


    2026/07/20 23:52:59 INFO mlflow.tracking.fluent: Experiment with name 'sklearn-autolog-demo' does not exist. Creating a new experiment.


    2026/07/20 23:53:08 INFO mlflow.tracking.fluent: Autologging successfully enabled for sklearn.


    2026/07/20 23:53:09 INFO mlflow.utils.autologging_utils: Created MLflow autologging run with ID 'b7503fed4e2340f0aa736b3040ca78b0', which will track hyperparameters, performance metrics, model artifacts, and lineage information for the current sklearn workflow


    2026/07/20 23:53:09 INFO mlflow.utils.uv_utils: Detected uv project: found uv.lock and pyproject.toml in /Users/mac/Documents/admin/AgenticCraft/mlflow-tutorials/tutorial_2_autolog_in_mlflow


    2026/07/20 23:53:09 WARNING mlflow.sklearn: Saving scikit-learn models in the pickle or cloudpickle format requires exercising caution because these formats rely on Python's object serialization mechanism, which can execute arbitrary code during deserialization. The recommended safe alternative is the 'skops' format. For more information, see: https://scikit-learn.org/stable/model_persistence.html


    2026/07/20 23:53:09 INFO mlflow.utils.uv_utils: Detected uv project: found uv.lock and pyproject.toml in /Users/mac/Documents/admin/AgenticCraft/mlflow-tutorials/tutorial_2_autolog_in_mlflow


    2026/07/20 23:53:09 INFO mlflow.utils.environment: Detected uv project at /Users/mac/Documents/admin/AgenticCraft/mlflow-tutorials/tutorial_2_autolog_in_mlflow. Attempting to export requirements via 'uv export'.


    2026/07/20 23:53:09 INFO mlflow.utils.uv_utils: Exported 177 dependencies via uv


    2026/07/20 23:53:09 INFO mlflow.utils.environment: Successfully exported 177 requirements from uv project. Skipping package capture based inference.


    2026/07/20 23:53:11 WARNING mlflow.utils.environment: Failed to resolve installed pip version. ``pip`` will be added to conda.yaml environment spec without a version specifier.


    /Users/mac/Documents/admin/AgenticCraft/mlflow-tutorials/tutorial_2_autolog_in_mlflow/.venv/lib/python3.12/site-packages/sklearn/metrics/_classification.py:3424: FutureWarning: `y_pred` was renamed to `y_proba` in version 1.9 and will be removed in 1.11. Use `y_proba` instead.
      warnings.warn(


    Matplotlib is building the font cache; this may take a moment.


    accuracy: 1.0


## Step 3 — Change a setting and rerun

Now vary a hyperparameter. Each `fit()` becomes its own tracked run, so you can compare them later.


```python
for depth in (2, 4, 8):
    model = RandomForestClassifier(n_estimators=100, max_depth=depth, random_state=42)
    model.fit(X_tr, y_tr)
    print(f"max_depth={depth}  ->  test acc {model.score(X_te, y_te):.3f}")
```

    2026/07/20 23:53:45 INFO mlflow.utils.autologging_utils: Created MLflow autologging run with ID '44a0680080094b9b83469fbb03f75c67', which will track hyperparameters, performance metrics, model artifacts, and lineage information for the current sklearn workflow


    2026/07/20 23:53:45 INFO mlflow.utils.uv_utils: Detected uv project: found uv.lock and pyproject.toml in /Users/mac/Documents/admin/AgenticCraft/mlflow-tutorials/tutorial_2_autolog_in_mlflow


    2026/07/20 23:53:45 WARNING mlflow.sklearn: Saving scikit-learn models in the pickle or cloudpickle format requires exercising caution because these formats rely on Python's object serialization mechanism, which can execute arbitrary code during deserialization. The recommended safe alternative is the 'skops' format. For more information, see: https://scikit-learn.org/stable/model_persistence.html


    2026/07/20 23:53:45 INFO mlflow.utils.uv_utils: Detected uv project: found uv.lock and pyproject.toml in /Users/mac/Documents/admin/AgenticCraft/mlflow-tutorials/tutorial_2_autolog_in_mlflow


    2026/07/20 23:53:45 INFO mlflow.utils.environment: Detected uv project at /Users/mac/Documents/admin/AgenticCraft/mlflow-tutorials/tutorial_2_autolog_in_mlflow. Attempting to export requirements via 'uv export'.


    2026/07/20 23:53:45 INFO mlflow.utils.uv_utils: Exported 177 dependencies via uv


    2026/07/20 23:53:45 INFO mlflow.utils.environment: Successfully exported 177 requirements from uv project. Skipping package capture based inference.


    2026/07/20 23:53:46 WARNING mlflow.utils.environment: Failed to resolve installed pip version. ``pip`` will be added to conda.yaml environment spec without a version specifier.


    /Users/mac/Documents/admin/AgenticCraft/mlflow-tutorials/tutorial_2_autolog_in_mlflow/.venv/lib/python3.12/site-packages/sklearn/metrics/_classification.py:3424: FutureWarning: `y_pred` was renamed to `y_proba` in version 1.9 and will be removed in 1.11. Use `y_proba` instead.
      warnings.warn(


    2026/07/20 23:53:48 INFO mlflow.utils.autologging_utils: Created MLflow autologging run with ID 'a07d8a67cf484aeabc9527a40815146d', which will track hyperparameters, performance metrics, model artifacts, and lineage information for the current sklearn workflow


    max_depth=2  ->  test acc 1.000


    2026/07/20 23:53:48 INFO mlflow.utils.uv_utils: Detected uv project: found uv.lock and pyproject.toml in /Users/mac/Documents/admin/AgenticCraft/mlflow-tutorials/tutorial_2_autolog_in_mlflow


    2026/07/20 23:53:48 WARNING mlflow.sklearn: Saving scikit-learn models in the pickle or cloudpickle format requires exercising caution because these formats rely on Python's object serialization mechanism, which can execute arbitrary code during deserialization. The recommended safe alternative is the 'skops' format. For more information, see: https://scikit-learn.org/stable/model_persistence.html


    2026/07/20 23:53:48 INFO mlflow.utils.uv_utils: Detected uv project: found uv.lock and pyproject.toml in /Users/mac/Documents/admin/AgenticCraft/mlflow-tutorials/tutorial_2_autolog_in_mlflow


    2026/07/20 23:53:48 INFO mlflow.utils.environment: Detected uv project at /Users/mac/Documents/admin/AgenticCraft/mlflow-tutorials/tutorial_2_autolog_in_mlflow. Attempting to export requirements via 'uv export'.


    2026/07/20 23:53:48 INFO mlflow.utils.uv_utils: Exported 177 dependencies via uv


    2026/07/20 23:53:48 INFO mlflow.utils.environment: Successfully exported 177 requirements from uv project. Skipping package capture based inference.


    2026/07/20 23:53:49 WARNING mlflow.utils.environment: Failed to resolve installed pip version. ``pip`` will be added to conda.yaml environment spec without a version specifier.


    /Users/mac/Documents/admin/AgenticCraft/mlflow-tutorials/tutorial_2_autolog_in_mlflow/.venv/lib/python3.12/site-packages/sklearn/metrics/_classification.py:3424: FutureWarning: `y_pred` was renamed to `y_proba` in version 1.9 and will be removed in 1.11. Use `y_proba` instead.
      warnings.warn(


    2026/07/20 23:53:49 INFO mlflow.utils.autologging_utils: Created MLflow autologging run with ID '2dc1921d952c4a4ba9dc6b8412c3cb7e', which will track hyperparameters, performance metrics, model artifacts, and lineage information for the current sklearn workflow


    2026/07/20 23:53:49 INFO mlflow.utils.uv_utils: Detected uv project: found uv.lock and pyproject.toml in /Users/mac/Documents/admin/AgenticCraft/mlflow-tutorials/tutorial_2_autolog_in_mlflow


    2026/07/20 23:53:49 WARNING mlflow.sklearn: Saving scikit-learn models in the pickle or cloudpickle format requires exercising caution because these formats rely on Python's object serialization mechanism, which can execute arbitrary code during deserialization. The recommended safe alternative is the 'skops' format. For more information, see: https://scikit-learn.org/stable/model_persistence.html


    2026/07/20 23:53:49 INFO mlflow.utils.uv_utils: Detected uv project: found uv.lock and pyproject.toml in /Users/mac/Documents/admin/AgenticCraft/mlflow-tutorials/tutorial_2_autolog_in_mlflow


    2026/07/20 23:53:49 INFO mlflow.utils.environment: Detected uv project at /Users/mac/Documents/admin/AgenticCraft/mlflow-tutorials/tutorial_2_autolog_in_mlflow. Attempting to export requirements via 'uv export'.


    max_depth=4  ->  test acc 1.000


    2026/07/20 23:53:49 INFO mlflow.utils.uv_utils: Exported 177 dependencies via uv


    2026/07/20 23:53:49 INFO mlflow.utils.environment: Successfully exported 177 requirements from uv project. Skipping package capture based inference.


    2026/07/20 23:53:50 WARNING mlflow.utils.environment: Failed to resolve installed pip version. ``pip`` will be added to conda.yaml environment spec without a version specifier.


    /Users/mac/Documents/admin/AgenticCraft/mlflow-tutorials/tutorial_2_autolog_in_mlflow/.venv/lib/python3.12/site-packages/sklearn/metrics/_classification.py:3424: FutureWarning: `y_pred` was renamed to `y_proba` in version 1.9 and will be removed in 1.11. Use `y_proba` instead.
      warnings.warn(


    max_depth=8  ->  test acc 1.000


## Step 4 — Open the MLflow UI

Run this in a terminal (not the notebook), from the same folder:

```bash
mlflow ui --backend-store-uri sqlite:///mlflow.db
```

Then open **http://localhost:5000**.

> **macOS gotcha:** port 5000 is used by AirPlay Receiver. If the UI won't load, run `mlflow ui --port 5001` (and open :5001), or turn off AirPlay Receiver in System Settings > General > AirDrop & Handoff.

In the UI you can:
- Click a run to see auto-logged **params** (n_estimators, max_depth), **metrics**, and the saved **model** artifact.
- Select two or more runs and hit **Compare** to see them side by side.

That comparison is the whole point: you can now tell which settings gave the best result.


```python
# Optional: list your runs programmatically instead of the UI
runs = mlflow.search_runs(experiment_names=["sklearn-autolog-demo"])
cols = [col for col in runs.columns
        if col.startswith("params.") or col.startswith("metrics.")][:8]
print(runs[["run_id"] + cols].to_string(index=False) if not runs.empty else "No runs yet.")
```

                              run_id  metrics.training_log_loss  metrics.training_precision_score  metrics.RandomForestClassifier_score_X_te  metrics.training_score  metrics.training_recall_score  metrics.training_accuracy_score  metrics.training_roc_auc  metrics.training_f1_score
    2dc1921d952c4a4ba9dc6b8412c3cb7e                   0.035202                          1.000000                                        1.0                1.000000                       1.000000                         1.000000                  1.000000                   1.000000
    a07d8a67cf484aeabc9527a40815146d                   0.060804                          0.984146                                        1.0                0.983333                       0.983333                         0.983333                  1.000000                   0.983333
    44a0680080094b9b83469fbb03f75c67                   0.151527                          0.950000                                        1.0                0.950000                       0.950000                         0.950000                  0.996769                   0.950000
    b7503fed4e2340f0aa736b3040ca78b0                   0.037030                          1.000000                                        1.0                1.000000                       1.000000                         1.000000                  1.000000                   1.000000


## Recap

- **One line**, `mlflow.autolog()`, turned an untracked script into a full experiment history.
- Params, metrics, model, and signature were captured with no manual logging.
- The UI lets you compare runs and pick a winner.

**Next:** Notebook 2 does the same for PyTorch, with one important catch.
