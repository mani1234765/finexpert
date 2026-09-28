import json
from collections import Counter
from pathlib import Path


INPUT_DIR = Path("data/splits")
OUTPUT_DIR = Path("data/sft")

SPLITS = {
    "train": {
        "input": INPUT_DIR / "train.jsonl",
        "output": OUTPUT_DIR / "train.jsonl",
        "expected_count": 240,
    },
    "validation": {
        "input": INPUT_DIR / "validation.jsonl",
        "output": OUTPUT_DIR / "validation.jsonl",
        "expected_count": 30,
    },
    "test": {
        "input": INPUT_DIR / "test.jsonl",
        "output": OUTPUT_DIR / "test.jsonl",
        "expected_count": 30,
    },
}


SYSTEM_PROMPT = (
    "You are FinExpert, a specialized financial analysis assistant. "
    "Use only the financial information provided in the user input. "
    "Show relevant quantitative calculations when appropriate, "
    "distinguish reported facts from interpretation, and avoid "
    "inventing financial information or unsupported causal claims."
)


REQUIRED_ROLES = (
    "system",
    "user",
    "assistant",
)


def load_jsonl(path):
    if not path.exists():
        raise FileNotFoundError(
            f"Input file not found: {path}"
        )

    records = []

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
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON at {path}, "
                    f"line {line_number}: {exc}"
                ) from exc

            records.append(record)

    if not records:
        raise ValueError(
            f"No records found in {path}"
        )

    return records


def convert_example(example):
    required_fields = (
        "example_id",
        "instruction",
        "input",
        "expected_output",
        "category",
        "difficulty",
    )

    missing = [
        field
        for field in required_fields
        if field not in example
    ]

    if missing:
        raise ValueError(
            f"Example {example.get('example_id', '<unknown>')} "
            f"is missing fields: {missing}"
        )

    instruction = str(
        example["instruction"]
    ).strip()

    input_text = str(
        example["input"]
    ).strip()

    expected_output = str(
        example["expected_output"]
    ).strip()

    if not instruction:
        raise ValueError(
            f"{example['example_id']} has an empty instruction."
        )

    if not input_text:
        raise ValueError(
            f"{example['example_id']} has an empty input."
        )

    if not expected_output:
        raise ValueError(
            f"{example['example_id']} has an empty expected output."
        )

    user_content = (
        f"{instruction}\n\n"
        f"Financial data:\n"
        f"{input_text}"
    )

    return {
        "messages": [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": user_content,
            },
            {
                "role": "assistant",
                "content": expected_output,
            },
        ],
        "example_id": example["example_id"],
        "category": example["category"],
        "difficulty": example["difficulty"],
        "reasoning_type": example.get(
            "reasoning_type",
            [],
        ),
        "source_type": example.get(
            "source_type"
        ),
        "company": example.get(
            "company"
        ),
    }


def validate_converted_record(record):
    if "messages" not in record:
        raise ValueError(
            "Converted record is missing 'messages'."
        )

    messages = record["messages"]

    if len(messages) != 3:
        raise ValueError(
            f"{record.get('example_id', '<unknown>')} "
            "must contain exactly 3 messages."
        )

    roles = tuple(
        message.get("role")
        for message in messages
    )

    if roles != REQUIRED_ROLES:
        raise ValueError(
            f"{record.get('example_id', '<unknown>')} "
            f"has invalid roles: {roles}"
        )

    for index, message in enumerate(
        messages
    ):
        content = message.get(
            "content"
        )

        if not isinstance(
            content,
            str,
        ):
            raise ValueError(
                f"{record.get('example_id', '<unknown>')} "
                f"message {index} has non-string content."
            )

        if not content.strip():
            raise ValueError(
                f"{record.get('example_id', '<unknown>')} "
                f"message {index} is empty."
            )


def validate_split_conversion(
    original,
    converted,
):
    if len(original) != len(converted):
        raise ValueError(
            "Original and converted record counts differ."
        )

    original_ids = [
        item["example_id"]
        for item in original
    ]

    converted_ids = [
        item["example_id"]
        for item in converted
    ]

    if original_ids != converted_ids:
        raise ValueError(
            "Example ID ordering changed during conversion."
        )

    for original_record, converted_record in zip(
        original,
        converted,
    ):
        validate_converted_record(
            converted_record
        )

        if (
            original_record["expected_output"].strip()
            != converted_record["messages"][2]["content"].strip()
        ):
            raise ValueError(
                f"Assistant target changed for "
                f"{original_record['example_id']}."
            )

        if (
            original_record["category"]
            != converted_record["category"]
        ):
            raise ValueError(
                f"Category changed for "
                f"{original_record['example_id']}."
            )

        if (
            original_record["difficulty"]
            != converted_record["difficulty"]
        ):
            raise ValueError(
                f"Difficulty changed for "
                f"{original_record['example_id']}."
            )


def write_jsonl(
    path,
    records,
):
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "w",
        encoding="utf-8",
    ) as file:
        for record in records:
            file.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                )
                + "\n"
            )


def print_distribution(
    name,
    records,
):
    category_counts = Counter(
        record["category"]
        for record in records
    )

    difficulty_counts = Counter(
        record["difficulty"]
        for record in records
    )

    print(
        f"\n{name}"
    )
    print(
        "-" * len(name)
    )
    print(
        f"Total: {len(records)}"
    )

    print(
        "\nCategories:"
    )

    for category, count in sorted(
        category_counts.items()
    ):
        print(
            f"  {category:<35}{count}"
        )

    print(
        "\nDifficulty:"
    )

    for difficulty, count in sorted(
        difficulty_counts.items()
    ):
        print(
            f"  {difficulty:<15}{count}"
        )


def main():
    print(
        "\n"
        "============================================================"
    )
    print(
        "\n                 FINEXPERT SFT PREPARATION"
    )
    print(
        "\n============================================================"
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    all_ids = set()

    for split_name, config in SPLITS.items():
        print(
            f"\nPreparing {split_name}..."
        )

        original = load_jsonl(
            config["input"]
        )

        if len(original) != config["expected_count"]:
            raise RuntimeError(
                f"{split_name} expected "
                f"{config['expected_count']} records, "
                f"found {len(original)}."
            )

        converted = [
            convert_example(example)
            for example in original
        ]

        validate_split_conversion(
            original=original,
            converted=converted,
        )

        for record in converted:
            example_id = record["example_id"]

            if example_id in all_ids:
                raise RuntimeError(
                    f"Duplicate example ID across "
                    f"SFT splits: {example_id}"
                )

            all_ids.add(
                example_id
            )

        write_jsonl(
            config["output"],
            converted,
        )

        print(
            f"  Input:  {config['input']}"
        )
        print(
            f"  Output: {config['output']}"
        )
        print(
            f"  Records: {len(converted)}"
        )

        print_distribution(
            f"{split_name.upper()} SFT DISTRIBUTION",
            converted,
        )

    expected_total = sum(
        config["expected_count"]
        for config in SPLITS.values()
    )

    if len(all_ids) != expected_total:
        raise RuntimeError(
            "Cross-split example ID validation failed."
        )

    print(
        "\n============================================================"
    )
    print(
        "\n                 SFT PREPARATION COMPLETE"
    )
    print(
        "\n============================================================"
    )

    print(
        "\nCreated:"
    )

    for config in SPLITS.values():
        print(
            f"  {config['output']}"
        )

    print(
        "\nTotal examples: "
        f"{len(all_ids)}"
    )

    print(
        "\nFormat:"
    )

    print(
        "  system -> user -> assistant"
    )

    print(
        "\nValidation: PASS"
    )

    print(
        "\n============================================================"
    )


if __name__ == "__main__":
    main()
