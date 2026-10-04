"""Two scorers: an LLM judge (Gemini) and a code check on the trace."""

from mlflow.entities import Feedback, SpanType
from mlflow.genai.scorers import RelevanceToQuery, scorer

from shared.config import MODEL

# Built-in LLM judge. "vertex_ai:/<model>" makes Gemini on the Agent Platform the judge
# (Application Default Credentials, project and location set in agent.setup()).
relevance = RelevanceToQuery(model=f"vertex_ai:/{MODEL}")


@scorer
def right_tool(trace, expectations) -> Feedback:
    """Pass if the expected tool shows up as a TOOL span in the trace."""
    called = [span.name for span in trace.search_spans(span_type=SpanType.TOOL)]
    expected = expectations["expected_tool"]
    return Feedback(
        value=expected in called,
        rationale=f"Expected {expected}, agent called: {', '.join(called) or 'no tools'}",
    )


SCORERS = [relevance, right_tool]
