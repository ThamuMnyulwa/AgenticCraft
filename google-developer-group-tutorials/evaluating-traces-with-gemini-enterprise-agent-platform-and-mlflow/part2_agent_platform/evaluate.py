"""Evaluate the deployed agent with the Agent Platform eval service.

Same five questions as Part 1. Two managed rubric judges, our own LLM judge
(same guideline as Part 1), and the same right_tool code check as Part 1.

Step 2 scores locally (all four metrics, results to GCS). Step 3 creates a
managed evaluation run with the three judges, so the results also show in the
Agent Platform console. right_tool is Python, so it cannot run in the service.
"""

import time

import agentplatform
import pandas as pd
from agentplatform import types

from part2_agent_platform.agent.agent import root_agent
from part2_agent_platform.settings import load_agent_resource, load_settings
from shared.config import JUDGE_GUIDELINE
from shared.eval_data import EVAL_DATA

EXPECTED_TOOL = {row["inputs"]["question"]: row["expectations"]["expected_tool"] for row in EVAL_DATA}


def find_values(data, key: str) -> list:
    """Collect every value stored under `key` anywhere in nested dicts and lists."""
    if isinstance(data, dict):
        found = [data[key]] if key in data else []
        return found + [v for value in data.values() for v in find_values(value, key)]
    if isinstance(data, list):
        return [v for item in data for v in find_values(item, key)]
    return []


def right_tool(instance: dict) -> dict:
    """Pass (1.0) if the expected tool appears in the agent's tool calls."""
    question = " ".join(find_values(instance.get("prompt", {}), "text")).strip()
    expected = EXPECTED_TOOL.get(question)
    called = [call["name"] for call in find_values(instance.get("intermediate_events", []), "function_call")]
    return {
        "score": 1.0 if expected in called else 0.0,
        "explanation": f"Expected {expected}, agent called: {', '.join(called) or 'no tools'}",
    }


EXPERIMENT = "devfest-travel-assistant"


def get_or_create_experiment(client) -> str:
    """One evaluation experiment in the console that groups every run of this demo."""
    for experiment in client.evals.list_evaluation_experiments().evaluation_experiments or []:
        if experiment.display_name == EXPERIMENT:
            return experiment.name
    return client.evals.create_evaluation_experiment(display_name=EXPERIMENT).name


# Our own LLM judge, with the same guideline as Part 1's MLflow Guidelines scorer.
# The eval service fills in {prompt} and {response} and expects the judge to reply
# in JSON ({{ and }} are literal braces). MetricPromptBuilder does not ask for JSON,
# so the service could not parse its replies; this explicit prompt fixes that.
JUDGE_PROMPT = (
    "You are judging the answer of a travel assistant.\n\n"
    f"Guideline: {JUDGE_GUIDELINE}\n\n"
    "User question:\n{prompt}\n\n"
    "Assistant answer:\n{response}\n\n"
    "Reply with JSON only, no other text, in exactly this form:\n"
    '{{"score": 1, "explanation": "one sentence"}}\n'
    "Use score 1 if the answer meets the guideline and 0 if it does not."
)
travel_guidelines = types.LLMMetric(name="travel_guidelines", prompt_template=JUDGE_PROMPT)


if __name__ == "__main__":
    settings = load_settings()
    client = agentplatform.Client(project=settings.project, location=settings.region)
    results_uri = f"gs://{settings.bucket}/evals"

    questions = list(EXPECTED_TOOL)
    dataset = pd.DataFrame(
        {
            "prompt": questions,
            "session_inputs": [types.evals.SessionInput(user_id="devfest-eval", state={})] * len(questions),
        }
    )

    print("Step 1: running the five questions through the deployed agent")
    answered = client.evals.run_inference(agent=load_agent_resource(), src=dataset).eval_dataset_df

    # run_inference records the conversation but not the agent's tool definitions,
    # and evaluate() ignores agent_info when a row already has agent_data. Without
    # this, the tool-use judge thinks the agent has no tools and under-scores it.
    agent_info = types.evals.AgentInfo.load_from_agent(root_agent)
    agents = {name: cfg.model_dump(mode="json", exclude_none=True) for name, cfg in agent_info.agents.items()}
    answered["agent_data"] = [{**row, "agents": agents} for row in answered["agent_data"]]

    print("Step 2: scoring the answers and tool calls")
    result = client.evals.evaluate(
        dataset=answered,
        metrics=[
            types.RubricMetric.FINAL_RESPONSE_QUALITY,  # did it complete the task well?
            # Did it use its tools sensibly? The service refuses to score a row with
            # no tool calls at all, so the bicycle row logs an error and is left out.
            types.RubricMetric.TOOL_USE_QUALITY,
            travel_guidelines,  # our own judge
            types.Metric(name="right_tool", custom_function=right_tool),
        ],
        config={"dest": results_uri},
    )

    print("\nPer-row results")
    names = ["final_response_quality_v1", "tool_use_quality_v1", "travel_guidelines", "right_tool"]
    for question, case in zip(questions, result.eval_case_results, strict=True):
        scores = case.response_candidate_results[0].metric_results
        cells = [
            f"{name.removesuffix('_v1')}={scores[name].score if scores[name].score is not None else 'n/a'}"
            for name in names
        ]
        print(f"  {'  '.join(cells)}  {question}")

    print("\nSummary metrics")
    for summary in result.summary_metrics:
        print(f"  {summary.metric_name}: {summary.mean_score}")

    print(f"\nResults written to {results_uri}")
    print(
        f"Browse them: https://console.cloud.google.com/storage/browser/{settings.bucket}/evals?project={settings.project}"
    )

    print("\nStep 3: managed evaluation run, so the judges show in the console")
    # No agent argument: the rows are already answered, so the service only scores them.
    run = client.evals.create_evaluation_run(
        dataset=types.EvaluationDataset(eval_dataset_df=answered),
        dest=f"gs://{settings.bucket}/eval-runs",
        display_name="devfest-travel-assistant-eval",
        evaluation_experiment=get_or_create_experiment(client),
        metrics=[
            types.RubricMetric.FINAL_RESPONSE_QUALITY,
            types.RubricMetric.TOOL_USE_QUALITY,
            travel_guidelines,
        ],
    )
    while run.state.name not in ("SUCCEEDED", "FAILED", "CANCELLED"):
        time.sleep(10)
        run = client.evals.get_evaluation_run(name=run.name)
    print(f"  {run.state.name}: {run.name}")
    print(f"  Console: Agent Platform > Evaluation > Experiments > '{EXPERIMENT}' ({settings.region})")
