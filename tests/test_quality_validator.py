from finexpert.data.quality_validator import (
    validate_required_content,
    normalize_text,
    generate_example_fingerprint,
    check_duplicate,
)

from finexpert.data.schema import FinancialExample


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


def test_required_content_valid():

    example = create_example()

    result = validate_required_content(example)

    assert result["success"] is True
    assert result["reason"] is None


def test_instruction_empty():

    example = create_example(
        instruction="   "
    )

    result = validate_required_content(example)

    assert result["success"] is False
    assert result["reason"] == "instruction_empty"


def test_input_empty():

    example = create_example(
        input=""
    )

    result = validate_required_content(example)

    assert result["success"] is False
    assert result["reason"] == "input_empty"


def test_expected_output_empty():

    example = create_example(
        expected_output=""
    )

    result = validate_required_content(example)

    assert result["success"] is False
    assert result["reason"] == "expected_output_empty"


def test_normalize_text():

    result = normalize_text(
        "  Revenue   Increased   By 30%  "
    )

    assert result == "revenue increased by 30%"


def test_generate_example_fingerprint():

    example = create_example()

    fingerprint = generate_example_fingerprint(example)

    assert isinstance(fingerprint, str)
    assert len(fingerprint) == 64


def test_duplicate_example():

    example = create_example()

    fingerprint = generate_example_fingerprint(example)

    result = check_duplicate(
        example,
        {fingerprint},
    )

    assert result["success"] is False
    assert result["reason"] == "duplicate_example"


def test_unique_example():

    example = create_example()

    result = check_duplicate(
        example,
        set(),
    )

    assert result["success"] is True
    assert result["reason"] is None