"""Reasoning-rich training targets by self-distillation (rejection sampling).

Idea (STaR / rejection-sampling fine-tuning): let the base model answer the
*training* questions with its own step-by-step reasoning, keep only the answers
our scorer verifies as correct, and train on those. The model learns reasoning
in its own natural style, and only reasoning that reached the right answer.

Rules that keep this honest:
* only training-split questions are ever generated on; evaluation questions never
  are (the notebook checks);
* correctness is decided by the same scorers used for evaluation (lenient
  extraction, so a missing "Answer:" line alone does not reject good reasoning);
* the final line is rewritten to the gold answer in canonical form
  ("Answer: 12.6 million"), so the answer conventions stay consistent with the
  rest of the training data; the reasoning itself is the model's own;
* rejected questions keep their template target, so v2-A and v2-B train on the
  exact same questions and differ only in the targets of accepted examples.
"""

from __future__ import annotations

import re
from typing import Any, Callable

Record = dict[str, Any]

_ANSWER_LINE = re.compile(r"^\W*(?:final\s+)?answer\W*:.*$", re.IGNORECASE | re.MULTILINE)
MAX_REASONING_CHARS = 4000
MIN_REASONING_CHARS = 20


def split_reasoning(prediction: str) -> str:
    """The model's working: everything before its last 'Answer:' line (or all of it if none)."""
    matches = list(_ANSWER_LINE.finditer(prediction))
    reasoning = prediction[: matches[-1].start()] if matches else prediction
    return reasoning.strip()


def rejection_reason(prediction: dict[str, Any], correct: bool) -> str | None:
    """Why a generated answer cannot be used as a target (None = usable)."""
    text = prediction.get("prediction") or ""
    reasoning = split_reasoning(text)
    if prediction.get("hit_token_limit"):
        return "hit_token_limit"
    if not correct:
        return "wrong_answer"
    if "<think>" in text or "<|im_" in text:
        return "template_tokens"
    if len(reasoning) < MIN_REASONING_CHARS or not re.search(r"\d", reasoning):
        return "no_reasoning"
    if len(reasoning) > MAX_REASONING_CHARS:
        return "too_long"
    if _ANSWER_LINE.search(reasoning):
        return "multiple_answer_lines"
    return None


def distilled_target(reasoning: str, gold_answer_text: str) -> str:
    return f"{reasoning.strip()}\n\nAnswer: {gold_answer_text}"


def build_distilled_targets(records: list[Record], predictions: dict[str, dict[str, Any]],
                            is_correct: Callable[[Record, str], bool]) -> list[dict[str, Any]]:
    """One row per record: accepted (with its new target) or rejected (with the reason)."""
    rows = []
    for record in records:
        prediction = predictions[record["example_id"]]
        correct = is_correct(record, prediction.get("prediction") or "")
        reason = rejection_reason(prediction, correct)
        row = {
            "example_id": record["example_id"],
            "source": record.get("source_type"),
            "answer_type": record.get("answer_type"),
            "accepted": reason is None,
            "rejection_reason": reason,
            "base_prediction": prediction.get("prediction"),
            "n_new_tokens": prediction.get("n_new_tokens"),
        }
        if reason is None:
            row["target"] = distilled_target(split_reasoning(prediction["prediction"]),
                                             record["gold"]["answer_text"])
        rows.append(row)
    return rows


def apply_targets(records: list[Record], rows: list[dict[str, Any]]) -> list[Record]:
    """Copies of `records` with accepted distilled targets swapped in for the assistant turn."""
    targets = {row["example_id"]: row["target"] for row in rows if row["accepted"]}
    updated = []
    for record in records:
        if record["example_id"] in targets:
            messages = [dict(m) for m in record["messages"]]
            for message in messages:
                if message["role"] == "assistant":
                    message["content"] = targets[record["example_id"]]
            record = {**record, "messages": messages, "target_style": "distilled"}
        updated.append(record)
    return updated
