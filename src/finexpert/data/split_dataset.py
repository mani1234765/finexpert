import itertools
import json
import random
import re
from collections import Counter, defaultdict
from pathlib import Path


INPUT_FILE = Path(
    "data/raw/generated_explanations.jsonl"
)

OUTPUT_DIR = Path(
    "data/splits"
)

TRAIN_FILE = OUTPUT_DIR / "train.jsonl"
VALIDATION_FILE = OUTPUT_DIR / "validation.jsonl"
TEST_FILE = OUTPUT_DIR / "test.jsonl"

RANDOM_SEED = 42

TRAIN_RATIO = 0.80
VALIDATION_RATIO = 0.10
TEST_RATIO = 0.10


SCENARIO_PREFIXES = {
    "fin_rev": "revenue_growth",
    "fin_profit": "profitability",
    "fin_opex": "operating_expenses",
    "fin_debt": "debt_leverage",
    "fin_liq": "liquidity",
    "fin_cash": "cash_flow",
    "fin_eff": "efficiency",
    "fin_risk": "risk_analysis",
    "fin_multi": "multi_metric_comparison",
    "fin_comp": "comprehensive_performance",
}


TASKS = [
    "financial_explanation",
    "financial_classification",
    "financial_report_generation",
]


DIFFICULTIES = [
    "easy",
    "medium",
    "hard",
]


def load_dataset(path):
    if not path.exists():
        raise FileNotFoundError(
            f"Dataset file not found: {path}"
        )

    examples = []

    with path.open(
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
                examples.append(
                    json.loads(line)
                )
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON at line "
                    f"{line_number}: {exc}"
                ) from exc

    if not examples:
        raise ValueError(
            "Dataset is empty."
        )

    return examples


def get_scenario(example):
    example_id = example["example_id"]

    match = re.match(
        r"^(fin_[a-z]+)_\d+$",
        example_id,
    )

    if match is None:
        raise ValueError(
            f"Unable to determine scenario "
            f"from example ID: {example_id}"
        )

    prefix = match.group(1)

    if prefix not in SCENARIO_PREFIXES:
        raise ValueError(
            f"Unknown scenario prefix "
            f"'{prefix}' in {example_id}"
        )

    return SCENARIO_PREFIXES[prefix]


def get_stratum(example):
    return (
        get_scenario(example),
        example["category"],
        example["difficulty"],
    )


def _find_three_examples_covering_task_and_difficulty(
    examples,
):
    """
    Find exactly three distinct examples such that:

        tasks       = all 3 tasks exactly once
        difficulties = all 3 difficulties exactly once

    The search is tiny for this dataset:
    each scenario contains 30 examples.
    """
    for combination in itertools.combinations(
        examples,
        3,
    ):
        tasks = {
            item["category"]
            for item in combination
        }

        difficulties = {
            item["difficulty"]
            for item in combination
        }

        if (
            len(tasks) == len(TASKS)
            and len(difficulties)
            == len(DIFFICULTIES)
        ):
            return list(combination)

    return None


def split_scenario(
    examples,
    rng,
):
    """
    Split one 30-example scenario into:

        Train       24
        Validation   3
        Test         3

    Validation contains one example from each task
    and one example from each difficulty.

    Test does the same using different examples.

    Therefore, after doing this independently for all
    10 scenarios:

        Train:
            10 x 24 = 240

        Validation:
            10 x 3 = 30

        Test:
            10 x 3 = 30

    And each split retains balanced task/difficulty
    distributions.
    """
    if len(examples) != 30:
        raise RuntimeError(
            "Expected exactly 30 examples per "
            f"scenario, got {len(examples)}."
        )

    examples = list(examples)
    rng.shuffle(examples)

    validation = (
        _find_three_examples_covering_task_and_difficulty(
            examples
        )
    )

    if validation is None:
        raise RuntimeError(
            "Unable to construct a validation subset "
            "covering all tasks and difficulties."
        )

    validation_ids = {
        item["example_id"]
        for item in validation
    }

    remaining = [
        item
        for item in examples
        if item["example_id"]
        not in validation_ids
    ]

    test = (
        _find_three_examples_covering_task_and_difficulty(
            remaining
        )
    )

    if test is None:
        raise RuntimeError(
            "Unable to construct a test subset "
            "covering all tasks and difficulties."
        )

    test_ids = {
        item["example_id"]
        for item in test
    }

    train = [
        item
        for item in remaining
        if item["example_id"]
        not in test_ids
    ]

    if len(train) != 24:
        raise RuntimeError(
            f"Expected 24 train examples, "
            f"got {len(train)}."
        )

    return (
        train,
        validation,
        test,
    )


def write_jsonl(
    path,
    examples,
):
    with path.open(
        "w",
        encoding="utf-8",
    ) as file:
        for example in examples:
            file.write(
                json.dumps(
                    example,
                    ensure_ascii=False,
                )
                + "\n"
            )


def distribution(
    examples,
    key,
):
    return Counter(
        example[key]
        for example in examples
    )


def scenario_distribution(
    examples,
):
    return Counter(
        get_scenario(example)
        for example in examples
    )


def print_distribution(
    title,
    examples,
):
    print(
        f"\n{title}"
    )

    print(
        "-" * len(title)
    )

    print(
        f"Total: {len(examples)}"
    )

    print(
        "\nScenarios:"
    )

    for scenario, count in sorted(
        scenario_distribution(
            examples
        ).items()
    ):
        print(
            f"  {scenario:<30}"
            f"{count}"
        )

    print(
        "\nTasks:"
    )

    for task, count in sorted(
        distribution(
            examples,
            "category",
        ).items()
    ):
        print(
            f"  {task:<35}"
            f"{count}"
        )

    print(
        "\nDifficulty:"
    )

    for difficulty, count in sorted(
        distribution(
            examples,
            "difficulty",
        ).items()
    ):
        print(
            f"  {difficulty:<15}"
            f"{count}"
        )


def validate_split_sizes(
    train,
    validation,
    test,
    total,
):
    expected = {
        "train": int(total * TRAIN_RATIO),
        "validation": int(
            total * VALIDATION_RATIO
        ),
        "test": (
            total
            - int(total * TRAIN_RATIO)
            - int(total * VALIDATION_RATIO)
        ),
    }

    actual = {
        "train": len(train),
        "validation": len(validation),
        "test": len(test),
    }

    if actual != expected:
        raise RuntimeError(
            "Unexpected split sizes.\n"
            f"Expected: {expected}\n"
            f"Actual:   {actual}"
        )


def validate_no_overlap(
    train,
    validation,
    test,
):
    train_ids = {
        item["example_id"]
        for item in train
    }

    validation_ids = {
        item["example_id"]
        for item in validation
    }

    test_ids = {
        item["example_id"]
        for item in test
    }

    if train_ids & validation_ids:
        raise RuntimeError(
            "Train/validation overlap detected."
        )

    if train_ids & test_ids:
        raise RuntimeError(
            "Train/test overlap detected."
        )

    if validation_ids & test_ids:
        raise RuntimeError(
            "Validation/test overlap detected."
        )


def validate_scenario_distribution(
    original,
    train,
    validation,
    test,
):
    original_counts = scenario_distribution(
        original
    )

    train_counts = scenario_distribution(
        train
    )

    validation_counts = scenario_distribution(
        validation
    )

    test_counts = scenario_distribution(
        test
    )

    for scenario, count in original_counts.items():
        expected = (
            24,
            3,
            3,
        )

        actual = (
            train_counts[scenario],
            validation_counts[scenario],
            test_counts[scenario],
        )

        if actual != expected:
            raise RuntimeError(
                f"Scenario split failure for "
                f"{scenario}.\n"
                f"Expected: {expected}\n"
                f"Actual:   {actual}"
            )


def validate_task_distribution(
    train,
    validation,
    test,
):
    expected = {
        "train": {
            "financial_explanation": 80,
            "financial_classification": 80,
            "financial_report_generation": 80,
        },
        "validation": {
            "financial_explanation": 10,
            "financial_classification": 10,
            "financial_report_generation": 10,
        },
        "test": {
            "financial_explanation": 10,
            "financial_classification": 10,
            "financial_report_generation": 10,
        },
    }

    actual = {
        "train": distribution(
            train,
            "category",
        ),
        "validation": distribution(
            validation,
            "category",
        ),
        "test": distribution(
            test,
            "category",
        ),
    }

    for split_name in expected:
        for task in TASKS:
            if actual[split_name][task] != (
                expected[split_name][task]
            ):
                raise RuntimeError(
                    f"Task distribution failure "
                    f"for {split_name} / {task}: "
                    f"expected "
                    f"{expected[split_name][task]}, "
                    f"got "
                    f"{actual[split_name][task]}"
                )


def validate_difficulty_distribution(
    train,
    validation,
    test,
):
    expected = {
        "train": {
            "easy": 80,
            "medium": 80,
            "hard": 80,
        },
        "validation": {
            "easy": 10,
            "medium": 10,
            "hard": 10,
        },
        "test": {
            "easy": 10,
            "medium": 10,
            "hard": 10,
        },
    }

    actual = {
        "train": distribution(
            train,
            "difficulty",
        ),
        "validation": distribution(
            validation,
            "difficulty",
        ),
        "test": distribution(
            test,
            "difficulty",
        ),
    }

    for split_name in expected:
        for difficulty in DIFFICULTIES:
            if actual[split_name][difficulty] != (
                expected[split_name][difficulty]
            ):
                raise RuntimeError(
                    f"Difficulty distribution failure "
                    f"for {split_name} / {difficulty}: "
                    f"expected "
                    f"{expected[split_name][difficulty]}, "
                    f"got "
                    f"{actual[split_name][difficulty]}"
                )


def validate_within_scenario_balance(
    train,
    validation,
    test,
):
    """
    Check that every scenario has:

        Train:
            8 examples per task
            8 examples per difficulty

        Validation:
            1 per task
            1 per difficulty

        Test:
            1 per task
            1 per difficulty
    """
    split_map = {
        "train": train,
        "validation": validation,
        "test": test,
    }

    expected_counts = {
        "train": 8,
        "validation": 1,
        "test": 1,
    }

    for split_name, examples in split_map.items():
        grouped = defaultdict(list)

        for example in examples:
            grouped[
                get_scenario(example)
            ].append(example)

        for scenario, scenario_examples in (
            grouped.items()
        ):
            task_counts = Counter(
                item["category"]
                for item in scenario_examples
            )

            difficulty_counts = Counter(
                item["difficulty"]
                for item in scenario_examples
            )

            expected = expected_counts[
                split_name
            ]

            for task in TASKS:
                if task_counts[task] != expected:
                    raise RuntimeError(
                        f"Within-scenario task "
                        f"imbalance: "
                        f"{split_name} / "
                        f"{scenario} / "
                        f"{task}: "
                        f"expected {expected}, "
                        f"got "
                        f"{task_counts[task]}"
                    )

            for difficulty in DIFFICULTIES:
                if (
                    difficulty_counts[difficulty]
                    != expected
                ):
                    raise RuntimeError(
                        f"Within-scenario difficulty "
                        f"imbalance: "
                        f"{split_name} / "
                        f"{scenario} / "
                        f"{difficulty}: "
                        f"expected {expected}, "
                        f"got "
                        f"{difficulty_counts[difficulty]}"
                    )


def main():
    print(
        "\n"
        "============================================================"
    )

    print(
        "\n"
        "                 FINEXPERT DATASET SPLIT"
    )

    print(
        "\n"
        "============================================================"
    )

    examples = load_dataset(
        INPUT_FILE
    )

    print(
        f"\nLoaded examples: {len(examples)}"
    )

    if len(examples) != 300:
        raise RuntimeError(
            "This split configuration expects "
            "exactly 300 examples."
        )

    grouped_by_scenario = defaultdict(list)

    for example in examples:
        grouped_by_scenario[
            get_scenario(example)
        ].append(example)

    if len(grouped_by_scenario) != 10:
        raise RuntimeError(
            "Expected 10 scenarios, "
            f"found {len(grouped_by_scenario)}."
        )

    # --------------------------------------------------------
    # Deterministic scenario-level split.
    # --------------------------------------------------------

    rng = random.Random(
        RANDOM_SEED
    )

    train = []
    validation = []
    test = []

    for scenario in sorted(
        grouped_by_scenario
    ):
        (
            train_items,
            validation_items,
            test_items,
        ) = split_scenario(
            grouped_by_scenario[scenario],
            rng,
        )

        train.extend(
            train_items
        )

        validation.extend(
            validation_items
        )

        test.extend(
            test_items
        )

    # --------------------------------------------------------
    # Final deterministic ordering.
    # --------------------------------------------------------

    train.sort(
        key=lambda item: item["example_id"]
    )

    validation.sort(
        key=lambda item: item["example_id"]
    )

    test.sort(
        key=lambda item: item["example_id"]
    )

    # --------------------------------------------------------
    # Validation.
    # --------------------------------------------------------

    validate_split_sizes(
        train=train,
        validation=validation,
        test=test,
        total=len(examples),
    )

    validate_no_overlap(
        train=train,
        validation=validation,
        test=test,
    )

    validate_scenario_distribution(
        original=examples,
        train=train,
        validation=validation,
        test=test,
    )

    validate_task_distribution(
        train=train,
        validation=validation,
        test=test,
    )

    validate_difficulty_distribution(
        train=train,
        validation=validation,
        test=test,
    )

    validate_within_scenario_balance(
        train=train,
        validation=validation,
        test=test,
    )

    # --------------------------------------------------------
    # Output.
    # --------------------------------------------------------

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    write_jsonl(
        TRAIN_FILE,
        train,
    )

    write_jsonl(
        VALIDATION_FILE,
        validation,
    )

    write_jsonl(
        TEST_FILE,
        test,
    )

    # --------------------------------------------------------
    # Summary.
    # --------------------------------------------------------

    print(
        "\n============================================================"
    )

    print(
        "\n                 SPLIT COMPLETE"
    )

    print(
        "\n============================================================"
    )

    print(
        f"\nTrain:      {len(train)}"
        f" -> {TRAIN_FILE}"
    )

    print(
        f"Validation: {len(validation)}"
        f" -> {VALIDATION_FILE}"
    )

    print(
        f"Test:       {len(test)}"
        f" -> {TEST_FILE}"
    )

    print_distribution(
        "TRAIN DISTRIBUTION",
        train,
    )

    print_distribution(
        "VALIDATION DISTRIBUTION",
        validation,
    )

    print_distribution(
        "TEST DISTRIBUTION",
        test,
    )

    print(
        "\n"
        "============================================================"
    )

    print(
        "\nSPLIT VALIDATION: PASS"
    )

    print(
        "\n============================================================"
    )


if __name__ == "__main__":
    main()
