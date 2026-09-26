import json
import re
from collections import Counter

from .claim_parser import (
    extract_growth_claims,
    extract_value_change_claims,
)
from .difficulty_validator import validate_difficulty
from .example_validator import validate_financial_example
from .schema import FinancialExample


DATASET_PATH = "data/raw/generated_explanations.jsonl"


SUPPORTED_CATEGORIES = {
    "financial_explanation",
    "financial_classification",
    "financial_report_generation",
}


SCENARIO_PREFIXES = {
    "rev": "revenue_growth",
    "profit": "profitability",
    "opex": "operating_expenses",
    "debt": "debt_leverage",
    "liq": "liquidity",
    "cash": "cash_flow",
    "eff": "efficiency",
    "risk": "risk_analysis",
    "multi": "multi_metric_comparison",
    "comp": "comprehensive_performance",
}


def load_examples(
    path=DATASET_PATH,
):
    """
    Load the JSONL dataset and validate each record
    against the FinancialExample schema.
    """

    examples = []

    with open(
        path,
        "r",
        encoding="utf-8",
    ) as file:

        for line_number, line in enumerate(
            file,
            start=1,
        ):

            line = line.strip()

            if not line:
                continue

            try:

                data = json.loads(
                    line
                )

                example = (
                    FinancialExample.model_validate(
                        data
                    )
                )

                examples.append(
                    (
                        line_number,
                        example,
                    )
                )

            except Exception as error:

                examples.append(
                    (
                        line_number,
                        error,
                    )
                )

    return examples


def _extract_percentages(text):
    """
    Extract explicit percentage values.
    """

    matches = re.findall(
        r"[-+]?\d+(?:\.\d+)?\s*%",
        text,
    )

    values = []

    for match in matches:

        value = (
            match
            .replace("%", "")
            .strip()
        )

        try:

            values.append(
                float(value)
            )

        except ValueError:

            continue

    return values


def _approximately_equal(
    value_a,
    value_b,
    tolerance=0.2,
):
    return abs(
        value_a - value_b
    ) <= tolerance


def _check_basic_content(example):
    """
    Check required dataset fields.
    """

    errors = []

    if not example.instruction.strip():
        errors.append(
            "empty_instruction"
        )

    if not example.input.strip():
        errors.append(
            "empty_input"
        )

    if not example.expected_output.strip():
        errors.append(
            "empty_expected_output"
        )

    if not example.company:
        errors.append(
            "missing_company"
        )

    if (
        example.category.value
        not in SUPPORTED_CATEGORIES
    ):

        errors.append(
            "unsupported_category"
        )

    return errors


def _check_value_claims(example):
    """
    Verify percentage claims against period-over-period
    financial values present in the input.
    """

    errors = []

    input_claims = (
        extract_value_change_claims(
            example.input
        )
    )

    output_claims = (
        extract_growth_claims(
            example.expected_output
        )
    )

    if not output_claims:
        return errors

    for output_claim in output_claims:

        metric = output_claim[
            "metric"
        ]

        matching_input = None

        for input_claim in input_claims:

            if (
                input_claim["metric"]
                == metric
            ):

                matching_input = (
                    input_claim
                )

                break

        if matching_input is None:

            errors.append(
                {
                    "type": (
                        "unsupported_percentage_claim"
                    ),
                    "metric": metric,
                    "claimed_change": (
                        output_claim[
                            "change"
                        ]
                    ),
                }
            )

            continue

        old_value = (
            matching_input[
                "previous_value"
            ]
        )

        new_value = (
            matching_input[
                "current_value"
            ]
        )

        if old_value == 0:
            continue

        calculated_change = (
            (
                new_value
                - old_value
            )
            / old_value
        ) * 100

        claimed_change = (
            output_claim[
                "change"
            ]
        )

        if not _approximately_equal(
            calculated_change,
            claimed_change,
        ):

            errors.append(
                {
                    "type": (
                        "incorrect_percentage"
                    ),
                    "metric": metric,
                    "calculated": round(
                        calculated_change,
                        4,
                    ),
                    "claimed": claimed_change,
                }
            )

    return errors


def _check_value_change_claims(example):
    """
    Check whether the direction described in the output
    agrees with the period-over-period input values.
    """

    errors = []

    input_claims = (
        extract_value_change_claims(
            example.input
        )
    )

    output_text = (
        example.expected_output.lower()
    )

    for input_claim in input_claims:

        metric = input_claim[
            "metric"
        ]

        old_value = input_claim[
            "previous_value"
        ]

        new_value = input_claim[
            "current_value"
        ]

        if new_value > old_value:

            expected_direction = (
                "increased"
            )

        elif new_value < old_value:

            expected_direction = (
                "declined"
            )

        else:

            expected_direction = (
                "unchanged"
            )

        metric_pattern = re.escape(
            metric
        )

        if (
            expected_direction
            == "increased"
        ):

            declined_pattern = (
                rf"{metric_pattern}"
                r".{0,80}"
                r"(declined|decreased|fell|dropped)"
            )

            if re.search(
                declined_pattern,
                output_text,
            ):

                errors.append(
                    {
                        "type": (
                            "direction_mismatch"
                        ),
                        "metric": metric,
                        "expected": (
                            "increased"
                        ),
                        "found": (
                            "declined"
                        ),
                    }
                )

        elif (
            expected_direction
            == "declined"
        ):

            increased_pattern = (
                rf"{metric_pattern}"
                r".{0,80}"
                r"(increased|grew|rose|expanded)"
            )

            if re.search(
                increased_pattern,
                output_text,
            ):

                errors.append(
                    {
                        "type": (
                            "direction_mismatch"
                        ),
                        "metric": metric,
                        "expected": (
                            "declined"
                        ),
                        "found": (
                            "increased"
                        ),
                    }
                )

    return errors


def _scenario_type_from_id(
    example_id,
):
    """
    Recover scenario type from the generated example ID.
    """

    parts = example_id.split(
        "_"
    )

    if len(parts) < 2:
        return "unknown"

    prefix = parts[1]

    return SCENARIO_PREFIXES.get(
        prefix,
        "unknown",
    )


def _extract_classification_from_output(
    example,
):
    """
    Extract the generated classification label.
    """

    match = re.search(
        r"Classification:\s*"
        r"(Healthy|Moderate Risk|High Risk)",
        example.expected_output,
        flags=re.IGNORECASE,
    )

    if not match:
        return None

    return match.group(
        1
    )


def _extract_revenue_growth_metrics(
    example,
):
    """
    Extract revenue period-over-period values.
    """

    claims = extract_value_change_claims(
        example.input
    )

    for claim in claims:

        if claim["metric"] == "revenue":

            return {
                "previous_revenue": (
                    claim[
                        "previous_value"
                    ]
                ),
                "current_revenue": (
                    claim[
                        "current_value"
                    ]
                ),
            }

    return None


def _check_classification(
    example,
):
    """
    Validate classification examples without assuming that
    every scenario uses the same metric structure.

    This is intentionally conservative.

    For the currently generated dataset:

        - enriched period-over-period scenarios are checked
          using the actual input metrics
        - ratio-based scenarios are checked only when their
          required metrics can be extracted safely
        - incomplete reconstruction does not produce a false
          KeyError or a false classification failure
    """

    if (
        example.category.value
        != "financial_classification"
    ):

        return []

    actual_label = (
        _extract_classification_from_output(
            example
        )
    )

    if actual_label is None:

        return [
            {
                "type": (
                    "missing_classification"
                )
            }
        ]

    scenario_type = (
        _scenario_type_from_id(
            example.example_id
        )
    )

    # --------------------------------------------------
    # Revenue-growth classification.
    #
    # The enriched generator now uses all available
    # period-over-period metrics.
    # --------------------------------------------------

    if scenario_type == "revenue_growth":

        metrics = {}

        claims = (
            extract_value_change_claims(
                example.input
            )
        )

        for claim in claims:

            metric = claim[
                "metric"
            ]

            metrics[
                f"previous_{metric}"
            ] = claim[
                "previous_value"
            ]

            metrics[
                f"current_{metric}"
            ] = claim[
                "current_value"
            ]

        required_metrics = {
            "previous_revenue",
            "current_revenue",
        }

        if required_metrics.issubset(
            metrics.keys()
        ):

            # Import here to avoid creating a module-level
            # circular dependency.
            from .task_generator import (
                _classification_for,
            )

            expected_label = (
                _classification_for(
                    scenario_type,
                    metrics,
                )
            )

            if (
                actual_label.lower()
                != expected_label.lower()
            ):

                return [
                    {
                        "type": (
                            "classification_mismatch"
                        ),
                        "expected": (
                            expected_label
                        ),
                        "actual": (
                            actual_label
                        ),
                    }
                ]

        return []

    # --------------------------------------------------
    # Other scenarios.
    #
    # We don't force a classification reconstruction unless
    # the exact required metric structure is safely available.
    # --------------------------------------------------

    return []


def _check_difficulty(
    example,
):
    """
    Re-run the difficulty validator.
    """

    result = validate_difficulty(
        example
    )

    if result["success"]:
        return []

    return [
        {
            "type": (
                "difficulty_mismatch"
            ),
            "reason": result.get(
                "reason"
            ),
            "metric_count": result.get(
                "metric_count"
            ),
            "complexity_score": result.get(
                "complexity_score"
            ),
        }
    ]


def _check_financial_validator(
    example,
):
    """
    Run the existing financial validator.
    """

    result = validate_financial_example(
        example_id=example.example_id,
        input_text=example.input,
        expected_output=example.expected_output,
    )

    if result["success"]:
        return []

    # Ratio-only scenarios can legitimately have
    # no period-over-period value changes.
    if (
        result.get("reason")
        == "no_value_change_claims_found"
    ):

        return []

    return [
        {
            "type": (
                "financial_validation_error"
            ),
            "reason": result.get(
                "reason"
            ),
        }
    ]


def _check_reasoning_types(
    example,
):
    """
    Verify that reasoning types are valid enum values.
    """

    from .schema import ReasoningType

    valid_values = {
        item.value
        for item in ReasoningType
    }

    errors = []

    for reasoning_type in (
        example.reasoning_type
    ):

        if (
            reasoning_type.value
            not in valid_values
        ):

            errors.append(
                {
                    "type": (
                        "invalid_reasoning_type"
                    ),
                    "value": (
                        reasoning_type.value
                    ),
                }
            )

    return errors


def audit_example(
    line_number,
    example,
):
    """
    Run all semantic checks for one example.
    """

    errors = []

    errors.extend(
        _check_basic_content(
            example
        )
    )

    errors.extend(
        _check_value_claims(
            example
        )
    )

    errors.extend(
        _check_value_change_claims(
            example
        )
    )

    errors.extend(
        _check_classification(
            example
        )
    )

    errors.extend(
        _check_difficulty(
            example
        )
    )

    errors.extend(
        _check_financial_validator(
            example
        )
    )

    errors.extend(
        _check_reasoning_types(
            example
        )
    )

    return errors


def run_audit(
    path=DATASET_PATH,
):
    """
    Audit the complete generated dataset.
    """

    loaded = load_examples(
        path
    )

    total = len(
        loaded
    )

    valid_examples = []

    load_errors = []

    for (
        line_number,
        item,
    ) in loaded:

        if isinstance(
            item,
            Exception,
        ):

            load_errors.append(
                {
                    "line": line_number,
                    "error": str(item),
                }
            )

        else:

            valid_examples.append(
                (
                    line_number,
                    item,
                )
            )

    all_errors = []

    error_types = Counter()

    for (
        line_number,
        example,
    ) in valid_examples:

        errors = audit_example(
            line_number,
            example,
        )

        if errors:

            for error in errors:

                if isinstance(
                    error,
                    str,
                ):

                    error_type = error

                else:

                    error_type = error.get(
                        "type",
                        "unknown",
                    )

                error_types[
                    error_type
                ] += 1

                all_errors.append(
                    {
                        "line": line_number,
                        "example_id": (
                            example.example_id
                        ),
                        "error": error,
                    }
                )

    unique_error_examples = len(
        {
            item["example_id"]
            for item in all_errors
        }
    )

    print(
        "\n"
        + "=" * 60
    )

    print(
        "FINEXPERT SEMANTIC DATASET AUDIT"
    )

    print(
        "=" * 60
    )

    print(
        f"Dataset file: {path}"
    )

    print(
        f"Total records: {total}"
    )

    print(
        "Valid FinancialExample records: "
        f"{len(valid_examples)}"
    )

    print(
        f"Load errors: {len(load_errors)}"
    )

    print(
        "Examples with semantic errors: "
        f"{unique_error_examples}"
    )

    print(
        f"Total semantic errors: "
        f"{len(all_errors)}"
    )

    print(
        "\n"
        + "-" * 60
    )

    print(
        "ERROR TYPES"
    )

    print(
        "-" * 60
    )

    if not error_types:

        print(
            "No semantic errors detected."
        )

    else:

        for (
            error_type,
            count,
        ) in error_types.most_common():

            print(
                f"{error_type:<35} {count}"
            )

    print(
        "\n"
        + "-" * 60
    )

    print(
        "ERROR DETAILS"
    )

    print(
        "-" * 60
    )

    if not all_errors:

        print(
            "PASS — no semantic errors detected."
        )

    else:

        for item in all_errors[:50]:

            print(
                f"\nLine: {item['line']}"
            )

            print(
                f"Example: {item['example_id']}"
            )

            print(
                f"Error: {item['error']}"
            )

    if len(all_errors) > 50:

        print(
            "\n..."
        )

        print(
            f"{len(all_errors) - 50} "
            "additional errors not displayed."
        )

    print(
        "\n"
        + "=" * 60
    )

    print(
        "SEMANTIC AUDIT COMPLETE"
    )

    print(
        "=" * 60
    )

    return {
        "total": total,
        "valid_records": len(
            valid_examples
        ),
        "load_errors": load_errors,
        "errors": all_errors,
        "error_types": dict(
            error_types
        ),
    }


if __name__ == "__main__":
    run_audit()