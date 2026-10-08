"""Tests for FinQA / TAT-QA evaluation."""

import importlib.util
import json
from pathlib import Path

import pytest

from finexpert.data.external.subset import allocate, select_subset
from finexpert.evaluation.qa.extraction import extract_answer, parse_number, split_answer_and_scale
from finexpert.evaluation.qa.scoring import score_finqa

ROOT = Path(__file__).resolve().parents[1]
TATQA = ROOT / "data" / "external" / "raw" / "TAT-QA"
BUILT = ROOT / "data" / "external" / "finqa" / "validation.jsonl"
HAS_TATQA = (TATQA / "tatqa_metric.py").exists() and importlib.util.find_spec("pandas") is not None


# -------------------------------------------------------------- extraction

def test_last_answer_line_wins_and_markdown_is_removed():
    text = "Answer: 1\nmore working\n**Answer:** 2.5%"
    assert extract_answer(text).text == "2.5%"
    assert extract_answer(text).method == "answer_line"


def test_strict_needs_answer_line_lenient_falls_back():
    text = "Revenue grew from 100 to 120, so growth is 20%."
    assert extract_answer(text).text is None
    lenient = extract_answer(text, lenient=True)
    assert (lenient.text, lenient.method) == ("20%", "last_number")
    assert extract_answer("So the answer is 42", lenient=True).method == "answer_is"


@pytest.mark.parametrize("text, value, percent, scale", [
    ("$1,234.5 million", 1234.5, False, "million"),
    ("(12.5)%", -12.5, True, "percent"),
    ("−3", -3.0, False, ""),
    ("42.", 42.0, False, ""),
])
def test_parse_number(text, value, percent, scale):
    parsed = parse_number(text)
    assert (parsed.value, parsed.is_percent, parsed.scale) == (value, percent, scale)


@pytest.mark.parametrize("text, expected", [
    ("13.91%", (["13.91"], "percent")),
    ("582 thousand", (["582"], "thousand")),
    ("A; B; C", (["A", "B", "C"], "")),
])
def test_split_answer_and_scale(text, expected):
    assert split_answer_and_scale(text) == expected


# ----------------------------------------------------------------- FinQA

@pytest.mark.parametrize("answer, gold, correct", [
    ("0.46%", 0.00455, True),      # 2-dp rounding of a percent
    ("14.46%", 0.14464, True),     # ratio gold, percent answer
    ("14%", 0.14464, True),        # coarser, but precise enough for the value
    ("14.46", 0.14464, True),      # percent without the sign
    ("0", 0.3, False),             # rounding too coarse for the value
    ("0.004", 0.0046, False),      # 13% off
    ("705", 704.25, False),        # outside 0.1%
    ("704.25", 704.25, True),
    ("(41)", -41.0, True),         # accounting negative
])
def test_finqa_numeric_scoring(answer, gold, correct):
    assert score_finqa(f"Calculation:\n...\nAnswer: {answer}", {"value": gold})["correct"] is correct


def test_finqa_yes_no():
    assert score_finqa("Answer: No.", {"value": "no"})["correct"]
    assert not score_finqa("Answer: yes", {"value": "no"})["correct"]


def test_finqa_missing_answer_line_is_wrong_in_strict_mode():
    result = score_finqa("the result is 704.25", {"value": 704.25})
    assert (result["correct"], result["method"]) == (False, "none")
    assert score_finqa("the result is 704.25", {"value": 704.25}, lenient=True)["correct"]


# ---------------------------------------------------------------- subset

def test_allocate_respects_minimum_and_total():
    plan = allocate({"a": 1000, "b": 10, "c": 300}, total=100, minimum=20)
    assert plan["b"] == 10 and sum(plan.values()) == 100 and plan["a"] > plan["c"]


def test_select_subset_is_deterministic_and_skips_long_examples():
    records = [{"example_id": f"x{i}", "answer_type": "span" if i % 2 else "arithmetic",
                "flags": {"est_tokens": 5000 if i == 0 else 100}} for i in range(200)]
    first = select_subset(records, 50, seed=1)
    assert first == select_subset(records, 50, seed=1)
    assert len(first) == 50 and "x0" not in first


# ------------------------------------------- full-data invariants (need the data)

@pytest.mark.skipif(not BUILT.exists() or not HAS_TATQA, reason="external data not built or pandas missing")
def test_reference_answers_score_perfectly_on_official_scorers():
    from finexpert.evaluation.qa.report import build_qa_report

    for split in ("validation", "test"):
        records = [json.loads(line) for source in ("finqa", "tatqa")
                   for line in (ROOT / "data" / "external" / source / f"{split}.jsonl").read_text(encoding="utf-8").splitlines()]
        report = build_qa_report(records, {r["example_id"]: r["messages"][2]["content"] for r in records}, str(TATQA))
        assert report["summary"]["finqa"]["strict"]["accuracy"] == 1.0
        if split == "test":  # tie-break regression: perfect answers must also get the scale right
            assert report["summary"]["tatqa"]["official"]["scale_accuracy"] == 1.0
        # One TAT-QA validation gold answer contains a stray backtick ("`70.07"); everything else is exact.
        assert report["summary"]["tatqa"]["strict"]["n"] - report["summary"]["tatqa"]["strict"]["correct"] <= 1
