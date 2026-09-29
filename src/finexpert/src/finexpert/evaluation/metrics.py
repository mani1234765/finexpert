"""
Pure, model-agnostic scoring functions for finexpert generations.

Nothing here touches a model or a GPU: every function takes plain
strings (a reference answer, a model prediction, a prompt) and
returns a bool/float/set. That means the same code can score
predictions produced in Colab, in a local script, or from a
different model entirely -- you only need a predictions file.
"""

import re
from collections import Counter

LABEL_RE = re.compile(
    r"^\s*Classification:\s*(Healthy|Moderate Risk|High Risk)",
    re.IGNORECASE,
)

FIGURE_RE = re.compile(r"₹\s*(\d+(?:\.\d+)?)\s*Cr", re.IGNORECASE)

# Any standalone number, currency or not -- used for the stricter
# "did the model change a digit" check (catches things like a
# 0.40 ratio being written as 0.040, which FIGURE_RE alone misses
# because it only looks at ₹...Cr amounts).
NUMBER_RE = re.compile(r"\d+(?:\.\d+)?")


def extract_label(text):
    """Return 'Healthy' / 'Moderate Risk' / 'High Risk', or None."""

    match = LABEL_RE.match(text.strip())

    return match.group(1) if match else None


def is_correct_label(reference, prediction):
    ref_label = extract_label(reference)
    pred_label = extract_label(prediction)

    if ref_label is None:
        raise ValueError(
            "reference has no 'Classification: <label>' line -- "
            "is_correct_label should only be called on "
            "financial_classification examples"
        )

    return pred_label is not None and pred_label.lower() == ref_label.lower()


def is_format_ok(prediction):
    """True if the prediction starts with 'Classification: <label>'."""

    return extract_label(prediction) is not None


def extract_currency_figures(text):
    return {float(v) for v in FIGURE_RE.findall(text)}


def figures_are_grounded(prediction, reference, prompt):
    """
    True if every ₹...Cr figure in `prediction` also appears in
    `reference` or `prompt`. Catches invented currency figures.
    """

    allowed = extract_currency_figures(reference) | extract_currency_figures(prompt)
    predicted = extract_currency_figures(prediction)

    return predicted <= allowed


def numeric_mismatch(reference, prediction):
    """
    Return the sorted list of numbers (any number, not just currency)
    that appear in `prediction` more often than in `reference`.

    This is stricter than figures_are_grounded: it also catches a
    ratio or percentage being stated wrong (e.g. reference says
    "0.40" and the model says "0.040"), which the currency-only
    check can't see since neither value has a ₹/Cr around it.

    An empty list means every number the model wrote is accounted
    for in the reference -- not proof the model calculated anything,
    just that it didn't drift from the reference's own figures.
    """

    ref_counts = Counter(NUMBER_RE.findall(reference))
    pred_counts = Counter(NUMBER_RE.findall(prediction))

    extra = pred_counts - ref_counts

    return sorted(extra.elements(), key=float)
