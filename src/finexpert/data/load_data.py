import json

from pydantic import ValidationError

from .schema import FinancialExample
from .example_validator import validate_financial_example
from .quality_validator import (
    validate_required_content,
    check_duplicate,
)


INPUT_FILE = "data/raw/finexpert.jsonl"
VALIDATED_FILE = "data/processed/validated.jsonl"
REJECTED_FILE = "data/rejected/rejected.jsonl"


def load_and_validate_data():
    total = 0
    schema_valid = 0
    quality_valid = 0
    financial_valid = 0
    duplicates = 0
    rejected = 0

    existing_fingerprints = set()

    with (
        open(INPUT_FILE, "r") as input_file,
        open(VALIDATED_FILE, "w") as validated_file,
        open(REJECTED_FILE, "w") as rejected_file,
    ):
        for line in input_file:

            if not line.strip():
                continue

            total += 1

            example = json.loads(line)

            # -----------------------------------
            # 1. Schema validation
            # -----------------------------------

            try:
                validated = FinancialExample(**example)
                schema_valid += 1

            except ValidationError as error:

                rejected += 1

                rejected_example = {
                    "example_id": example.get("example_id"),
                    "example": example,
                    "rejection_stage": "schema_validation",
                    "rejection_reason": str(error),
                }

                rejected_file.write(
                    json.dumps(rejected_example) + "\n"
                )

                continue

            # -----------------------------------
            # 2. Required content validation
            # -----------------------------------

            quality_result = validate_required_content(
                validated
            )

            if not quality_result["success"]:

                rejected += 1

                rejected_example = {
                    "example_id": validated.example_id,
                    "example": example,
                    "rejection_stage": "quality_validation",
                    "rejection_reason": quality_result["reason"],
                }

                rejected_file.write(
                    json.dumps(rejected_example) + "\n"
                )

                continue

            quality_valid += 1

            # -----------------------------------
            # 3. Financial validation
            # -----------------------------------

            financial_result = validate_financial_example(
                example_id=validated.example_id,
                input_text=validated.input,
                expected_output=validated.expected_output,
            )

            if not financial_result["success"]:

                rejected += 1

                rejected_example = {
                    "example_id": validated.example_id,
                    "example": example,
                    "rejection_stage": "financial_validation",
                    "rejection_reason": financial_result["reason"],
                    "details": financial_result,
                }

                rejected_file.write(
                    json.dumps(rejected_example) + "\n"
                )

                continue

            financial_valid += 1

            # -----------------------------------
            # 4. Duplicate detection
            # -----------------------------------

            duplicate_result = check_duplicate(
                validated,
                existing_fingerprints,
            )

            if not duplicate_result["success"]:

                duplicates += 1
                rejected += 1

                rejected_example = {
                    "example_id": validated.example_id,
                    "example": example,
                    "rejection_stage": "duplicate_detection",
                    "rejection_reason": duplicate_result["reason"],
                    "fingerprint": duplicate_result["fingerprint"],
                }

                rejected_file.write(
                    json.dumps(rejected_example) + "\n"
                )

                continue

            # -----------------------------------
            # 5. Accept example
            # -----------------------------------

            existing_fingerprints.add(
                duplicate_result["fingerprint"]
            )

            validated_file.write(
                json.dumps(
                    validated.model_dump(mode="json")
                ) + "\n"
            )

    # -----------------------------------
    # Validation summary
    # -----------------------------------

    print("\n========== DATA VALIDATION SUMMARY ==========")

    print(f"Total examples:       {total}")
    print(f"Schema valid:         {schema_valid}")
    print(f"Quality valid:        {quality_valid}")
    print(f"Financial valid:      {financial_valid}")
    print(f"Duplicates:           {duplicates}")
    print(f"Rejected:             {rejected}")

    print("=============================================")


if __name__ == "__main__":
    load_and_validate_data()