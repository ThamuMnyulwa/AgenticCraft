from part2_agent_platform.evaluate import right_tool


def eval_case(question: str, tools: list[str]) -> dict:
    events = [{"content": {"parts": [{"function_call": {"name": name, "args": {}}}]}} for name in tools]
    return {"prompt": {"parts": [{"text": question}]}, "intermediate_events": events}


def test_passes_when_expected_tool_called():
    result = right_tool(eval_case("What is 1234 * 5678?", ["calculator"]))
    assert result["score"] == 1.0


def test_fails_when_no_tool_called():
    result = right_tool(eval_case("How many wheels do 2 bicycles have?", []))
    assert result["score"] == 0.0
    assert "no tools" in result["explanation"]
