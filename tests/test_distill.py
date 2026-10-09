"""Tests for self-distilled (rejection-sampled) training targets."""

from finexpert.data.distill import (
    apply_targets, build_distilled_targets, distilled_target, rejection_reason, split_reasoning,
)


def _record(example_id, gold="12.6 million"):
    return {"example_id": example_id, "source_type": "tatqa", "answer_type": "arithmetic",
            "gold": {"answer_text": gold},
            "messages": [{"role": "system", "content": "S"}, {"role": "user", "content": "Q"},
                         {"role": "assistant", "content": "Calculation:\n44.1 - 56.7 = -12.6\nAnswer: -12.6 million"}]}


def _pred(text, hit=False):
    return {"prediction": text, "hit_token_limit": hit, "n_new_tokens": 50}


GOOD = "From the table, 2019 is 44.1 and 2018 is 56.7.\nChange = 44.1 - 56.7 = -12.6\n\n**Answer:** -12.6"


def test_split_reasoning_drops_the_answer_line():
    assert split_reasoning(GOOD) == "From the table, 2019 is 44.1 and 2018 is 56.7.\nChange = 44.1 - 56.7 = -12.6"
    assert split_reasoning("no answer line, 3 + 4 = 7") == "no answer line, 3 + 4 = 7"


def test_target_uses_model_reasoning_and_canonical_gold_answer():
    target = distilled_target(split_reasoning(GOOD), "-12.6 million")
    assert target.endswith("\n\nAnswer: -12.6 million") and target.startswith("From the table")


def test_rejection_reasons():
    assert rejection_reason(_pred(GOOD), correct=True) is None
    assert rejection_reason(_pred(GOOD), correct=False) == "wrong_answer"
    assert rejection_reason(_pred(GOOD, hit=True), correct=True) == "hit_token_limit"
    assert rejection_reason(_pred("Answer: 5"), correct=True) == "no_reasoning"
    assert rejection_reason(_pred("x = 1 + 1 = 2\nAnswer: 2\nmore 3\nAnswer: 2"), correct=True) == "multiple_answer_lines"
    assert rejection_reason(_pred("<think>1+1</think> 2\nAnswer: 2"), correct=True) == "template_tokens"


def test_build_and_apply_keep_rejected_examples_unchanged():
    records = [_record("a"), _record("b")]
    predictions = {"a": _pred(GOOD), "b": _pred("I think 3 + 3 = 6\nAnswer: 6")}
    rows = build_distilled_targets(records, predictions, lambda r, p: r["example_id"] == "a")
    assert [r["accepted"] for r in rows] == [True, False]
    assert rows[1]["rejection_reason"] == "wrong_answer" and "target" not in rows[1]

    updated = apply_targets(records, rows)
    assert updated[0]["messages"][2]["content"].endswith("Answer: 12.6 million")
    assert updated[0]["target_style"] == "distilled"
    assert updated[1] == records[1]                      # rejected: template target kept
    assert records[0]["messages"][2]["content"].startswith("Calculation:")  # originals not mutated
