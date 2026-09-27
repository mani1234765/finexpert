from finexpert.data.difficulty_validator import (
    extract_financial_metrics,
    validate_difficulty,
)
from finexpert.data.schema import FinancialExample


def make_example(
    difficulty,
    input_text,
    reasoning_type,
):
    return FinancialExample(
        example_id="test",
        instruction="Analyze the financial information.",
        input=input_text,
        expected_output="Financial analysis.",
        category="financial_explanation",
        difficulty=difficulty,
        reasoning_type=reasoning_type,
        source_type="synthetic",
        company="Test Company",
    )


def test_extract_single_metric():
    metrics = extract_financial_metrics(
        "Revenue increased from ₹100 Cr to ₹120 Cr."
    )

    assert metrics == {"revenue"}


def test_extract_multiple_metrics():
    metrics = extract_financial_metrics(
        "Revenue increased while operating profit declined "
        "and debt increased."
    )

    assert metrics == {
        "revenue",
        "operating_profit",
        "debt",
    }


def test_easy_example_is_valid():
    example = make_example(
        difficulty="easy",
        input_text=(
            "Revenue increased from ₹100 Cr to ₹120 Cr."
        ),
        reasoning_type=[
            "numerical_reasoning",
        ],
    )

    result = validate_difficulty(example)

    assert result["success"] is True


def test_medium_requires_multiple_metrics():
    example = make_example(
        difficulty="medium",
        input_text=(
            "Revenue increased from ₹100 Cr to ₹120 Cr."
        ),
        reasoning_type=[
            "numerical_reasoning",
            "trend_analysis",
        ],
    )

    result = validate_difficulty(example)

    assert result["success"] is False
    assert (
        result["reason"]
        == "insufficient_metric_complexity"
    )


def test_medium_example_is_valid():
    example = make_example(
        difficulty="medium",
        input_text=(
            "Revenue increased from ₹100 Cr to ₹120 Cr. "
            "Operating profit declined from ₹30 Cr to ₹25 Cr."
        ),
        reasoning_type=[
            "numerical_reasoning",
            "trend_analysis",
        ],
    )

    result = validate_difficulty(example)

    assert result["success"] is True


def test_hard_requires_multiple_metrics():
    example = make_example(
        difficulty="hard",
        input_text=(
            "Revenue increased from ₹100 Cr to ₹120 Cr. "
            "Operating profit declined from ₹30 Cr to ₹25 Cr."
        ),
        reasoning_type=[
            "numerical_reasoning",
            "trend_analysis",
            "risk_analysis",
        ],
    )

    result = validate_difficulty(example)

    assert result["success"] is False
    assert (
        result["reason"]
        == "insufficient_metric_complexity"
    )


def test_hard_example_is_valid():
    example = make_example(
        difficulty="hard",
        input_text=(
            "Revenue increased from ₹100 Cr to ₹120 Cr. "
            "Operating profit declined from ₹30 Cr to ₹25 Cr. "
            "Debt increased from ₹40 Cr to ₹70 Cr. "
            "Cash declined from ₹30 Cr to ₹20 Cr."
        ),
        reasoning_type=[
            "numerical_reasoning",
            "trend_analysis",
            "comparison",
            "risk_analysis",
        ],
    )

    result = validate_difficulty(example)

    assert result["success"] is True