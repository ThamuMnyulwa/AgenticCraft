"""The same agent as Part 1, rebuilt with ADK so it can run on Agent Runtime."""

from google.adk.agents import LlmAgent
from google.adk.models import Gemini

from shared.config import MODEL, MODEL_LOCATION, SYSTEM_INSTRUCTION
from shared.tools import TOOLS

root_agent = LlmAgent(
    name="travel_assistant",
    # The agent runs in europe-west1, but the model is served from the global endpoint.
    model=Gemini(model=MODEL, client_kwargs={"enterprise": True, "location": MODEL_LOCATION}),
    instruction=SYSTEM_INSTRUCTION,
    tools=TOOLS,
)
