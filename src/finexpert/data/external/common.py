"""Helpers shared by the FinQA and TAT-QA converters.

Every converted record uses the same chat format as data/sft/*.jsonl, so the
training notebook can mix real-report and synthetic data without changes.
Targets always put the working first and the answer last ("Answer: ..."),
following the v1.1 finding that labels chosen before the evidence are less
reliable.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable

# Same system prompt as the synthetic FinExpert data.
SYSTEM_PROMPT = (
    "You are FinExpert, a specialized financial analysis assistant. Use only the financial "
    "information provided in the user input. Show relevant quantitative calculations when "
    "appropriate, distinguish reported facts from interpretation, and avoid inventing financial "
    "information or unsupported causal claims."
)

QA_INSTRUCTION = (
    "Answer the question using only the context above. Show your working first, then give the "
    "final answer on the last line in the form \"Answer: <value>\"."
)

CATEGORY = "financial_qa"

# Qwen tokenizes digits one by one, so numeric-heavy text runs short on
# characters per token. 3 characters per token is deliberately conservative;
# the training notebook re-checks exact token counts.
CHARS_PER_TOKEN = 3.0
MAX_TRAIN_TOKENS = 2048


def fmt_num(value: float, max_decimals: int = 4) -> str:
    """Readable number: integers without decimals, others rounded, no trailing zeros."""
    if value is None or (isinstance(value, float) and (math.isnan(value) or math.isinf(value))):
        raise ValueError(f"cannot format {value!r}")
    if abs(value - round(value)) < 1e-9:
        text = str(int(round(value)))
        return "0" if text == "-0" else text
    text = f"{value:.{max_decimals}f}".rstrip("0").rstrip(".")
    if text in {"0", "-0"}:  # very small non-zero value: 3 significant digits, never 1e-05 style
        decimals = -math.floor(math.log10(abs(value))) + 2
        text = f"{value:.{decimals}f}".rstrip("0").rstrip(".")
    return text


def markdown_table(rows: list[list[Any]]) -> str:
    """Render rows as a markdown table; the first row is the header."""
    if not rows:
        return ""
    width = max(len(row) for row in rows)

    def cell(value: Any) -> str:
        return " ".join(str(value).split()).replace("|", "\\|")

    lines = []
    for index, row in enumerate(rows):
        padded = [cell(v) for v in row] + [""] * (width - len(row))
        lines.append("| " + " | ".join(padded) + " |")
        if index == 0:
            lines.append("|" + "---|" * width)
    return "\n".join(lines)


def estimate_tokens(*texts: str) -> int:
    return math.ceil(sum(len(t) for t in texts) / CHARS_PER_TOKEN)


def build_user_message(context: str, question: str) -> str:
    return f"{context.strip()}\n\nQuestion: {question.strip()}\n\n{QA_INSTRUCTION}"


def build_record(
    *,
    example_id: str,
    source: str,
    source_id: str,
    split: str,
    difficulty: str,
    context: str,
    question: str,
    target: str,
    gold: dict[str, Any],
    answer_type: str,
    flags: dict[str, Any],
) -> dict[str, Any]:
    user = build_user_message(context, question)
    return {
        "example_id": example_id,
        "category": CATEGORY,
        "difficulty": difficulty,
        "source_type": source,
        "source_id": source_id,
        "source_split": split,
        "answer_type": answer_type,
        "gold": gold,
        "flags": {**flags, "est_tokens": estimate_tokens(SYSTEM_PROMPT, user, target)},
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user},
            {"role": "assistant", "content": target},
        ],
    }


def numbers_agree(value: float, reference: float, reference_text: str | None = None) -> bool:
    """True if value equals reference allowing for the reference's own rounding.

    A written answer of "14%" agrees with 14.46 because "14%" is rounded to
    0 decimals; "14.5%" would not agree with 14.46... unless rounded to 1 dp.
    """
    decimals = 0
    if reference_text is not None:
        cleaned = reference_text.replace(",", "").replace("$", "").replace("%", "").strip()
        if "." in cleaned:
            decimals = len(cleaned.split(".", 1)[1].rstrip())
    else:
        decimals = 6
    tolerance = 0.5 * 10 ** (-decimals) + 1e-9
    return abs(round(value, decimals) - reference) <= tolerance or abs(value - reference) <= tolerance


def write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            count += 1
    return count


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
