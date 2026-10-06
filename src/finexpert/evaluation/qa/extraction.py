"""Pull the final answer out of a model response.

Two modes are reported side by side:

* strict  - the answer must be on a line starting with "Answer:" (the trained
  format; the last such line wins). Headline numbers use strict.
* lenient - if there is no Answer line, fall back to "the answer is X" or the
  last number in the text. This keeps base or prompted models from scoring
  zero purely on format, so format and reasoning failures can be told apart.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_ANSWER_LINE = re.compile(r"^\W*answer\W*:\s*(?P<answer>.+?)\s*$", re.IGNORECASE | re.MULTILINE)
_ANSWER_IS = re.compile(r"\banswer\s+is\s*:?\s*(?P<answer>[^\n]+)", re.IGNORECASE)
_NUMBER = re.compile(r"\(?-?\$?\s*\d[\d,]*(?:\.\d+)?\s*%?\)?")
_SCALES = ("thousand", "million", "billion")


@dataclass(frozen=True)
class Extracted:
    text: str | None
    method: str  # "answer_line" | "answer_is" | "last_number" | "none"


def extract_answer(response: str | None, lenient: bool = False) -> Extracted:
    response = (response or "").strip()
    matches = list(_ANSWER_LINE.finditer(response))
    if matches:
        return Extracted(_clean(matches[-1].group("answer")), "answer_line")
    if lenient:
        matches = list(_ANSWER_IS.finditer(response))
        if matches:
            return Extracted(_clean(matches[-1].group("answer")), "answer_is")
        numbers = _NUMBER.findall(response)
        if numbers:
            return Extracted(numbers[-1].strip(), "last_number")
    return Extracted(None, "none")


def _clean(text: str) -> str:
    """Remove markdown emphasis only; scorers handle punctuation themselves."""
    return text.strip().strip("*_`").strip()


@dataclass(frozen=True)
class ParsedNumber:
    value: float
    is_percent: bool
    scale: str  # "", "thousand", "million", "billion", "percent"


def parse_number(text: str | None) -> ParsedNumber | None:
    """'$1,234.5 million' -> 1234.5 million; '(12.5)%' -> -12.5 percent; '−3' -> -3."""
    if not text:
        return None
    cleaned = text.lower().replace("−", "-").replace("–", "-").replace(",", "").replace("$", "").strip()
    scale = ""
    for word in _SCALES:
        if re.search(rf"\b{word}s?\b", cleaned):
            scale = word
            cleaned = re.sub(rf"\b{word}s?\b", "", cleaned).strip()
    is_percent = "%" in cleaned or bool(re.search(r"\bpercent\b", cleaned))
    cleaned = cleaned.replace("%", "").replace("percent", "").strip().rstrip(".").strip()
    negative = cleaned.startswith("(") and cleaned.endswith(")")
    match = re.search(r"-?\d+(?:\.\d+)?", cleaned)
    if not match:
        return None
    value = float(match.group(0))
    if negative and value > 0:
        value = -value
    return ParsedNumber(value, is_percent, "percent" if is_percent else scale)


def split_answer_and_scale(text: str | None) -> tuple[list[str], str]:
    """'Answer' text -> (answer strings, scale) in the form TAT-QA's official scorer expects.

    '13.91%' -> (['13.91'], 'percent'); '582 thousand' -> (['582'], 'thousand');
    'A; B; C' -> (['A', 'B', 'C'], '').
    """
    if not text:
        return [], ""
    parts = [p.strip() for p in text.split(";") if p.strip()]
    scale = ""
    cleaned = []
    for part in parts:
        lowered = part.lower()
        if lowered.endswith("%"):
            scale, part = "percent", part[:-1].strip()
        else:
            for word in _SCALES:
                if re.search(rf"\s{word}s?$", lowered):
                    scale, part = word, re.sub(rf"\s{word}s?$", "", part, flags=re.IGNORECASE).strip()
                    break
        cleaned.append(part)
    return cleaned, scale
