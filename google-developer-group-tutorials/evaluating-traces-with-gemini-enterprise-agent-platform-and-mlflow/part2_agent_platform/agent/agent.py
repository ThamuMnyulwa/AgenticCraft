"""The same agent as Part 1, rebuilt with ADK so it can run on Agent Runtime."""

from google.adk.agents import LlmAgent

from shared.config import MODEL, SYSTEM_INSTRUCTION
from shared.tools import TOOLS

root_agent = LlmAgent(
    name="travel_assistant",
    model=MODEL,
    instruction=SYSTEM_INSTRUCTION,
    tools=TOOLS,
)
