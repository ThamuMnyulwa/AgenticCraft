"""Evaluate the deployed agent with the Agent Platform eval service.

Same five questions as Part 1. Two managed rubric metrics, plus the same
right_tool check from Part 1 written as a custom metric.
"""

import agentplatform
import pandas as pd
from agentplatform import types

from part2_agent_platform.agent.agent import root_agent
from part2_agent_platform.settings import load_agent_resource, load_settings
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
    answered = client.evals.run_inference(agent=load_agent_resource(), src=dataset)

    print("Step 2: scoring the answers and tool calls")
    result = client.evals.evaluate(
        dataset=answered,
        metrics=[
            types.RubricMetric.FINAL_RESPONSE_QUALITY,  # did it complete the task well?
            types.RubricMetric.TOOL_USE_QUALITY,  # did it use its tools sensibly?
            types.Metric(name="right_tool", custom_function=right_tool),
        ],
        agent_info=types.evals.AgentInfo.load_from_agent(root_agent),
        config={"dest": results_uri},
    )

    print("\nSummary metrics")
    for summary in result.summary_metrics:
        print(f"  {summary.metric_name}: {summary.mean_score}")

    print(f"\nResults written to {results_uri}")
    print(
        f"Browse them: https://console.cloud.google.com/storage/browser/{settings.bucket}/evals?project={settings.project}"
    )
