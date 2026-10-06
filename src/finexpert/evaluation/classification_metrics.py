"""Classification metrics for the financial_classification task.

Pure Python on purpose: the test split has only ~10 classification examples,
so these numbers must be exact and easy to audit by hand.  A missing or
unparseable label is kept as its own prediction ("<missing>") so it counts
as an error everywhere instead of silently disappearing.
"""

from __future__ import annotations

import math
from typing import Any

LABELS = ("Healthy", "Moderate Risk", "High Risk")
MISSING = "<missing>"


def wilson_interval(successes: int, n: int, z: float = 1.96) -> tuple[float, float] | None:
    """95% Wilson score interval; well-behaved for small n and p near 0 or 1."""
    if n == 0:
        return None
    p = successes / n
    denominator = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denominator
    half = z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denominator
    return max(0.0, centre - half), min(1.0, centre + half)


def _safe_div(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def classification_metrics(pairs: list[tuple[str, str | None]]) -> dict[str, Any] | None:
    """Compute metrics from (expected, predicted) label pairs."""
    if not pairs:
        return None

    pairs = [(expected, predicted or MISSING) for expected, predicted in pairs]
    predicted_columns = list(LABELS) + (
        [MISSING] if any(predicted == MISSING for _, predicted in pairs) else []
    )

    matrix = {
        expected: {predicted: 0 for predicted in predicted_columns}
        for expected in LABELS
    }
    for expected, predicted in pairs:
        matrix[expected][predicted] += 1

    n = len(pairs)
    correct = sum(expected == predicted for expected, predicted in pairs)

    per_label: dict[str, dict[str, float]] = {}
    for label in LABELS:
        true_positive = matrix[label][label]
        predicted_total = sum(matrix[expected][label] for expected in LABELS)
        support = sum(matrix[label].values())
        precision = _safe_div(true_positive, predicted_total)
        recall = _safe_div(true_positive, support)
        f1 = _safe_div(2 * precision * recall, precision + recall)
        per_label[label] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "support": support,
            "predicted": predicted_total,
        }

    def average(metric: str, weighted: bool) -> float:
        if weighted:
            return _safe_div(
                sum(per_label[label][metric] * per_label[label]["support"] for label in LABELS),
                n,
            )
        return sum(per_label[label][metric] for label in LABELS) / len(LABELS)

    interval = wilson_interval(correct, n)

    return {
        "n": n,
        "correct": correct,
        "accuracy": correct / n,
        "accuracy_ci95": list(interval) if interval else None,
        "macro": {m: average(m, weighted=False) for m in ("precision", "recall", "f1")},
        "weighted": {m: average(m, weighted=True) for m in ("precision", "recall", "f1")},
        "per_label": per_label,
        "confusion_matrix": {
            "rows_expected": list(LABELS),
            "columns_predicted": predicted_columns,
            "counts": [[matrix[expected][predicted] for predicted in predicted_columns] for expected in LABELS],
        },
        "missing_predictions": sum(predicted == MISSING for _, predicted in pairs),
    }
