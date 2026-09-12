import json

from finexpert.data.generation_pipeline import (
    generate_and_validate_examples,
)


def test_generation_pipeline_creates_valid_examples(
    tmp_path,
):
    output_file = (
        tmp_path / "generated.jsonl"
    )

    result = generate_and_validate_examples(
        count=10,
        output_file=output_file,
    )

    # All requested examples should be generated.
    assert result["generated"] == 10

    # At least one example should pass all validation stages.
    assert result["accepted"] > 0

    # Every generated example must be either
    # accepted or rejected.
    assert (
        result["accepted"]
        + result["rejected"]
        == result["generated"]
    )

    # No generated example should fail because
    # of an incorrect financial calculation.
    assert result["financial_errors"] == 0

    # The output file should contain only
    # accepted examples.
    lines = (
        output_file.read_text(
            encoding="utf-8"
        )
        .strip()
        .splitlines()
    )

    assert len(lines) == result["accepted"]

    for line in lines:
        example = json.loads(line)

        assert "example_id" in example
        assert "instruction" in example
        assert "input" in example
        assert "expected_output" in example
        assert "category" in example
        assert "difficulty" in example
        assert "reasoning_type" in example