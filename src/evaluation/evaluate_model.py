import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

DEFAULT_TEST_FILE = Path("data/sft/test.jsonl")
DEFAULT_PREDICTIONS_FILE = Path("data/evaluation/test_predictions.jsonl")
DEFAULT_REPORT_FILE = Path("data/evaluation/evaluation_report.json")

ALIASES = {
    "operating profit": "operating_profit",
    "net profit": "net_profit",
    "cash flow": "cash_flow",
    "cash reserves": "cash",
    "operating expenses": "operating_expenses",
    "revenue": "revenue",
    "profit": "profit",
    "earnings": "earnings",
    "expenses": "expenses",
    "debt": "debt",
    "cash": "cash",
    "total assets": "total_assets",
    "net income": "net_income",
    "equity": "equity",
}

VALUE_RE = re.compile(
    r"(?P<metric>operating expenses|operating profit|net profit|cash flow|cash reserves|revenue|profit|earnings|expenses|debt|cash)"
    r"\s+(?P<direction>increased|increases|grew|rose|declined|decreased|decreases|fell|dropped|drop|changed)"
    r"\s+from\s+₹?\s*(?P<old>\d+(?:\.\d+)?)\s*(?:Cr|crore|crores|Lakh|Lakhs|Million|Billion)?"
    r"\s+to\s+₹?\s*(?P<new>\d+(?:\.\d+)?)\s*(?:Cr|crore|crores|Lakh|Lakhs|Million|Billion)?",
    re.I,
)

PCT_RE = re.compile(
    r"(?P<metric>operating profit|net profit|cash flow|operating expenses|revenue|profit|earnings|expenses|debt|cash)"
    r"\s+(?P<direction>increased|increases|grew|rose|declined|decreased|decreases|fell|dropped|drop|changed)"
    r"\s+by\s+(?P<value>-?\d+(?:\.\d+)?)\s*%",
    re.I,
)

RATIO_RE = re.compile(
    r"(?P<metric>debt-to-equity|debt-to-revenue|current ratio|asset turnover|cash-to-debt|return on assets|return on equity|operating margin|net profit margin|profit margin)"
    r"(?:\s+ratio)?\s+(?:is|was|equals|of)\s+(?P<value>-?\d+(?:\.\d+)?)\s*%?",
    re.I,
)

LABEL_RE = re.compile(
    r"classification\s*:\s*(healthy|moderate\s+risk|high\s+risk)",
    re.I,
)

SECTION_RE = re.compile(
    r"(?im)^\s*(Executive Summary|Quantitative Analysis|Key Observations|Potential Risks and Opportunities|Risks and Opportunities|Areas Requiring Further Investigation|Conclusion)\s*:"
)


def load_jsonl(path):
    records = []
    with Path(path).open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON at {path}:{line_no}") from exc
    return records


def normalize_metric(metric):
    metric = re.sub(r"\s+", " ", metric.strip().lower())
    return ALIASES.get(metric, metric.replace("-", "_"))


def extract_label(text):
    m = LABEL_RE.search(text)
    if not m:
        return None
    value = re.sub(r"\s+", " ", m.group(1).strip()).lower()
    return {"healthy": "Healthy", "moderate risk": "Moderate Risk", "high risk": "High Risk"}[value]


def extract_claims(text):
    claims = []
    for m in VALUE_RE.finditer(text):
        claims.append({
            "type": "value_change",
            "metric": normalize_metric(m.group("metric")),
            "old": float(m.group("old")),
            "new": float(m.group("new")),
        })
    for m in PCT_RE.finditer(text):
        value = float(m.group("value"))
        if m.group("direction").lower() in {"declined", "decreased", "decreases", "fell", "dropped", "drop"}:
            value = -abs(value)
        else:
            value = abs(value)
        claims.append({
            "type": "percentage_change",
            "metric": normalize_metric(m.group("metric")),
            "value": value,
        })
    for m in RATIO_RE.finditer(text):
        claims.append({
            "type": "ratio",
            "metric": normalize_metric(m.group("metric")),
            "value": float(m.group("value")),
        })
    return claims


def close(a, b, tol=0.11):
    return abs(float(a) - float(b)) <= tol


def claim_match(a, b):
    if a["type"] != b["type"] or a["metric"] != b["metric"]:
        return False
    if a["type"] == "value_change":
        return close(a["old"], b["old"]) and close(a["new"], b["new"])
    return close(a["value"], b["value"])


def compare_claims(expected, generated):
    used = set()
    matched = 0
    for exp in expected:
        for i, got in enumerate(generated):
            if i in used:
                continue
            if claim_match(exp, got):
                used.add(i)
                matched += 1
                break
    return matched, used


def section_score(expected, generated):
    e = {x.lower() for x in SECTION_RE.findall(expected)}
    g = {x.lower() for x in SECTION_RE.findall(generated)}
    return 1.0 if not e else len(e & g) / len(e)


def evaluate_one(reference, prediction):
    expected = reference["messages"][2]["content"]
    generated = prediction["generated"]
    exp_claims = extract_claims(expected)
    gen_claims = extract_claims(generated)
    matched, used = compare_claims(exp_claims, gen_claims)
    numerical = matched / len(exp_claims) if exp_claims else 1.0
    grounding = len(used) / len(gen_claims) if gen_claims else (1.0 if not exp_claims else 0.0)
    expected_label = extract_label(expected)
    generated_label = extract_label(generated)
    class_correct = None
    if reference["category"] == "financial_classification":
        class_correct = expected_label is not None and expected_label == generated_label

    sections = section_score(expected, generated)
    category = reference["category"]
    if category == "financial_classification":
        semantic = 0.70 * numerical + 0.30 * (1.0 if class_correct else 0.0)
    elif category == "financial_explanation":
        semantic = 0.85 * numerical + 0.15 * grounding
    elif category == "financial_report_generation":
        semantic = 0.70 * numerical + 0.20 * sections + 0.10 * grounding
    else:
        semantic = numerical

    return {
        "example_id": reference["example_id"],
        "category": category,
        "difficulty": reference["difficulty"],
        "numerical_accuracy": numerical,
        "grounding": grounding,
        "section_score": sections,
        "expected_classification": expected_label,
        "generated_classification": generated_label,
        "classification_correct": class_correct,
        "semantic_score": semantic,
        "expected_claims": exp_claims,
        "generated_claims": gen_claims,
    }


def evaluate(test_file, predictions_file, report_file):
    refs = load_jsonl(test_file)
    preds = load_jsonl(predictions_file)
    pred_map = {x["example_id"]: x for x in preds}
    ref_ids = {x["example_id"] for x in refs}
    pred_ids = set(pred_map)
    missing = sorted(ref_ids - pred_ids)
    extra = sorted(pred_ids - ref_ids)
    if missing:
        raise ValueError("Missing predictions: " + ", ".join(missing))
    if extra:
        raise ValueError("Unknown prediction IDs: " + ", ".join(extra))

    results = [evaluate_one(ref, pred_map[ref["example_id"]]) for ref in refs]

    by_cat = defaultdict(list)
    by_diff = defaultdict(list)
    for r in results:
        by_cat[r["category"]].append(r)
        by_diff[r["difficulty"]].append(r)

    def avg(items, key):
        return sum(x[key] for x in items) / len(items) if items else 0.0

    class_items = [r for r in results if r["classification_correct"] is not None]
    summary = {
        "examples": len(results),
        "semantic_score": avg(results, "semantic_score"),
        "numerical_accuracy": avg(results, "numerical_accuracy"),
        "grounding": avg(results, "grounding"),
        "section_score": avg(results, "section_score"),
        "classification_accuracy": (
            sum(r["classification_correct"] for r in class_items) / len(class_items)
            if class_items else None
        ),
        "by_category": {
            cat: {
                "count": len(items),
                "semantic_score": avg(items, "semantic_score"),
                "numerical_accuracy": avg(items, "numerical_accuracy"),
                "grounding": avg(items, "grounding"),
                "section_score": avg(items, "section_score"),
            }
            for cat, items in sorted(by_cat.items())
        },
        "by_difficulty": {
            diff: {
                "count": len(items),
                "semantic_score": avg(items, "semantic_score"),
                "numerical_accuracy": avg(items, "numerical_accuracy"),
            }
            for diff, items in sorted(by_diff.items())
        },
    }

    for cat, items in by_cat.items():
        class_items = [r for r in items if r["classification_correct"] is not None]
        if class_items:
            summary["by_category"][cat]["classification_accuracy"] = (
                sum(r["classification_correct"] for r in class_items) / len(class_items)
            )

    report = {"summary": summary, "examples": results}
    report_file = Path(report_file)
    report_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def print_report(report):
    s = report["summary"]
    print("\n============================================================")
    print("                 FINEXPERT EVALUATION")
    print("============================================================")
    print(f"\nExamples:             {s['examples']}")
    print(f"Semantic score:       {s['semantic_score'] * 100:.2f}%")
    print(f"Numerical accuracy:   {s['numerical_accuracy'] * 100:.2f}%")
    print(f"Grounding:            {s['grounding'] * 100:.2f}%")
    print(f"Section coverage:     {s['section_score'] * 100:.2f}%")
    if s["classification_accuracy"] is not None:
        print(f"Classification acc.:  {s['classification_accuracy'] * 100:.2f}%")

    print("\n---------------- BY TASK ----------------")
    for cat, v in s["by_category"].items():
        print(f"\n{cat}")
        print(f"  Examples:           {v['count']}")
        print(f"  Semantic score:     {v['semantic_score'] * 100:.2f}%")
        print(f"  Numerical accuracy: {v['numerical_accuracy'] * 100:.2f}%")
        print(f"  Grounding:          {v['grounding'] * 100:.2f}%")
        if "classification_accuracy" in v:
            print(f"  Classification acc.: {v['classification_accuracy'] * 100:.2f}%")
        if cat == "financial_report_generation":
            print(f"  Section coverage:   {v['section_score'] * 100:.2f}%")

    print("\n---------------- BY DIFFICULTY ------------")
    for diff, v in s["by_difficulty"].items():
        print(f"{diff:<10} semantic={v['semantic_score'] * 100:.2f}%  numerical={v['numerical_accuracy'] * 100:.2f}%")
    print("\n============================================================")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", default=str(DEFAULT_TEST_FILE))
    parser.add_argument("--predictions", default=str(DEFAULT_PREDICTIONS_FILE))
    parser.add_argument("--output", default=str(DEFAULT_REPORT_FILE))
    args = parser.parse_args()
    print_report(evaluate(args.test, args.predictions, args.output))
