import hashlib


def validate_required_content(example):
    """
    Validate that all required text fields contain content.
    """

    required_fields = [
        "example_id",
        "instruction",
        "input",
        "expected_output",
    ]

    for field in required_fields:
        value = getattr(example, field, None)

        if value is None:
            return {
                "success": False,
                "reason": f"{field}_missing",
            }

        if not isinstance(value, str):
            return {
                "success": False,
                "reason": f"{field}_must_be_string",
            }

        if not value.strip():
            return {
                "success": False,
                "reason": f"{field}_empty",
            }

    return {
        "success": True,
        "reason": None,
    }


def normalize_text(text):
    """
    Normalize text before duplicate comparison.

    Converts text to lowercase and removes
    unnecessary whitespace.
    """

    return " ".join(text.lower().split())


def generate_example_fingerprint(example):
    """
    Generate a deterministic fingerprint for an example.

    The fingerprint is based on the instruction,
    input, and expected output.
    """

    content = "|".join(
        [
            normalize_text(example.instruction),
            normalize_text(example.input),
            normalize_text(example.expected_output),
        ]
    )

    return hashlib.sha256(
        content.encode("utf-8")
    ).hexdigest()


def check_duplicate(example, existing_fingerprints):
    """
    Check whether an example already exists.

    Returns a structured result.
    """

    fingerprint = generate_example_fingerprint(example)

    if fingerprint in existing_fingerprints:
        return {
            "success": False,
            "reason": "duplicate_example",
            "fingerprint": fingerprint,
        }

    return {
        "success": True,
        "reason": None,
        "fingerprint": fingerprint,
    }