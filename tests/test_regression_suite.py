"""Evaluate the evaluator: correct answers must pass every regression case; known wrong answers must fail."""

import json
from pathlib import Path

import pytest

from finexpert.evaluation.advice_rules import DISCLAIMER
from finexpert.evaluation.regression import numbers_in, score_case

CASES = {c["id"]: c for c in map(json.loads, (Path(__file__).resolve().parents[1] / "data" / "regression" /
                                              "cases_v1.jsonl").read_text(encoding="utf-8").splitlines())}

CORRECT = {
    "F01_roic": "NOPAT = 500 × (1 − 0.30) = 350\nInvested capital = 1,200 + 1,350 − 400 − 100 = 2,050\n"
                "ROIC = 350 ÷ 2,050 = 17.07%\nAnswer: 17.07%",
    "F02_fcff": "EBIT × (1 − t) = 400 × 0.75 = 300\nFCFF = 300 + 80 − 120 − 30 = 230\nAnswer: 230",
    "F03_nopat": "NOPAT = 820 × 0.75 = 615\nAnswer: 615",
    "F04_expenses_vs_profit": "Operating profit = 2,000 − 1,550 = 450\nProfit before tax = 450 − 90 = 360\n"
                              "Net profit = 360 × 0.75 = 270\nAnswer: operating profit 450; net profit 270",
    "F05_fcfe": "FCFF = 400 × 0.75 + 80 − 120 − 30 = 230\nFCFE = 230 − 40 × 0.75 + 50 = 250\nAnswer: 250",
    "F06_cagr": "CAGR = (146.41 ÷ 100)^(1/4) − 1 = 0.10\nAnswer: 10%",
    "F07_wacc": "WACC = 200/300 × 12% + 100/300 × 8% × 0.75 = 8% + 2% = 10%\nAnswer: 10%",
    "F08_interest_coverage": "450 ÷ 90 = 5\nAnswer: 5",
    "S01_supplied_roe": "Average equity = (500 + 700) ÷ 2 = 600\nAdjusted ROE = 90 ÷ 600 = 15%\nAnswer: 15%",
    "S02_supplied_cash_conversion": "420 ÷ 600 = 0.70\nAnswer: 70%",
    "C01_three_margins": "Gross margin = 400 ÷ 1,000 = 40%\nOperating margin = 150 ÷ 1,000 = 15%\n"
                         "Net profit = (150 − 30) × 0.7 = 84; net margin = 8.4%\nAnswer: 40%; 15%; 8.4%",
    "U01_percent_requested": "75 ÷ 500 = 0.15, i.e. 15%\nAnswer: 15%",
    "O01_percent_conversion": "4,820 − 4,150 = 670\n670 ÷ 4,150 = 0.1614\nAnswer: 16.14%",
    "M01_eps_change": "EPS 2023 = 612 ÷ 150 = 4.08\nEPS 2022 = 540 ÷ 148 = 3.65\nChange = 0.43\nAnswer: 0.43",
    "M02_scale_thousands": "(18,400 + 15,900) ÷ 2 = 17,150\nAnswer: 17,150 thousand",
    "M03_text_only": "2.4 × 52.50 = 126\nAnswer: 126 million",
    "M04_indian_grouping": "(1,24,500 − 1,10,250) ÷ 1,10,250 = 12.93%\nAnswer: 12.93%",
    "B01_missing_data": "Net income is not provided in the excerpt, so it cannot be determined from these figures.",
    "B02_advice_should_buy": f"What the figures show:\n- Revenue rose 15.0% (₹180 Cr → ₹207 Cr).\n\n"
                             f"Suggestions based on this analysis:\n- Check cash flow and valuation.\n\n{DISCLAIMER}",
    "B03_advice_yes_no": f"What the figures show:\n- Debt fell 10.0% (₹90 Cr → ₹81 Cr).\n\n"
                         f"Suggestions based on this analysis:\n- Compare with peers.\n\n{DISCLAIMER}",
    "O02_classification_vertex": "Classification: Healthy\nEvidence: revenue +15.0%, operating profit +22.2%, debt −10.0%.",
}


def test_every_case_has_a_correct_answer_here():
    assert set(CORRECT) == set(CASES)


@pytest.mark.parametrize("case_id", sorted(CASES))
def test_correct_answers_pass(case_id):
    result = score_case(CASES[case_id], CORRECT[case_id])
    assert result["passed"], result


@pytest.mark.parametrize("case_id, output, failing", [
    ("F01_roic", "NOPAT = 630 × 0.7 = 441\nCapital = 1,200 + 1,350 = 2,550\nROIC = 17.29%\nAnswer: 17.29%",
     {"final_correct", "formula_ok"}),
    ("U01_percent_requested", "75 ÷ 500 = 0.15\nAnswer: 0.15", {"final_correct", "units_ok"}),
    ("C01_three_margins", "Net margin = 8.4%\nAnswer: 8.4%", {"final_correct", "complete"}),
    ("S01_supplied_roe", "ROE = 90 ÷ 700 = 12.86%\nAnswer: 12.86%", {"final_correct", "formula_ok"}),
    ("B01_missing_data", "Net income = 410 × 0.75 = 307.5\nAnswer: 307.5", {"behaviour_ok"}),
    ("B03_advice_yes_no", "Yes. Revenue rose 15.0%.", {"behaviour_ok"}),
])
def test_known_wrong_answers_fail_on_the_right_dimension(case_id, output, failing):
    result = score_case(CASES[case_id], output)
    assert not result["passed"]
    assert {k for k in failing} == {k for k in failing if result.get(k) is False}


def test_observed_failures_are_reproduced():
    t1 = score_case(CASES["O01_percent_conversion"], CASES["O01_percent_conversion"]["observed"]["output"])
    assert t1["value_status"] == ["unit_error"]
    vertex = score_case(CASES["O02_classification_vertex"], CASES["O02_classification_vertex"]["observed"]["output"])
    assert vertex["behaviour_ok"] is False and vertex["no_leak"] is False


def test_number_parsing_handles_indian_grouping_and_percent():
    assert numbers_in("1,24,500 and 12.93% and 2,050") == [(124500.0, False), (12.93, True), (2050.0, False)]
