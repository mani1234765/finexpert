import math
import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .schema import FinancialExample


SIMILARITY_THRESHOLD = 0.85

# Two examples must have extremely similar numerical
# content before numerical similarity contributes to
# near-duplicate rejection.
NUMERIC_DUPLICATE_THRESHOLD = 0.99


def normalize_text(text):
    """
    Normalize financial terminology before similarity comparison.
    """

    replacements = {
        "increased": "grew",
        "increases": "grew",
        "increase": "grew",
        "declined": "fell",
        "decreased": "fell",
        "decreases": "fell",
        "decrease": "fell",
        "crore": "cr",
        "crores": "cr",
        "million": "m",
        "billion": "b",
    }

    normalized = text.lower()

    for old, new in replacements.items():
        normalized = normalized.replace(
            old,
            new,
        )

    return normalized


def build_example_text(example):
    """
    Convert a FinancialExample into text used for
    similarity comparison.

    example_id is intentionally excluded.
    """

    return " ".join(
        [
            example.instruction,
            example.input,
            example.expected_output,
        ]
    )


def _as_text(value):
    """
    Convert either a string or FinancialExample
    into comparable text.
    """

    if isinstance(value, FinancialExample):
        return build_example_text(value)

    if isinstance(value, str):
        return value

    raise TypeError(
        "value must be a string or FinancialExample"
    )


def _extract_numbers(text):
    """
    Extract numerical values from financial text.

    Examples:
        100
        100.5
        -25
        30.2
    """

    matches = re.findall(
        r"(?<![A-Za-z])[-+]?\d+(?:\.\d+)?",
        text,
    )

    return [
        float(value)
        for value in matches
    ]


def _number_similarity(value_a, value_b):
    """
    Compare two numerical values.

    Exact values receive 1.0.

    Values with materially different magnitudes receive
    lower similarity.
    """

    if value_a == value_b:
        return 1.0

    if value_a == 0 and value_b == 0:
        return 1.0

    if value_a == 0 or value_b == 0:
        return 0.0

    if (value_a < 0) != (value_b < 0):
        return 0.0

    absolute_a = abs(value_a)
    absolute_b = abs(value_b)

    ratio = max(
        absolute_a / absolute_b,
        absolute_b / absolute_a,
    )

    similarity = math.exp(
        -abs(math.log(ratio))
    )

    return max(
        0.0,
        min(
            1.0,
            similarity,
        ),
    )


def calculate_numeric_similarity(
    text_a,
    text_b,
):
    """
    Calculate similarity between numerical content
    in two pieces of text.
    """

    numbers_a = _extract_numbers(text_a)
    numbers_b = _extract_numbers(text_b)

    if not numbers_a and not numbers_b:
        return 1.0

    if not numbers_a or not numbers_b:
        return 0.0

    count_similarity = (
        min(
            len(numbers_a),
            len(numbers_b),
        )
        /
        max(
            len(numbers_a),
            len(numbers_b),
        )
    )

    pair_count = min(
        len(numbers_a),
        len(numbers_b),
    )

    pair_similarities = [
        _number_similarity(
            numbers_a[index],
            numbers_b[index],
        )
        for index in range(pair_count)
    ]

    positional_similarity = (
        sum(pair_similarities)
        / pair_count
    )

    return (
        positional_similarity
        * count_similarity
    )


def calculate_similarity(
    text_a,
    text_b,
):
    """
    Calculate combined semantic and numerical similarity.

    This function is useful for measuring similarity.

    Duplicate rejection itself is handled separately by
    check_near_duplicate().
    """

    text_a = _as_text(text_a)
    text_b = _as_text(text_b)

    normalized_a = normalize_text(text_a)
    normalized_b = normalize_text(text_b)

    if normalized_a == normalized_b:
        return 1.0

    vectorizer = TfidfVectorizer(
        lowercase=True,
        ngram_range=(1, 2),
    )

    vectors = vectorizer.fit_transform(
        [
            normalized_a,
            normalized_b,
        ]
    )

    textual_similarity = float(
        cosine_similarity(
            vectors[0:1],
            vectors[1:2],
        )[0][0]
    )

    numeric_similarity = (
        calculate_numeric_similarity(
            normalized_a,
            normalized_b,
        )
    )

    combined_similarity = (
        textual_similarity
        * numeric_similarity
    )

    combined_similarity = float(
        round(
            combined_similarity,
            10,
        )
    )

    return max(
        0.0,
        min(
            1.0,
            combined_similarity,
        ),
    )


def build_similarity_matrix(
    examples,
):
    """
    Build a combined similarity matrix.

    Numerical differences reduce similarity, preventing
    template-heavy financial examples from being treated
    as identical.
    """

    if not examples:
        return []

    texts = [
        normalize_text(
            build_example_text(example)
        )
        for example in examples
    ]

    vectorizer = TfidfVectorizer(
        lowercase=True,
        ngram_range=(1, 2),
    )

    vectors = vectorizer.fit_transform(
        texts
    )

    textual_matrix = cosine_similarity(
        vectors
    )

    count = len(examples)

    similarity_matrix = [
        [0.0 for _ in range(count)]
        for _ in range(count)
    ]

    for i in range(count):
        for j in range(count):

            if i == j:
                similarity_matrix[i][j] = 1.0
                continue

            if texts[i] == texts[j]:
                similarity_matrix[i][j] = 1.0
                continue

            numeric_similarity = (
                calculate_numeric_similarity(
                    texts[i],
                    texts[j],
                )
            )

            similarity_matrix[i][j] = max(
                0.0,
                min(
                    1.0,
                    float(textual_matrix[i][j])
                    * numeric_similarity,
                ),
            )

    return similarity_matrix


def _has_nearly_identical_numbers(
    text_a,
    text_b,
    threshold=NUMERIC_DUPLICATE_THRESHOLD,
):
    """
    Determine whether two examples contain essentially
    the same numerical information.

    This is intentionally strict.

    A small difference in a financial value should normally
    be considered a new synthetic example rather than a
    duplicate.

    Examples:

        100 vs 100
        -> duplicate

        100 vs 101
        -> potentially duplicate if all other numbers match
           closely enough

        100 vs 150
        -> different scenario
    """

    numbers_a = _extract_numbers(text_a)
    numbers_b = _extract_numbers(text_b)

    if not numbers_a or not numbers_b:
        return (
            not numbers_a
            and not numbers_b
        )

    if len(numbers_a) != len(numbers_b):
        return False

    similarities = [
        _number_similarity(
            value_a,
            value_b,
        )
        for value_a, value_b in zip(
            numbers_a,
            numbers_b,
        )
    ]

    return all(
        similarity >= threshold
        for similarity in similarities
    )


def check_near_duplicate(
    example,
    existing_examples,
    threshold=SIMILARITY_THRESHOLD,
):
    """
    Check whether an example is a genuine near duplicate.

    Rejection requires BOTH:

        1. High semantic similarity.
        2. Essentially identical numerical content.

    This prevents synthetic examples such as:

        Current assets = ₹100 Cr
        Current liabilities = ₹80 Cr

    and

        Current assets = ₹150 Cr
        Current liabilities = ₹100 Cr

    from being rejected merely because both use the
    same financial-analysis template.
    """

    if not existing_examples:
        return {
            "success": True,
            "reason": None,
            "similarity": 0.0,
            "matched_example_id": None,
        }

    new_text = normalize_text(
        build_example_text(example)
    )

    existing_texts = [
        normalize_text(
            build_example_text(item)
        )
        for item in existing_examples
    ]

    vectorizer = TfidfVectorizer(
        lowercase=True,
        ngram_range=(1, 2),
    )

    vectors = vectorizer.fit_transform(
        [
            new_text,
            *existing_texts,
        ]
    )

    textual_similarities = cosine_similarity(
        vectors[0:1],
        vectors[1:],
    )[0]

    best_similarity = 0.0
    best_index = None

    for index, textual_similarity in enumerate(
        textual_similarities
    ):

        textual_similarity = float(
            textual_similarity
        )

        numeric_similarity = (
            calculate_numeric_similarity(
                new_text,
                existing_texts[index],
            )
        )

        combined_similarity = (
            textual_similarity
            * numeric_similarity
        )

        if combined_similarity > best_similarity:
            best_similarity = combined_similarity

        # Genuine near duplicate:
        #
        # High semantic similarity
        # +
        # Essentially identical financial numbers
        #
        if (
            textual_similarity >= threshold
            and _has_nearly_identical_numbers(
                new_text,
                existing_texts[index],
            )
        ):
            best_index = index
            best_similarity = combined_similarity
            break

    if best_index is not None:

        matched_example = existing_examples[
            best_index
        ]

        return {
            "success": False,
            "reason": "near_duplicate_example",
            "similarity": best_similarity,
            "matched_example_id": (
                matched_example.example_id
            ),
        }

    return {
        "success": True,
        "reason": None,
        "similarity": best_similarity,
        "matched_example_id": None,
    }