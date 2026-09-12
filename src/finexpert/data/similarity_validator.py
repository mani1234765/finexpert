from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .schema import FinancialExample


SIMILARITY_THRESHOLD = 0.85


def normalize_text(text):
    """
    Normalize financial terminology before
    similarity comparison.
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
    Convert a FinancialExample into the text used
    for similarity comparison.

    example_id is intentionally excluded because
    IDs should not affect semantic similarity.
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


def calculate_similarity(
    text_a,
    text_b,
):
    """
    Calculate cosine similarity between two strings
    or FinancialExample objects.
    """

    text_a = _as_text(text_a)
    text_b = _as_text(text_b)

    normalized_a = normalize_text(text_a)
    normalized_b = normalize_text(text_b)

    # Avoid floating-point values such as
    # 1.0000000000000004 for identical text.
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

    similarity = cosine_similarity(
        vectors[0:1],
        vectors[1:2],
    )[0][0]

    similarity = float(
        round(
            similarity,
            10,
        )
    )

    # Protect against tiny floating-point overflow.
    if similarity > 1.0:
        similarity = 1.0

    if similarity < 0.0:
        similarity = 0.0

    return similarity


def build_similarity_matrix(
    examples,
):
    """
    Build a TF-IDF cosine similarity matrix.
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

    return cosine_similarity(
        vectors
    )


def check_near_duplicate(
    example,
    existing_examples,
    threshold=SIMILARITY_THRESHOLD,
):
    """
    Check whether an example is a near duplicate
    of any existing example.
    """

    if not existing_examples:
        return {
            "success": True,
            "reason": None,
            "similarity": 0.0,
            "matched_example_id": None,
        }

    all_examples = [
        *existing_examples,
        example,
    ]

    similarity_matrix = build_similarity_matrix(
        all_examples
    )

    new_index = len(all_examples) - 1

    similarities = similarity_matrix[
        new_index,
        :-1,
    ]

    if len(similarities) == 0:
        return {
            "success": True,
            "reason": None,
            "similarity": 0.0,
            "matched_example_id": None,
        }

    max_index = int(
        similarities.argmax()
    )

    max_similarity = float(
        similarities[max_index]
    )

    matched_example = existing_examples[
        max_index
    ]

    matched_example_id = (
        matched_example.example_id
    )

    if max_similarity >= threshold:
        return {
            "success": False,
            "reason": "near_duplicate_example",
            "similarity": max_similarity,
            "matched_example_id": matched_example_id,
        }

    return {
        "success": True,
        "reason": None,
        "similarity": max_similarity,
        "matched_example_id": None,
    }