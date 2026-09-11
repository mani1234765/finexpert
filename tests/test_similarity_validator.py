from finexpert.data.schema import FinancialExample
from finexpert.data.similarity_validator import (
    build_example_text,
    calculate_similarity,
    check_near_duplicate,
)


def create_example(**overrides):
    data = {
        "example_id": "test_1",
        "instruction": "Explain the revenue performance.",
        "input": "Revenue increased from ₹100 Cr to ₹130 Cr.",
        "expected_output": "Revenue increased by 30%.",
        "category": "financial_explanation",
        "difficulty": "easy",
        "reasoning_type": ["trend_analysis"],
        "source_type": "synthetic",
        "company": "ABC Industries",
    }

    data.update(overrides)

    return FinancialExample(**data)


def test_build_example_text():

    example = create_example()

    result = build_example_text(example)

    assert "Explain the revenue performance." in result
    assert "Revenue increased from ₹100 Cr to ₹130 Cr." in result
    assert "Revenue increased by 30%." in result


def test_identical_examples_have_high_similarity():

    example_a = create_example(
        example_id="test_1"
    )

    example_b = create_example(
        example_id="test_2"
    )

    similarity = calculate_similarity(
        example_a,
        example_b,
    )

    assert similarity == 1.0


def test_near_duplicate_examples_have_high_similarity():

    example_a = create_example()

    example_b = create_example(
        example_id="test_2",
        input="Revenue grew from ₹100 crore to ₹130 crore.",
        expected_output="Revenue grew by 30%.",
    )

    similarity = calculate_similarity(
        example_a,
        example_b,
    )

    assert similarity >= 0.85


def test_different_examples_have_low_similarity():

    example_a = create_example()

    example_b = create_example(
        example_id="test_2",
        instruction="Assess liquidity risk.",
        input="The company has ₹50 Cr in cash and ₹200 Cr in debt.",
        expected_output=(
            "The company may face elevated liquidity risk "
            "due to its debt position."
        ),
        category="financial_classification",
        difficulty="medium",
        reasoning_type=["risk_analysis"],
        company="XYZ Industries",
    )

    similarity = calculate_similarity(
        example_a,
        example_b,
    )

    assert similarity < 0.85


def test_near_duplicate_is_rejected():

    example_a = create_example()

    example_b = create_example(
        example_id="test_2",
        input="Revenue grew from ₹100 crore to ₹130 crore.",
        expected_output="Revenue grew by 30%.",
    )

    result = check_near_duplicate(
        example_b,
        [example_a],
        threshold=0.85,
    )

    assert result["success"] is False
    assert result["reason"] == "near_duplicate_example"
    assert result["matched_example_id"] == "test_1"


def test_unique_example_is_accepted():

    example_a = create_example()

    example_b = create_example(
        example_id="test_2",
        instruction="Assess liquidity risk.",
        input="The company has ₹50 Cr in cash and ₹200 Cr in debt.",
        expected_output=(
            "The company may face elevated liquidity risk "
            "due to its debt position."
        ),
        category="financial_classification",
        difficulty="medium",
        reasoning_type=["risk_analysis"],
        company="XYZ Industries",
    )

    result = check_near_duplicate(
        example_b,
        [example_a],
        threshold=0.85,
    )

    assert result["success"] is True
    assert result["reason"] is None