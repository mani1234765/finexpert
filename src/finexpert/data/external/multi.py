"""Multi-question examples: several questions about one document, answered in order.

Built from the single-question FinQA / TAT-QA records, so every sub-answer keeps its verified gold answer and can
be scored with the official scorers. Questions are only bundled when their context text is byte-identical (same
report page or table), each source question is used in at most one bundle per split, and questions with identical
working and answer about the same document (FinQA rewordings) are kept once.

Prompt:   <context>  Questions: 1. ... 2. ...  <instruction>
Target:   Q1. <question> / <working> / Answer 1: <value>   (blank line)   Q2. ...
"""

from __future__ import annotations

import random
import re
from collections import defaultdict
from typing import Any

from .common import SYSTEM_PROMPT, estimate_tokens

QUESTION_SEPARATOR = "\n\nQuestion: "
MULTI_INSTRUCTION = (
    "Answer each question in order, using only the context above. For each question, show your working first, then "
    "give its final answer on its own line in the form \"Answer N: <value>\", where N is the question number."
)
CATEGORY = "financial_qa_multi"
BUNDLE_SIZES = (2, 3, 4)
BUNDLE_WEIGHTS = (0.4, 0.35, 0.25)
_FINAL_ANSWER = re.compile(r"^Answer:\s*(.+)$", re.MULTILINE)


def split_user(record: dict[str, Any]) -> tuple[str, str]:
    """(context, question) of a single-question record."""
    user = record["messages"][1]["content"]
    context, rest = user.split(QUESTION_SEPARATOR, 1)
    return context, rest.split("\n\n", 1)[0]


def working(record: dict[str, Any]) -> str:
    """The single-question target without its final 'Answer:' line."""
    target = record["messages"][2]["content"]
    matches = list(_FINAL_ANSWER.finditer(target))
    if not matches:
        raise ValueError(f"{record['example_id']}: target has no 'Answer:' line")
    return target[: matches[-1].start()].rstrip()


def build_bundle(records: list[dict[str, Any]], bundle_id: str) -> dict[str, Any]:
    contexts = {split_user(r)[0] for r in records}
    if len(contexts) != 1:
        raise ValueError(f"{bundle_id}: questions do not share an identical context")
    context = contexts.pop()
    questions = [split_user(r)[1] for r in records]
    user = (f"{context}\n\nQuestions:\n" + "\n".join(f"{i}. {q}" for i, q in enumerate(questions, 1))
            + f"\n\n{MULTI_INSTRUCTION}")
    target = "\n\n".join(f"Q{i}. {q}\n{working(r)}\nAnswer {i}: {r['gold']['answer_text']}"
                         for i, (q, r) in enumerate(zip(questions, records), 1))
    items = [{key: r[key] for key in ("example_id", "source_type", "source_id", "source_split", "answer_type",
                                      "difficulty", "gold", "flags")} for r in records]
    return {
        "example_id": bundle_id,
        "category": CATEGORY,
        "difficulty": f"{len(records)}_questions",
        "source_type": records[0]["source_type"],
        "source_split": records[0]["source_split"],
        "answer_type": "multi",
        "items": items,
        "flags": {"n_questions": len(records), "est_tokens": estimate_tokens(SYSTEM_PROMPT, user, target)},
        "messages": [{"role": "system", "content": SYSTEM_PROMPT},
                     {"role": "user", "content": user},
                     {"role": "assistant", "content": target}],
    }


def build_bundles(records: list[dict[str, Any]], seed: int, max_est_tokens: int | None = None) -> list[dict[str, Any]]:
    """Deterministically split each document's questions into bundles of 2-4 (leftover singles are dropped)."""
    rng = random.Random(seed)
    by_context: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    seen: set[tuple[str, str, str]] = set()
    for record in sorted(records, key=lambda r: r["example_id"]):
        context = split_user(record)[0]
        # FinQA sometimes asks the same thing twice about a page; identical working + answer = one question
        key = (context, working(record), record["gold"]["answer_text"])
        if key in seen:
            continue
        seen.add(key)
        by_context[context].append(record)

    bundles: list[dict[str, Any]] = []
    for context in sorted(by_context, key=lambda c: by_context[c][0]["example_id"]):
        group = by_context[context][:]
        rng.shuffle(group)
        while len(group) >= 2:
            size = rng.choices(BUNDLE_SIZES, BUNDLE_WEIGHTS)[0]
            size = min(size, len(group))
            if len(group) - size == 1:      # never strand a single question if a bigger bundle can take it
                size = min(size + 1, len(group), max(BUNDLE_SIZES))
            chunk, group = group[:size], group[size:]
            source = chunk[0]["source_type"]
            bundle = build_bundle(chunk, f"multi_{source}_{chunk[0]['source_split']}_{len(bundles):05d}")
            if max_est_tokens is None or bundle["flags"]["est_tokens"] <= max_est_tokens:
                bundles.append(bundle)
    return bundles
