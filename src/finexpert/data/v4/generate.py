"""Teacher generation for v4 targets: generate, check, retry, judge, sample for human calibration.

GPU-free logic (the notebook supplies `generate(prompts, temperature) -> outputs`), so all of it is unit-tested.

Flow per item: greedy attempt -> automatic checks -> up to two retries with sampling for failures -> LLM judge on
accepted items -> keep items scoring >= 4 on every criterion. A blind sample of 30 judged items is written for
human calibration (docs/v4_judge.md).
"""

from __future__ import annotations

import csv
import json
import random
import re
from typing import Any, Callable, Sequence

from finexpert.data.v4.concepts import explanation_checks
from finexpert.data.v4.teacher import assessment_target
from finexpert.evaluation.advice_rules import check_advice

Generate = Callable[[list[str], float], list[str]]

CRITERIA = {"explain": ("correctness", "clarity", "completeness"),
            "assess": ("correctness", "clarity", "completeness", "grounding")}
RUBRIC = (
    "correctness: 5 = every statement and number is right, 3 = one minor slip, 1 = a wrong definition or calculation; "
    "clarity: 5 = a learner understands it on first read, 3 = understandable with effort, 1 = confusing; "
    "completeness: 5 = covers everything the question and the given figures allow, 3 = one part thin, "
    "1 = parts missing (judge the answer, not how much information the input contained); "
    "grounding: 5 = every point follows from the given figures, 3 = one point generic, 1 = unsupported claims"
)
JUDGE_PROMPT = (
    "You are grading an answer written for someone learning financial analysis.\n\nQuestion:\n{question}\n\n"
    "Answer:\n{answer}\n\nScore each criterion from 1 to 5 using this rubric: {rubric}\n"
    "Criteria to score: {criteria}.\n"
    'Reply in JSON only, with a reason of at most 15 words, for example '
    '{{"correctness": 4, "clarity": 5, "reason": "one short sentence"}}'
)
_BULLET = re.compile(r"^- \S", re.MULTILINE)


def suggestions_ok(text: str) -> bool:
    lines = [line for line in text.strip().splitlines() if line.strip()]
    return 2 <= len(lines) <= 4 and all(_BULLET.match(line) for line in lines) and len(text.split()) <= 80


def clean_output(text: str) -> str:
    """Strip trailing whitespace on every line (markdown line breaks) and around the whole text."""
    return "\n".join(line.rstrip() for line in text.strip().splitlines())


def check_item(kind: str, item: dict[str, Any], output: str) -> dict[str, Any]:
    """Automatic checks; returns {'passed', 'target', 'details'}."""
    output = clean_output(output)
    if kind == "explain":
        details = explanation_checks(output, item["has_formula"])
        return {"passed": details["passed"], "target": output, "details": details}
    target = assessment_target(item["facts"], output)
    details = check_advice(target, item["user"])
    passed = details["passed"] and suggestions_ok(output)
    return {"passed": passed, "target": target, "details": {**details, "suggestions_format": suggestions_ok(output)}}


def generate_with_retries(kind: str, items: Sequence[dict[str, Any]], generate: Generate,
                          temperatures: Sequence[float] = (0.0, 0.7, 0.7)) -> list[dict[str, Any]]:
    """Greedy first; failures are retried with sampling. One result per item, in input order."""
    results: dict[str, dict[str, Any]] = {}
    pending = list(items)
    for attempt, temperature in enumerate(temperatures, 1):
        if not pending:
            break
        outputs = generate([item["teacher_prompt"] for item in pending], temperature)
        still_failing = []
        for item, output in zip(pending, outputs):
            checked = check_item(kind, item, output)
            results[item["id"]] = {"id": item["id"], "attempts": attempt, "raw": output, **checked}
            if not checked["passed"]:
                still_failing.append(item)
        pending = still_failing
    return [results[item["id"]] for item in items]


def judge_prompt(kind: str, question: str, answer: str) -> str:
    return JUDGE_PROMPT.format(question=question, answer=answer, rubric=RUBRIC, criteria=", ".join(CRITERIA[kind]))


def parse_judge(text: str, kind: str) -> dict[str, Any] | None:
    """The first JSON object in the reply, if it scores every criterion with an integer 1-5."""
    match = re.search(r"\{[^{}]*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        scores = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    if not all(isinstance(scores.get(c), int) and 1 <= scores[c] <= 5 for c in CRITERIA[kind]):
        return None
    return scores


def judge_accepts(scores: dict[str, Any] | None, kind: str, threshold: int = 4) -> bool:
    return scores is not None and all(scores[c] >= threshold for c in CRITERIA[kind])


def write_calibration_sample(rows: list[dict[str, Any]], path_sheet: str, path_key: str, n: int = 30,
                             seed: int = 20261018) -> list[str]:
    """Blind sheet for human scoring (no judge scores) plus a separate key file with the judge's scores."""
    judged = sorted((r for r in rows if r.get("judge") is not None), key=lambda r: r["id"])
    sample = random.Random(seed).sample(judged, min(n, len(judged)))
    with open(path_sheet, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["id", "kind", "question", "answer", "correctness", "clarity", "completeness", "grounding"])
        for row in sample:
            writer.writerow([row["id"], row["kind"], row["question"], row["target"], "", "", "",
                             "" if row["kind"] == "assess" else "n/a"])
    with open(path_key, "w", encoding="utf-8") as handle:
        json.dump({row["id"]: row["judge"] for row in sample}, handle, indent=2)
    return [row["id"] for row in sample]
