from .claim_parser import (
    extract_growth_claims,
    extract_value_change_claims,
)
from .financial_validator import percentage_change


SUPPORTED_GROWTH_METRICS = {
    "revenue",
    "operating profit",
    "net profit",
    "profit",
    "earnings",
    "expenses",
    "operating expenses",
    "cash flow",
    "debt",
    "cash",
    "cash reserves",
}


def _validate_growth_claim(
    input_text,
    expected_output,
):
    """
    Validate percentage growth claims in the expected output
    against value changes present in the input.
    """

    input_claims = extract_value_change_claims(
        input_text
    )

    output_claims = extract_growth_claims(
        expected_output
    )

    if not input_claims and not output_claims:
        return {
            "success": True,
            "reason": None,
            "details": {
                "claim_count": 0,
            },
        }

    if not input_claims:
        return {
            "success": False,
            "reason": "no_value_change_claims_found",
        }

    if not output_claims:
        return {
            "success": False,
            "reason": "no_financial_claims_found",
        }

    validated_claims = []

    for output_claim in output_claims:

        metric = output_claim["metric"]

        if metric not in SUPPORTED_GROWTH_METRICS:
            return {
                "success": False,
                "reason": "unsupported_growth_metric",
                "metric": metric,
            }

        matching_input_claim = None

        for input_claim in input_claims:

            if input_claim["metric"] == metric:
                matching_input_claim = input_claim
                break

        if matching_input_claim is None:
            continue

        calculated = percentage_change(
            matching_input_claim["previous_value"],
            matching_input_claim["current_value"],
        )

        if not calculated["success"]:
            return {
                "success": False,
                "reason": calculated["reason"],
                "metric": metric,
            }

        calculated_change = calculated[
            "calculated_value"
        ]

        claimed_change = output_claim[
            "change"
        ]

        if not _approximately_equal(
            calculated_change,
            claimed_change,
        ):
            return {
                "success": False,
                "reason": "incorrect_financial_claim",
                "metric": metric,
                "calculated_change": calculated_change,
                "claimed_change": claimed_change,
            }

        validated_claims.append({
            "metric": metric,
            "calculated_change": calculated_change,
            "claimed_change": claimed_change,
        })

    if not validated_claims:
        return {
            "success": False,
            "reason": "no_matching_growth_claim_found",
        }

    details = {
        **validated_claims[-1],
        "claim_count": len(validated_claims),
    }

    return {
        "success": True,
        "reason": None,
        "details": details,
    }


def _approximately_equal(
    value_a,
    value_b,
    tolerance=0.1,
):
    """
    Compare two numerical values using a small tolerance.
    """

    return abs(value_a - value_b) <= tolerance


def validate_financial_example(
    example_id,
    input_text,
    expected_output,
):
    """
    Validate financial calculations contained in an example.
    """

    if not input_text.strip():
        return {
            "success": False,
            "reason": "empty_input",
            "example_id": example_id,
        }

    if not expected_output.strip():
        return {
            "success": False,
            "reason": "empty_expected_output",
            "example_id": example_id,
        }

    result = _validate_growth_claim(
        input_text=input_text,
        expected_output=expected_output,
    )

    if not result["success"]:
        return {
            **result,
            "example_id": example_id,
        }

    return {
        **result,
        "example_id": example_id,
    }