"""Tests for v4 teacher generation logic (stand-in teacher, no GPU)."""

import csv
import json

from finexpert.data.v4.figures import compute_facts, parse_figures
from finexpert.data.v4.generate import (
    check_item, generate_with_retries, judge_accepts, parse_judge, suggestions_ok, write_calibration_sample,
)

DATA = "Vertex reported revenue changing from ₹180 Cr to ₹207 Cr. Total debt changed from ₹90 Cr to ₹81 Cr."
ASSESS = {"id": "a1", "user": f"Financial data:\n{DATA}\n\nQuestion: Should I invest?",
          "facts": compute_facts(parse_figures(DATA)), "teacher_prompt": "PROMPT-a1"}
GOOD = "- Growth and lower debt point the same way.\n- Check whether profit becomes cash."
BAD = "- This is a good investment, you should buy."


def test_suggestions_format():
    assert suggestions_ok(GOOD)
    assert not suggestions_ok("- only one bullet")
    assert not suggestions_ok("No bullets here.\nAt all.")


def test_check_item_builds_target_and_applies_rules():
    good = check_item("assess", ASSESS, GOOD)
    assert good["passed"] and good["target"].startswith("What the figures show:")
    assert not check_item("assess", ASSESS, BAD)["passed"]


def test_failures_are_retried_with_sampling_and_kept_in_order():
    calls = []

    def teacher(prompts, temperature):
        calls.append((len(prompts), temperature))
        return [BAD if temperature == 0.0 else GOOD for _ in prompts]

    items = [ASSESS, {**ASSESS, "id": "a2"}]
    results = generate_with_retries("assess", items, teacher)
    assert [r["id"] for r in results] == ["a1", "a2"]
    assert all(r["passed"] and r["attempts"] == 2 for r in results)
    assert calls == [(2, 0.0), (2, 0.7)]          # third round never needed


def test_items_failing_every_attempt_are_reported_as_failed():
    results = generate_with_retries("assess", [ASSESS], lambda prompts, t: [BAD for _ in prompts])
    assert results[0]["passed"] is False and results[0]["attempts"] == 3


def test_parse_judge_and_threshold():
    reply = 'Sure! {"correctness": 5, "clarity": 4, "completeness": 4, "reason": "fine"} trailing'
    scores = parse_judge(reply, "explain")
    assert scores["correctness"] == 5 and judge_accepts(scores, "explain")
    assert not judge_accepts({"correctness": 5, "clarity": 3, "completeness": 5}, "explain")
    assert parse_judge('{"correctness": 5, "clarity": 4}', "explain") is None          # missing criterion
    assert parse_judge('{"correctness": "5", "clarity": 4, "completeness": 4}', "explain") is None
    assert parse_judge("no json at all", "explain") is None


def test_calibration_sheet_is_blind(tmp_path):
    rows = [{"id": f"x{i}", "kind": "explain", "question": "Q?", "target": "A.",
             "judge": {"correctness": 5, "clarity": 5, "completeness": 4}} for i in range(40)]
    ids = write_calibration_sample(rows, tmp_path / "sheet.csv", tmp_path / "key.json", n=30)
    with open(tmp_path / "sheet.csv", encoding="utf-8") as handle:
        sheet = list(csv.reader(handle))
    assert len(sheet) == 31 and all(r[4] == "" and r[5] == "" for r in sheet[1:])   # human columns empty
    assert set(json.loads((tmp_path / "key.json").read_text(encoding="utf-8"))) == set(ids)
