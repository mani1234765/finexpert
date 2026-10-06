"""Convert TAT-QA (Zhu et al., ACL 2021; CC BY 4.0) to FinExpert chat records.

Gold answer = TAT-QA's `answer` with its `scale` (thousand / million /
billion / percent). The official test answers are in
`tatqa_dataset_test_gold.json`. Arithmetic derivations are re-evaluated and
count derivations re-counted; examples whose working disagrees with their
own answer are flagged and excluded from training only.

Derivations use accounting notation: "(6,919)" is -6919 and "65%" is 0.65.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .common import build_record, fmt_num, markdown_table, numbers_agree

SCALE_SUFFIX = {"": "", "thousand": " thousand", "million": " million", "billion": " billion", "percent": "%"}
_SAFE_EXPR = re.compile(r"[\d.\s+\-*/()]+")
_ACCOUNTING_NEGATIVE = re.compile(r"\((\s*\d[\d,]*(?:\.\d+)?\s*)\)")
_PERCENT = re.compile(r"(\d[\d,]*(?:\.\d+)?)\s*%")


def evaluate_derivation(derivation: str) -> float | None:
    """Evaluate an arithmetic derivation; None if it is not plain arithmetic."""
    expr = derivation.replace("$", "").replace("[", "(").replace("]", ")")
    expr = _ACCOUNTING_NEGATIVE.sub(lambda m: f"(-{m.group(1).strip()})", expr)
    expr = _PERCENT.sub(lambda m: f"({m.group(1)}/100)", expr)
    expr = expr.replace(",", "").replace("×", "*").replace("÷", "/")
    if not expr.strip() or not _SAFE_EXPR.fullmatch(expr):
        return None
    try:
        return float(eval(expr, {"__builtins__": {}}, {}))  # noqa: S307 - charset-restricted above
    except (ZeroDivisionError, SyntaxError, TypeError):
        return None


def pretty_derivation(derivation: str) -> str:
    text = " ".join(derivation.replace("[", "(").replace("]", ")").split())
    text = re.sub(r"\s*\*\s*", " × ", text)
    text = re.sub(r"(?<=[\d)%])\s*/\s*(?=[\d(])", " ÷ ", text)
    return text


def with_scale(value_text: str, scale: str) -> str:
    return f"{value_text}{SCALE_SUFFIX.get(scale, '')}"


def difficulty_for(question: dict[str, Any]) -> str:
    kind = question["answer_type"]
    if kind == "span":
        return "easy"
    if kind in {"multi-span", "count"}:
        return "medium"
    n_ops = len(re.findall(r"(?<=[\d)%\s])[+\-*/](?=[\s\d(])", question["derivation"]))
    return "easy" if n_ops <= 1 else ("medium" if n_ops == 2 else "hard")


def _source_phrase(answer_from: str) -> str:
    return {"table": "the table", "text": "the text", "table-text": "the table and the text"}.get(answer_from, "the context")


def build_target(question: dict[str, Any]) -> tuple[str, dict[str, Any], dict[str, Any]]:
    """Return (target text, gold, flags) for one question."""
    kind, scale, answer = question["answer_type"], question["scale"], question["answer"]
    source = _source_phrase(question["answer_from"])
    flags: dict[str, Any] = {}

    try:
        numeric_answer = float(str(answer).replace(",", "")) if kind == "arithmetic" else None
    except ValueError:  # e.g. one train "arithmetic" answer is a date
        numeric_answer = None
        flags["non_numeric_arithmetic_answer"] = True

    if kind == "arithmetic" and numeric_answer is None:
        answer_text = str(answer).strip()
        flags["derivation_consistent"] = False
        lines = [f"Calculation using figures from {source}:", pretty_derivation(question["derivation"]),
                 f"Answer: {answer_text}"]
        gold = {"value": answer_text, "scale": scale, "answer_text": answer_text,
                "derivation": question["derivation"]}

    elif kind == "arithmetic":
        gold_value = numeric_answer
        answer_text = with_scale(fmt_num(gold_value, 2), scale)
        computed = evaluate_derivation(question["derivation"])
        flags["derivation_consistent"] = computed is not None and any(
            numbers_agree(c, gold_value, str(answer)) for c in (computed, computed * 100)
        )
        lines = [f"Calculation using figures from {source}:"]
        if computed is not None:
            lines.append(f"{pretty_derivation(question['derivation'])} = {fmt_num(computed)}")
            if scale == "percent" and not numbers_agree(computed, gold_value, str(answer)) \
                    and numbers_agree(computed * 100, gold_value, str(answer)):
                lines.append(f"As a percentage: {fmt_num(computed)} × 100 = {answer_text}")
        else:
            lines.append(pretty_derivation(question["derivation"]))
        lines.append(f"Answer: {answer_text}")
        gold = {"value": gold_value, "scale": scale, "answer_text": answer_text, "derivation": question["derivation"]}

    elif kind == "count":
        items = [item.strip() for item in question["derivation"].split("##") if item.strip()]
        count = int(float(str(answer)))
        flags["derivation_consistent"] = len(items) == count
        answer_text = str(count)
        lines = [f"Items counted from {source}: " + "; ".join(items), f"Answer: {answer_text}"]
        gold = {"value": count, "scale": "", "answer_text": answer_text, "items": items}

    else:  # span / multi-span: stated directly in the context
        spans = [str(a).strip() for a in (answer if isinstance(answer, list) else [answer])]
        answer_text = "; ".join(with_scale(s, scale) for s in spans)
        flags["derivation_consistent"] = True
        subject = "The answers are" if kind == "multi-span" else "The answer is"
        lines = [f"{subject} stated directly in {source}.", f"Answer: {answer_text}"]
        gold = {"value": spans, "scale": scale, "answer_text": answer_text}

    return "\n".join(lines), gold, flags


def build_context(context: dict[str, Any]) -> str:
    paragraphs = sorted(context["paragraphs"], key=lambda p: p.get("order", 0))
    text = "\n\n".join(p["text"].strip() for p in paragraphs if p["text"].strip())
    return "Excerpt from a company annual report:\n\n" + markdown_table(context["table"]["table"]) + (
        "\n\n" + text if text else "")


def load_split(tatqa_dir: Path, split: str) -> list[dict[str, Any]]:
    filename = {"train": "tatqa_dataset_train.json", "validation": "tatqa_dataset_dev.json",
                "test": "tatqa_dataset_test_gold.json"}[split]
    return json.loads((tatqa_dir / "dataset_raw" / filename).read_text(encoding="utf-8"))


def convert_split(tatqa_dir: Path, split: str) -> list[dict[str, Any]]:
    records = []
    for context in load_split(tatqa_dir, split):
        context_text = build_context(context)
        for question in sorted(context["questions"], key=lambda q: q.get("order", 0)):
            target, gold, flags = build_target(question)
            records.append(build_record(
                example_id=f"tatqa_{split}_{question['uid']}",
                source="tatqa",
                source_id=question["uid"],
                split=split,
                difficulty=difficulty_for(question),
                context=context_text,
                question=question["question"],
                target=target,
                gold=gold,
                answer_type=question["answer_type"],
                flags={**flags, "answer_from": question["answer_from"], "table_uid": context["table"]["uid"]},
            ))
    return records
