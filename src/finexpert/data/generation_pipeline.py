import json
from pathlib import Path

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
    """Distribute requested examples evenly across scenarios."""
    scenario_count = len(SCENARIO_TYPES)
    base_count = count // scenario_count
    remainder = count % scenario_count

    return {
        scenario: base_count + (1 if index < remainder else 0)
        for index, scenario in enumerate(SCENARIO_TYPES)
    }


def get_task(index):
    """Cycle through the three FinExpert training tasks."""
    return TASK_TYPES[index % len(TASK_TYPES)]


def get_difficulty(index):
    """Cycle through easy, medium and hard."""
    return DIFFICULTIES[index % len(DIFFICULTIES)]


def generate_example_id(scenario_type, scenario_number):
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

    return f"{prefixes[scenario_type]}_{scenario_number:03d}"


def generate_and_validate_examples(
    count=TARGET_EXAMPLES,
    output_file=OUTPUT_FILE,
):
    """
    Generate a balanced FinExpert dataset.

    Each scenario receives an equal number of examples.
    Within each scenario, task and difficulty are independently
    cycled so the final dataset is balanced across both axes.
    """
    if count <= 0:
        raise ValueError("count must be greater than zero.")

    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    scenario_targets = get_scenario_targets(count)

    accepted_examples = []
    existing_fingerprints = set()

    scenario_counts = {
        scenario: 0 for scenario in SCENARIO_TYPES
    }
    task_counts = {task: 0 for task in TASK_TYPES}
    scenario_metric_fingerprints = {
        scenario: set() for scenario in SCENARIO_TYPES
    }
    difficulty_counts = {
        difficulty: 0 for difficulty in DIFFICULTIES
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

    with output_file.open("w", encoding="utf-8") as file:
        for scenario_type in SCENARIO_TYPES:
            target = scenario_targets[scenario_type]
            scenario_attempts = 0

            while scenario_counts[scenario_type] < target:
                scenario_attempts += 1

                if scenario_attempts > MAX_ATTEMPTS_PER_SCENARIO:
                    raise RuntimeError(
                        f"Unable to generate enough valid examples for "
                        f"scenario '{scenario_type}'. Accepted "
                        f"{scenario_counts[scenario_type]} of {target} "
                        f"after {MAX_ATTEMPTS_PER_SCENARIO} attempts."
                    )

                scenario_number = scenario_counts[scenario_type] + 1

                # These are based on the accepted position within the
                # current scenario, so rejected attempts do not distort
                # the requested task/difficulty distribution.
                local_index = scenario_number - 1

                # Ten examples per task and ten examples per
                # difficulty within every 30-example scenario block.
                task = get_task(local_index)
                task_index = TASK_TYPES.index(task)
                # Latin-square assignment: every task receives an equal
                # mix of easy, medium, and hard examples within each
                # scenario, while the global dataset remains balanced.
                scenario_index = SCENARIO_TYPES.index(scenario_type)
                difficulty = DIFFICULTIES[
                    (local_index // len(TASK_TYPES) + task_index + scenario_index)
                    % len(DIFFICULTIES)
                ]

                company = COMPANIES[generated % len(COMPANIES)]
                example_id = generate_example_id(
                    scenario_type,
                    scenario_number,
                )
                seed = generated + 1
                generated += 1

                try:
                    scenario = generate_scenario(
                        scenario_type=scenario_type,
                        seed=seed,
                    )
                    metric_fingerprint = json.dumps(
                        scenario["metrics"],
                        sort_keys=True,
                    )

                    # Keep numerical scenarios unique within a scenario family.
                    # This is important because the same numerical case may be
                    # used by different training tasks, and cross-task duplicates
                    # should not consume the dataset's diversity budget.
                    if metric_fingerprint in scenario_metric_fingerprints[scenario_type]:
                        rejected += 1
                        continue

                    # Reserve this numerical scenario immediately. If the
                    # rendered example is rejected later, retrying the same
                    # numerical case would not add diversity.
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
                        f"[REJECTED] {scenario_type} | "
                        f"generation error: {type(exc).__name__}: {exc}"
                    )
                    continue

                try:
                    example = FinancialExample(**example_data)
                except Exception as exc:
                    schema_errors += 1
                    rejected += 1
                    print(
                        f"[REJECTED] {scenario_type} | "
                        f"schema error: {type(exc).__name__}: {exc}"
                    )
                    continue

                quality_result = validate_required_content(example)
                if not quality_result["success"]:
                    quality_errors += 1
                    rejected += 1
                    print(
                        f"[REJECTED] {scenario_type} | "
                        f"quality error: {quality_result.get('reason')}"
                    )
                    continue

                financial_result = validate_financial_example(
                    example_id=example.example_id,
                    input_text=example.input,
                    expected_output=example.expected_output,
                )
                if not financial_result["success"]:
                    financial_reason = financial_result.get("reason")

                    # The current financial validator focuses on
                    # period-over-period growth claims. Ratio-only
                    # scenarios (for example liquidity, efficiency,
                    # and risk analysis) do not contain a value-change
                    # claim to validate, so they are allowed through
                    # while the existing claim checks remain strict.
                    if financial_reason != "no_value_change_claims_found":
                        financial_errors += 1
                        rejected += 1
                        print(
                            f"[REJECTED] {scenario_type} | "
                            f"financial error: {financial_reason}"
                        )
                        continue

                duplicate_result = check_duplicate(
                    example,
                    existing_fingerprints,
                )
                if not duplicate_result["success"]:
                    duplicates += 1
                    rejected += 1
                    print(
                        f"[REJECTED] {scenario_type} | exact duplicate"
                    )
                    continue

                current_prefix = example_id.split("_")[1]
                comparable_examples = [
                    item
                    for item in accepted_examples
                    if (
                        item.category.value == task
                        and item.example_id.split("_")[1]
                        != current_prefix
                    )
                ]

                near_duplicate_result = check_near_duplicate(
                    example,
                    comparable_examples,
                    threshold=NEAR_DUPLICATE_THRESHOLD,
                )
                if not near_duplicate_result["success"]:
                    near_duplicates += 1
                    rejected += 1
                    print(
                        f"[REJECTED] {scenario_type} | near duplicate "
                        f"similarity={near_duplicate_result['similarity']:.3f}"
                    )
                    continue

                accepted_examples.append(example)
                existing_fingerprints.add(
                    duplicate_result["fingerprint"]
                )

                scenario_counts[scenario_type] += 1
                task_counts[task] += 1
                difficulty_counts[difficulty] += 1
                accepted += 1

                file.write(
                    json.dumps(
                        example.model_dump(mode="json"),
                        ensure_ascii=False,
                    )
                    + "\n"
                )
                file.flush()

                print(
                    f"[ACCEPTED] {accepted}/{count} | "
                    f"{scenario_type} {scenario_counts[scenario_type]}/{target} | "
                    f"{task} | {difficulty}"
                )

    print(
        "\n"
        "========================================\n"
        "       FINEXPERT DATASET SUMMARY\n"
        "========================================"
    )
    print(f"Target examples:     {count}")
    print(f"Generated attempts:  {generated}")
    print(f"Accepted examples:   {accepted}")
    print(f"Rejected examples:   {rejected}")
    print(f"Exact duplicates:    {duplicates}")
    print(f"Near duplicates:     {near_duplicates}")
    print(f"Financial errors:    {financial_errors}")
    print(f"Schema errors:       {schema_errors}")
    print(f"Quality errors:      {quality_errors}")
    print(f"Generation errors:   {generation_errors}")

    print("\n------------- SCENARIOS -------------")
    for scenario in SCENARIO_TYPES:
        print(f"{scenario:<30}{scenario_counts[scenario]}")

    print("\n--------------- TASKS ---------------")
    for task in TASK_TYPES:
        print(f"{task:<30}{task_counts[task]}")

    print("\n------------ DIFFICULTY -------------")
    for difficulty in DIFFICULTIES:
        print(f"{difficulty:<30}{difficulty_counts[difficulty]}")

    print("========================================\n")

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
