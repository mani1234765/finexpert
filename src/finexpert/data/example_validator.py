import re

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
        # Nothing quantified in either the input or the
        # output (e.g. a purely ratio-based explanation
        # with no period-over-period change). There is no
        # growth claim to verify, so this is trivially valid.
        return {
            "success": True,
            "reason": None,
            "details": {"claim_count": 0},
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

    # Group input claims by metric, preserving the order they appear
    # in the text. A metric can legitimately appear more than once
    # (e.g. "revenue" once for the primary scenario and again inside
    # an appended related-scenario context). Matching every output
    # claim against the *first* same-named input claim -- regardless
    # of which occurrence it actually belongs to -- caused primary
    # and related claims to be cross-checked against each other's
    # numbers, producing false "incorrect_financial_claim" failures.
    # Consuming claims in appearance order keeps each output claim
    # paired with the correct occurrence instead.
    remaining_by_metric = {}
    for input_claim in input_claims:
        remaining_by_metric.setdefault(
            input_claim["metric"], []
        ).append(input_claim)

    validated_claims = []

    for output_claim in output_claims:

        metric = output_claim["metric"]

        if metric not in SUPPORTED_GROWTH_METRICS:
            return {
                "success": False,
                "reason": "unsupported_growth_metric",
                "metric": metric,
            }

        bucket = remaining_by_metric.get(metric)

        if not bucket:
            continue

        matching_input_claim = bucket.pop(0)

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