"""Parse FinExpert's synthetic scenario sentences and compute verified facts from them.

Analysis-based suggestions (v4) are built in two parts:
1. "What the figures show" - computed here, deterministically, so every number in it is correct by construction.
2. "Suggestions based on this analysis" - written by a teacher model from those facts, then checked
   (see finexpert.evaluation.advice_rules).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_CHANGE = re.compile(r"(?P<name>[a-z][a-z -]*?)\s+(?:changing|changed|increasing)\s+from\s+₹(?P<a>[\d.]+) Cr"
                     r"\s+to\s+₹(?P<b>[\d.]+) Cr", re.IGNORECASE)
_STATIC = re.compile(r"(?P<name>[a-z][a-z -]*?)\s+(?:is|was|were|of)\s+₹(?P<v>[\d.]+) Cr", re.IGNORECASE)
_ALIASES = {"total debt": "debt", "profit": "profit", "net income": "net income"}


@dataclass
class Figures:
    changes: dict[str, tuple[float, float]]   # metric -> (previous, current)
    levels: dict[str, float]                  # metric -> current value
    previous: dict[str, float]                # metric -> previous-period value (stated as levels)

    def current(self, name: str) -> float | None:
        if name in self.levels:
            return self.levels[name]
        if name in self.changes:
            return self.changes[name][1]
        return None


def _clean(name: str) -> str:
    name = re.sub(r"^.*\breported\s+", "", name.strip().lower())
    name = name.removeprefix("and ").strip()
    return _ALIASES.get(name, name)


def parse_figures(text: str) -> Figures:
    """Extract changes ('X changed from a to b') and levels ('X is v') from scenario sentences."""
    changes: dict[str, tuple[float, float]] = {}
    levels: dict[str, float] = {}
    previous: dict[str, float] = {}
    for sentence in re.split(r"(?<=Cr)\.\s*", text):
        for match in _CHANGE.finditer(sentence):
            changes[_clean(match.group("name"))] = (float(match.group("a")), float(match.group("b")))
        remainder = _CHANGE.sub("", sentence)
        for clause in re.split(r",\s*(?:and\s+)?|\s+and\s+", remainder):
            for match in _STATIC.finditer(clause):
                name = _clean(match.group("name"))
                value = float(match.group("v"))
                if name.startswith("previous-period "):
                    previous[name.removeprefix("previous-period ")] = value
                else:
                    levels[name] = value
    for name, value in previous.items():   # 'previous-period X was a' + 'X of b' = a change
        if name in levels:
            changes[name] = (value, levels.pop(name))
    return Figures(changes, levels, previous)


def _num(value: float) -> str:
    return f"{value:,.2f}".rstrip("0").rstrip(".")


def _pct(value: float) -> str:
    return f"{value:.1f}%"


def compute_facts(figures: Figures) -> list[str]:
    """Plain-language fact lines with their calculations, e.g.
    'Revenue rose 15.0% (₹180 Cr → ₹207 Cr).'"""
    facts: list[str] = []
    for name, (a, b) in figures.changes.items():
        label = name.capitalize()
        if a == 0:
            facts.append(f"{label} changed from ₹{_num(a)} Cr to ₹{_num(b)} Cr.")
            continue
        change = (b - a) / a * 100
        verb = "rose" if change > 0 else ("fell" if change < 0 else "was unchanged")
        detail = f" {_pct(abs(change))}" if change else ""
        facts.append(f"{label} {verb}{detail} (₹{_num(a)} Cr → ₹{_num(b)} Cr).")

    revenue = figures.changes.get("revenue")
    for profit_name, label in (("operating profit", "Operating margin"), ("profit", "Profit margin")):
        profit = figures.changes.get(profit_name)
        if revenue and profit and revenue[0] and revenue[1]:
            before, after = profit[0] / revenue[0] * 100, profit[1] / revenue[1] * 100
            facts.append(f"{label} moved from {_pct(before)} to {_pct(after)} "
                         f"(₹{_num(profit[0])} ÷ ₹{_num(revenue[0])} Cr → ₹{_num(profit[1])} ÷ ₹{_num(revenue[1])} Cr).")
        elif figures.current("revenue") and figures.current(profit_name) is not None:
            r, p = figures.current("revenue"), figures.current(profit_name)
            facts.append(f"{label} is {_pct(p / r * 100)} (₹{_num(p)} ÷ ₹{_num(r)} Cr).")

    ratios = [
        ("debt", "revenue", "Debt-to-revenue", False), ("cash", "debt", "Cash-to-debt", False),
        ("current assets", "current liabilities", "Current ratio", False),
        ("revenue", "total assets", "Asset turnover", False), ("net income", "total assets", "Return on assets", True),
        ("debt", "equity", "Debt-to-equity", False), ("operating expenses", "revenue", "Operating expense ratio", True),
    ]
    for top, bottom, label, as_percent in ratios:
        t, b = figures.current(top), figures.current(bottom)
        if t is None or not b:
            continue
        value = t / b
        shown = _pct(value * 100) if as_percent else f"{value:.2f}"
        facts.append(f"{label} is {shown} (₹{_num(t)} ÷ ₹{_num(b)} Cr).")
    return facts
