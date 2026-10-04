"""A small Gemini agent with function calling, traced end to end by MLflow."""

import os

import mlflow
from dotenv import load_dotenv
from google import genai
from google.genai import types

from shared.config import MODEL, SYSTEM_INSTRUCTION
from shared.tools import TOOLS

load_dotenv()

EXPERIMENT = "devfest-evals"
TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db")


def setup_mlflow() -> None:
    mlflow.set_tracking_uri(TRACKING_URI)
    mlflow.set_experiment(EXPERIMENT)
    mlflow.gemini.autolog()  # every Gemini call becomes an LLM span


client = genai.Client()  # reads GEMINI_API_KEY

# Autolog traces the LLM calls. We trace the tools ourselves so they show up as TOOL spans.
traced_tools = {tool.__name__: mlflow.trace(tool, span_type="TOOL") for tool in TOOLS}

config = types.GenerateContentConfig(
    system_instruction=SYSTEM_INSTRUCTION,
    tools=TOOLS,
    temperature=0,
    # We run the tool loop ourselves, so each step is visible in the trace.
    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
)


@mlflow.trace(span_type="AGENT")
def run_agent(question: str) -> str:
    contents = [types.Content(role="user", parts=[types.Part(text=question)])]

    for _ in range(5):  # safety limit on tool round trips
        response = client.models.generate_content(model=MODEL, contents=contents, config=config)
        if not response.function_calls:
            return response.text

        contents.append(response.candidates[0].content)
        results = [
            types.Part.from_function_response(name=call.name, response=traced_tools[call.name](**call.args))
            for call in response.function_calls
        ]
        contents.append(types.Content(role="user", parts=results))

    return "Sorry, I could not finish that request."
