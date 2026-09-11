from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def normalize_financial_text(text):
    """
    Normalize common financial terminology before
    calculating similarity.
    """

    replacements = {
        "increased": "grew",
        "increases": "grew",
        "increase": "grew",
        "rose": "grew",
        "crore": "cr",
        "crores": "cr",
        "lakhs": "lakh",
        "million": "mn",
        "billion": "bn",
    }

    normalized_text = text.lower()

    for old_value, new_value in replacements.items():
        normalized_text = normalized_text.replace(
            old_value,
            new_value,
        )

    return " ".join(normalized_text.split())


def build_example_text(example):
    """
    Combine the important textual fields of a financial example.

    Returns the original text without normalization.
    """

    return " ".join(
        [
            example.instruction,
            example.input,
            example.expected_output,
        ]
    )


def calculate_similarity(example_a, example_b):
    """
    Calculate cosine similarity between two financial examples.

    Financial text is normalized before calculating similarity.

    Returns a value between 0 and 1.

    1.0 -> identical textual representation
    0.0 -> completely different
    """

    text_a = normalize_financial_text(
        build_example_text(example_a)
    )

    text_b = normalize_financial_text(
        build_example_text(example_b)
    )

    vectorizer = TfidfVectorizer()

    vectors = vectorizer.fit_transform(
        [text_a, text_b]
    )

    similarity = cosine_similarity(
        vectors[0],
        vectors[1],
    )[0][0]

    return float(similarity)


def check_near_duplicate(
    example,
    existing_examples,
    threshold=0.85,
):
    """
    Check whether an example is too similar
    to an existing example.
    """

    for existing_example in existing_examples:

        similarity = calculate_similarity(
            example,
            existing_example,
        )

        if similarity >= threshold:

            return {
                "success": False,
                "reason": "near_duplicate_example",
                "similarity": similarity,
                "matched_example_id": (
                    existing_example.example_id
                ),
            }

    return {
        "success": True,
        "reason": None,
    }