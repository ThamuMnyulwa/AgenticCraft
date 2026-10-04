"""Send a handful of questions to the deployed agent so traces show up in Cloud Trace."""

import asyncio

import agentplatform

from part2_agent_platform.settings import load_agent_resource, load_settings
from shared.eval_data import EVAL_DATA

EXTRA_QUESTIONS = [
    "Is it warmer in Tokyo or London right now?",
    "What is the weather in Atlantis?",
]
QUESTIONS = [row["inputs"]["question"] for row in EVAL_DATA] + EXTRA_QUESTIONS


async def ask(remote_agent, question: str) -> None:
    tools, answer = [], ""
    async for event in remote_agent.async_stream_query(user_id="devfest-demo", message=question):
        for part in event.get("content", {}).get("parts", []):
            if "function_call" in part:
                tools.append(part["function_call"]["name"])
            if "text" in part:
                answer += part["text"]
    print(f"Q: {question}\n   tools: {', '.join(tools) or 'none'}\n   A: {answer.strip()}\n")


async def main() -> None:
    settings = load_settings()
    client = agentplatform.Client(project=settings.project, location=settings.region)
    remote_agent = client.runtimes.get(name=load_agent_resource())
    for question in QUESTIONS:
        await ask(remote_agent, question)
    print(f"Traces: https://console.cloud.google.com/traces/list?project={settings.project}")


if __name__ == "__main__":
    asyncio.run(main())
