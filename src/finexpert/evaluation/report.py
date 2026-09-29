"""
Build a scored report from a test split + a matching predictions file.

Decoupled from generation on purpose: the notebook writes predictions
to a plain {example_id: prediction} file once, and this module (and
its tests) can be run anywhere, repeatedly, without a GPU.
"""

from collections import Counter, defaultdict

from .metrics import (
    extract_label,
    figures_are_grounded,
    is_correct_label,
    is_format_ok,
    numeric_mismatch,
)


def evaluate_example(row, prediction):
    """
    Score a single example. `row` is one test-split record with
    keys example_id/category/difficulty/user/assistant (as produced
    by the notebook's `load()` helper). `prediction` is the model's
    raw generated text for that example.
    """

    result = {
        "example_id": row["example_id"],
        "category": row["category"],
        "difficulty": row["difficulty"],
        "prediction": prediction,
        "figures_grounded": figures_are_grounded(
            prediction, row["assistant"], row["user"]
        ),
        "extra_numbers": numeric_mismatch(row["assistant"], prediction),
    }

    if row["category"] == "financial_classification":
        result["reference_label"] = extract_label(row["assistant"])
        result["predicted_label"] = extract_label(prediction)
        result["format_ok"] = is_format_ok(prediction)
        result["label_correct"] = (
            result["format_ok"]
            and is_correct_label(row["assistant"], prediction)
        )

    return result


def build_report(rows, predictions_by_id):
    """
    rows: list of test-split records.
    predictions_by_id: dict example_id -> prediction text.

    Returns a dict with per-category summaries and the full list of
    per-example results, so both "what's my headline number" and
    "which specific examples are wrong" come out of one call.
    """

    missing = [r["example_id"] for r in rows if r["example_id"] not in predictions_by_id]
    if missing:
        raise ValueError(
            f"No prediction found for {len(missing)} example(s), "
            f"e.g. {missing[:5]}"
        )

    results = [
        evaluate_example(row, predictions_by_id[row["example_id"]])
        for row in rows
    ]

    by_category = defaultdict(list)
    for r in results:
        by_category[r["category"]].append(r)

    summary = {}
    for category, items in by_category.items():
        entry = {
            "n": len(items),
            "figure_fidelity": round(
                sum(i["figures_grounded"] for i in items) / len(items), 3
            ),
            "numeric_exact": round(
                sum(not i["extra_numbers"] for i in items) / len(items), 3
            ),
        }

        if category == "financial_classification":
            entry["format_rate"] = round(
                sum(i["format_ok"] for i in items) / len(items), 3
            )
            entry["label_accuracy"] = round(
                sum(i["label_correct"] for i in items) / len(items), 3
            )

        summary[category] = entry

    misses = [
        r for r in results
        if r.get("label_correct") is False
        or not r["figures_grounded"]
        or r["extra_numbers"]
    ]

    return {
        "n_examples": len(results),
        "by_category": summary,
        "by_difficulty": {
            diff: round(
                sum(
                    r.get("label_correct", r["figures_grounded"] and not r["extra_numbers"])
                    for r in results if r["difficulty"] == diff
                )
                / max(sum(1 for r in results if r["difficulty"] == diff), 1),
                3,
            )
            for diff in sorted({r["difficulty"] for r in results})
        },
        "misses": misses,
        "results": results,
    }


def format_report(report):
    """Render a build_report() dict as a short, readable text summary."""

    lines = [f"Evaluated {report['n_examples']} examples", ""]

    for category, stats in report["by_category"].items():
        parts = [f"n={stats['n']}", f"figure_fidelity={stats['figure_fidelity']}", f"numeric_exact={stats['numeric_exact']}"]
        if "label_accuracy" in stats:
            parts.insert(1, f"label_accuracy={stats['label_accuracy']}")
            parts.insert(2, f"format_rate={stats['format_rate']}")
        lines.append(f"{category:30s} " + " | ".join(parts))

    lines.append("")
    lines.append("By difficulty (pass rate): " + str(report["by_difficulty"]))

    if report["misses"]:
        lines.append("")
        lines.append(f"{len(report['misses'])} example(s) need a look:")
        for m in report["misses"]:
            reason = []
            if m.get("label_correct") is False:
                reason.append(f"label ref={m['reference_label']} pred={m['predicted_label']}")
            if not m["figures_grounded"]:
                reason.append("invented currency figure")
            if m["extra_numbers"]:
                reason.append(f"number mismatch: {m['extra_numbers']}")
            lines.append(f"  {m['example_id']:16s} {m['category']:28s} {'; '.join(reason)}")

    return "\n".join(lines)
