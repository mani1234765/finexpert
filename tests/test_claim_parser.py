from finexpert.data.claim_parser import (
    extract_percentage_claims,
    extract_money_values,
    extract_growth_claims,
)


def test_extract_percentage_claims():
    result = extract_percentage_claims(
        "Revenue increased by 30% while profit declined by 25%."
    )

    assert len(result) == 2
    assert result[0]["value"] == 30.0
    assert result[1]["value"] == -25.0


def test_extract_money_values():
    result = extract_money_values(
        "Revenue increased from ₹100 Cr to ₹130 Cr."
    )

    assert len(result) == 2
    assert result[0]["value"] == 100.0
    assert result[0]["unit"] == "cr"
    assert result[1]["value"] == 130.0
    assert result[1]["unit"] == "cr"


def test_extract_growth_claims():
    result = extract_growth_claims(
        "Revenue increased by 15% while net profit declined by 8.6%."
    )

    assert len(result) == 2

    assert result[0]["metric"] == "revenue"
    assert result[0]["change"] == 15.0

    assert result[1]["metric"] == "net profit"
    assert result[1]["change"] == -8.6

def test_extract_value_change_claims():
    from finexpert.data.claim_parser import extract_value_change_claims

    result = extract_value_change_claims(
        "Revenue increased from ₹100 Cr to ₹130 Cr."
    )

    assert len(result) == 1

    assert result[0]["metric"] == "revenue"
    assert result[0]["previous_value"] == 100.0
    assert result[0]["current_value"] == 130.0
    assert result[0]["previous_unit"] == "cr"
    assert result[0]["current_unit"] == "cr"