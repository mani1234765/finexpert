"""Tests for paired run comparison."""

import pytest
from scipy.stats import binomtest

from finexpert.evaluation.compare import compare_qa_reports, format_comparison, mcnemar_exact


@pytest.mark.parametrize("b, c", [(47, 31), (42, 40), (28, 14), (31, 128), (0, 5), (3, 3)])
def test_mcnemar_matches_scipy_binomial_test(b, c):
    expected = binomtest(min(b, c), b + c, 0.5).pvalue
    assert mcnemar_exact(b, c) == pytest.approx(expected, rel=1e-9)


def test_mcnemar_no_discordant_pairs():
    assert mcnemar_exact(0, 0) == 1.0


def _report(results):
    return {"examples": [{"example_id": i, "source": "finqa", "strict": {"correct": ok}} for i, ok in results.items()]}


def test_compare_counts_discordant_pairs():
    a = _report({"q1": True, "q2": True, "q3": False, "q4": False})
    b = _report({"q1": True, "q2": False, "q3": True, "q4": True})
    row = compare_qa_reports(a, b, "finqa")
    assert (row["both_right"], row["a_right_b_wrong"], row["a_wrong_b_right"], row["both_wrong"]) == (1, 1, 2, 0)
    assert row["difference_b_minus_a"] == pytest.approx(0.25)


def test_compare_refuses_different_question_sets():
    with pytest.raises(ValueError):
        compare_qa_reports(_report({"q1": True}), _report({"q2": True}), "finqa")


def test_tiny_p_values_are_not_printed_as_zero():
    row = {"source": "tatqa", "n": 300, "accuracy_a": 0.3, "accuracy_b": 0.6, "difference_b_minus_a": 0.3,
           "a_right_b_wrong": 31, "a_wrong_b_right": 128, "p_value": mcnemar_exact(31, 128)}
    assert "< 0.0001" in format_comparison([row], "a", "b")
