"""Ask the agent three questions as one chat session, so we have traces to look at.

The three traces share a session ID, so the MLflow "Sessions" page shows them as one
conversation. (The agent itself is stateless: each question stands on its own.)
"""

from datetime import datetime

from part1_mlflow.agent import run_agent, setup

QUESTIONS = [
    "What's the weather like in Cape Town today?",
    "What is 1234 * 5678?",
    "Is it warmer in Tokyo or London right now?",
]

if __name__ == "__main__":
    setup()
    session_id = f"trip-planning-{datetime.now():%Y%m%d-%H%M%S}"
    print(f"Session: {session_id}\n")
    for question in QUESTIONS:
        print(f"Q: {question}\nA: {run_agent(question, session_id=session_id)}\n")
