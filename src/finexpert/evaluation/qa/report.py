"""Aggregate per-example QA scores into a report with confidence intervals."""

from __future__ import annotations

import random
from collections import defaultdict
from typing import Any

from ..classification_metrics import wilson_interval
from .scoring import load_tatqa_gold, score_finqa, score_tatqa

BOOTSTRAP_SAMPLES = 1000
BOOTSTRAP_SEED = 0


def _bootstrap_ci(values: list[float]) -> list[float] | None:
    if not values:
        return None
    rng = random.Random(BOOTSTRAP_SEED)
    n = len(values)
    means = sorted(sum(rng.choice(values) for _ in range(n)) / n for _ in range(BOOTSTRAP_SAMPLES))
    return [means[int(0.025 * BOOTSTRAP_SAMPLES)], means[int(0.975 * BOOTSTRAP_SAMPLES) - 1]]


def _rate(flags: list[bool]) -> dict[str, Any]:
    n, k = len(flags), sum(flags)
    return {"n": n, "correct": k, "accuracy": k / n if n else None,
            "ci95": list(wilson_interval(k, n)) if n else None}


def _group(rows: list[dict[str, Any]], key: str, metric: str) -> dict[str, Any]:
    groups: defaultdict[str, list[bool]] = defaultdict(list)
    for row in rows:
        groups[str(row[key])].append(bool(row["strict"][metric]))
    return {name: _rate(values) for name, values in sorted(groups.items())}


def score_record(record: dict[str, Any], prediction: str | None, tatqa_dir: str | None) -> dict[str, Any]:
    if record["source_type"] == "finqa":
        strict = score_finqa(prediction, record["gold"])
        lenient = score_finqa(prediction, record["gold"], lenient=True)
    elif record["source_type"] == "tatqa":
        if tatqa_dir is None:
            raise ValueError("tatqa_dir is required to score TAT-QA records")
        annotation = load_tatqa_gold(tatqa_dir, record["source_split"])[record["source_id"]]
        strict = score_tatqa(prediction, annotation, tatqa_dir)
        lenient = score_tatqa(prediction, annotation, tatqa_dir, lenient=True)
    else:
        raise ValueError(f"unknown source {record['source_type']!r}")
    return {
        "example_id": record["example_id"],
        "source": record["source_type"],
        "answer_type": record["answer_type"],
        "difficulty": record["difficulty"],
        "n_steps": record["flags"].get("n_steps"),
        "gold": record["gold"]["answer_text"],
        "has_prediction": prediction is not None,
        "strict": strict,
        "lenient": lenient,
    }


def summarize_source(rows: list[dict[str, Any]]) -> dict[str, Any]:
    source = rows[0]["source"]
    summary: dict[str, Any] = {
        "n": len(rows),
        "missing_predictions": sum(not r["has_prediction"] for r in rows),
        "strict": _rate([r["strict"]["correct"] for r in rows]),
        "lenient": _rate([r["lenient"]["correct"] for r in rows]),
        "answer_line_rate": sum(r["strict"]["method"] == "answer_line" for r in rows) / len(rows),
        "by_answer_type": _group(rows, "answer_type", "correct"),
        "by_difficulty": _group(rows, "difficulty", "correct"),
    }
    if source == "tatqa":
        f1 = [r["strict"]["f1"] for r in rows]
        summary["official"] = {
            "em": sum(r["strict"]["em"] for r in rows) / len(rows),
            "f1": sum(f1) / len(f1),
            "f1_ci95": _bootstrap_ci(f1),
            "scale_accuracy": sum(r["strict"]["scale_correct"] for r in rows) / len(rows),
            "lenient_em": sum(r["lenient"]["em"] for r in rows) / len(rows),
            "lenient_f1": sum(r["lenient"]["f1"] for r in rows) / len(rows),
        }
    if source == "finqa":
        summary["by_program_steps"] = _group(rows, "n_steps", "correct")
    return summary


def build_qa_report(records: list[dict[str, Any]], predictions: dict[str, str | None],
                    tatqa_dir: str | None = None) -> dict[str, Any]:
    rows = [score_record(r, predictions.get(r["example_id"]), tatqa_dir) for r in records]
    by_source: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_source[row["source"]].append(row)
    unknown = sorted(set(predictions) - {r["example_id"] for r in records})
    return {
        "summary": {source: summarize_source(items) for source, items in sorted(by_source.items())},
        "unmatched_prediction_ids": unknown[:50],
        "n_unmatched_predictions": len(unknown),
        "examples": rows,
    }


def format_qa_report(report: dict[str, Any]) -> str:
    def pct(x: float | None) -> str:
        return "-" if x is None else f"{x * 100:.1f}%"

    lines = ["=" * 64, "FINEXPERT QA EVALUATION", "=" * 64]
    for source, s in report["summary"].items():
        lo, hi = s["strict"]["ci95"]
        lines += ["", f"[{source}]  n={s['n']}  missing predictions={s['missing_predictions']}",
                  f"  Accuracy (strict):   {pct(s['strict']['accuracy'])}  95% CI {pct(lo)}-{pct(hi)}",
                  f"  Accuracy (lenient):  {pct(s['lenient']['accuracy'])}",
                  f"  'Answer:' line rate: {pct(s['answer_line_rate'])}"]
        if "official" in s:
            o = s["official"]
            lines += [f"  Official EM / F1:    {pct(o['em'])} / {pct(o['f1'])}  "
                      f"(F1 95% CI {pct(o['f1_ci95'][0])}-{pct(o['f1_ci95'][1])})",
                      f"  Scale accuracy:      {pct(o['scale_accuracy'])}"]
        for title, key in [("by answer type", "by_answer_type"), ("by difficulty", "by_difficulty"),
                           ("by program steps", "by_program_steps")]:
            if key in s:
                lines.append(f"  {title}: " + ", ".join(
                    f"{name} {pct(v['accuracy'])} (n={v['n']})" for name, v in s[key].items()))
    if report["n_unmatched_predictions"]:
        lines.append(f"\nWARNING: {report['n_unmatched_predictions']} prediction ids are not in the evaluated set")
    return "\n".join(lines)
