from finexpert.evaluation.report import build_report, format_report


ROWS = [
    {
        "example_id": "c1",
        "category": "financial_classification",
        "difficulty": "easy",
        "messages": [
            {"role": "system", "content": "..."},
            {"role": "user", "content": "Revenue is ₹500 Cr."},
            {"role": "assistant", "content": "Classification: Healthy\nEvidence: Revenue is ₹500 Cr."},
        ],
    },
    {
        "example_id": "e1",
        "category": "financial_explanation",
        "difficulty": "medium",
        "messages": [
            {"role": "system", "content": "..."},
            {"role": "user", "content": "Revenue increased from ₹500 Cr to ₹575 Cr."},
            {"role": "assistant", "content": "Revenue increased by 15%, from ₹500 Cr to ₹575 Cr."},
        ],
    },
    {
        "example_id": "r1",
        "category": "financial_report_generation",
        "difficulty": "medium",
        "messages": [
            {"role": "system", "content": "..."},
            {"role": "user", "content": "Revenue increased from ₹500 Cr to ₹575 Cr."},
            {"role": "assistant", "content": (
                "Executive Summary: Revenue increased by 15%.\n\n"
                "Quantitative Analysis: Revenue increased by 15%.\n\n"
                "Key Observations: Revenue increased.\n\n"
                "Risks and Opportunities: None stated.\n\n"
                "Areas Requiring Further Investigation: More history.\n\n"
                "Conclusion: The figures should be reviewed together."
            )},
        ],
    },
]


def test_report_aggregates_findings():
    predictions = {row["example_id"]: row["messages"][2]["content"] for row in ROWS}
    report = build_report(ROWS, predictions)

    assert report["summary"]["classification"]["accuracy"] == 1.0
    assert report["summary"]["numerical"]["numeric_precision"] == 1.0
    assert report["summary"]["numerical"]["numeric_recall"] == 1.0
    assert report["summary"]["structure"]["section_coverage"] == 1.0
    assert report["summary"]["semantic_evaluation"]["status"] == "deferred"


def test_report_identifies_numeric_failure_from_input():
    predictions = {
        "c1": ROWS[0]["messages"][2]["content"],
        "e1": "Revenue increased by 14.3%, from ₹500 Cr to ₹575 Cr.",
        "r1": ROWS[2]["messages"][2]["content"],
    }

    report = build_report(ROWS, predictions)
    codes = report["summary"]["failure_breakdown"]["finding_codes"]
    assert codes["PERCENTAGE_MATH_ERROR"] == 1


def test_missing_prediction_raises():
    predictions = {
        "c1": ROWS[0]["messages"][2]["content"],
        "e1": ROWS[1]["messages"][2]["content"],
    }
    try:
        build_report(ROWS, predictions)
    except ValueError as exc:
        assert "Missing predictions" in str(exc)
    else:
        raise AssertionError("Expected missing prediction error")


def test_format_report_is_readable():
    predictions = {row["example_id"]: row["messages"][2]["content"] for row in ROWS}
    text = format_report(build_report(ROWS, predictions))
    assert "FINEXPERT EVALUATION" in text
    assert "Numeric precision" in text
    assert "Section coverage" in text
    assert "Semantic evaluation:  deferred" in text
