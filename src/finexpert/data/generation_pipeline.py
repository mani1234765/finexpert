import json
from pathlib import Path

from .example_generator import generate_explanation_example
from .example_validator import validate_financial_example
from .quality_validator import (
    check_duplicate,
    validate_required_content,
)
from .schema import FinancialExample
from .similarity_validator import check_near_duplicate


OUTPUT_FILE = Path(
    "data/raw/generated_explanations.jsonl"
)

NEAR_DUPLICATE_THRESHOLD = 0.85

TARGET_EXAMPLES = 300

MAX_ATTEMPTS_PER_SCENARIO = 100

SCENARIO_TYPES = [
    "revenue_growth",
    "profitability",
    "operating_expenses",
    "debt_leverage",
    "liquidity",
    "cash_flow",
    "efficiency",
    "risk_analysis",
    "multi_metric_comparison",
    "comprehensive_performance",
]

COMPANIES = [
    "ABC Industries",
    "XYZ Technologies",
    "Nova Financials",
    "Apex Manufacturing",
    "Vertex Solutions",
    "Orion Enterprises",
    "Summit Industries",
    "Pioneer Technologies",
    "Horizon Manufacturing",
    "Atlas Solutions",
    "BluePeak Industries",
    "Crest Financials",
    "Evergreen Technologies",
    "Prime Manufacturing",
    "NextGen Solutions",
]


def get_scenario_targets(count):
    """
    Distribute requested examples evenly across
    the available scenario types.
    """

    scenario_count = len(SCENARIO_TYPES)

    base_count = count // scenario_count
    remainder = count % scenario_count

    targets = {}

    for index, scenario in enumerate(SCENARIO_TYPES):
        targets[scenario] = base_count

        if index < remainder:
            targets[scenario] += 1

    return targets


def get_difficulty(index):
    """
    Distribute easy, medium and hard examples
    approximately evenly.
    """

    position = index % 3

    if position == 0:
        return "easy"

    if position == 1:
        return "medium"

    return "hard"


def generate_example_id(
    scenario_type,
    scenario_number,
):
    """
    Generate a unique example ID.
    """

    prefixes = {
        "revenue_growth": "fin_rev",
        "profitability": "fin_profit",
        "operating_expenses": "fin_opex",
        "debt_leverage": "fin_debt",
        "liquidity": "fin_liq",
        "cash_flow": "fin_cash",
        "efficiency": "fin_eff",
        "risk_analysis": "fin_risk",
        "multi_metric_comparison": "fin_multi",
        "comprehensive_performance": "fin_comp",
    }

    return (
        f"{prefixes[scenario_type]}"
        f"_{scenario_number:03d}"
    )


def generate_and_validate_examples(
    count=TARGET_EXAMPLES,
    output_file=OUTPUT_FILE,
):
    """
    Generate and validate financial examples.

    The default production target is 300 accepted
    examples.

    The count parameter can be changed for tests.

    Rejected examples are replaced with new attempts.

    A maximum attempt limit prevents an individual
    scenario from entering an infinite loop.
    """

    if count <= 0:
        raise ValueError(
            "count must be greater than zero."
        )

    output_file = Path(output_file)

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    scenario_targets = get_scenario_targets(count)

    accepted_examples = []

    existing_fingerprints = set()

    scenario_counts = {
        scenario: 0
        for scenario in SCENARIO_TYPES
    }

    difficulty_counts = {
        "easy": 0,
        "medium": 0,
        "hard": 0,
    }

    generated = 0
    accepted = 0
    rejected = 0
    duplicates = 0
    near_duplicates = 0
    financial_errors = 0
    schema_errors = 0
    quality_errors = 0

    with output_file.open(
        "w",
        encoding="utf-8",
    ) as file:

        for scenario_type in SCENARIO_TYPES:

            target = scenario_targets[scenario_type]

            scenario_attempts = 0

            while (
                scenario_counts[scenario_type]
                < target
            ):

                scenario_attempts += 1

                if (
                    scenario_attempts
                    > MAX_ATTEMPTS_PER_SCENARIO
                ):
                    raise RuntimeError(
                        f"Unable to generate enough valid "
                        f"examples for scenario "
                        f"'{scenario_type}'. "
                        f"Accepted "
                        f"{scenario_counts[scenario_type]} "
                        f"of {target} after "
                        f"{MAX_ATTEMPTS_PER_SCENARIO} "
                        f"attempts."
                    )

                scenario_number = (
                    scenario_counts[scenario_type]
                    + 1
                )

                difficulty = get_difficulty(
                    accepted
                )

                company = COMPANIES[
                    generated
                    % len(COMPANIES)
                ]

                example_id = generate_example_id(
                    scenario_type,
                    scenario_number,
                )

                seed = generated + 1

                generated += 1

                # -----------------------------
                # Generate
                # -----------------------------

                try:
                    example_data = (
                        generate_explanation_example(
                            scenario_type=scenario_type,
                            difficulty=difficulty,
                            example_id=example_id,
                            company=company,
                            seed=seed,
                        )
                    )

                except Exception as exc:
                    rejected += 1

                    print(
                        f"[REJECTED] "
                        f"{scenario_type} "
                        f"| generation error: "
                        f"{type(exc).__name__}"
                    )

                    continue

                # -----------------------------
                # Schema validation
                # -----------------------------

                try:
                    example = FinancialExample(
                        **example_data
                    )

                except Exception as exc:
                    schema_errors += 1
                    rejected += 1

                    print(
                        f"[REJECTED] "
                        f"{scenario_type} "
                        f"| schema error: "
                        f"{type(exc).__name__}"
                    )

                    continue

                # -----------------------------
                # Required content
                # -----------------------------

                quality_result = (
                    validate_required_content(
                        example
                    )
                )

                if not quality_result["success"]:
                    quality_errors += 1
                    rejected += 1

                    print(
                        f"[REJECTED] "
                        f"{scenario_type} "
                        f"| quality error: "
                        f"{quality_result.get('reason')}"
                    )

                    continue

                # -----------------------------
                # Financial validation
                # -----------------------------

                financial_result = (
                    validate_financial_example(
                        example_id=example.example_id,
                        input_text=example.input,
                        expected_output=(
                            example.expected_output
                        ),
                    )
                )

                if not financial_result["success"]:
                    financial_errors += 1
                    rejected += 1

                    print(
                        f"[REJECTED] "
                        f"{scenario_type} "
                        f"| financial error: "
                        f"{financial_result.get('reason')}"
                    )

                    continue

                # -----------------------------
                # Exact duplicate
                # -----------------------------

                duplicate_result = check_duplicate(
                    example,
                    existing_fingerprints,
                )

                if not duplicate_result["success"]:
                    duplicates += 1
                    rejected += 1

                    print(
                        f"[REJECTED] "
                        f"{scenario_type} "
                        f"| exact duplicate"
                    )

                    continue

                # -----------------------------
                # Near duplicate
                # -----------------------------

                near_duplicate_result = (
                    check_near_duplicate(
                        example,
                        accepted_examples,
                        threshold=(
                            NEAR_DUPLICATE_THRESHOLD
                        ),
                    )
                )

                if not near_duplicate_result["success"]:
                    near_duplicates += 1
                    rejected += 1

                    print(
                        f"[REJECTED] "
                        f"{scenario_type} "
                        f"| near duplicate "
                        f"similarity="
                        f"{near_duplicate_result['similarity']:.3f}"
                    )

                    continue

                # -----------------------------
                # Accept
                # -----------------------------

                accepted_examples.append(
                    example
                )

                existing_fingerprints.add(
                    duplicate_result[
                        "fingerprint"
                    ]
                )

                scenario_counts[
                    scenario_type
                ] += 1

                difficulty_counts[
                    difficulty
                ] += 1

                accepted += 1

                # -----------------------------
                # Write
                # -----------------------------

                file.write(
                    json.dumps(
                        example.model_dump(
                            mode="json"
                        ),
                        ensure_ascii=False,
                    )
                    + "\n"
                )

                file.flush()

                print(
                    f"[ACCEPTED] "
                    f"{accepted}/{count} "
                    f"| {scenario_type} "
                    f"{scenario_counts[scenario_type]}/"
                    f"{target} "
                    f"| {difficulty}"
                )

    # -----------------------------
    # Summary
    # -----------------------------

    print(
        "\n"
        "========================================\n"
        "       FINEXPERT DATASET SUMMARY\n"
        "========================================"
    )

    print(
        f"Target examples:     {count}"
    )

    print(
        f"Generated attempts:  {generated}"
    )

    print(
        f"Accepted examples:   {accepted}"
    )

    print(
        f"Rejected examples:   {rejected}"
    )

    print(
        f"Exact duplicates:    {duplicates}"
    )

    print(
        f"Near duplicates:     {near_duplicates}"
    )

    print(
        f"Financial errors:    {financial_errors}"
    )

    print(
        f"Schema errors:       {schema_errors}"
    )

    print(
        f"Quality errors:      {quality_errors}"
    )

    print(
        "\n"
        "------------- SCENARIOS -------------"
    )

    for scenario in SCENARIO_TYPES:
        print(
            f"{scenario:<30}"
            f"{scenario_counts[scenario]}"
        )

    print(
        "\n"
        "------------ DIFFICULTY -------------"
    )

    for difficulty in [
        "easy",
        "medium",
        "hard",
    ]:
        print(
            f"{difficulty:<30}"
            f"{difficulty_counts[difficulty]}"
        )

    print(
        "========================================\n"
    )

    return {
        "target": count,
        "generated": generated,
        "accepted": accepted,
        "rejected": rejected,
        "duplicates": duplicates,
        "near_duplicates": near_duplicates,
        "financial_errors": financial_errors,
        "schema_errors": schema_errors,
        "quality_errors": quality_errors,
        "scenario_counts": scenario_counts,
        "difficulty_counts": difficulty_counts,
    }


if __name__ == "__main__":
    generate_and_validate_examples()