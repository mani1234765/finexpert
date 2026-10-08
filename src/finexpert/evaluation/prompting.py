"""Prompt construction for training, zero-shot and few-shot evaluation.

Why this module exists
----------------------
Training and evaluation must build prompts in *exactly* the same way: a single
character of difference (an extra newline, a different role tag) is a
distribution shift the model never saw. Keeping prompt construction in one
tested place, instead of in notebook cells, removes that risk.

Baselines
---------
* zero-shot: the base model gets the same system prompt and instructions the
  fine-tuned model was trained with. Measures what the model can do "as is".
* few-shot: the same, preceded by worked examples written as earlier chat
  turns (user question -> assistant answer). This is the standard way to show
  an instruction-tuned model the expected format and reasoning style without
  training it, and it is the baseline fine-tuning has to beat to justify itself.

Few-shot examples come from the TRAINING split only and are chosen
deterministically (the shortest example that fits each slot, ties broken by
id), so every run sees identical prompts and no evaluation question can leak
into a prompt. Examples for one source come from different documents (a
different company for FinQA, a different table for TAT-QA), so the prompt
shows variety rather than two views of the same table.
"""

from __future__ import annotations

import re
from typing import Any, Callable

Record = dict[str, Any]

# One slot = one worked example. Each source gets examples that cover its main
# answer styles, so the model sees both shapes of answer it will be asked for.
FEW_SHOT_SLOTS: dict[str, list[tuple[str, Callable[[Record], bool]]]] = {
    "finqa": [
        ("percent change, 2 steps",
         lambda r: r["answer_type"] == "arithmetic" and r["flags"].get("n_steps") == 2 and r["gold"].get("is_percent")),
        ("single calculation",
         lambda r: r["answer_type"] == "arithmetic" and r["flags"].get("n_steps") == 1 and not r["gold"].get("is_percent")),
    ],
    "tatqa": [
        ("calculation", lambda r: r["answer_type"] == "arithmetic"),
        ("value read from the report", lambda r: r["answer_type"] == "span"),
    ],
    "financial_explanation": [("explanation", lambda r: True)],
    "financial_classification": [("classification", lambda r: True)],
    "financial_report_generation": [("report", lambda r: True)],
}


def source_key(record: Record) -> str:
    """FinQA/TAT-QA records are keyed by source, synthetic records by task category."""
    source = record.get("source_type")
    return source if source in ("finqa", "tatqa") else record["category"]


def _messages(record: Record) -> dict[str, str]:
    return {m["role"]: m["content"].strip() for m in record["messages"]}


def document_key(record: Record) -> str:
    """The document an example comes from: FinQA company, TAT-QA table, else the example itself."""
    if record.get("source_type") == "finqa":
        return "finqa:" + record["source_id"].split("/")[0]
    if record.get("source_type") == "tatqa":
        return "tatqa:" + record["flags"]["table_uid"]
    return record["example_id"]


def _length(record: Record) -> int:
    parts = _messages(record)
    return len(parts["user"]) + len(parts["assistant"])


def select_few_shot(train_records: list[Record], max_chars_per_example: int = 6000) -> dict[str, list[Record]]:
    """Pick worked examples per source key: for each slot, the shortest matching
    training example (ties by example_id) from a document not already used."""
    by_key: dict[str, list[Record]] = {}
    for record in train_records:
        by_key.setdefault(source_key(record), []).append(record)

    selected: dict[str, list[Record]] = {}
    for key, slots in FEW_SHOT_SLOTS.items():
        pool = sorted((r for r in by_key.get(key, []) if _length(r) <= max_chars_per_example),
                      key=lambda r: (_length(r), r["example_id"]))
        chosen: list[Record] = []
        for _name, matches in slots:
            used = {document_key(r) for r in chosen}
            pick = next((r for r in pool if matches(r) and document_key(r) not in used), None)
            if pick is None:
                raise ValueError(f"no training example fits slot {_name!r} for {key!r}")
            chosen.append(pick)
        selected[key] = chosen
    return selected


def build_messages(record: Record, shots: list[Record] | None = None) -> list[dict[str, str]]:
    """Chat messages for one question: system, then worked examples as earlier
    turns, then the question. With no shots this is exactly the training prompt."""
    parts = _messages(record)
    messages = [{"role": "system", "content": parts["system"]}]
    for shot in shots or []:
        if shot["example_id"] == record["example_id"]:
            raise ValueError("a question cannot be its own worked example")
        shot_parts = _messages(shot)
        messages += [{"role": "user", "content": shot_parts["user"]},
                     {"role": "assistant", "content": shot_parts["assistant"]}]
    messages.append({"role": "user", "content": parts["user"]})
    return messages


def to_chatml(messages: list[dict[str, str]], add_generation_prompt: bool = True) -> str:
    """Render messages in Qwen's ChatML, by hand.

    Built manually rather than with tokenizer.apply_chat_template so the text is
    byte-identical to training and never gains an empty <think> block."""
    text = "".join(f"<|im_start|>{m['role']}\n{m['content']}<|im_end|>\n" for m in messages)
    return text + ("<|im_start|>assistant\n" if add_generation_prompt else "")


def training_text(record: Record) -> str:
    """Full training example: the zero-shot prompt plus the target answer."""
    return to_chatml(build_messages(record)) + _messages(record)["assistant"] + "<|im_end|>\n"


_COMPLETED_ANSWER = re.compile(r"^\W*answer\W*:[^\n]*\S[^\n]*\n", re.IGNORECASE | re.MULTILINE)


def answer_line_complete(generated: str) -> bool:
    """True once the text contains a finished 'Answer: ...' line (followed by a newline).

    Used as a stop condition for base models, which often keep writing after
    answering. Scoring reads the last Answer line, so stopping right after the
    first one only removes text the scorer would never use - unless the model
    was about to revise its answer, which is noted in the run report."""
    return bool(_COMPLETED_ANSWER.search(generated))
