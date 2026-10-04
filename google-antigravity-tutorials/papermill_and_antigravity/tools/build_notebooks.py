"""Authoring utility: (re)generate all five demo notebooks from source.

Run from the repo root:
    uv run --project after python tools/build_notebooks.py
"""

from pathlib import Path

import nbformat as nbf

KERNELSPEC = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python"},
}


def code(source, tags=None):
    cell = nbf.v4.new_code_cell(source)
    if tags:
        cell.metadata["tags"] = tags
    return cell


def md(source):
    return nbf.v4.new_markdown_cell(source)


def write(path, cells):
    nb = nbf.v4.new_notebook()
    nb.metadata.update(KERNELSPEC)
    nb.cells = cells
    stem = Path(path).stem
    for i, cell in enumerate(nb.cells):
        cell.id = f"{stem}-{i}"
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    nbf.write(nb, path)
    print(f"wrote {path}")


FE = """\
def engineer_features(df):
    # Turn raw Titanic rows into model-ready numeric features.
    out = pd.DataFrame()
    out["Pclass"] = df["Pclass"]
    out["Sex"] = (df["Sex"] == "female").astype(int)
    out["Age"] = df["Age"].fillna(df["Age"].median())
    out["Fare"] = df["Fare"].fillna(df["Fare"].median())
    out["SibSp"] = df["SibSp"]
    out["Parch"] = df["Parch"]
    embarked = pd.get_dummies(df["Embarked"].fillna("S"), prefix="Embarked")
    for col in ["Embarked_C", "Embarked_Q", "Embarked_S"]:
        out[col] = embarked[col].astype(int) if col in embarked else 0
    return out"""


# --- before/: step (1), everything in one notebook --------------------------

write(
    "before/titanic_model.ipynb",
    [
        md(
            "# Titanic survival — everything in one notebook\n\n"
            "Step ① of the talk: data → feature engineering → model training → "
            "scoring, all in a single notebook, run by hand."
        ),
        code("""\
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split"""),
        md("## Load data"),
        code("""\
df = pd.read_csv("data/titanic.csv")
print(f"{len(df)} passengers")
df.head()"""),
        md("## Feature engineering"),
        code(FE),
        code("""\
X = engineer_features(df)
y = df["Survived"]
X.head()"""),
        md("## Model training"),
        code("""\
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
model = LogisticRegression(max_iter=1000)
model.fit(X_train, y_train)"""),
        md("## Scoring / model serving"),
        code("""\
accuracy = accuracy_score(y_test, model.predict(X_test))
print(f"Holdout accuracy: {accuracy:.3f}")"""),
        code("""\
predictions = pd.DataFrame({
    "PassengerId": df.loc[X_test.index, "PassengerId"],
    "SurvivalProbability": model.predict_proba(X_test)[:, 1].round(3),
    "PredictedSurvived": model.predict(X_test),
})
predictions.to_csv("predictions.csv", index=False)
predictions.head(10)"""),
    ],
)


# --- after/: step (4), four single-purpose notebooks -------------------------

write(
    "after/notebooks/fs_train.ipynb",
    [
        md(
            "# FS_TRAIN — feature engineering (training data)\n\n"
            "Reads raw training data, writes model-ready features including the "
            "`Survived` label."
        ),
        code(
            '''\
# Parameters (papermill overrides these at run time)
input_path = "data/train.csv"
features_path = "output/train_features.csv"''',
            tags=["parameters"],
        ),
        code("import pandas as pd"),
        code("""\
df = pd.read_csv(input_path)
print(f"{len(df)} passengers read from {input_path}")"""),
        code(FE),
        code("""\
features = engineer_features(df)
features["Survived"] = df["Survived"]
features.to_csv(features_path, index=False)
print(f"Wrote {features.shape[0]} rows x {features.shape[1]} cols to {features_path}")
features.head()"""),
    ],
)

write(
    "after/notebooks/train.ipynb",
    [
        md(
            "# TRAIN — fit the model\n\n"
            "Reads engineered training features, fits a logistic regression, "
            "saves the model object."
        ),
        code(
            '''\
# Parameters (papermill overrides these at run time)
features_path = "output/train_features.csv"
model_path = "output/model.pkl"''',
            tags=["parameters"],
        ),
        code("""\
import pickle

import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split"""),
        code("""\
features = pd.read_csv(features_path)
y = features.pop("Survived")
X = features
print(f"{len(X)} rows, {X.shape[1]} features")"""),
        code("""\
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
model = LogisticRegression(max_iter=1000)
model.fit(X_train, y_train)
accuracy = accuracy_score(y_test, model.predict(X_test))
print(f"Holdout accuracy: {accuracy:.3f}")"""),
        code("""\
with open(model_path, "wb") as f:
    pickle.dump(model, f)
print(f"Model saved to {model_path}")"""),
    ],
)

write(
    "after/notebooks/fs_score.ipynb",
    [
        md(
            "# FS_SCORE — feature engineering (scoring data)\n\n"
            "Reads raw, unlabelled passenger data and writes model-ready features, "
            "keeping `PassengerId` so predictions can be traced back."
        ),
        code(
            '''\
# Parameters (papermill overrides these at run time)
input_path = "data/score.csv"
features_path = "output/score_features.csv"''',
            tags=["parameters"],
        ),
        code("import pandas as pd"),
        code("""\
df = pd.read_csv(input_path)
print(f"{len(df)} passengers read from {input_path}")"""),
        code(FE),
        code("""\
features = engineer_features(df)
features.insert(0, "PassengerId", df["PassengerId"])
features.to_csv(features_path, index=False)
print(f"Wrote {features.shape[0]} rows x {features.shape[1]} cols to {features_path}")
features.head()"""),
    ],
)

write(
    "after/notebooks/score.ipynb",
    [
        md(
            "# SCORE — predict with the trained model\n\n"
            "Loads the pickled model and the engineered scoring features, writes "
            "predictions."
        ),
        code(
            '''\
# Parameters (papermill overrides these at run time)
features_path = "output/score_features.csv"
model_path = "output/model.pkl"
predictions_path = "output/predictions.csv"''',
            tags=["parameters"],
        ),
        code("""\
import pickle

import pandas as pd"""),
        code("""\
with open(model_path, "rb") as f:
    model = pickle.load(f)
model"""),
        code("""\
features = pd.read_csv(features_path)
passenger_ids = features.pop("PassengerId")
print(f"{len(features)} passengers to score")"""),
        code("""\
predictions = pd.DataFrame({
    "PassengerId": passenger_ids,
    "SurvivalProbability": model.predict_proba(features)[:, 1].round(3),
    "PredictedSurvived": model.predict(features),
})
predictions.to_csv(predictions_path, index=False)
print(f"Wrote {len(predictions)} predictions to {predictions_path}")
predictions.head(10)"""),
    ],
)
