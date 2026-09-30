"""Backwards-compatible low-level helpers.

The evaluation pipeline itself now uses the evaluator/Finding contract.
These small helpers remain so existing tests or scripts that imported the
previous API do not break while callers migrate to the structured evaluators.
"""

import re
from collections import Counter

LABEL_RE = re.compile(
    r"^\s*Classification\s*:\s*(Healthy|Moderate\s+Risk|High\s+Risk)",
    re.IGNORECASE,
)
CURRENCY_RE = re.compile(
    r"₹\s*(\d+(?:\.\d+)?)\s*(?:Cr|crore|crores|Lakh|Lakhs|Million|Billion)",
    re.IGNORECASE,
)
NUMBER_RE = re.compile(r"\d+(?:\.\d+)?")


def extract_label(text: str) -> str | None:
    match = LABEL_RE.match(text.strip())
    if not match:
        return None
    value = re.sub(r"\s+", " ", match.group(1).strip()).lower()
    return {
        "healthy": "Healthy",
        "moderate risk": "Moderate Risk",
        "high risk": "High Risk",
    }[value]


def is_correct_label(reference: str, prediction: str) -> bool:
    ref_label = extract_label(reference)
    pred_label = extract_label(prediction)
    if ref_label is None:
        raise ValueError("reference has no valid Classification line")
    return pred_label is not None and pred_label.lower() == ref_label.lower()


def is_format_ok(prediction: str) -> bool:
    return extract_label(prediction) is not None


def _currency_figures(text: str) -> Counter[float]:
    return Counter(float(value) for value in CURRENCY_RE.findall(text))


def figures_are_grounded(prediction: str, reference: str, prompt: str) -> bool:
    allowed = _currency_figures(reference) | _currency_figures(prompt)
    return _currency_figures(prediction) <= allowed


def numeric_mismatch(reference: str, prediction: str) -> list[str]:
    ref_counts = Counter(NUMBER_RE.findall(reference))
    pred_counts = Counter(NUMBER_RE.findall(prediction))
    extra = pred_counts - ref_counts
    return sorted(extra.elements(), key=float)
