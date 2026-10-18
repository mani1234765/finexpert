"""Financial concepts for explanation training (v4).

Terms are split by a stable hash of the term into train / validation / test (about 70 / 15 / 15), so evaluation asks
about concepts the model never trained on: it tests whether the model learned to explain, not to recall.

Targets are written by a teacher model in a fixed structure and must pass `explanation_checks` (and, for a sample,
the LLM judge and human scoring described in docs/v4_judge.md).
"""

from __future__ import annotations

import hashlib
import re
from typing import Any

# (term, category, has_formula)
CONCEPTS: list[tuple[str, str, bool]] = [
    ("gross margin", "profitability", True), ("operating margin", "profitability", True),
    ("net profit margin", "profitability", True), ("EBITDA", "profitability", True),
    ("EBITDA margin", "profitability", True), ("EBIT", "profitability", True),
    ("return on equity (ROE)", "profitability", True), ("return on assets (ROA)", "profitability", True),
    ("return on capital employed (ROCE)", "profitability", True), ("return on invested capital (ROIC)", "profitability", True),
    ("contribution margin", "profitability", True), ("operating leverage", "profitability", True),
    ("profit before tax (PBT)", "profitability", True), ("profit after tax (PAT)", "profitability", True),
    ("earnings per share (EPS)", "profitability", True), ("diluted EPS", "profitability", True),
    ("DuPont analysis", "profitability", True), ("gross profit", "profitability", True),
    ("current ratio", "liquidity", True), ("quick ratio", "liquidity", True), ("cash ratio", "liquidity", True),
    ("working capital", "liquidity", True), ("net working capital", "liquidity", True),
    ("cash conversion cycle", "liquidity", True), ("liquidity", "liquidity", False),
    ("defensive interval ratio", "liquidity", True),
    ("debt-to-equity ratio", "leverage", True), ("debt-to-assets ratio", "leverage", True), ("net debt", "leverage", True),
    ("net debt to EBITDA", "leverage", True), ("interest coverage ratio", "leverage", True),
    ("debt service coverage ratio (DSCR)", "leverage", True), ("financial leverage", "leverage", True),
    ("equity multiplier", "leverage", True), ("solvency", "leverage", False), ("capital structure", "leverage", False),
    ("gearing", "leverage", True), ("fixed charge coverage ratio", "leverage", True),
    ("asset turnover", "efficiency", True), ("inventory turnover", "efficiency", True),
    ("days inventory outstanding", "efficiency", True), ("receivables turnover", "efficiency", True),
    ("days sales outstanding (DSO)", "efficiency", True), ("payables turnover", "efficiency", True),
    ("days payable outstanding (DPO)", "efficiency", True), ("fixed asset turnover", "efficiency", True),
    ("working capital turnover", "efficiency", True), ("operating expense ratio", "efficiency", True),
    ("operating cash flow", "cash flow", False), ("free cash flow", "cash flow", True),
    ("free cash flow to equity (FCFE)", "cash flow", True), ("capital expenditure (capex)", "cash flow", False),
    ("cash flow from investing activities", "cash flow", False), ("cash flow from financing activities", "cash flow", False),
    ("cash conversion ratio", "cash flow", True), ("operating cash flow ratio", "cash flow", True),
    ("cash burn rate", "cash flow", True), ("dividend payout ratio", "cash flow", True), ("retention ratio", "cash flow", True),
    ("price-to-earnings ratio (P/E)", "valuation", True), ("price-to-book ratio (P/B)", "valuation", True),
    ("price-to-sales ratio (P/S)", "valuation", True), ("enterprise value (EV)", "valuation", True),
    ("EV/EBITDA", "valuation", True), ("dividend yield", "valuation", True), ("earnings yield", "valuation", True),
    ("market capitalisation", "valuation", True), ("book value per share", "valuation", True),
    ("PEG ratio", "valuation", True), ("free cash flow yield", "valuation", True), ("intrinsic value", "valuation", False),
    ("discounted cash flow (DCF)", "valuation", False), ("terminal value", "valuation", False),
    ("cost of equity", "valuation", False), ("weighted average cost of capital (WACC)", "valuation", True),
    ("year-on-year growth (YoY)", "growth", True), ("quarter-on-quarter growth (QoQ)", "growth", True),
    ("compound annual growth rate (CAGR)", "growth", True), ("organic growth", "growth", False),
    ("same-store sales growth", "growth", True), ("revenue run rate", "growth", True),
    ("sustainable growth rate", "growth", True), ("base effect", "growth", False),
    ("revenue from operations", "income statement", False), ("other income", "income statement", False),
    ("cost of goods sold (COGS)", "income statement", False), ("operating expenses (opex)", "income statement", False),
    ("depreciation", "income statement", False), ("amortisation", "income statement", False),
    ("finance costs", "income statement", False), ("exceptional items", "income statement", False),
    ("effective tax rate", "income statement", True), ("total comprehensive income", "income statement", False),
    ("employee benefit expense", "income statement", False),
    ("total assets", "balance sheet", False), ("current assets", "balance sheet", False),
    ("current liabilities", "balance sheet", False), ("shareholders' equity", "balance sheet", True),
    ("retained earnings", "balance sheet", False), ("reserves and surplus", "balance sheet", False),
    ("goodwill", "balance sheet", False), ("intangible assets", "balance sheet", False),
    ("trade receivables", "balance sheet", False), ("inventories", "balance sheet", False),
    ("trade payables", "balance sheet", False), ("contingent liabilities", "balance sheet", False),
    ("capital employed", "balance sheet", True), ("non-current liabilities", "balance sheet", False),
    ("deferred tax liability", "balance sheet", False), ("lease liabilities", "balance sheet", False),
    ("accrual accounting", "accounting", False), ("revenue recognition", "accounting", False),
    ("matching principle", "accounting", False), ("going concern", "accounting", False),
    ("impairment", "accounting", False), ("write-off", "accounting", False), ("provision", "accounting", False),
    ("consolidated vs standalone financial statements", "accounting", False), ("minority interest", "accounting", False),
    ("Ind AS", "accounting", False), ("audit qualification", "accounting", False),
    ("related-party transactions", "accounting", False),
    ("crore and lakh", "india", True), ("promoter holding", "india", False), ("pledged promoter shares", "india", False),
    ("FII and DII holdings", "india", False), ("SEBI", "india", False), ("quarterly results under SEBI LODR", "india", False),
    ("GST", "india", False), ("TDS", "india", False), ("bonus issue", "india", False), ("stock split", "india", False),
    ("rights issue", "india", False), ("buyback", "india", False), ("free float", "india", True),
    ("net interest margin (NIM)", "banking", True), ("gross NPA", "banking", True), ("net NPA", "banking", True),
    ("provision coverage ratio (PCR)", "banking", True), ("CASA ratio", "banking", True),
    ("capital adequacy ratio (CAR)", "banking", True), ("credit-deposit ratio", "banking", True),
    ("cost-to-income ratio", "banking", True), ("assets under management (AUM)", "banking", False),
    ("cost of funds", "banking", True), ("yield on advances", "banking", True), ("slippage ratio", "banking", True),
    ("beta", "risk", True), ("volatility", "risk", False), ("credit rating", "risk", False),
    ("liquidity risk", "risk", False), ("concentration risk", "risk", False), ("foreign exchange risk", "risk", False),
    ("interest rate risk", "risk", False), ("refinancing risk", "risk", False), ("margin of safety", "risk", True),
    ("red flags in financial statements", "risk", False), ("earnings quality", "risk", False),
    ("one-off items", "risk", False),
]

QUESTION_TEMPLATES = (
    "What does {term} mean?",
    "Explain {term} and how it is calculated.",
    "Why does {term} matter when analysing a company?",
    "How should I interpret {term}?",
)
SECTIONS = ("Meaning:", "How it is calculated:", "Example:", "How to read it:")
_EQUATION = re.compile(r"(?P<lhs>[\d.,\s()+\-×÷*/]+?)\s*=\s*(?P<rhs>-?[\d.,]*\d)\s*(?P<pct>%?)")
_ADVICE = re.compile(r"\b(?:you\s+should\s+(?:buy|sell|invest)|i\s+recommend|good\s+(?:buy|investment))\b",
                     re.IGNORECASE)


def split_of(term: str) -> str:
    """Stable split by term name (about 70 / 15 / 15)."""
    bucket = int(hashlib.sha256(term.lower().encode()).hexdigest(), 16) % 100
    return "train" if bucket < 70 else ("validation" if bucket < 85 else "test")


def concept_records() -> list[dict[str, Any]]:
    return [{"term": term, "category": category, "has_formula": has_formula, "split": split_of(term)}
            for term, category, has_formula in CONCEPTS]


def explanation_checks(text: str, has_formula: bool) -> dict[str, Any]:
    """Automatic checks for a teacher-written explanation; quality is judged separately (docs/v4_judge.md)."""
    from finexpert.data.external.tatqa import evaluate_derivation

    wrong = []
    for match in _EQUATION.finditer(text):
        lhs = match.group("lhs").replace("×", "*").replace("÷", "/")
        if not re.search(r"\d\s*[*/+\-]\s*[\d(]", lhs):
            continue
        value = evaluate_derivation(lhs)
        if value is None:
            continue
        rhs = match.group("rhs").replace(",", "")
        decimals = len(rhs.split(".")[1]) if "." in rhs else 0
        candidates = (value, value * 100) if match.group("pct") else (value,)
        if not any(abs(c - float(rhs)) <= 0.5 * 10 ** -decimals + 1e-9 + 0.001 * abs(c) for c in candidates):
            wrong.append(match.group(0).strip())
    required = [s for s in SECTIONS if has_formula or s != "How it is calculated:"]
    words = len(text.split())
    results = {"length_ok": 60 <= words <= 220, "has_sections": all(s in text for s in required),
               "arithmetic_ok": not wrong, "no_advice": not _ADVICE.search(text)}
    return {**results, "passed": all(results.values()), "words": words, "wrong_equations": wrong}
