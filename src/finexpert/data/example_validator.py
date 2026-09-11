from .claim_parser import (
    extract_growth_claims,
    extract_value_change_claims,
)
from .financial_validator import (
    revenue_growth_rate,
    earning_growth_rate,
)


def compare_values(expected_value, calculated_value):
    """
    Compare two financial values.

    Allows normal floating-point representation
    differences such as 30 and 30.0.
    """

    return abs(expected_value - calculated_value) < 1e-9


def validate_growth_claim(
    metric,
    previous_value,
    current_value,
    expected_change,
):
    """
    Validate a single financial growth claim.
    """

    if metric == "revenue":
        calculation = revenue_growth_rate(
            previous_value,
            current_value,
        )

    elif metric in {
    "earnings",
    "profit",
    "net profit",
    "operating profit",
}:
        calculation = earning_growth_rate(
            previous_value,
            current_value,
        )

    else:
        return {
            "success": False,
            "reason": "unsupported_growth_metric",
            "metric": metric,
        }

    if not calculation["success"]:
        return {
            "success": False,
            "reason": calculation["reason"],
            "metric": metric,
        }

    calculated_change = calculation["calculated_value"]

    if not compare_values(
        expected_change,
        calculated_change,
    ):
        return {
            "success": False,
            "reason": "incorrect_financial_claim",
            "metric": metric,
            "expected_change": expected_change,
            "calculated_change": calculated_change,
        }

    return {
        "success": True,
        "metric": metric,
        "expected_change": expected_change,
        "calculated_change": calculated_change,
    }


def validate_financial_example(
    example_id,
    input_text,
    expected_output,
):
    """
    Validate all financial growth claims in an example.

    Every expected financial claim must:
    1. Match a financial value change in the input.
    2. Be calculated correctly.
    3. Use a supported financial metric.

    The example passes only when ALL claims pass.
    """

    input_claims = extract_value_change_claims(
        input_text
    )

    if not input_claims:
        return {
            "success": False,
            "example_id": example_id,
            "reason": "no_value_change_claims_found",
        }

    expected_claims = extract_growth_claims(
        expected_output
    )

    if not expected_claims:
        return {
            "success": False,
            "example_id": example_id,
            "reason": "no_financial_claims_found",
        }

    validated_claims = []

    for expected_claim in expected_claims:

        matching_input_claim = None

        for input_claim in input_claims:
            if (
                input_claim["metric"]
                == expected_claim["metric"]
            ):
                matching_input_claim = input_claim
                break

        if matching_input_claim is None:
            return {
                "success": False,
                "example_id": example_id,
                "reason": "matching_financial_claim_not_found",
                "details": {
                    "metric": expected_claim["metric"],
                    "expected_change": expected_claim["change"],
                },
            }

        result = validate_growth_claim(
            metric=expected_claim["metric"],
            previous_value=matching_input_claim[
                "previous_value"
            ],
            current_value=matching_input_claim[
                "current_value"
            ],
            expected_change=expected_claim[
                "change"
            ],
        )

        if not result["success"]:
            return {
                "success": False,
                "example_id": example_id,
                "reason": result["reason"],
                "details": result,
            }

        validated_claims.append(result)

    # Preserve the original single-claim response fields
    # while also exposing multi-claim information.
    first_claim = validated_claims[0]

    return {
        "success": True,
        "example_id": example_id,
        "reason": None,
        "details": {
            "expected_change": first_claim["expected_change"],
            "calculated_change": first_claim["calculated_change"],
            "validated_claims": validated_claims,
            "claim_count": len(validated_claims),
        },
    }