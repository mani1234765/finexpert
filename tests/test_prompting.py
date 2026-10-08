"""Tests for prompt construction (training format, zero-shot, few-shot)."""

import json
from pathlib import Path

import pytest

from finexpert.evaluation.prompting import (
    FEW_SHOT_SLOTS, answer_line_complete, document_key, build_messages, select_few_shot, source_key, to_chatml, training_text,
)

ROOT = Path(__file__).resolve().parents[1]
EXTERNAL = ROOT / "data" / "external"


def _read(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _pilot_prompt(r):
    """The exact prompt formula used by the v2-pilot notebook (frozen here on purpose)."""
    d = {m["role"]: m["content"].strip() for m in r["messages"]}
    return ("<|im_start|>system\n" + d["system"] + "<|im_end|>\n<|im_start|>user\n" + d["user"]
            + "<|im_end|>\n<|im_start|>assistant\n")


def _record(example_id, user="Q?", assistant="Answer: 1", **extra):
    return {"example_id": example_id, "messages": [{"role": "system", "content": "SYS"},
                                                   {"role": "user", "content": user},
                                                   {"role": "assistant", "content": assistant}], **extra}


def test_zero_shot_prompt_is_byte_identical_to_training_format():
    synthetic = _read(ROOT / "data" / "sft" / "train.jsonl")[:20]
    for r in synthetic:
        assert to_chatml(build_messages(r)) == _pilot_prompt(r)
        assert training_text(r) == _pilot_prompt(r) + {m["role"]: m["content"].strip() for m in r["messages"]}[
            "assistant"] + "<|im_end|>\n"


def test_few_shot_examples_are_earlier_chat_turns():
    shot = _record("s1", user="Example question", assistant="Answer: 7")
    text = to_chatml(build_messages(_record("q1", user="Real question"), [shot]))
    assert text == ("<|im_start|>system\nSYS<|im_end|>\n"
                    "<|im_start|>user\nExample question<|im_end|>\n"
                    "<|im_start|>assistant\nAnswer: 7<|im_end|>\n"
                    "<|im_start|>user\nReal question<|im_end|>\n"
                    "<|im_start|>assistant\n")


def test_question_cannot_be_its_own_example():
    with pytest.raises(ValueError):
        build_messages(_record("q1"), [_record("q1")])


def test_source_key():
    assert source_key({"source_type": "finqa"}) == "finqa"
    assert source_key({"source_type": "synthetic", "category": "financial_report_generation"}) == "financial_report_generation"


@pytest.mark.parametrize("text, done", [
    ("Calculation:\n1. 2 + 2 = 4\nAnswer: 4\n", True),
    ("Calculation:\n1. 2 + 2 = 4\nAnswer: 4", False),        # line not finished yet
    ("**Answer:** 12%\n", True),
    ("Answer:\n", False),                                     # nothing after the colon yet
    ("The answer depends on...\n", False),
])
def test_answer_line_complete(text, done):
    assert answer_line_complete(text) is done


@pytest.mark.skipif(not (EXTERNAL / "finqa" / "train.jsonl").exists(), reason="external data not built")
def test_few_shot_selection_on_real_data_is_deterministic_and_leak_free():
    train = (_read(EXTERNAL / "finqa" / "train.jsonl") + _read(EXTERNAL / "tatqa" / "train.jsonl")
             + _read(ROOT / "data" / "sft" / "train.jsonl"))
    shots = select_few_shot(train)
    assert shots == select_few_shot(list(reversed(train)))          # order-independent
    assert set(shots) == set(FEW_SHOT_SLOTS)
    for key, examples in shots.items():
        assert len(examples) == len(FEW_SHOT_SLOTS[key])
        assert len({document_key(e) for e in examples}) == len(examples)  # different documents
        for (name, matches), example in zip(FEW_SHOT_SLOTS[key], examples):
            assert source_key(example) == key and matches(example), (key, name)

    subset = json.loads((EXTERNAL / "eval_subset_v1.json").read_text())
    held_out = {i for s in subset["sources"].values() for i in s["example_ids"]}
    synthetic_test = {r["example_id"] for r in _read(ROOT / "data" / "sft" / "test.jsonl")}
    chosen = {e["example_id"] for examples in shots.values() for e in examples}
    assert not chosen & (held_out | synthetic_test)
