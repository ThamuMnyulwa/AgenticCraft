from part2_agent_platform.evaluate import JUDGE_PROMPT
from shared.config import JUDGE_GUIDELINE


def test_part2_judge_uses_the_same_guideline_as_part1():
    assert JUDGE_GUIDELINE in JUDGE_PROMPT


def test_judge_prompt_has_the_service_placeholders():
    assert "{prompt}" in JUDGE_PROMPT and "{response}" in JUDGE_PROMPT
