from finexpert.data.example_validator import (
    validate_financial_example,
)


def test_validate_revenue_growth_correct():

    result = validate_financial_example(
        example_id="test_1",
        input_text="Revenue increased from ₹100 Cr to ₹130 Cr.",
        expected_output="Revenue increased by 30%.",
    )

    assert result["success"] is True
    assert result["example_id"] == "test_1"
    assert result["reason"] is None
    assert result["details"]["calculated_change"] == 30.0


def test_validate_revenue_growth_incorrect():

    result = validate_financial_example(
        example_id="test_2",
        input_text="Revenue increased from ₹100 Cr to ₹130 Cr.",
        expected_output="Revenue increased by 20%.",
    )

    assert result["success"] is False
    assert result["reason"] == "incorrect_financial_claim"


def test_validate_revenue_growth_negative():

    result = validate_financial_example(
        example_id="test_3",
        input_text="Revenue declined from ₹200 Cr to ₹150 Cr.",
        expected_output="Revenue declined by 25%.",
    )

    assert result["success"] is True
    assert result["details"]["calculated_change"] == -25.0


def test_no_value_change_claims():

    result = validate_financial_example(
        example_id="test_4",
        input_text="Revenue performance was strong.",
        expected_output="Revenue increased by 30%.",
    )

    assert result["success"] is False
    assert result["reason"] == "no_value_change_claims_found"


def test_no_expected_financial_claims():

    result = validate_financial_example(
        example_id="test_5",
        input_text="Revenue increased from ₹100 Cr to ₹130 Cr.",
        expected_output="Revenue performance was strong.",
    )

    assert result["success"] is False
    assert result["reason"] == "no_financial_claims_found"


def test_supported_debt_growth_metric():

    result = validate_financial_example(
        example_id="test_6",
        input_text="Debt increased from ₹100 Cr to ₹150 Cr.",
        expected_output="Debt increased by 50%.",
    )

    assert result["success"] is True


def test_multiple_claims_all_valid():

    result = validate_financial_example(
        example_id="multi_1",
        input_text=(
            "Revenue increased from ₹100 Cr to ₹130 Cr, "
            "while net profit decreased from ₹20 Cr to ₹15 Cr."
        ),
        expected_output=(
            "Revenue increased by 30%, "
            "while net profit decreased by 25%."
        ),
    )

    assert result["success"] is True
    assert result["details"]["claim_count"] == 2


def test_multiple_claims_one_incorrect():

    result = validate_financial_example(
        example_id="multi_2",
        input_text=(
            "Revenue increased from ₹100 Cr to ₹130 Cr, "
            "while net profit decreased from ₹20 Cr to ₹15 Cr."
        ),
        expected_output=(
            "Revenue increased by 30%, "
            "while net profit decreased by 40%."
        ),
    )

    assert result["success"] is False
    assert result["reason"] == "incorrect_financial_claim"


def test_validate_operating_profit_growth_correct():

    result = validate_financial_example(
        example_id="operating_profit_1",
        input_text=(
            "Operating profit increased "
            "from ₹20 Cr to ₹25 Cr."
        ),
        expected_output=(
            "Operating profit increased by 25%."
        ),
    )

    assert result["success"] is True
    assert result["details"]["calculated_change"] == 25.0


def test_validate_operating_profit_growth_negative():

    result = validate_financial_example(
        example_id="operating_profit_2",
        input_text=(
            "Operating profit decreased "
            "from ₹20 Cr to ₹15 Cr."
        ),
        expected_output=(
            "Operating profit decreased by 25%."
        ),
    )

    assert result["success"] is True
    assert result["details"]["calculated_change"] == -25.0


def test_validate_operating_profit_growth_incorrect():

    result = validate_financial_example(
        example_id="operating_profit_3",
        input_text=(
            "Operating profit decreased "
            "from ₹20 Cr to ₹15 Cr."
        ),
        expected_output=(
            "Operating profit decreased by 20%."
        ),
    )

    assert result["success"] is False
    assert result["reason"] == "incorrect_financial_claim"


def test_revenue_and_operating_profit_both_valid():

    result = validate_financial_example(
        example_id="multi_3",
        input_text=(
            "Revenue increased from ₹100 Cr to ₹130 Cr, "
            "while operating profit decreased from ₹20 Cr to ₹15 Cr."
        ),
        expected_output=(
            "Revenue increased by 30%, "
            "while operating profit decreased by 25%."
        ),
    )

    assert result["success"] is True
    assert result["details"]["claim_count"] == 2