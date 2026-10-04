"""Human review examples: a review queue, review questions and example reviews.

The MLflow "Review" page lists review queues. This script puts the latest eval
run's traces in the "devfest-review" queue, with two review questions (label
schemas), and logs scripted EXAMPLE reviews of what a reviewer would write, marked
as such. Each reviewed item is marked complete, and the reviews also show next to
the judges' scores on each trace. (Databricks labeling sessions are not needed.)
"""

import mlflow
from mlflow.entities import AssessmentSource, AssessmentSourceType, SpanType
from mlflow.genai import label_schemas, review_queues

from part1_mlflow.agent import EXPERIMENT, setup
from shared.eval_data import EVAL_DATA

EXPECTED_TOOL = {row["inputs"]["question"]: row["expectations"]["expected_tool"] for row in EVAL_DATA}
REVIEWER_NAME = "example-reviewer"
REVIEWER = AssessmentSource(source_type=AssessmentSourceType.HUMAN, source_id=REVIEWER_NAME)
QUEUE_NAME = "devfest-review"

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


def ensure_label_schemas(experiment_id: str) -> list[str]:
    """Create the review questions if missing. Returns their schema IDs."""
    existing = {s.name: s for s in label_schemas.list_label_schemas(experiment_id)}
    for name, spec in SCHEMAS.items():
        if name not in existing:
            existing[name] = label_schemas.create_label_schema(name, experiment_id=experiment_id, **spec)
    return [existing[name].schema_id for name in SCHEMAS]


def ensure_queue(experiment_id: str, schema_ids: list[str]):
    """The "devfest-review" queue on the Review page (review_queues is experimental)."""
    for queue in review_queues.list_review_queues(experiment_id=experiment_id):
        if queue.name == QUEUE_NAME:
            return queue
    return review_queues.create_review_queue(
        QUEUE_NAME, queue_type="custom", schema_ids=schema_ids, experiment_id=experiment_id
    )


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
    queue = ensure_queue(experiment_id, ensure_label_schemas(experiment_id))
    run_id = latest_eval_run_id(experiment_id)
    traces = mlflow.search_traces(run_id=run_id)
    queued = {item.item_id for item in review_queues.list_review_queue_items(queue.queue_id)}
    new_items = [trace_id for trace_id in traces["trace_id"] if trace_id not in queued]
    if new_items:
        review_queues.add_items_to_review_queue(queue.queue_id, item_ids=new_items)

    print(f"Example human reviews on evaluation run {run_id}")
    for _, row in traces.iterrows():
        question = row["request"]["question"]
        if already_reviewed(row["assessments"]):
            verdict = "already reviewed"
        else:
            trace = mlflow.get_trace(row["trace_id"])
            called = [span.name for span in trace.search_spans(span_type=SpanType.TOOL)]
            right = log_example_review(row["trace_id"], question, called)
            verdict = "Right tool" if right else "Wrong or no tool"
        review_queues.set_review_queue_item_status(
            queue.queue_id, item_id=row["trace_id"], status="complete", completed_by=REVIEWER_NAME
        )
        print(f"  {verdict:17}  {question}")
    print(f"\nReview page: queue '{QUEUE_NAME}'. Also on each trace of run {run_id}.")
