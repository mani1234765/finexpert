import json
import re
from functools import lru_cache
from pathlib import Path

from .difficulty_scenarios import build_difficulty_scenario
from .example_validator import validate_financial_example
from .quality_validator import check_duplicate, validate_required_content
from .schema import FinancialExample
from .similarity_validator import check_near_duplicate
from .source_consistency_validator import validate_source_consistency
from .task_generator import generate_training_example


OUTPUT_FILE = Path("data/raw/generated_explanations.jsonl")
NEAR_DUPLICATE_THRESHOLD = 0.85
TARGET_EXAMPLES = 300
MAX_ATTEMPTS_PER_SCENARIO = 100
PREFLIGHT_MAX_SEEDS = 500
PREFLIGHT_MIN_CANDIDATES = 8

SCENARIO_TYPES = [
    "revenue_growth", "profitability", "operating_expenses",
    "debt_leverage", "liquidity", "cash_flow", "efficiency",
    "risk_analysis", "multi_metric_comparison", "comprehensive_performance",
]
TASK_TYPES = [
    "financial_explanation",
    "financial_classification",
    "financial_report_generation",
]
DIFFICULTIES = ["easy", "medium", "hard"]
CLASSIFICATION_LABELS = ["Healthy", "Moderate Risk", "High Risk"]
COMPANIES = [
    "ABC Industries", "XYZ Technologies", "Nova Financials", "Apex Manufacturing",
    "Vertex Solutions", "Orion Enterprises", "Summit Industries", "Pioneer Technologies",
    "Horizon Manufacturing", "Atlas Solutions", "BluePeak Industries", "Crest Financials",
    "Evergreen Technologies", "Prime Manufacturing", "NextGen Solutions",
]


def get_scenario_targets(count):
    base, rem = divmod(count, len(SCENARIO_TYPES))
    return {s: base + (i < rem) for i, s in enumerate(SCENARIO_TYPES)}


def get_task(index):
    return TASK_TYPES[index % len(TASK_TYPES)]


def get_difficulty_for_slot(slot_index):
    """Assign difficulty from the global dataset slot index."""
    task = get_task(slot_index)
    task_index = TASK_TYPES.index(task)
    return DIFFICULTIES[
        (slot_index // len(TASK_TYPES) + task_index) % len(DIFFICULTIES)
    ]


def get_task_targets(count):
    base, rem = divmod(count, len(TASK_TYPES))
    return {t: base + (i < rem) for i, t in enumerate(TASK_TYPES)}


def get_classification_label_targets(count):
    base, rem = divmod(count, len(CLASSIFICATION_LABELS))
    return {l: base + (i < rem) for i, l in enumerate(CLASSIFICATION_LABELS)}


def get_classification_label(expected_output):
    match = re.search(
        r"classification\s*:\s*(healthy|moderate\s+risk|high\s+risk)",
        expected_output,
        flags=re.IGNORECASE,
    )
    if match is None:
        return None
    normalized = re.sub(r"\s+", " ", match.group(1).strip()).lower()
    return {
        "healthy": "Healthy",
        "moderate risk": "Moderate Risk",
        "high risk": "High Risk",
    }.get(normalized)


def generate_example_id(scenario_type, scenario_number):
    prefixes = {
        "revenue_growth": "fin_rev", "profitability": "fin_profit",
        "operating_expenses": "fin_opex", "debt_leverage": "fin_debt",
        "liquidity": "fin_liq", "cash_flow": "fin_cash",
        "efficiency": "fin_eff", "risk_analysis": "fin_risk",
        "multi_metric_comparison": "fin_multi",
        "comprehensive_performance": "fin_comp",
    }
    return f"{prefixes[scenario_type]}_{scenario_number:03d}"


def _metric_fingerprint(scenario_result):
    return json.dumps(scenario_result["scenario"]["metrics"], sort_keys=True)


def _generate_candidate(scenario_type, task, difficulty, example_id, company, seed):
    # Authoritative scenario path. task_generator uses this same path internally.
    scenario_result = build_difficulty_scenario(
        scenario_type=scenario_type,
        difficulty=difficulty,
        seed=seed,
        company=company,
    )
    example_data = generate_training_example(
        scenario_type=scenario_type,
        task=task,
        difficulty=difficulty,
        example_id=example_id,
        company=company,
        seed=seed,
    )
    return example_data, _metric_fingerprint(scenario_result)


def _validate_candidate(example_data):
    try:
        example = FinancialExample(**example_data)
    except Exception as exc:
        return False, None, f"schema error: {type(exc).__name__}: {exc}"

    quality = validate_required_content(example)
    if not quality["success"]:
        return False, None, f"quality error: {quality.get('reason')}"

    financial = validate_financial_example(
        example_id=example.example_id,
        input_text=example.input,
        expected_output=example.expected_output,
    )
    if not financial["success"] and financial.get("reason") != "no_value_change_claims_found":
        return False, None, f"financial error: {financial.get('reason')}"

    source = validate_source_consistency(
        input_text=example.input,
        expected_output=example.expected_output,
    )
    if not source["success"]:
        return False, None, f"source consistency error: {source.get('reason')}"

    return True, example, None


def _required_combinations(scenario_targets):
    """Return the exact scenario/task/difficulty combinations required."""
    required = set()
    global_slot_index = 0

    for scenario, target in scenario_targets.items():
        for _ in range(target):
            task = get_task(global_slot_index)
            difficulty = get_difficulty_for_slot(global_slot_index)
            required.add((scenario, task, difficulty))
            global_slot_index += 1

    return required


def _preflight(scenario_targets):
    """Discover valid seeds and feasible classification labels before production."""
    task_pools = {}
    classification_pools = {}
    next_seed = {}

    print("\n========================================")
    print("          FINEXPERT PREFLIGHT")
    print("========================================")

    for scenario, task, difficulty in sorted(_required_combinations(scenario_targets)):
        key = (scenario, task, difficulty)
        seen = set()
        valid_seeds = []
        labels = {label: [] for label in CLASSIFICATION_LABELS}
        last_seed = 0

        for seed in range(1, PREFLIGHT_MAX_SEEDS + 1):
            last_seed = seed
            try:
                data, fingerprint = _generate_candidate(
                    scenario, task, difficulty, "preflight_000", COMPANIES[0], seed
                )
            except Exception:
                continue

            if fingerprint in seen:
                continue

            ok, example, _ = _validate_candidate(data)
            if not ok:
                continue
            seen.add(fingerprint)

            if task == "financial_classification":
                label = get_classification_label(example.expected_output)
                if label in labels and len(labels[label]) < PREFLIGHT_MIN_CANDIDATES:
                    labels[label].append(seed)
            elif len(valid_seeds) < PREFLIGHT_MIN_CANDIDATES:
                valid_seeds.append(seed)

            if task != "financial_classification":
                if len(valid_seeds) >= PREFLIGHT_MIN_CANDIDATES:
                    break
            elif all((not pool or len(pool) >= PREFLIGHT_MIN_CANDIDATES) for pool in labels.values()) and seed >= 100:
                break

        next_seed[key] = last_seed + 1

        if task == "financial_classification":
            pools = {label: seeds for label, seeds in labels.items() if seeds}
            if not pools:
                raise RuntimeError(
                    f"PREFLIGHT FAILED: no valid classification candidate for {scenario} | {difficulty}"
                )
            classification_pools[key] = pools
            print(
                f"[PREFLIGHT OK] {scenario} | {task} | {difficulty} | "
                + ", ".join(f"{label}={len(seeds)}" for label, seeds in pools.items())
            )
        else:
            if not valid_seeds:
                raise RuntimeError(
                    f"PREFLIGHT FAILED: no valid candidate for {scenario} | {task} | {difficulty}"
                )
            task_pools[key] = valid_seeds
            print(f"[PREFLIGHT OK] {scenario} | {task} | {difficulty} | valid={len(valid_seeds)}")

    print("========================================\n")
    return task_pools, classification_pools, next_seed


def _classification_slots(scenario_targets, classification_pools):
    slots = []
    global_slot_index = 0

    for scenario, target in scenario_targets.items():
        for i in range(target):
            task = get_task(global_slot_index)
            if task != "financial_classification":
                global_slot_index += 1
                continue

            difficulty = get_difficulty_for_slot(global_slot_index)
            key = (scenario, task, difficulty)
            slots.append({
                "scenario": scenario,
                "number": i + 1,
                "global_slot_index": global_slot_index,
                "difficulty": difficulty,
                "key": key,
                "labels": tuple(sorted(classification_pools[key])),
            })

            global_slot_index += 1

    return slots


def _solve_classification_plan(slots, targets):
    """Exact small backtracking solver for the global 34/33/33 label quotas."""
    if not slots:
        return {}

    ordered = sorted(
        slots,
        key=lambda s: (len(s["labels"]), s["scenario"], s["number"]),
    )

    @lru_cache(maxsize=None)
    def solve(i, healthy, moderate, high):
        if i == len(ordered):
            return () if (
                healthy == targets["Healthy"]
                and moderate == targets["Moderate Risk"]
                and high == targets["High Risk"]
            ) else None

        counts = {
            "Healthy": healthy,
            "Moderate Risk": moderate,
            "High Risk": high,
        }
        labels = sorted(
            ordered[i]["labels"],
            key=lambda label: -(targets[label] - counts[label]),
        )

        for label in labels:
            if counts[label] >= targets[label]:
                continue
            new = counts.copy()
            new[label] += 1
            tail = solve(
                i + 1,
                new["Healthy"],
                new["Moderate Risk"],
                new["High Risk"],
            )
            if tail is not None:
                return (label,) + tail
        return None

    solution = solve(0, 0, 0, 0)
    if solution is None:
        raise RuntimeError(
            "CLASSIFICATION PREFLIGHT FAILED: requested 34/33/33 distribution "
            "is not feasible with the available scenario/difficulty labels."
        )

    return {
        (slot["scenario"], slot["number"]): label
        for slot, label in zip(ordered, solution)
    }


def _find_classification_seed(
    scenario,
    difficulty,
    desired_label,
    company,
    example_id,
    pool,
    used_fingerprints,
    start_seed,
):
    seeds = list(pool) + list(range(start_seed, start_seed + PREFLIGHT_MAX_SEEDS))
    seen = set()

    for seed in seeds:
        if seed in seen:
            continue
        seen.add(seed)
        try:
            data, fingerprint = _generate_candidate(
                scenario, "financial_classification", difficulty,
                example_id, company, seed
            )
        except Exception:
            continue
        if fingerprint in used_fingerprints:
            continue
        ok, example, _ = _validate_candidate(data)
        if not ok:
            continue
        if get_classification_label(example.expected_output) != desired_label:
            continue
        return seed, data, fingerprint

    raise RuntimeError(
        f"Unable to generate fresh classification candidate for "
        f"{scenario} | {difficulty} | {desired_label}"
    )


def _find_task_seed(
    scenario,
    task,
    difficulty,
    company,
    example_id,
    pool,
    used_fingerprints,
    start_seed,
):
    seeds = list(pool) + list(range(start_seed, start_seed + PREFLIGHT_MAX_SEEDS))
    seen = set()

    for seed in seeds:
        if seed in seen:
            continue
        seen.add(seed)
        try:
            data, fingerprint = _generate_candidate(
                scenario, task, difficulty, example_id, company, seed
            )
        except Exception:
            continue
        if fingerprint in used_fingerprints:
            continue
        ok, _, _ = _validate_candidate(data)
        if not ok:
            continue
        return seed, data, fingerprint

    raise RuntimeError(
        f"Unable to generate fresh candidate for {scenario} | {task} | {difficulty}"
    )


def generate_and_validate_examples(count=TARGET_EXAMPLES, output_file=OUTPUT_FILE):
    """
    Production pipeline in one place.

    1. Plan scenario/task/difficulty slots.
    2. Preflight only the combinations actually required.
    3. Discover feasible classification labels from the real generator.
    4. Solve the global classification quota before production.
    5. Generate using the same authoritative difficulty-scenario path as task_generator.py.
    6. Validate schema/content/math/source consistency/duplicates.
    7. Reserve numerical fingerprints only after acceptance.
    """
    if count <= 0:
        raise ValueError("count must be greater than zero.")

    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    scenario_targets = get_scenario_targets(count)
    task_targets = get_task_targets(count)
    classification_targets = get_classification_label_targets(
        task_targets["financial_classification"]
    )

    task_pools, classification_pools, next_seed = _preflight(scenario_targets)
    slots = _classification_slots(scenario_targets, classification_pools)
    classification_plan = _solve_classification_plan(slots, classification_targets)

    print("Classification plan:")
    for label in CLASSIFICATION_LABELS:
        print(f"  {label:<15} {sum(v == label for v in classification_plan.values())}")
    print()

    accepted_examples = []
    existing_fingerprints = set()
    scenario_metric_fingerprints = {s: set() for s in SCENARIO_TYPES}
    scenario_counts = {s: 0 for s in SCENARIO_TYPES}
    task_counts = {t: 0 for t in TASK_TYPES}
    difficulty_counts = {d: 0 for d in DIFFICULTIES}
    classification_counts = {l: 0 for l in CLASSIFICATION_LABELS}

    generated = accepted = rejected = duplicates = near_duplicates = 0
    financial_errors = schema_errors = quality_errors = generation_errors = 0

    with output_file.open("w", encoding="utf-8") as file:
        for scenario in SCENARIO_TYPES:
            target = scenario_targets[scenario]
            attempts = 0

            while scenario_counts[scenario] < target:
                attempts += 1
                if attempts > MAX_ATTEMPTS_PER_SCENARIO:
                    raise RuntimeError(
                        f"Unable to generate enough valid examples for scenario "
                        f"'{scenario}'. Accepted {scenario_counts[scenario]} of {target} "
                        f"after {MAX_ATTEMPTS_PER_SCENARIO} attempts."
                    )

                number = scenario_counts[scenario] + 1
                local_index = number - 1

                global_slot_index = (
                    sum(
                        scenario_targets[item]
                        for item in SCENARIO_TYPES[:SCENARIO_TYPES.index(scenario)]
                    )
                    + local_index
                )

                task = get_task(global_slot_index)
                difficulty = get_difficulty_for_slot(global_slot_index)
                company = COMPANIES[generated % len(COMPANIES)]
                example_id = generate_example_id(scenario, number)

                generated += 1

                try:
                    key = (scenario, task, difficulty)
                    if task == "financial_classification":
                        desired_label = classification_plan[(scenario, number)]
                        seed, data, metric_fp = _find_classification_seed(
                            scenario, difficulty, desired_label, company, example_id,
                            classification_pools[key][desired_label],
                            scenario_metric_fingerprints[scenario],
                            next_seed[key],
                        )
                    else:
                        seed, data, metric_fp = _find_task_seed(
                            scenario, task, difficulty, company, example_id,
                            task_pools[key],
                            scenario_metric_fingerprints[scenario],
                            next_seed[key],
                        )
                except Exception as exc:
                    generation_errors += 1
                    rejected += 1
                    print(f"[REJECTED] {scenario} | generation error: {type(exc).__name__}: {exc}")
                    continue

                try:
                    example = FinancialExample(**data)
                except Exception as exc:
                    schema_errors += 1
                    rejected += 1
                    print(f"[REJECTED] {scenario} | schema error: {type(exc).__name__}: {exc}")
                    continue

                quality = validate_required_content(example)
                if not quality["success"]:
                    quality_errors += 1
                    rejected += 1
                    print(f"[REJECTED] {scenario} | quality error: {quality.get('reason')}")
                    continue

                financial = validate_financial_example(
                    example_id=example.example_id,
                    input_text=example.input,
                    expected_output=example.expected_output,
                )
                if not financial["success"] and financial.get("reason") != "no_value_change_claims_found":
                    financial_errors += 1
                    rejected += 1
                    print(f"[REJECTED] {scenario} | financial error: {financial.get('reason')}")
                    continue

                source = validate_source_consistency(
                    input_text=example.input,
                    expected_output=example.expected_output,
                )
                if not source["success"]:
                    financial_errors += 1
                    rejected += 1
                    print(f"[REJECTED] {scenario} | source consistency error: {source.get('reason')}")
                    continue

                if task == "financial_classification":
                    actual_label = get_classification_label(example.expected_output)
                    desired_label = classification_plan[(scenario, number)]
                    if actual_label != desired_label:
                        generation_errors += 1
                        rejected += 1
                        print(
                            f"[REJECTED] {scenario} | classification mismatch: "
                            f"expected {desired_label}, got {actual_label}"
                        )
                        continue
                    if classification_counts[actual_label] >= classification_targets[actual_label]:
                        generation_errors += 1
                        rejected += 1
                        print(f"[REJECTED] {scenario} | classification quota exceeded: {actual_label}")
                        continue

                duplicate = check_duplicate(example, existing_fingerprints)
                if not duplicate["success"]:
                    duplicates += 1
                    rejected += 1
                    print(f"[REJECTED] {scenario} | exact duplicate")
                    continue

                current_prefix = example_id.split("_")[1]
                comparable = [
                    item for item in accepted_examples
                    if item.category.value == task
                    and item.example_id.split("_")[1] != current_prefix
                ]
                near = check_near_duplicate(
                    example,
                    comparable,
                    threshold=NEAR_DUPLICATE_THRESHOLD,
                )
                if not near["success"]:
                    near_duplicates += 1
                    rejected += 1
                    print(f"[REJECTED] {scenario} | near duplicate similarity={near['similarity']:.3f}")
                    continue

                accepted_examples.append(example)
                existing_fingerprints.add(duplicate["fingerprint"])
                scenario_metric_fingerprints[scenario].add(metric_fp)
                scenario_counts[scenario] += 1
                task_counts[task] += 1
                difficulty_counts[difficulty] += 1

                if task == "financial_classification":
                    classification_counts[get_classification_label(example.expected_output)] += 1

                accepted += 1
                file.write(json.dumps(example.model_dump(mode="json"), ensure_ascii=False) + "\n")
                file.flush()

                print(
                    f"[ACCEPTED] {accepted}/{count} | {scenario} "
                    f"{scenario_counts[scenario]}/{target} | {task} | {difficulty}"
                )

    if accepted != count:
        raise RuntimeError(f"Dataset generation finished with {accepted} accepted examples, but {count} were required.")

    for task, target in task_targets.items():
        if task_counts[task] != target:
            raise RuntimeError(f"Task balance failure for {task}: got {task_counts[task]}, expected {target}.")

    base, rem = divmod(count, len(DIFFICULTIES))
    difficulty_targets = {d: base + (i < rem) for i, d in enumerate(DIFFICULTIES)}
    for difficulty, target in difficulty_targets.items():
        if difficulty_counts[difficulty] != target:
            raise RuntimeError(f"Difficulty balance failure for {difficulty}: got {difficulty_counts[difficulty]}, expected {target}.")

    for label, target in classification_targets.items():
        if classification_counts[label] != target:
            raise RuntimeError(f"Classification balance failure for {label}: got {classification_counts[label]}, expected {target}.")

    print("\n========================================")
    print("       FINEXPERT DATASET SUMMARY")
    print("========================================")
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

    print("\n------ CLASSIFICATION LABELS --------")
    for label in CLASSIFICATION_LABELS:
        print(f"{label:<30}{classification_counts[label]}/{classification_targets[label]}")

    print("\n========================================\n")

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
        "classification_label_counts": classification_counts,
        "classification_label_targets": classification_targets,
    }


if __name__ == "__main__":
    generate_and_validate_examples()
