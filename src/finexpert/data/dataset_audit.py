import json
from collections import Counter
from pathlib import Path

from .schema import FinancialExample


DATASET_FILE = Path(
    "data/raw/generated_explanations.jsonl"
)


def load_examples():
    examples = []

    with DATASET_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:

        for line in file:
            line = line.strip()

            if not line:
                continue

            data = json.loads(line)

            examples.append(
                FinancialExample.model_validate(data)
            )

    return examples


def print_distribution(
    title,
    counter,
):
    print()
    print("=" * 60)
    print(title)
    print("=" * 60)

    for key, value in sorted(
        counter.items()
    ):
        print(
            f"{str(key):35} {value}"
        )


def audit_dataset():
    examples = load_examples()

    print()
    print("=" * 60)
    print("FINEXPERT DATASET AUDIT")
    print("=" * 60)

    print(
        f"Dataset file: {DATASET_FILE}"
    )

    print(
        f"Total examples: {len(examples)}"
    )

    category_counts = Counter(
        example.category.value
        for example in examples
    )

    difficulty_counts = Counter(
        example.difficulty.value
        for example in examples
    )

    scenario_counts = Counter(
        example.example_id.split("_")[1]
        if "_" in example.example_id
        else "unknown"
        for example in examples
    )

    reasoning_counts = Counter()

    for example in examples:
        for reasoning_type in (
            example.reasoning_type
        ):
            reasoning_counts[
                reasoning_type.value
            ] += 1

    print_distribution(
        "CATEGORY DISTRIBUTION",
        category_counts,
    )

    print_distribution(
        "DIFFICULTY DISTRIBUTION",
        difficulty_counts,
    )

    print_distribution(
        "REASONING TYPE DISTRIBUTION",
        reasoning_counts,
    )

    print_distribution(
        "EXAMPLE ID PREFIX DISTRIBUTION",
        scenario_counts,
    )

    print()
    print("=" * 60)
    print("DATASET CONTENT CHECKS")
    print("=" * 60)

    empty_instruction = 0
    empty_input = 0
    empty_output = 0
    missing_company = 0

    for example in examples:

        if not example.instruction.strip():
            empty_instruction += 1

        if not example.input.strip():
            empty_input += 1

        if not example.expected_output.strip():
            empty_output += 1

        if not example.company:
            missing_company += 1

    print(
        f"Empty instructions: {empty_instruction}"
    )

    print(
        f"Empty inputs: {empty_input}"
    )

    print(
        f"Empty expected outputs: {empty_output}"
    )

    print(
        f"Missing company values: {missing_company}"
    )

    unique_ids = {
        example.example_id
        for example in examples
    }

    print(
        f"Unique example IDs: {len(unique_ids)}"
    )

    if len(unique_ids) != len(examples):
        print(
            "WARNING: Duplicate example IDs found."
        )
    else:
        print(
            "Example IDs: PASS"
        )

    print()
    print("=" * 60)
    print("SAMPLE EXAMPLES")
    print("=" * 60)

    for index, example in enumerate(
        examples[:5],
        start=1,
    ):
        print()
        print(
            f"--- Example {index} ---"
        )

        print(
            f"ID: {example.example_id}"
        )

        print(
            f"Category: {example.category.value}"
        )

        print(
            f"Difficulty: {example.difficulty.value}"
        )

        print(
            "Reasoning: "
            + ", ".join(
                item.value
                for item in example.reasoning_type
            )
        )

        print(
            f"Company: {example.company}"
        )

        print(
            f"Instruction: {example.instruction}"
        )

        print(
            f"Input: {example.input}"
        )

        print(
            f"Expected output: "
            f"{example.expected_output}"
        )

    print()
    print("=" * 60)
    print("AUDIT COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    audit_dataset()