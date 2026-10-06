"""Tests for the FinQA / TAT-QA converters (no download needed except the last tests)."""

import json
from pathlib import Path

import pytest

from finexpert.data.external import finqa, tatqa
from finexpert.data.external.common import fmt_num, markdown_table, numbers_agree

RAW = Path(__file__).resolve().parents[1] / "data" / "external" / "raw"


# ------------------------------------------------------------------ common

@pytest.mark.parametrize("value, expected", [
    (5.0, "5"), (-0.0, "0"), (1.80250, "1.8025"), (0.53232, "0.5323"), (0.00003, "3e-05"), (-12.5, "-12.5"),
])
def test_fmt_num(value, expected):
    assert fmt_num(value) == expected


def test_markdown_table_pads_and_escapes():
    table = markdown_table([["", "2019"], ["a|b", "1", "extra"]])
    assert table.splitlines()[0] == "|  | 2019 |  |"
    assert "a\\|b" in table


@pytest.mark.parametrize("value, reference, text, ok", [
    (14.464, 14.0, "14%", True),      # written answer rounded to 0 dp
    (14.464, 14.5, "14.5%", True),
    (14.464, 14.6, "14.6%", False),
    (705.25, 704.25, "704.25", False),
])
def test_numbers_agree_respects_reference_rounding(value, reference, text, ok):
    assert numbers_agree(value, reference, text) is ok


# ------------------------------------------------------------------- FinQA

TABLE = [["net income", "$ 100", "$ 200", "$ 300"], ["revenue , total", "1,000", "2,000", "3,000"]]


def test_parse_program_handles_commas_in_row_names():
    steps = finqa.parse_program("table_average(revenue , total, none), divide(#0, const_100)")
    assert steps == [("table_average", "revenue , total", "none"), ("divide", "#0", "const_100")]


def test_execute_matches_official_semantics():
    steps = finqa.parse_program("table_sum(net income, none), divide(#0, const_1000), multiply(#1, 5%)")
    results, final = finqa.execute(steps, TABLE)
    assert results[0] == 600
    assert final == round(600 / 1000 * 0.05, 5)


def test_execute_greater_and_const_m1():
    _, final = finqa.execute(finqa.parse_program("greater(3, 2)"), [])
    assert final == "yes"
    _, final = finqa.execute(finqa.parse_program("multiply(4, const_m1)"), [])
    assert final == -4


def test_execute_unknown_row_raises():
    with pytest.raises(ValueError):
        finqa.execute(finqa.parse_program("table_max(missing row, none)"), TABLE)


def _finqa_example(program, exe_ans, answer):
    return {
        "id": "ABC/2015/page_10.pdf-1", "filename": "ABC/2015/page_10.pdf",
        "pre_text": ["revenue grew .", "."], "post_text": [],
        "table_ori": [["", "2015", "2014"], ["Revenue", "$1,100", "$1,000"]],
        "table": [["", "2015", "2014"], ["revenue", "$ 1100", "$ 1000"]],
        "qa": {"question": "what was the growth?", "program": program, "exe_ans": exe_ans, "answer": answer},
    }


def test_convert_percent_answer_puts_working_before_answer():
    record = finqa.convert_example(_finqa_example("subtract(1100, 1000), divide(#0, 1000)", 0.1, "10%"), "train", 0)
    target = record["messages"][2]["content"]
    assert target.splitlines() == [
        "Calculation:", "1. 1100 − 1000 = 100", "2. 100 ÷ 1000 = 0.1",
        "As a percentage: 0.1 × 100 = 10%", "Answer: 10%",
    ]
    assert record["flags"]["executor_matches_gold"] and record["flags"]["written_answer_consistent"]
    assert record["difficulty"] == "medium"
    assert "Excerpt from the 2015 annual report of ABC (page 10)" in record["messages"][1]["content"]
    assert record["messages"][1]["content"].count(" . ") == 0  # lone "." sentences dropped


def test_convert_flags_inconsistent_written_answer():
    record = finqa.convert_example(_finqa_example("subtract(1100, 1000)", 100.0, "99"), "train", 0)
    assert record["flags"]["written_answer_consistent"] is False
    assert record["messages"][2]["content"].endswith("Answer: 100")  # gold = executed result


# ------------------------------------------------------------------ TAT-QA

@pytest.mark.parametrize("derivation, expected", [
    ("7,572 - (6,919)", 14491),            # accounting negative
    ("((4,961)- 1,256)/1,256", -4.9498),
    ("65% * 3,433", 2231.45),
    ("[(61+9)/2] / [(87+9)/2]", 0.72917),  # square brackets
    ("$1.3 billion + 992 million", None),  # unit words: not checkable
])
def test_evaluate_derivation(derivation, expected):
    value = tatqa.evaluate_derivation(derivation)
    if expected is None:
        assert value is None
    else:
        assert value == pytest.approx(expected, abs=1e-4)


def _question(**overrides):
    base = {"uid": "q1", "order": 1, "question": "What is X?", "answer": ["2.9"], "derivation": "",
            "answer_type": "span", "answer_from": "table", "scale": "percent"}
    return {**base, **overrides}


def test_span_target_has_scale():
    target, gold, flags = tatqa.build_target(_question())
    assert target.splitlines() == ["The answer is stated directly in the table.", "Answer: 2.9%"]
    assert flags["derivation_consistent"] and gold["answer_text"] == "2.9%"


def test_arithmetic_percent_target_converts_ratio():
    target, gold, flags = tatqa.build_target(_question(
        answer_type="arithmetic", answer=16, derivation="(2.9-2.5)/2.5", answer_from="table"))
    assert target.splitlines()[-2:] == ["As a percentage: 0.16 × 100 = 16%", "Answer: 16%"]
    assert flags["derivation_consistent"]


def test_count_mismatch_is_flagged():
    _, _, flags = tatqa.build_target(_question(answer_type="count", answer="3", derivation="a ## b", scale=""))
    assert flags["derivation_consistent"] is False


def test_non_numeric_arithmetic_answer_is_flagged_not_crashing():
    _, gold, flags = tatqa.build_target(_question(answer_type="arithmetic", answer="31 January 2029",
                                                   derivation="x", scale=""))
    assert flags["derivation_consistent"] is False and gold["answer_text"] == "31 January 2029"


# ------------------------------------------- full-data checks (need the clones)

@pytest.mark.skipif(not (RAW / "FinQA" / "dataset").exists(), reason="FinQA not cloned")
def test_executor_reproduces_every_finqa_gold_answer():
    for split in ("train", "validation", "test"):
        records = finqa.convert_split(RAW / "FinQA", split)
        assert all(r["flags"]["executor_matches_gold"] for r in records), split


@pytest.mark.skipif(not (RAW / "TAT-QA" / "dataset_raw").exists(), reason="TAT-QA not cloned")
def test_tatqa_ids_unique_and_test_has_gold():
    for split in ("train", "validation", "test"):
        records = tatqa.convert_split(RAW / "TAT-QA", split)
        assert len({r["example_id"] for r in records}) == len(records)
        assert all(r["gold"]["answer_text"] for r in records)
    assert len(json.loads((RAW / "TAT-QA" / "dataset_raw" / "tatqa_dataset_test_gold.json").read_text())) > 0
