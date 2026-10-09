"""Paired comparison of two evaluation runs on the same questions.

Why paired: both models answer the *same* questions, so the right question is
"on the questions where the two models disagree, does one win more often than
chance?". McNemar's exact test answers exactly that, using only the
discordant pairs:

    b = questions model A got right and model B got wrong
    c = questions model A got wrong and model B got right

Under "no difference", each discordant question is a fair coin flip, so the
smaller of b and c follows Binomial(b + c, 0.5). Comparing two independent
accuracies (and their separate confidence intervals) instead throws away the
pairing and is far less sensitive.
"""

from __future__ import annotations

import math
from typing import Any


def mcnemar_exact(b: int, c: int) -> float:
    """Two-sided exact McNemar p-value from the two discordant counts."""
    n = b + c
    if n == 0:
        return 1.0
    tail = sum(math.comb(n, i) for i in range(min(b, c) + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def _correct_by_id(report: dict[str, Any], source: str) -> dict[str, bool]:
    return {e["example_id"]: bool(e["strict"]["correct"]) for e in report["examples"] if e["source"] == source}


def compare_qa_reports(report_a: dict[str, Any], report_b: dict[str, Any], source: str) -> dict[str, Any]:
    """Paired comparison of two QA reports on one source (finqa or tatqa), strict scoring."""
    a, b = _correct_by_id(report_a, source), _correct_by_id(report_b, source)
    if set(a) != set(b):
        raise ValueError(f"{source}: the two reports cover different questions; a paired comparison needs identical ones")
    ids = sorted(a)
    a_only = sum(a[i] and not b[i] for i in ids)
    b_only = sum(b[i] and not a[i] for i in ids)
    n = len(ids)
    return {
        "source": source, "n": n,
        "accuracy_a": sum(a.values()) / n, "accuracy_b": sum(b.values()) / n,
        "difference_b_minus_a": (sum(b.values()) - sum(a.values())) / n,
        "both_right": sum(a[i] and b[i] for i in ids), "both_wrong": sum(not a[i] and not b[i] for i in ids),
        "a_right_b_wrong": a_only, "a_wrong_b_right": b_only,
        "p_value": mcnemar_exact(a_only, b_only),
    }


def _format_p(p: float) -> str:
    return "< 0.0001" if p < 0.0001 else f"{p:.4f}"


def format_comparison(rows: list[dict[str, Any]], name_a: str, name_b: str) -> str:
    """Markdown table of paired comparisons."""
    lines = [f"| Source | n | {name_a} | {name_b} | Difference | {name_a} only right | {name_b} only right | McNemar p |",
             "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['source']} | {r['n']} | {r['accuracy_a'] * 100:.1f}% | {r['accuracy_b'] * 100:.1f}% | "
                     f"{r['difference_b_minus_a'] * 100:+.1f} pts | {r['a_right_b_wrong']} | {r['a_wrong_b_right']} | "
                     f"{_format_p(r['p_value'])} |")
    return "\n".join(lines)
