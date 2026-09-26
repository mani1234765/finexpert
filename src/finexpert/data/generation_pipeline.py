import json
from pathlib import Path

from .difficulty_validator import validate_difficulty
from .example_validator import validate_financial_example
from .quality_validator import (
    check_duplicate,
    validate_required_content,
)
from .schema import FinancialExample
from .scenario_generator import generate_scenario
from .similarity_validator import check_near_duplicate
from .task_generator import generate_training_example


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
    Distribute examples evenly across scenario types.
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


def get_task(index):
    """
    Cycle through the three FinExpert training tasks.
    """

    return TASK_TYPES[
        index % len(TASK_TYPES)
    ]


def get_difficulty(
    local_index,
    task,
    scenario_index,
):
    """
    Distribute easy, medium and hard examples
    across tasks and scenarios.

    The assignment is deterministic so the dataset
    remains reproducible.
    """

    task_index = TASK_TYPES.index(task)

    difficulty_index = (
        local_index // len(TASK_TYPES)
        + task_index
        + scenario_index
    ) % len(DIFFICULTIES)

    return DIFFICULTIES[
        difficulty_index
    ]


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

    The pipeline generates examples through the
    task_generator so that:

        scenario
            ↓
        difficulty-aware input
            ↓
        task-specific output
            ↓
        validation
            ↓
        accepted dataset

    Each scenario receives an equal number of examples.

    Tasks are balanced across the dataset.

    Difficulty levels are balanced across the dataset.

    Numerical scenarios are kept unique within
    each scenario family.
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
                scenario_counts[scenario_type]
                < target
            ):

                scenario_attempts += 1

                if (
                    scenario_attempts
                    > MAX_ATTEMPTS_PER_SCENARIO
                ):
                    raise RuntimeError(
                        "Unable to generate enough "
                        "valid examples for scenario "
                        f"'{scenario_type}'. "
                        f"Accepted "
                        f"{scenario_counts[scenario_type]} "
                        f"of {target} after "
                        f"{MAX_ATTEMPTS_PER_SCENARIO} "
                        "attempts."
                    )

                # --------------------------------------------------
                # Determine task and difficulty.
                # --------------------------------------------------

                local_index = (
                    scenario_counts[scenario_type]
                )

                task = get_task(
                    local_index
                )

                scenario_index = (
                    SCENARIO_TYPES.index(
                        scenario_type
                    )
                )

                difficulty = get_difficulty(
                    local_index=local_index,
                    task=task,
                    scenario_index=scenario_index,
                )

                # --------------------------------------------------
                # Company / ID / seed.
                # --------------------------------------------------

                company = COMPANIES[
                    generated
                    % len(COMPANIES)
                ]

                scenario_number = (
                    scenario_counts[
                        scenario_type
                    ] + 1
                )

                example_id = generate_example_id(
                    scenario_type=scenario_type,
                    scenario_number=scenario_number,
                )

                seed = generated + 1

                generated += 1

                # --------------------------------------------------
                # Generate the numerical scenario first.
                #
                # This is used only for diversity tracking.
                #
                # The same seed is passed to task_generator,
                # which creates the authoritative example.
                # --------------------------------------------------

                try:

                    scenario = generate_scenario(
                        scenario_type=scenario_type,
                        seed=seed,
                    )

                    metric_fingerprint = json.dumps(
                        scenario["metrics"],
                        sort_keys=True,
                    )

                except Exception as exc:

                    generation_errors += 1
                    rejected += 1

                    print(
                        f"[REJECTED] "
                        f"{scenario_type} | "
                        f"scenario generation error: "
                        f"{type(exc).__name__}: {exc}"
                    )

                    continue

                # --------------------------------------------------
                # Prevent duplicate numerical scenarios.
                # --------------------------------------------------

                if (
                    metric_fingerprint
                    in scenario_metric_fingerprints[
                        scenario_type
                    ]
                ):

                    rejected += 1

                    continue

                scenario_metric_fingerprints[
                    scenario_type
                ].add(
                    metric_fingerprint
                )

                # --------------------------------------------------
                # IMPORTANT:
                #
                # Use the task_generator.
                #
                # Do NOT use generate_explanation_example()
                # here.
                # --------------------------------------------------

                try:

                    example_data = (
                        generate_training_example(
                            scenario_type=scenario_type,
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
                        f"generation error: "
                        f"{type(exc).__name__}: {exc}"
                    )

                    continue

                # --------------------------------------------------
                # Schema validation.
                # --------------------------------------------------

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
                        f"{type(exc).__name__}: {exc}"
                    )

                    continue

                # --------------------------------------------------
                # Required content validation.
                # --------------------------------------------------

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
                        f"{scenario_type} | "
                        f"quality error: "
                        f"{quality_result.get('reason')}"
                    )

                    continue

                # --------------------------------------------------
                # Financial calculation validation.
                # --------------------------------------------------

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

                    financial_reason = (
                        financial_result.get(
                            "reason"
                        )
                    )

                    # Ratio-only scenarios may not have
                    # period-over-period value changes.
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

                # --------------------------------------------------
                # Difficulty validation.
                # --------------------------------------------------

                difficulty_result = validate_difficulty(
                        input_text=example.input,
                        expected_output=example.expected_output,
                        difficulty=example.difficulty.value,
                        reasoning_types=[
                            reasoning_type.value
                            for reasoning_type in example.reasoning_type
                        ],

                    )
                

                if not difficulty_result["success"]:

            
                    rejected += 1

                    details = difficulty_result.get("details") or {}
                    metric_count = details.get(
                        "metric_count",
                        "unknown",
                    )
                    

                    print(
                        f"[REJECTED] "
                        f"{scenario_type} | "
                        f"difficulty error: "
                        f"{difficulty_result.get('reason', 'unknown')} "
                        f"| difficulty={difficulty} "
                        f"| metrics={metric_count} "
                    )

                    continue

                # --------------------------------------------------
                # Exact duplicate validation.
                # --------------------------------------------------

                duplicate_result = (
                    check_duplicate(
                        example,
                        existing_fingerprints,
                    )
                )

                if not duplicate_result["success"]:

                    duplicates += 1
                    rejected += 1

                    print(
                        f"[REJECTED] "
                        f"{scenario_type} | "
                        "exact duplicate"
                    )

                    continue

                # --------------------------------------------------
                # Near duplicate validation.
                #
                # Compare primarily against examples
                # from the same task so that the same
                # scenario can legitimately teach
                # different task behaviors.
                # --------------------------------------------------

                comparable_examples = [
                    item
                    for item in accepted_examples
                    if (
                        item.category.value
                        == task
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
                        "near duplicate "
                        f"similarity="
                        f"{near_duplicate_result['similarity']:.3f}"
                    )

                    continue

                # --------------------------------------------------
                # ACCEPT.
                # --------------------------------------------------

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

                accepted += 1

                # --------------------------------------------------
                # Write JSONL.
                # --------------------------------------------------

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

    # ============================================================
    # FINAL SUMMARY
    # ============================================================

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
        "\n------------- SCENARIOS -------------"
    )

    for scenario in SCENARIO_TYPES:

        print(
            f"{scenario:<30}"
            f"{scenario_counts[scenario]}"
        )

    print(
        "\n--------------- TASKS ---------------"
    )

    for task in TASK_TYPES:

        print(
            f"{task:<30}"
            f"{task_counts[task]}"
        )

    print(
        "\n------------ DIFFICULTY -------------"
    )

    for difficulty in DIFFICULTIES:

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
        "generation_errors": generation_errors,
        "scenario_counts": scenario_counts,
        "task_counts": task_counts,
        "difficulty_counts": difficulty_counts,
    }


if __name__ == "__main__":
    generate_and_validate_examples()