import json
import re
from pathlib import Path

from .example_validator import validate_financial_example
from .quality_validator import (
    check_duplicate,
    validate_required_content,
)
from .schema import FinancialExample
from .source_consistency_validator import validate_source_consistency
from .scenario_generator import generate_scenario
from .similarity_validator import check_near_duplicate
from .task_generator import generate_training_example
from .classification_rules import (
    classify_financial_health,
)
from .difficulty_scenarios import build_difficulty_scenario


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


TASK_TYPES = [
    "financial_explanation",
    "financial_classification",
    "financial_report_generation",
]


DIFFICULTIES = [
    "easy",
    "medium",
    "hard",
]


CLASSIFICATION_LABELS = [
    "Healthy",
    "Moderate Risk",
    "High Risk",
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
    Distribute requested examples evenly across scenarios.

    Example:
        count=300 -> 30 examples per scenario
        count=10  -> 1 example per scenario
    """

    scenario_count = len(SCENARIO_TYPES)

    base_count = count // scenario_count

    remainder = count % scenario_count

    return {
        scenario: (
            base_count
            + (1 if index < remainder else 0)
        )
        for index, scenario in enumerate(SCENARIO_TYPES)
    }


def get_task(index):
    """
    Cycle through the three FinExpert training tasks.
    """

    return TASK_TYPES[
        index % len(TASK_TYPES)
    ]


def get_difficulty(index):
    """
    Cycle through easy, medium and hard.
    """

    return DIFFICULTIES[
        index % len(DIFFICULTIES)
    ]


def get_task_targets(count):
    """
    Distribute examples approximately evenly
    across the three task types.
    """

    task_count = len(TASK_TYPES)

    base_count = count // task_count

    remainder = count % task_count

    return {
        task: (
            base_count
            + (1 if index < remainder else 0)
        )
        for index, task in enumerate(TASK_TYPES)
    }


def get_task_target(count, task):
    """
    Return the expected number of examples for
    a specific task.
    """

    return get_task_targets(count)[task]


def get_classification_label_targets(
    classification_count
):
    """
    Distribute classification examples across:

        Healthy       -> largest share when needed
        Moderate Risk
        High Risk

    For 100 examples:

        Healthy       -> 34
        Moderate Risk -> 33
        High Risk     -> 33
    """

    label_count = len(CLASSIFICATION_LABELS)

    base_count = (
        classification_count
        // label_count
    )

    remainder = (
        classification_count
        % label_count
    )

    return {
        label: (
            base_count
            + (1 if index < remainder else 0)
        )
        for index, label in enumerate(
            CLASSIFICATION_LABELS
        )
    }


def get_classification_label(
    expected_output
):
    """
    Extract the classification label from the
    generated expected output.

    Expected format:

        Classification: Healthy

    or:

        Classification: Moderate Risk

    or:

        Classification: High Risk
    """

    match = re.search(
        r"classification\s*:\s*"
        r"(healthy|moderate\s+risk|high\s+risk)",
        expected_output,
        flags=re.IGNORECASE,
    )

    if match is None:
        return None

    normalized = re.sub(
        r"\s+",
        " ",
        match.group(1).strip(),
    ).lower()

    mapping = {
        "healthy": "Healthy",
        "moderate risk": "Moderate Risk",
        "high risk": "High Risk",
    }

    return mapping.get(normalized)

def find_classification_scenario(
    scenario_type,
    desired_label,
    difficulty,
    company,
    start_seed,
    existing_fingerprints,
    max_search=1000,
):
    """
    Find a numerical scenario that produces the requested
    classification label using the same enriched scenario
    generation path used by generate_training_example().
    """

    for seed in range(
        start_seed,
        start_seed + max_search,
    ):
        difficulty_result = build_difficulty_scenario(
            scenario_type=scenario_type,
            difficulty=difficulty,
            seed=seed,
            company=company,
        )

        scenario = difficulty_result["scenario"]

        label = classify_financial_health(
            scenario_type=scenario_type,
            metrics=scenario["metrics"],
        )

        if label != desired_label:
            continue

        metric_fingerprint = json.dumps(
            scenario["metrics"],
            sort_keys=True,
        )

        if metric_fingerprint in existing_fingerprints:
            continue

        return seed, scenario

    raise RuntimeError(
        f"Unable to find a new {scenario_type} scenario "
        f"producing classification label '{desired_label}' "
        f"for difficulty '{difficulty}' "
        f"after {max_search} seed attempts."
    )


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
    Generate a balanced FinExpert dataset.

    The pipeline balances:

    1. Scenario
    2. Task
    3. Difficulty
    4. Classification labels

    It also validates:

    - Pydantic schema
    - Required content
    - Financial calculations
    - Source consistency
    - Exact duplicates
    - Numerical-aware near duplicates

    Difficulty validation is intentionally NOT performed here.

    Difficulty is already generated as part of the authoritative
    training-example generation path in task_generator.py.
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

    scenario_targets = get_scenario_targets(
        count
    )

    task_targets = get_task_targets(count)

    classification_target = task_targets[
        "financial_classification"
    ]

    classification_label_targets = (
        get_classification_label_targets(
            classification_target
        )
    )

    accepted_examples = []

    existing_fingerprints = set()

    scenario_counts = {
        scenario: 0
        for scenario in SCENARIO_TYPES
    }

    task_counts = {
        task: 0
        for task in TASK_TYPES
    }

    difficulty_counts = {
        difficulty: 0
        for difficulty in DIFFICULTIES
    }

    classification_label_counts = {
        label: 0
        for label in CLASSIFICATION_LABELS
    }

    scenario_metric_fingerprints = {
        scenario: set()
        for scenario in SCENARIO_TYPES
    }

    generated = 0

    accepted = 0

    rejected = 0

    duplicates = 0

    near_duplicates = 0

    financial_errors = 0

    schema_errors = 0

    quality_errors = 0

    generation_errors = 0

    with output_file.open(
        "w",
        encoding="utf-8",
    ) as file:

        for scenario_type in SCENARIO_TYPES:

            target = scenario_targets[
                scenario_type
            ]

            scenario_attempts = 0

            while (
                scenario_counts[
                    scenario_type
                ]
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
                    scenario_counts[
                        scenario_type
                    ]
                    + 1
                )

                # ----------------------------------------
                # Task assignment
                # ----------------------------------------

                local_index = (
                    scenario_number - 1
                )

                task = get_task(
                    local_index
                )

                task_index = (
                    TASK_TYPES.index(task)
                )

                scenario_index = (
                    SCENARIO_TYPES.index(
                        scenario_type
                    )
                )

                # ----------------------------------------
                # Difficulty assignment
                # ----------------------------------------
                #
                # Latin-square style assignment keeps
                # task/difficulty combinations balanced
                # within each scenario.
                #
                # Rejected attempts do not change the
                # accepted-position based assignment.
                # ----------------------------------------

                difficulty = DIFFICULTIES[
                    (
                        local_index
                        // len(TASK_TYPES)
                        + task_index
                        + scenario_index
                    )
                    % len(DIFFICULTIES)
                ]

                company = COMPANIES[
                    generated
                    % len(COMPANIES)
                ]

                example_id = (
                    generate_example_id(
                        scenario_type,
                        scenario_number,
                    )
                )

                # ----------------------------------------
                # Generate numerical scenario
                # ----------------------------------------

                try:
                    if task == "financial_classification":
                        scenario_supported_labels ={
                            "cash_flow": {
                                "Moderate Risk",
                                "High Risk",
                            }
                        }

                        supported_labels = scenario_supported_labels.get(
                            scenario_type,
                            set(CLASSIFICATION_LABELS),
                        )

                        remaining_labels = [
                            label
                            for label in CLASSIFICATION_LABELS
                            if (
                                label in supported_labels
                                and classification_label_counts[label]
                                <classification_label_targets[label]
                            )
                        ]

                        if not remaining_labels:
                            raise RuntimeError(
                                f"No feasible classification label remains for"
                                f"scenario '{scenario_type}' ."

                            )

                        desired_label = max(
                            remaining_labels,
                            key=lambda label:
                                classification_label_targets[label]
                                - classification_label_counts[label],
                        )

                        seed, scenario = find_classification_scenario(
                            scenario_type=scenario_type,
                            desired_label=desired_label,
                            difficulty=difficulty,
                            company=company,
                            start_seed=generated + 1,
                            existing_fingerprints=
                                scenario_metric_fingerprints[scenario_type]


                        )
                    else:
                        seed = generated + 1

                        scenario = generate_scenario(
                            scenario_type=scenario_type,
                            seed=seed,
                        )

                    generated += 1

                    metric_fingerprint = json.dumps(
                        scenario["metrics"],
                        sort_keys=True,
                    )

                    if metric_fingerprint in (
                        scenario_metric_fingerprints[scenario_type]
                    ):
                        rejected += 1
                        continue

                    scenario_metric_fingerprints[scenario_type].add(
                        metric_fingerprint
                    )

                    example_data = generate_training_example(
                        scenario_type=scenario_type,
                        task=task,
                        difficulty=difficulty,
                        example_id=example_id,
                        company=company,
                        seed=seed,
                    )
                except Exception as exc:
                    generation_errors += 1
                    rejected += 1

                    print(
                        f"[REJECTED] {scenario_type} |"
                        f"generation error: "
                        f"{type(exc).__name__}: {exc}"
                    )

                    continue

                # ----------------------------------------
                # Generate training example
                # ----------------------------------------

                try:

                    example_data = (
                        generate_training_example(
                            scenario_type=(
                                scenario_type
                            ),
                            task=task,
                            difficulty=difficulty,
                            example_id=example_id,
                            company=company,
                            seed=seed,
                        )
                    )

                except Exception as exc:

                    generation_errors += 1

                    rejected += 1

                    print(
                        f"[REJECTED] "
                        f"{scenario_type} | "
                        f"training generation error: "
                        f"{type(exc).__name__}: "
                        f"{exc}"
                    )

                    continue

                # ----------------------------------------
                # Schema validation
                # ----------------------------------------

                try:

                    example = FinancialExample(
                        **example_data
                    )

                except Exception as exc:

                    schema_errors += 1

                    rejected += 1

                    print(
                        f"[REJECTED] "
                        f"{scenario_type} | "
                        f"schema error: "
                        f"{type(exc).__name__}: "
                        f"{exc}"
                    )

                    continue

                # ----------------------------------------
                # Required content validation
                # ----------------------------------------

                quality_result = (
                    validate_required_content(
                        example
                    )
                )

                if not quality_result[
                    "success"
                ]:

                    quality_errors += 1

                    rejected += 1

                    print(
                        f"[REJECTED] "
                        f"{scenario_type} | "
                        f"quality error: "
                        f"{quality_result.get('reason')}"
                    )

                    continue

                # ----------------------------------------
                # Financial calculation validation
                # ----------------------------------------

                financial_result = (
                    validate_financial_example(
                        example_id=(
                            example.example_id
                        ),
                        input_text=(
                            example.input
                        ),
                        expected_output=(
                            example.expected_output
                        ),
                    )
                )

                if not financial_result[
                    "success"
                ]:

                    financial_reason = (
                        financial_result.get(
                            "reason"
                        )
                    )

                    # Ratio-only scenarios may not
                    # contain period-over-period
                    # value-change claims.
                    if (
                        financial_reason
                        != "no_value_change_claims_found"
                    ):

                        financial_errors += 1

                        rejected += 1

                        print(
                            f"[REJECTED] "
                            f"{scenario_type} | "
                            f"financial error: "
                            f"{financial_reason}"
                        )

                        continue

                # ----------------------------------------
                # Source consistency validation
                # ----------------------------------------

                source_result = (
                    validate_source_consistency(
                        input_text=(
                            example.input
                        ),
                        expected_output=(
                            example.expected_output
                        ),
                    )
                )

                if not source_result[
                    "success"
                ]:

                    financial_errors += 1

                    rejected += 1

                    print(
                        f"[REJECTED] "
                        f"{scenario_type} | "
                        f"source consistency error: "
                        f"{source_result.get('reason')} | "
                        f"unsupported="
                        f"{source_result.get('unsupported_numbers', [])}"
                    )

                    print(
                        "\nSOURCE RESULT:"
                    )

                    print(
                        source_result
                    )

                    print(
                        "\n---REJECTED INPUT---\n"
                        f"{example.input}\n"
                        "\n---REJECTED OUTPUT---\n"
                        f"{example.expected_output}\n"
                        "----------------------\n"
                    )

                    continue

                # ----------------------------------------
                # Classification label balancing
                # ----------------------------------------

                if (
                    task
                    == "financial_classification"
                ):

                    classification_label = (
                        get_classification_label(
                            example.expected_output
                        )
                    )

                    if (
                        classification_label
                        not in CLASSIFICATION_LABELS
                    ):

                        quality_errors += 1

                        rejected += 1

                        print(
                            f"[REJECTED] "
                            f"{scenario_type} | "
                            f"classification label "
                            f"missing or invalid"
                        )

                        continue

                    label_target = (
                        classification_label_targets[
                            classification_label
                        ]
                    )

                    label_count = (
                        classification_label_counts[
                            classification_label
                        ]
                    )

                    if (
                        label_count
                        >= label_target
                    ):

                        rejected += 1

                        print(
                            f"[REJECTED] "
                            f"{scenario_type} | "
                            f"classification label quota "
                            f"reached: "
                            f"{classification_label}"
                        )

                        continue

                # ----------------------------------------
                # Exact duplicate validation
                # ----------------------------------------

                duplicate_result = (
                    check_duplicate(
                        example,
                        existing_fingerprints,
                    )
                )

                if not duplicate_result[
                    "success"
                ]:

                    duplicates += 1

                    rejected += 1

                    print(
                        f"[REJECTED] "
                        f"{scenario_type} | "
                        f"exact duplicate"
                    )

                    continue

                # ----------------------------------------
                # Near duplicate validation
                # ----------------------------------------
                #
                # Compare examples from the same task,
                # but do not compare examples from the
                # same scenario family.
                #
                # This prevents the numerical diversity
                # requirement from fighting against the
                # semantic similarity check.
                # ----------------------------------------

                current_prefix = (
                    example_id.split("_")[1]
                )

                comparable_examples = [
                    item
                    for item in accepted_examples
                    if (
                        item.category.value
                        == task
                        and item.example_id.split(
                            "_"
                        )[1]
                        != current_prefix
                    )
                ]

                near_duplicate_result = (
                    check_near_duplicate(
                        example,
                        comparable_examples,
                        threshold=(
                            NEAR_DUPLICATE_THRESHOLD
                        ),
                    )
                )

                if not near_duplicate_result[
                    "success"
                ]:

                    near_duplicates += 1

                    rejected += 1

                    print(
                        f"[REJECTED] "
                        f"{scenario_type} | "
                        f"near duplicate "
                        f"similarity="
                        f"{near_duplicate_result['similarity']:.3f}"
                    )

                    continue

                # ----------------------------------------
                # Accept example
                # ----------------------------------------

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

                task_counts[
                    task
                ] += 1

                difficulty_counts[
                    difficulty
                ] += 1

                if (
                    task
                    == "financial_classification"
                ):

                    classification_label = (
                        get_classification_label(
                            example.expected_output
                        )
                    )

                    classification_label_counts[
                        classification_label
                    ] += 1

                accepted += 1

                # ----------------------------------------
                # Write JSONL
                # ----------------------------------------

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
                    f"{accepted}/{count} | "
                    f"{scenario_type} "
                    f"{scenario_counts[scenario_type]}/"
                    f"{target} | "
                    f"{task} | "
                    f"{difficulty}"
                )

    # --------------------------------------------
    # Final validation
    # --------------------------------------------

    if accepted != count:

        raise RuntimeError(
            f"Dataset generation finished with "
            f"{accepted} accepted examples, "
            f"but {count} were required."
        )

    # --------------------------------------------
    # Summary
    # --------------------------------------------

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
        f"Generation errors:   {generation_errors}"
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
        "--------------- TASKS ---------------"
    )

    for task in TASK_TYPES:

        print(
            f"{task:<30}"
            f"{task_counts[task]}"
        )

    print(
        "\n"
        "------------ DIFFICULTY -------------"
    )

    for difficulty in DIFFICULTIES:

        print(
            f"{difficulty:<30}"
            f"{difficulty_counts[difficulty]}"
        )

    print(
        "\n"
        "------ CLASSIFICATION LABELS --------"
    )

    for label in CLASSIFICATION_LABELS:

        print(
            f"{label:<30}"
            f"{classification_label_counts[label]}"
            f"/"
            f"{classification_label_targets[label]}"
        )

    print(
        "\n"
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
        "generation_errors": generation_errors,
        "scenario_counts": scenario_counts,
        "task_counts": task_counts,
        "difficulty_counts": difficulty_counts,
        "classification_label_counts": (
            classification_label_counts
        ),
        "classification_label_targets": (
            classification_label_targets
        ),
    }


if __name__ == "__main__":
    generate_and_validate_examples()