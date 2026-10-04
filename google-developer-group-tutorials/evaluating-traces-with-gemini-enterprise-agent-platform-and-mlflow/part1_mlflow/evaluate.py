"""Run the agent over the eval dataset and score every trace.

With --gate, exit with an error when quality drops below the thresholds (used in CI).
"""

import sys

import mlflow

from part1_mlflow.agent import EXPERIMENT, run_agent, setup
from part1_mlflow.scorers import SCORERS, register_judges
from shared.eval_data import EVAL_DATA

UI_URL = "http://localhost:5000"

# Minimum share of rows that must pass. right_tool allows for the one row that fails on purpose.
THRESHOLDS = {"right_tool": 0.8, "relevance_to_query": 1.0}


def pass_rate(values) -> float:
    return sum(value is True or value == "yes" for value in values) / len(values)


if __name__ == "__main__":
    setup()
    register_judges()  # so they also show on the MLflow "Judges" page
    results = mlflow.genai.evaluate(data=EVAL_DATA, predict_fn=run_agent, scorers=SCORERS)

    table = results.result_df
    print("\nPer-row results")
    for _, row in table.iterrows():
        print(
            f"  right_tool={str(row['right_tool/value']):5}  "
            f"relevance={str(row['relevance_to_query/value']):4}  "
            f"guidelines={str(row['travel_guidelines/value']):4}  "
            f"{row['request']['question']}"
        )

    print("\nSummary metrics")
    for name, value in sorted(results.metrics.items()):
        print(f"  {name}: {value:.2f}" if isinstance(value, float) else f"  {name}: {value}")

    experiment_id = mlflow.get_experiment_by_name(EXPERIMENT).experiment_id
    print(f"\nOpen the run in the MLflow UI: {UI_URL}/#/experiments/{experiment_id}/runs/{results.run_id}")

    print("\nQuality gate")
    failed = False
    for scorer_name, minimum in THRESHOLDS.items():
        rate = pass_rate(table[f"{scorer_name}/value"])
        status = "ok" if rate >= minimum else "FAIL"
        failed |= rate < minimum
        print(f"  {status:4} {scorer_name}: {rate:.0%} passed (minimum {minimum:.0%})")

    if failed and "--gate" in sys.argv:
        sys.exit("Quality gate failed.")
