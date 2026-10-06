"""Per-example scoring for FinQA and TAT-QA.

FinQA - answer accuracy against the executed gold program result, accepting
ratio/percent equivalence (0.1446 == 14.46%); yes/no must match exactly.
A number is correct if it is within 0.1% of the gold value, or equals the
gold value rounded to the precision the model wrote, as long as that
precision is fine enough for the number (half a unit of the last written
digit is at most 5% of the value: "14%" for 14.46 counts, "0" for 0.3 does
not). Published FinQA numbers usually score generated programs
(execution accuracy); this scores final answers, and reports say so.

TAT-QA - the official TaTQAEmAndF1 scorer from the TAT-QA repository,
called per question exactly as its tatqa_eval.py does, so EM/F1 are
directly comparable to published results.
"""

from __future__ import annotations

import importlib
import json
import re
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any

from .extraction import extract_answer, parse_number, split_answer_and_scale

REL_TOLERANCE = 0.001
MAX_ROUNDING_SHARE = 0.05


def _decimals(text: str) -> int:
    match = re.search(r"\d+(?:\.(\d+))?", text.replace(",", ""))
    return len(match.group(1)) if match and match.group(1) else 0


def _close(predicted: float, gold: float, predicted_text: str) -> bool:
    tolerance = REL_TOLERANCE * abs(gold)
    rounding = 0.5 * 10 ** (-_decimals(predicted_text))
    if rounding <= MAX_ROUNDING_SHARE * abs(gold):
        tolerance = max(tolerance, rounding)
    return abs(predicted - gold) <= tolerance + 1e-9


def score_finqa(prediction: str | None, gold: dict[str, Any], lenient: bool = False) -> dict[str, Any]:
    extracted = extract_answer(prediction, lenient=lenient)
    result = {"extracted": extracted.text, "method": extracted.method, "correct": False}
    if extracted.text is None:
        return result
    gold_value = gold["value"]
    if isinstance(gold_value, str):  # yes / no
        word = extracted.text.strip().lower().split()[0].strip(".,") if extracted.text.strip() else ""
        result["correct"] = word == gold_value.lower()
        return result
    parsed = parse_number(extracted.text)
    if parsed is None:
        return result
    gold_value = float(gold_value)
    candidates = (gold_value, gold_value * 100, gold_value / 100)
    result["correct"] = any(_close(parsed.value, candidate, extracted.text) for candidate in candidates)
    return result


# ---------------------------------------------------------------- TAT-QA

@lru_cache(maxsize=1)
def _official_tatqa(tatqa_dir: str):
    """Import the official scorer module from the cloned TAT-QA repository."""
    if not (Path(tatqa_dir) / "tatqa_metric.py").exists():
        raise FileNotFoundError(f"{tatqa_dir}/tatqa_metric.py not found; clone TAT-QA first")
    if tatqa_dir not in sys.path:
        sys.path.insert(0, tatqa_dir)
    try:
        return importlib.import_module("tatqa_metric")
    except ModuleNotFoundError as error:
        raise ModuleNotFoundError(
            f"The official TAT-QA scorer needs {error.name}; run `uv sync` (it is a dev dependency)."
        ) from error


@lru_cache(maxsize=4)
def load_tatqa_gold(tatqa_dir: str, split: str) -> dict[str, dict[str, Any]]:
    """uid -> official question annotation, read from the source files (single source of truth)."""
    filename = {"validation": "tatqa_dataset_dev.json", "test": "tatqa_dataset_test_gold.json",
                "train": "tatqa_dataset_train.json"}[split]
    contexts = json.loads((Path(tatqa_dir) / "dataset_raw" / filename).read_text(encoding="utf-8"))
    return {q["uid"]: q for context in contexts for q in context["questions"]}


def score_tatqa(prediction: str | None, annotation: dict[str, Any], tatqa_dir: str,
                lenient: bool = False) -> dict[str, Any]:
    """Official EM/F1. The same answer string can be read two ways: with a
    trailing scale split off ("13%" -> 13, percent), as literal text
    ("approximately 13%"), or as a single span that contains ";". Both readings of the model's own string are scored
    and the better one kept; the string itself is never altered beyond that."""
    extracted = extract_answer(prediction, lenient=lenient)
    best = {"em": 0.0, "f1": 0.0, "scale": "", "scale_correct": False}
    module = _official_tatqa(tatqa_dir)
    for answers, scale in _readings(extracted.text):
        metric = module.TaTQAEmAndF1()
        metric(ground_truth=annotation, prediction=answers if answers else None, pred_scale=scale)
        exact_match, f1, scale_match, _ = metric.get_overall_metric()
        if (exact_match, f1) > (best["em"], best["f1"]):
            best = {"em": float(exact_match), "f1": float(f1), "scale": scale, "scale_correct": bool(scale_match)}
        elif not answers and scale == "" and not best["scale_correct"]:
            best["scale_correct"] = bool(scale_match)
    return {"extracted": extracted.text, "method": extracted.method, "pred_scale": best["scale"],
            "em": best["em"], "f1": best["f1"], "scale_correct": best["scale_correct"],
            "correct": bool(best["em"])}


def _readings(text: str | None) -> list[tuple[list[str], str]]:
    if not text:
        return [([], "")]
    variants = [text]
    if text.endswith(".") and not text.endswith(".."):
        variants.append(text[:-1].rstrip())
    readings = []
    for variant in variants:
        readings.append(split_answer_and_scale(variant))
        readings.append(([p.strip() for p in variant.split(";") if p.strip()], ""))
        readings.append(([variant], ""))  # one span that itself contains ";"
    return readings
