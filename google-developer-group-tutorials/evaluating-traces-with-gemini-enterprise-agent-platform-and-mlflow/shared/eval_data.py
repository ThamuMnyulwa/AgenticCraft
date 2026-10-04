"""Five evaluation rows, used by both parts. Each one says which tool the agent should use."""

EVAL_DATA = [
    {
        "inputs": {"question": "What's the weather in Johannesburg today?"},
        "expectations": {"expected_tool": "get_weather"},
    },
    {
        "inputs": {"question": "Should I pack an umbrella for London?"},
        "expectations": {"expected_tool": "get_weather"},
    },
    {
        "inputs": {"question": "What is 1234 * 5678?"},
        "expectations": {"expected_tool": "calculator"},
    },
    {
        "inputs": {"question": "Split a 2,450 rand dinner bill evenly between 7 friends. How much each?"},
        "expectations": {"expected_tool": "calculator"},
    },
    # THIS ROW FAILS ON PURPOSE.
    # The answer is arithmetic (2 x 2 = 4), so we expect the calculator.
    # But the system instruction says "complex arithmetic", the question reads
    # like trivia, and Gemini answers from memory without calling a tool.
    # The answer is still right, which is the point: a correct answer can hide
    # the wrong behaviour, and only the trace shows it. (Failed 3 out of 3 runs.)
    {
        "inputs": {"question": "How many wheels do 2 bicycles have?"},
        "expectations": {"expected_tool": "calculator"},
    },
]
