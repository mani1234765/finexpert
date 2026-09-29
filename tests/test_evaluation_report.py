import pytest

from finexpert.evaluation.report import build_report, format_report


ROWS = [
    {
        "example_id": "c1",
        "category": "financial_classification",
        "difficulty": "easy",
        "user": "Revenue is ₹500 Cr.",
        "assistant": "Classification: Healthy\nEvidence: Revenue is ₹500 Cr.",
    },
    {
        "example_id": "c2",
        "category": "financial_classification",
        "difficulty": "easy",
        "user": "Debt increased from ₹100 Cr to ₹200 Cr.",
        "assistant": "Classification: High Risk\nEvidence: Debt doubled.",
    },
    {
        "example_id": "e1",
        "category": "financial_explanation",
        "difficulty": "medium",
        "user": "Revenue increased from ₹500 Cr to ₹575 Cr.",
        "assistant": "Revenue increased by 15%, from ₹500 Cr to ₹575 Cr.",
    },
]


def test_perfect_model_scores_perfectly():
    predictions = {r["example_id"]: r["assistant"] for r in ROWS}

    report = build_report(ROWS, predictions)

    assert report["by_category"]["financial_classification"]["label_accuracy"] == 1.0
    assert report["by_category"]["financial_classification"]["format_rate"] == 1.0
    assert report["by_category"]["financial_explanation"]["figure_fidelity"] == 1.0
    assert report["misses"] == []


def test_wrong_label_is_reported_as_a_miss():
    predictions = {
        "c1": "Classification: High Risk\nEvidence: ...",  # wrong, was Healthy
        "c2": ROWS[1]["assistant"],
        "e1": ROWS[2]["assistant"],
    }

    report = build_report(ROWS, predictions)

    assert report["by_category"]["financial_classification"]["label_accuracy"] == 0.5
    miss_ids = {m["example_id"] for m in report["misses"]}
    assert "c1" in miss_ids
    assert "c2" not in miss_ids


def test_invented_figure_is_reported_as_a_miss():
    predictions = {
        "c1": ROWS[0]["assistant"],
        "c2": ROWS[1]["assistant"],
        "e1": "Revenue increased by 15%. Operating profit is ₹999 Cr.",
    }

    report = build_report(ROWS, predictions)

    assert report["by_category"]["financial_explanation"]["figure_fidelity"] == 0.0
    miss_ids = {m["example_id"] for m in report["misses"]}
    assert "e1" in miss_ids


def test_missing_prediction_raises():
    with pytest.raises(ValueError):
        build_report(ROWS, {"c1": ROWS[0]["assistant"], "c2": ROWS[1]["assistant"]})
    # e1 missing on purpose


def test_format_report_is_readable_text():
    predictions = {r["example_id"]: r["assistant"] for r in ROWS}
    report = build_report(ROWS, predictions)

    text = format_report(report)

    assert "financial_classification" in text
    assert "Evaluated 3 examples" in text
