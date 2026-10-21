"""Build the FinExpert regression set (committed): every observed failure type, frozen with a verified answer.

    uv run python scripts/build_regression_set.py

Expected values are computed with finexpert.finance.formulas, never typed by hand. Each case records its origin:
observed (a recorded failure, with the output), reconstructed (rebuilt to reproduce a reported failure whose exact
prompt was not recorded), or designed (a probe for a known weakness).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from finexpert.data.external.common import QA_INSTRUCTION, SYSTEM_PROMPT  # noqa: E402
from finexpert.data.v4.teacher import assessment_user  # noqa: E402
from finexpert.finance import formulas as f  # noqa: E402

CLASSIFY = ("Classify the company's overall financial health as Healthy, Moderate Risk, or High Risk using only the "
            "provided financial figures. Show the key calculations and cite the evidence supporting the classification.")
LEAKED = ["deterministic dataset-labeling rules"]
VERTEX = ("Vertex Solutions reported revenue changing from ₹180 Cr to ₹207 Cr. Operating profit changed from ₹27 Cr to "
          "₹33 Cr. Total debt changed from ₹90 Cr to ₹81 Cr.")


def report(rows: list[tuple[str, str]], unit: str = "₹ Cr") -> str:
    lines = [f"Excerpt from a company annual report ({unit}):", "", "| Item | FY2024 |", "|---|---|"]
    return "\n".join(lines + [f"| {k} | {v} |" for k, v in rows])


def qa(case_id, category, origin, note, context, question, checks, observed=None):
    user = f"{context}\n\nQuestion: {question}\n\n{QA_INSTRUCTION}"
    case = {"id": case_id, "category": category, "origin": origin, "note": note, "system": SYSTEM_PROMPT, "user": user,
            "checks": checks}
    return {**case, "observed": observed} if observed else case


def pct(value, **tol):
    return {"value": round(value, 4), "unit": "percent", **tol}


def num(value, **tol):
    return {"value": round(value, 4), "unit": "number", **tol}


def cases() -> list[dict]:
    out = []
    # ---- formula correctness (reported failures 1-4, 7)
    out.append(qa("F01_roic", "formula", "reconstructed",
                  "Reproduces reported ROIC failure: model used EBITDA for NOPAT (441) and gross capital (2,550).",
                  report([("EBIT", "500"), ("Depreciation and amortisation", "130"), ("EBITDA", "630"),
                          ("Tax rate", "30%"), ("Total debt", "1,200"), ("Total equity", "1,350"),
                          ("Cash and equivalents", "400"), ("Non-operating investments", "100")]),
                  "Calculate ROIC. Use invested capital = total debt + total equity − cash − non-operating investments.",
                  {"final": [pct(f.pct(f.roic(500, 0.30, f.invested_capital(1200, 1350, 400, 100))))],
                   "required_intermediates": [350, 2050], "forbidden_values": [441, 2550]}))
    out.append(qa("F02_fcff", "formula", "reconstructed",
                  "Reported failure: FCFF computed from EBITDA instead of EBIT(1 − t).",
                  report([("EBIT", "400"), ("Depreciation and amortisation", "80"), ("EBITDA", "480"),
                          ("Tax rate", "25%"), ("Capital expenditure", "120"), ("Increase in net working capital", "30")]),
                  "Calculate free cash flow to the firm (FCFF).",
                  {"final": [num(f.fcff(400, 0.25, 80, 120, 30))], "required_intermediates": [300],
                   "forbidden_values": [360, 290]}))
    out.append(qa("F03_nopat", "formula", "designed", "NOPAT must use EBIT, not EBITDA.",
                  report([("EBIT", "820"), ("EBITDA", "1,000"), ("Tax rate", "25%")]),
                  "What is NOPAT?", {"final": [num(f.nopat(820, 0.25))], "forbidden_values": [750]}))
    out.append(qa("F04_expenses_vs_profit", "formula", "reconstructed",
                  "Reported failure: operating and interest expenses treated as profit figures.",
                  report([("Revenue", "2,000"), ("Operating expenses", "1,550"), ("Interest expense", "90"),
                          ("Tax rate", "25%")]),
                  "What are the operating profit and the net profit?",
                  {"final": [num(2000 - 1550), num((2000 - 1550 - 90) * 0.75)], "required_intermediates": [360]}))
    out.append(qa("F05_fcfe", "formula", "designed", "Multi-step: FCFF then FCFE.",
                  report([("EBIT", "400"), ("Depreciation and amortisation", "80"), ("Tax rate", "25%"),
                          ("Capital expenditure", "120"), ("Increase in net working capital", "30"),
                          ("Interest expense", "40"), ("Net borrowing", "50")]),
                  "Calculate free cash flow to equity (FCFE).",
                  {"final": [num(f.fcfe(f.fcff(400, 0.25, 80, 120, 30), 40, 0.25, 50))],
                   "required_intermediates": [230]}))
    out.append(qa("F06_cagr", "formula", "designed", "CAGR, not the simple average growth (11.6%).",
                  report([("Revenue FY2020", "100"), ("Revenue FY2024", "146.41")]),
                  "What was the compound annual growth rate (CAGR) of revenue from FY2020 to FY2024 (4 years)?",
                  {"final": [pct(f.pct(f.cagr(100, 146.41, 4)))], "forbidden_values": [11.6, 11.60]}))
    out.append(qa("F07_wacc", "formula", "designed", "After-tax cost of debt; pre-tax WACC would be 10.67%.",
                  report([("Market value of equity", "200"), ("Market value of debt", "100"), ("Cost of equity", "12%"),
                          ("Pre-tax cost of debt", "8%"), ("Tax rate", "25%")]),
                  "Calculate the WACC.",
                  {"final": [pct(f.pct(f.wacc(200, 100, 0.12, 0.08, 0.25)))], "forbidden_values": [10.67]}))
    out.append(qa("F08_interest_coverage", "formula", "designed", "EBIT-based; EBITDA would give 6.22.",
                  report([("EBIT", "450"), ("EBITDA", "560"), ("Interest expense", "90")]),
                  "What is the interest coverage ratio?",
                  {"final": [num(f.interest_coverage(450, 90))], "forbidden_values": [6.22]}))
    # ---- following a supplied formula (reported failure 7)
    out.append(qa("S01_supplied_roe", "supplied_formula", "reconstructed",
                  "Reported failure: familiar formula used instead of the one supplied. Textbook (closing equity) = 12.86%.",
                  report([("Net income", "90"), ("Opening equity", "500"), ("Closing equity", "700")]),
                  "For this question, Adjusted ROE is defined as net income divided by the AVERAGE of opening and closing "
                  "equity. What is the Adjusted ROE?",
                  {"final": [pct(f.pct(f.roe(90, (500 + 700) / 2)))], "required_intermediates": [600],
                   "forbidden_values": [12.86]}))
    out.append(qa("S02_supplied_cash_conversion", "supplied_formula", "designed",
                  "Supplied definition: OCF ÷ EBITDA (70%); OCF ÷ net income would be 140%.",
                  report([("Operating cash flow", "420"), ("EBITDA", "600"), ("Net income", "300")]),
                  "Here, cash conversion is defined as operating cash flow divided by EBITDA. What is the cash conversion?",
                  {"final": [pct(f.pct(420 / 600))], "forbidden_values": [140]}))
    # ---- completeness and units (reported failures 5, 6)
    out.append(qa("C01_three_margins", "completeness", "reconstructed",
                  "Reported failure: only the net margin returned when three margins were asked for.",
                  report([("Revenue", "1,000"), ("Cost of goods sold", "600"), ("Operating expenses", "250"),
                          ("Interest expense", "30"), ("Tax rate", "30%")]),
                  "What were the gross margin, the operating margin and the net profit margin?",
                  {"final": [pct(f.pct(f.margin(400, 1000))), pct(f.pct(f.margin(150, 1000))),
                             pct(f.pct(f.margin((150 - 30) * 0.7, 1000)))]}))
    out.append(qa("U01_percent_requested", "units", "reconstructed",
                  "Reported failure: returned 0.15 when a percentage was requested.",
                  report([("Revenue", "500"), ("Operating income", "75")]),
                  "What was the operating margin? Express it as a percentage.",
                  {"final": [pct(f.pct(f.margin(75, 500)))]}))
    obs_t1 = ("Calculation:\n1. 4820 − 4150 = 670\n2. 670 ÷ 4150 = 0.1615\nAs a percentage: 0.1615 × 100 = 0.1615%\n"
              "Answer: 0.1615%")
    out.append(qa("O01_percent_conversion", "units", "observed",
                  "Observed on the Q4_K_M GGUF via Ollama (Mac), 16 Oct 2026; the evaluated adapter made this step "
                  "correctly in all 871 test-set cases.",
                  "Excerpt from a company annual report:\n\n| ($ in millions) | 2023 | 2022 |\n|---|---|---|\n"
                  "| Revenue | 4,820 | 4,150 |\n| Operating income | 690 | 602 |",
                  "What was the percentage change in revenue from 2022 to 2023?",
                  {"final": [pct(f.pct((4820 - 4150) / 4150), abs_tol=0.015)]},
                  observed={"model": "finexpert-qwen3-4b Q4_K_M GGUF", "platform": "Ollama on macOS",
                            "date": "2026-10-16", "output": obs_t1}))
    # ---- multi-step, scale and format probes (manual test sheet T2-T4, T6)
    out.append(qa("M01_eps_change", "multi_step", "designed", "Three steps: two EPS divisions and a difference.",
                  "Excerpt from a company annual report:\n\n| (in millions, except per share) | 2023 | 2022 |\n|---|---|---|\n"
                  "| Net income | 612 | 540 |\n| Weighted average shares outstanding | 150 | 148 |",
                  "By how much did earnings per share change from 2022 to 2023?",
                  {"final": [num(612 / 150 - 540 / 148, abs_tol=0.006)], "required_intermediates": [4.08]}))
    out.append(qa("M02_scale_thousands", "multi_step", "designed", "Scale must be kept (thousand).",
                  "Excerpt from a company annual report:\n\n| (in thousands) | 2021 | 2020 |\n|---|---|---|\n"
                  "| Accounts receivable | 18,400 | 15,900 |",
                  "What was the average accounts receivable for 2020 and 2021?", {"final": [num((18400 + 15900) / 2)]}))
    out.append(qa("M03_text_only", "multi_step", "designed", "Figures only in prose, not a table.",
                  "Excerpt from a company annual report:\n\nDuring fiscal 2023 the company repurchased 2.4 million shares "
                  "at an average price of $52.50 per share.",
                  "What was the total amount spent on share repurchases in fiscal 2023?", {"final": [num(2.4 * 52.5)]}))
    out.append(qa("M04_indian_grouping", "multi_step", "designed", "Lakh/crore digit grouping (1,24,500).",
                  "Excerpt from a company annual report:\n\n| (₹ in crore) | FY2024 | FY2023 |\n|---|---|---|\n"
                  "| Revenue from operations | 1,24,500 | 1,10,250 |",
                  "What was the growth in revenue from operations from FY2023 to FY2024?",
                  {"final": [pct(f.pct((124500 - 110250) / 110250))]}))
    # ---- behaviour
    out.append(qa("B01_missing_data", "behaviour", "designed", "Net income is not in the context: must not invent it.",
                  "Excerpt from a company annual report:\n\n| ($ in millions) | 2023 | 2022 |\n|---|---|---|\n"
                  "| Revenue | 2,300 | 2,050 |\n| Operating income | 410 | 365 |",
                  "What was the net income in 2023?", {"behaviour": "missing_data"}))
    for case_id, question in (("B02_advice_should_buy", "Should I buy shares in this company?"),
                              ("B03_advice_yes_no", "Just tell me yes or no: is this a good investment?")):
        out.append({"id": case_id, "category": "behaviour", "origin": "designed",
                    "note": "Analysis-based suggestions only: no verdict, no prediction, disclaimer.",
                    "system": SYSTEM_PROMPT, "user": assessment_user(VERTEX, question),
                    "checks": {"behaviour": "advice"}})
    obs_vertex = ("Classification: Moderate Risk\nEvidence: Quantitative analysis: Revenue increased by 15.0%, from ₹180 Cr "
                  "to ₹207 Cr. Operating profit increased by 22.2%, from ₹27 Cr to ₹33 Cr. Total debt declined by 10.0%, "
                  "from ₹90 Cr to ₹81 Cr. These reported signals should be interpreted together rather than in isolation.\n"
                  "Basis: The classification uses only the supplied financial figures and deterministic dataset-labeling "
                  "rules. It is not a complete credit, investment, or solvency assessment.")
    out.append({"id": "O02_classification_vertex", "category": "classification", "origin": "observed",
                "note": "Observed on the demo Space (Q4_K_M GGUF), 16 Oct 2026: labelling rules give Healthy; also leaks "
                        "a training phrase.",
                "system": SYSTEM_PROMPT, "user": f"{CLASSIFY}\n\nFinancial data:\n{VERTEX}",
                "checks": {"behaviour": "classification", "label": "Healthy", "no_leaked_phrases": LEAKED},
                "observed": {"model": "finexpert-qwen3-4b Q4_K_M GGUF", "platform": "Hugging Face Space (llama.cpp)",
                             "date": "2026-10-16", "output": obs_vertex}})
    return out


def main() -> None:
    rows = cases()
    path = Path("data/regression/cases_v1.jsonl")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    from collections import Counter
    print(len(rows), "cases |", dict(Counter(r["category"] for r in rows)), "|", dict(Counter(r["origin"] for r in rows)))


if __name__ == "__main__":
    main()
