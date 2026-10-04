"""Three scorers: a built-in LLM judge, our own LLM judge, and a code check on the trace."""

from mlflow.entities import Feedback, SpanType
from mlflow.genai.scorers import Guidelines, RelevanceToQuery, scorer

from shared.config import JUDGE_GUIDELINE, MODEL

# Built-in LLM judge. "vertex_ai:/<model>" makes Gemini on the Agent Platform the judge
# (Application Default Credentials, project and location set in agent.setup()).
relevance = RelevanceToQuery(model=f"vertex_ai:/{MODEL}")

# Our own judge: same Gemini, but criteria we wrote (shared with Part 2).
travel_guidelines = Guidelines(
    name="travel_guidelines",
    guidelines=[JUDGE_GUIDELINE],
    model=f"vertex_ai:/{MODEL}",
)


@scorer
def right_tool(trace, expectations) -> Feedback:
    """Pass if the expected tool shows up as a TOOL span in the trace."""
    called = [span.name for span in trace.search_spans(span_type=SpanType.TOOL)]
    expected = expectations["expected_tool"]
    return Feedback(
        value=expected in called,
        rationale=f"Expected {expected}, agent called: {', '.join(called) or 'no tools'}",
    )


SCORERS = [relevance, travel_guidelines, right_tool]

# The LLM judges, saved to the experiment so they show on the MLflow "Judges" page.
# right_tool is left out: MLflow only allows registering @scorer code on Databricks.
# It still runs in every evaluation; its scores are under "Evaluation runs".
REGISTERED_JUDGES = [relevance, travel_guidelines]


def register_judges() -> None:
    """Save the LLM judges to the active experiment. Safe to call on every run."""
    for judge in REGISTERED_JUDGES:
        judge.register()
