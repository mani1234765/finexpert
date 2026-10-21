"""Regression suite scoring: every observed failure type, scored on separate dimensions.

| Dimension     | Question it answers                                                                   |
|---------------|---------------------------------------------------------------------------------------|
| final_correct | Is every requested value present, in the requested unit?                              |
| formula_ok    | Do the required intermediate values appear, and none of the known wrong-formula values? |
| complete      | Did it answer every part (no missing value, even in the wrong unit)?                  |
| units_ok      | No value given in the wrong unit (e.g. 0.15 where 15% was asked for)?                 |
| behaviour_ok  | For behaviour cases: missing-data handling, advice rules, classification label        |

A case passes only if every dimension that applies to it passes.
"""

from __future__ import annotations

import re
from typing import Any

from .advice_rules import check_advice

_NUMBER = re.compile(r"(?<![\w.])-?\d{1,3}(?:,\d{2,3})+(?:\.\d+)?|(?<![\w.])-?\d+(?:\.\d+)?")
_MISSING = re.compile(r"\b(?:not\s+(?:provided|given|available|stated|included|reported)|cannot\s+be\s+(?:determined|"
                      r"calculated)|can't\s+be\s+(?:determined|calculated)|insufficient|does\s+not\s+(?:include|contain|"
                      r"provide)|no\s+(?:information|data)\s+(?:on|about|for))\b", re.IGNORECASE)
_LABEL = re.compile(r"^\W*classification\W*:\s*(Healthy|Moderate Risk|High Risk)\b", re.IGNORECASE | re.MULTILINE)


def numbers_in(text: str) -> list[tuple[float, bool]]:
    """(value, followed_by_percent) for every number; handles 1,250 and Indian 1,24,500 grouping."""
    found = []
    for match in _NUMBER.finditer(text):
        value = float(match.group(0).replace(",", ""))
        found.append((value, text[match.end():match.end() + 2].lstrip().startswith("%")))
    return found


def _close(a: float, b: float, rel: float, abs_tol: float) -> bool:
    return abs(a - b) <= max(abs_tol, rel * abs(b))


def _value_status(expected: dict[str, Any], numbers: list[tuple[float, bool]]) -> str:
    """'correct', 'unit_error' (right value, wrong scale) or 'missing'."""
    value, rel, abs_tol = expected["value"], expected.get("rel_tol", 0.002), expected.get("abs_tol", 0.006)
    if expected.get("unit") == "percent":
        if any(_close(v, value, rel, abs_tol) for v, _ in numbers):
            return "correct"
        if any(_close(v * 100, value, rel, abs_tol) for v, _ in numbers):
            return "unit_error"
        return "missing"
    return "correct" if any(_close(v, value, rel, abs_tol) for v, _ in numbers) else "missing"


def score_case(case: dict[str, Any], output: str) -> dict[str, Any]:
    output = output or ""
    checks = case["checks"]
    numbers = numbers_in(output)
    result: dict[str, Any] = {"id": case["id"], "category": case["category"]}

    if "final" in checks:
        statuses = [_value_status(expected, numbers) for expected in checks["final"]]
        result.update({"value_status": statuses,
                       "final_correct": all(s == "correct" for s in statuses),
                       "complete": all(s != "missing" for s in statuses),
                       "units_ok": "unit_error" not in statuses})
    if "required_intermediates" in checks or "forbidden_values" in checks:
        tolerance = checks.get("intermediate_rel_tol", 0.002)
        required = all(any(_close(v, x, tolerance, 0.006) for v, _ in numbers)
                       for x in checks.get("required_intermediates", []))
        forbidden = [x for x in checks.get("forbidden_values", [])
                     if any(_close(v, x, tolerance, 0.006) for v, _ in numbers)]
        result.update({"formula_ok": required and not forbidden, "forbidden_found": forbidden})

    behaviour = checks.get("behaviour")
    if behaviour == "missing_data":
        answer_lines = re.findall(r"^\W*answer\W*:\s*(.+)$", output, re.IGNORECASE | re.MULTILINE)
        gave_number = any(re.search(r"\d", line) for line in answer_lines)
        result["behaviour_ok"] = bool(_MISSING.search(output)) and not gave_number
    elif behaviour == "advice":
        verdict = check_advice(output, case["user"])
        result.update({"behaviour_ok": verdict["passed"],
                       "advice_failures": [k for k, v in verdict.items() if v is False]})
    elif behaviour == "classification":
        found = _LABEL.findall(output)
        result["behaviour_ok"] = bool(found) and found[0].lower() == checks["label"].lower()
    if checks.get("no_leaked_phrases"):
        leaked = [p for p in checks["no_leaked_phrases"] if p.lower() in output.lower()]
        result["no_leak"] = not leaked

    dimensions = [k for k in ("final_correct", "formula_ok", "complete", "units_ok", "behaviour_ok", "no_leak")
                  if k in result]
    result["passed"] = all(result[k] for k in dimensions)
    return result
