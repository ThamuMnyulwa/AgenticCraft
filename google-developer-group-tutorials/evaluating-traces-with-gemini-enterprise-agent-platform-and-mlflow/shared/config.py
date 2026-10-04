"""Settings shared by Part 1 (MLflow) and Part 2 (Agent Platform)."""

# The one place to change the model for the whole demo.
MODEL = "gemini-3.5-flash"

# Both parts call Gemini through the Agent Platform (billed to the Cloud billing
# account). gemini-3.5-flash is served from the global endpoint, not from
# europe-west1, so model calls go to "global" even though the infra is regional.
MODEL_LOCATION = "global"

# Same instruction in both parts, so the audience sees one agent at two scales.
# Note the word "complex": it is the realistic prompt bug the evals catch. The model
# decides "2 bicycles" is not complex and does the maths in its head.
SYSTEM_INSTRUCTION = (
    "You are a friendly travel assistant. "
    "Use the get_weather tool for weather questions. "
    "Use the calculator tool for complex arithmetic. "
    "Answer in one or two short sentences."
)
