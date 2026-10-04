"""Human review examples: review questions plus example reviews on the latest eval run.

MLflow labeling sessions (the Review App) need Databricks, but label schemas and
human feedback work on a local MLflow. The reviews below are scripted EXAMPLES of
what a reviewer would write, marked as such, so the audience can see where human
feedback sits next to the judges' scores on each trace.
"""

import mlflow
from mlflow.entities import AssessmentSource, AssessmentSourceType, SpanType
from mlflow.genai import label_schemas

from part1_mlflow.agent import EXPERIMENT, setup
from shared.eval_data import EVAL_DATA

EXPECTED_TOOL = {row["inputs"]["question"]: row["expectations"]["expected_tool"] for row in EVAL_DATA}
REVIEWER = AssessmentSource(source_type=AssessmentSourceType.HUMAN, source_id="example-reviewer")

# The questions a human reviewer answers for each trace.
SCHEMAS = {
    "used_right_tool": dict(
        type="feedback",
        input=label_schemas.InputPassFail(positive_label="Right tool", negative_label="Wrong or no tool"),
        instruction="Open the trace. Pass only if the agent called the tool the question needs.",
        enable_comment=True,
    ),
    "expected_answer": dict(
        type="expectation",
        input=label_schemas.InputText(),
        instruction="Write the answer (and tool use) you expected, if the agent got it wrong.",
    ),
}


def ensure_label_schemas(experiment_id: str) -> None:
    existing = {s.name for s in label_schemas.list_label_schemas(experiment_id)}
    for name, spec in SCHEMAS.items():
        if name not in existing:
            label_schemas.create_label_schema(name, experiment_id=experiment_id, **spec)


def latest_eval_run_id(experiment_id: str) -> str:
    runs = mlflow.search_runs([experiment_id], order_by=["attributes.start_time DESC"], max_results=20)
    eval_runs = runs[runs.filter(like="metrics.right_tool").notna().any(axis=1)]
    if eval_runs.empty:
        raise SystemExit("No evaluation run found. Run ./demo.sh part1 first.")
    return eval_runs.iloc[0]["run_id"]


def already_reviewed(assessments: list[dict]) -> bool:
    return any(
        a.get("assessment_name") == "used_right_tool" and a.get("source", {}).get("source_type") == "HUMAN"
        for a in assessments
    )


def log_example_review(trace_id: str, question: str, called: list[str]) -> bool:
    expected = EXPECTED_TOOL.get(question)
    right = expected in called
    comment = (
        "Example review: right tool, answer checks out."
        if right
        else f"Example review: the answer is right, but the agent did the maths in its head instead of "
        f"calling {expected}. The system prompt says 'complex arithmetic'; drop the word 'complex'."
    )
    mlflow.log_feedback(
        trace_id=trace_id,
        name="used_right_tool",
        value=right,
        source=REVIEWER,
        rationale=comment,
        metadata={"example": "true"},
    )
    if not right:
        mlflow.log_expectation(
            trace_id=trace_id,
            name="expected_answer",
            value=f"The same answer, after calling the {expected} tool.",
            source=REVIEWER,
            metadata={"example": "true"},
        )
    return right


if __name__ == "__main__":
    setup()
    experiment_id = mlflow.get_experiment_by_name(EXPERIMENT).experiment_id
    ensure_label_schemas(experiment_id)
    run_id = latest_eval_run_id(experiment_id)

    print(f"Example human reviews on evaluation run {run_id}")
    for _, row in mlflow.search_traces(run_id=run_id).iterrows():
        question = row["request"]["question"]
        if already_reviewed(row["assessments"]):
            print(f"  already reviewed   {question}")
            continue
        trace = mlflow.get_trace(row["trace_id"])
        called = [span.name for span in trace.search_spans(span_type=SpanType.TOOL)]
        right = log_example_review(row["trace_id"], question, called)
        print(f"  {'Right tool' if right else 'Wrong or no tool':17}  {question}")
    print(f"\nSee them on each trace: http://localhost:5000/#/experiments/{experiment_id}/runs/{run_id}")
