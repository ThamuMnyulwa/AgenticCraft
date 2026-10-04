from part1_mlflow.evaluate import THRESHOLDS, pass_rate


def test_pass_rate_counts_true_and_yes():
    assert pass_rate([True, True, True, True, False]) == 0.8
    assert pass_rate(["yes", "yes", "no", "yes"]) == 0.75


def test_one_deliberate_failure_still_passes_the_gate():
    assert pass_rate([True, True, True, True, False]) >= THRESHOLDS["right_tool"]
