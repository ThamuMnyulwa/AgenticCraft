"""One-off authoring utility: split the vendored Titanic CSV into the
after/ pipeline's train and score inputs.

Run from the repo root:
    uv run --project before python tools/split_data.py
"""

import pandas as pd

df = pd.read_csv("before/data/titanic.csv")
train = df.sample(frac=0.8, random_state=42).sort_values("PassengerId")
score = df.drop(index=train.index).sort_values("PassengerId").drop(columns=["Survived"])
train.to_csv("after/data/train.csv", index=False)
score.to_csv("after/data/score.csv", index=False)
print(f"train: {len(train)} rows, score: {len(score)} rows")
