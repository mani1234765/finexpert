"""Tests for multi-question bundles and their scoring."""

import importlib.util
import json
from pathlib import Path

import pytest

from finexpert.data.external.common import build_record
from finexpert.data.external.multi import MULTI_INSTRUCTION, build_bundle, build_bundles
from finexpert.evaluation.qa.multi import numbered_answers, score_bundle, summarize_multi

ROOT = Path(__file__).resolve().parents[1]
MULTI = ROOT / "data" / "external" / "multi" / "validation.jsonl"
TATQA = ROOT / "data" / "external" / "raw" / "TAT-QA"


def _finqa(example_id, context, question, working, answer_text, value):
    return build_record(example_id=example_id, source="finqa", source_id=example_id, split="validation",
                        difficulty="easy", context=context, question=question,
                        target=f"{working}\nAnswer: {answer_text}", answer_type="arithmetic",
                        gold={"value": value, "answer_text": answer_text}, flags={"n_steps": 1})


CTX = "| ($m) | 2023 | 2022 |\n|---|---|---|\n| Revenue | 120 | 100 |"
A = _finqa("q_a", CTX, "What was the revenue change?", "Calculation:\n1. 120 − 100 = 20", "20", 20.0)
B = _finqa("q_b", CTX, "What was the percentage change?", "Calculation:\n1. 20 ÷ 100 = 0.2", "20%", 0.2)
B_REWORDED = _finqa("q_c", CTX, "What is the % change in revenue?", "Calculation:\n1. 20 ÷ 100 = 0.2", "20%", 0.2)


def test_bundle_prompt_and_target_layout():
    bundle = build_bundle([A, B], "multi_test_00000")
    user, target = bundle["messages"][1]["content"], bundle["messages"][2]["content"]
    assert user == (f"{CTX}\n\nQuestions:\n1. What was the revenue change?\n2. What was the percentage change?"
                    f"\n\n{MULTI_INSTRUCTION}")
    assert target == ("Q1. What was the revenue change?\nCalculation:\n1. 120 − 100 = 20\nAnswer 1: 20\n\n"
                      "Q2. What was the percentage change?\nCalculation:\n1. 20 ÷ 100 = 0.2\nAnswer 2: 20%")
    assert [item["example_id"] for item in bundle["items"]] == ["q_a", "q_b"]


def test_questions_with_different_contexts_are_never_bundled():
    other = _finqa("q_x", "| other table |", "Q?", "Calculation:\n1. 1 + 1 = 2", "2", 2.0)
    with pytest.raises(ValueError):
        build_bundle([A, other], "bad")


def test_reworded_duplicates_are_kept_once():
    bundles = build_bundles([A, B, B_REWORDED], seed=1)
    ids = [item["example_id"] for b in bundles for item in b["items"]]
    assert sorted(ids) == ["q_a", "q_b"]


def test_numbered_answers_last_one_wins_and_markdown_is_removed():
    assert numbered_answers("Answer 1: 5\n**Answer 2:** 7%\nAnswer 1: 6") == {1: "6", 2: "7%"}


def test_score_bundle_scores_each_position_and_counts_missing_as_wrong():
    bundle = build_bundle([A, B], "multi_test_00000")
    rows = score_bundle(bundle, "Q1 ...\nAnswer 1: 20\n\nQ2 ...", tatqa_dir=None)
    assert [(r["position"], r["answered"], r["strict"]["correct"]) for r in rows] == [(1, True, True), (2, False, False)]
    summary = summarize_multi(rows)
    assert summary["all_questions_answered_rate"] == 0.0
    assert summary["by_position"][1]["accuracy"] == 1.0 and summary["by_position"][2]["accuracy"] == 0.0


@pytest.mark.skipif(not MULTI.exists() or importlib.util.find_spec("pandas") is None or not TATQA.exists(),
                    reason="multi data not built")
def test_reference_answers_score_perfectly():
    bundles = [json.loads(line) for line in MULTI.read_text().splitlines()]
    rows = [row for b in bundles for row in score_bundle(b, b["messages"][2]["content"], str(TATQA))]
    summary = summarize_multi(rows)
    assert summary["all_questions_answered_rate"] == 1.0
    assert summary["by_source"]["finqa"]["accuracy"] == 1.0
    assert summary["by_source"]["tatqa"]["n"] - summary["by_source"]["tatqa"]["correct"] <= 1  # known backtick gold
