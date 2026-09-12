import pytest

from finexpert.data.example_generator import (
    generate_explanation_example,
    format_value,
)


def test_format_value_integer():

    result = format_value(100)

    assert result == "₹100 Cr"


def test_format_value_decimal():

    result = format_value(34.5)

    assert result == "₹34.50 Cr"


def test_generate_revenue_growth_example():

    example = generate_explanation_example(
        scenario_type="revenue_growth",
        difficulty="easy",
        example_id="gen_1",
        company="ABC Industries",
        seed=42,
    )

    assert example["example_id"] == "gen_1"
    assert example["category"] == "financial_explanation"
    assert example["difficulty"] == "easy"
    assert example["source_type"] == "synthetic"

    assert "revenue" in example["instruction"].lower()
    assert "revenue" in example["input"].lower()
    assert "revenue" in example["expected_output"].lower()

    assert len(example["reasoning_type"]) >= 1


def test_generate_profitability_example():

    example = generate_explanation_example(
        scenario_type="profitability",
        difficulty="medium",
        example_id="gen_2",
        company="XYZ Technologies",
        seed=42,
    )

    assert example["example_id"] == "gen_2"
    assert example["category"] == "financial_explanation"
    assert example["difficulty"] == "medium"

    assert "revenue" in example["input"].lower()
    assert "operating profit" in example["input"].lower()

    assert "revenue" in example["expected_output"].lower()
    assert "operating profit" in example["expected_output"].lower()


def test_generate_liquidity_example():

    example = generate_explanation_example(
        scenario_type="liquidity",
        difficulty="easy",
        example_id="gen_3",
        company="ABC Industries",
        seed=42,
    )

    assert example["example_id"] == "gen_3"
    assert example["category"] == "financial_explanation"
    assert example["difficulty"] == "easy"

    assert "current assets" in example["input"].lower()
    assert "current liabilities" in example["input"].lower()

    assert "current ratio" in example["expected_output"].lower()


def test_unsupported_scenario_raises_error():

    with pytest.raises(ValueError):

        generate_explanation_example(
            scenario_type="unsupported_scenario",
            difficulty="easy",
            example_id="gen_4",
            company="ABC Industries",
            seed=42,
        )