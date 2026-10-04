"""Ask the agent three questions so we have traces to look at in the MLflow UI."""

from part1_mlflow.agent import run_agent, setup

QUESTIONS = [
    "What's the weather like in Cape Town today?",
    "What is 1234 * 5678?",
    "Is it warmer in Tokyo or London right now?",
]

if __name__ == "__main__":
    setup()
    for question in QUESTIONS:
        print(f"Q: {question}\nA: {run_agent(question)}\n")
