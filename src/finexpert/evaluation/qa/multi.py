"""Scoring for multi-question answers ("Answer 1: ...", "Answer 2: ...").

Each numbered answer is scored exactly like a single-question answer (same official scorers), so per-question
accuracy is directly comparable with single-question results on the same questions. Reports also show accuracy by
position, to measure whether later questions in a bundle suffer.
"""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Any

from ..classification_metrics import wilson_interval
from .report import score_record

_NUMBERED = re.compile(r"^\W*answer\s*(\d+)\W*:\s*(.+?)\s*$", re.IGNORECASE | re.MULTILINE)


def numbered_answers(text: str | None) -> dict[int, str]:
    """{question number: answer text}; the last line for a number wins (models sometimes restate)."""
    answers: dict[int, str] = {}
    for number, answer in _NUMBERED.findall(text or ""):
        answers[int(number)] = answer.strip().strip("*_`").strip()
    return answers


def score_bundle(bundle: dict[str, Any], prediction: str | None, tatqa_dir: str | None) -> list[dict[str, Any]]:
    """One row per sub-question, scored with the single-question scorers."""
    answers = numbered_answers(prediction)
    rows = []
    for position, item in enumerate(bundle["items"], 1):
        sub_prediction = f"Answer: {answers[position]}" if position in answers else None
        row = score_record(item, sub_prediction, tatqa_dir)
        row.update({"bundle_id": bundle["example_id"], "position": position,
                    "bundle_size": len(bundle["items"]), "answered": position in answers})
        rows.append(row)
    return rows


def summarize_multi(rows: list[dict[str, Any]]) -> dict[str, Any]:
    def rate(flags: list[bool]) -> dict[str, Any]:
        n, k = len(flags), sum(flags)
        return {"n": n, "correct": k, "accuracy": k / n if n else None,
                "ci95": list(wilson_interval(k, n)) if n else None}

    by_source: defaultdict[str, list[bool]] = defaultdict(list)
    by_position: defaultdict[int, list[bool]] = defaultdict(list)
    by_size: defaultdict[int, list[bool]] = defaultdict(list)
    for row in rows:
        ok = bool(row["strict"]["correct"])
        by_source[row["source"]].append(ok)
        by_position[row["position"]].append(ok)
        by_size[row["bundle_size"]].append(ok)
    bundles: defaultdict[str, list[bool]] = defaultdict(list)
    for row in rows:
        bundles[row["bundle_id"]].append(row["answered"])
    return {
        "questions": len(rows),
        "bundles": len(bundles),
        "all_questions_answered_rate": sum(all(v) for v in bundles.values()) / len(bundles) if bundles else None,
        "by_source": {k: rate(v) for k, v in sorted(by_source.items())},
        "by_position": {k: rate(v) for k, v in sorted(by_position.items())},
        "by_bundle_size": {k: rate(v) for k, v in sorted(by_size.items())},
    }
