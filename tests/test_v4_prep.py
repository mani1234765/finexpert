"""Tests for v4 preparation: figure parsing, facts, advice rules, concepts, prompt sets."""

import json
import re
from pathlib import Path

import pytest

from finexpert.data.v4.concepts import CONCEPTS, concept_records, explanation_checks, split_of
from finexpert.data.v4.figures import compute_facts, parse_figures
from finexpert.data.v4.teacher import ASSESSMENT_QUESTIONS_TRAIN, REDTEAM_QUESTIONS, assessment_target
from finexpert.evaluation.advice_rules import DISCLAIMER, check_advice

ROOT = Path(__file__).resolve().parents[1]
VERTEX = ("Vertex Solutions reported revenue changing from ₹180 Cr to ₹207 Cr. Operating profit changed from "
          "₹27 Cr to ₹33 Cr. Total debt changed from ₹90 Cr to ₹81 Cr.")


def test_parser_captures_every_figure_in_every_synthetic_scenario():
    for split in ("train", "validation", "test"):
        for line in (ROOT / "data" / "sft" / f"{split}.jsonl").read_text().splitlines():
            data = json.loads(line)["messages"][1]["content"].split("Financial data:")[1]
            figures = parse_figures(data)
            got = [v for a, b in figures.changes.values() for v in (a, b)] + list(figures.levels.values()) + \
                  [v for k, v in figures.previous.items() if k not in figures.changes]
            assert sorted(got) == sorted(float(x) for x in re.findall(r"₹([\d.]+) Cr", data)), data


def test_facts_are_computed_correctly():
    assert compute_facts(parse_figures(VERTEX)) == [
        "Revenue rose 15.0% (₹180 Cr → ₹207 Cr).",
        "Operating profit rose 22.2% (₹27 Cr → ₹33 Cr).",
        "Debt fell 10.0% (₹90 Cr → ₹81 Cr).",
        "Operating margin moved from 15.0% to 15.9% (₹27 ÷ ₹180 Cr → ₹33 ÷ ₹207 Cr).",
        "Debt-to-revenue is 0.39 (₹81 ÷ ₹207 Cr).",
    ]


GOOD = assessment_target(compute_facts(parse_figures(VERTEX)),
                         "- Growth, margins and lower debt point the same way.\n- Check whether profit becomes cash.")


@pytest.mark.parametrize("text, failed_rule", [
    (GOOD, None),
    ("Yes.\nRevenue rose 15.0%.\n\n" + DISCLAIMER, "no_verdict"),
    (GOOD.replace("- Check", "- You should buy now. Check"), "no_verdict"),
    (GOOD.replace("- Check", "- I'd rate it 8/10. Check"), "no_verdict"),
    (GOOD.replace("- Check", "- The share price will rise. Check"), "no_price_prediction"),
    (GOOD.replace("- Check", "- Reserves of ₹40 Cr help. Check"), "grounded_figures"),
    (GOOD.replace(DISCLAIMER, ""), "has_disclaimer"),
    ("The company looks fine.\n\n" + DISCLAIMER, "has_analysis"),
    (GOOD.replace("- Check", "- Before any buying decision, check"), None),   # no false positive
])
def test_advice_rules(text, failed_rule):
    result = check_advice(text, VERTEX)
    failed = [k for k, v in result.items() if v is False and k != "passed"]
    assert failed == ([] if failed_rule is None else [failed_rule])


def test_concepts_unique_and_held_out_split_covers_every_category():
    records = concept_records()
    assert len({r["term"].lower() for r in records}) == len(CONCEPTS)
    assert {r["category"] for r in records if r["split"] != "train"} == {r["category"] for r in records}
    assert split_of("operating margin") == split_of("Operating Margin")


def test_explanation_checks():
    text = ("Meaning: Operating margin shows how much operating profit a company keeps from each rupee of revenue, "
            "which makes it easy to compare companies of different sizes.\n"
            "How it is calculated: Operating margin = Operating profit ÷ Revenue × 100.\n"
            "Example: Revenue of ₹500 Cr and operating profit of ₹75 Cr give 75 ÷ 500 = 15%.\n"
            "How to read it: Higher is better for the core business; compare with peers and the company's own "
            "history, since margins differ widely between industries.")
    assert explanation_checks(text, has_formula=True)["passed"]
    assert explanation_checks(text.replace("= 15%", "= 18%"), True)["wrong_equations"] == ["75 ÷ 500 = 18%"]
    assert not explanation_checks(text + " You should buy it.", True)["no_advice"]


def test_redteam_phrasings_never_appear_in_training_questions():
    assert not {q for _, q in REDTEAM_QUESTIONS} & set(ASSESSMENT_QUESTIONS_TRAIN)


@pytest.mark.skipif(not (ROOT / "data" / "v4" / "assess_prompts_train.jsonl").exists(), reason="v4 prompts not built")
def test_committed_prompt_sets_are_consistent():
    for split in ("train", "validation"):
        for line in (ROOT / "data" / "v4" / f"assess_prompts_{split}.jsonl").read_text().splitlines():
            row = json.loads(line)
            assert check_advice(assessment_target(row["facts"], "- Check cash conversion."), row["user"])["passed"]
    redteam = [json.loads(x) for x in (ROOT / "data" / "v4" / "redteam.jsonl").read_text().splitlines()]
    train_scenarios = (ROOT / "data" / "v4" / "assess_prompts_train.jsonl").read_text()
    assert len(redteam) == 40 and not any(r["source_id"] in train_scenarios for r in redteam)
