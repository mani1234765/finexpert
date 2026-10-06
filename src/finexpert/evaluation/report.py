"""Evaluation orchestration and report aggregation.

Semantic evaluation is intentionally not implemented here.  This report only
aggregates deterministic evaluators whose checks can be explained from source
values or explicitly defined output structure.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from .classification_metrics import classification_metrics
from .context import EvaluationContext
from .evaluators import (
    GroundingEvaluator,
    LabelEvaluator,
    NumericalEvaluator,
    StructuralEvaluator,
)
from .finding import Finding


EVALUATORS = (
    LabelEvaluator(),
    GroundingEvaluator(),
    NumericalEvaluator(),
    StructuralEvaluator(),
)

SEMANTIC_EVALUATION_STATUS = {
    "status": "deferred",
    "reason": (
        "No validated semantic rubric is implemented yet. An LLM-as-judge or "
        "similar proxy could appear to measure meaning while mainly measuring "
        "style or agreement, so semantic scoring is deferred until a testable "
        "rubric and validation protocol exist."
    ),
}


def _text_from_row(row: dict[str, Any], index: int) -> str:
    messages = row.get("messages")
    if isinstance(messages, list) and len(messages) > index:
        content = messages[index].get("content")
        if isinstance(content, str):
            return content

    if index == 1 and isinstance(row.get("user"), str):
        return row["user"]
    if index == 2 and isinstance(row.get("assistant"), str):
        return row["assistant"]

    raise ValueError(
        f"Row {row.get('example_id', '<unknown>')} does not contain the expected text fields."
    )


def _prediction_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        generated = value.get("generated")
        if isinstance(generated, str):
            return generated
        prediction = value.get("prediction")
        if isinstance(prediction, str):
            return prediction
    raise ValueError("Prediction must be a string or an object containing 'generated'/'prediction'.")


def context_from_row(row: dict[str, Any], prediction: Any) -> EvaluationContext:
    return EvaluationContext(
        example_id=row["example_id"],
        category=row["category"],
        difficulty=row["difficulty"],
        source_text=_text_from_row(row, 1),
        expected_text=_text_from_row(row, 2),
        prediction_text=_prediction_text(prediction),
    )


def evaluate_example(row: dict[str, Any], prediction: Any) -> dict[str, Any]:
    context = context_from_row(row, prediction)
    findings: list[Finding] = []
    for evaluator in EVALUATORS:
        findings.extend(evaluator.evaluate(context))

    return {
        "example_id": context.example_id,
        "category": context.category,
        "difficulty": context.difficulty,
        # Diagnostic only: a verbatim copy of the reference is not a quality
        # metric, but a high rate shows the model reproducing templates.
        "reference_exact_match": context.prediction_text.strip() == context.expected_text.strip(),
        "findings": [finding.to_dict() for finding in findings],
    }


def _summary_findings(result: dict[str, Any], evaluator: str) -> list[dict[str, Any]]:
    return [
        finding
        for finding in result["findings"]
        if finding["evaluator"] == evaluator and finding["level"] == "summary"
    ]


def _aggregate_numeric(results: list[dict[str, Any]]) -> dict[str, Any]:
    summaries = []
    for result in results:
        summaries.extend(_summary_findings(result, "numerical"))

    expected = sum(f["details"]["expected_claim_count"] for f in summaries)
    generated = sum(f["details"]["generated_claim_count"] for f in summaries)
    valid = sum(f["details"]["valid_generated_claim_count"] for f in summaries)
    matched = sum(f["details"]["matched_expected_claim_count"] for f in summaries)

    return {
        "expected_claims": expected,
        "generated_claims": generated,
        "valid_generated_claims": valid,
        "matched_expected_claims": matched,
        "numeric_precision": valid / generated if generated else None,
        "numeric_recall": matched / expected if expected else None,
    }


def _aggregate_label(results: list[dict[str, Any]]) -> dict[str, Any] | None:
    items = []
    for result in results:
        items.extend(_summary_findings(result, "label"))
    if not items:
        return None
    return {
        "n": len(items),
        "accuracy": sum(item["passed"] for item in items) / len(items),
    }


def _label_pairs(results: list[dict[str, Any]]) -> list[tuple[str, str | None]]:
    pairs = []
    for result in results:
        for item in _summary_findings(result, "label"):
            expected = item["details"].get("expected_label")
            if expected is not None:
                pairs.append((expected, item["details"].get("predicted_label")))
    return pairs


def _classification_breakdown(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Accuracy by expected label, and by difficulty x expected label."""
    by_label: defaultdict[str, list[bool]] = defaultdict(list)
    by_difficulty_label: defaultdict[str, list[bool]] = defaultdict(list)
    for result in results:
        for item in _summary_findings(result, "label"):
            expected = item["details"].get("expected_label")
            if expected is None:
                continue
            by_label[expected].append(item["passed"])
            by_difficulty_label[f"{result['difficulty']} | {expected}"].append(item["passed"])

    def summarize(groups: dict[str, list[bool]]) -> dict[str, Any]:
        return {
            key: {"n": len(values), "correct": sum(values), "accuracy": sum(values) / len(values)}
            for key, values in sorted(groups.items())
        }

    return {
        "by_expected_label": summarize(by_label),
        "by_difficulty_and_label": summarize(by_difficulty_label),
    }


def _aggregate_grounding(results: list[dict[str, Any]]) -> dict[str, Any]:
    items = []
    for result in results:
        items.extend(_summary_findings(result, "grounding"))
    return {
        "n": len(items),
        "figure_fidelity": sum(item["passed"] for item in items) / len(items) if items else None,
    }


def _aggregate_structure(results: list[dict[str, Any]]) -> dict[str, Any] | None:
    items = []
    for result in results:
        items.extend(_summary_findings(result, "structural"))
    if not items:
        return None
    return {
        "n": len(items),
        "section_coverage": (
            sum(item["details"]["coverage"] for item in items) / len(items)
        ),
        "complete_reports": sum(item["passed"] for item in items) / len(items),
    }


def _failure_breakdown(results: list[dict[str, Any]]) -> dict[str, Any]:
    codes: Counter[str] = Counter()
    missing_metrics: Counter[str] = Counter()
    classification_errors = []
    structural_errors = []

    for result in results:
        for finding in result["findings"]:
            if finding["level"] == "detail" and not finding["passed"]:
                codes[finding["code"]] += 1

                if finding["code"] == "MISSING_EXPECTED_METRIC":
                    metric = finding["details"]["claim"]["metric"]
                    missing_metrics[metric] += 1

        label_items = _summary_findings(result, "label")
        for item in label_items:
            if not item["passed"]:
                classification_errors.append({
                    "example_id": result["example_id"],
                    "expected": item["details"].get("expected_label"),
                    "generated": item["details"].get("predicted_label"),
                })

        structural_items = _summary_findings(result, "structural")
        for item in structural_items:
            if not item["passed"]:
                structural_errors.append({
                    "example_id": result["example_id"],
                    "missing_sections": item["details"]["missing_sections"],
                    "coverage": item["details"]["coverage"],
                })

    return {
        "finding_codes": dict(codes),
        "missing_expected_metrics": dict(missing_metrics),
        "classification_errors": classification_errors,
        "structural_errors": structural_errors,
    }


def _summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    by_category: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    by_difficulty: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    by_category_difficulty: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)

    for result in results:
        by_category[result["category"]].append(result)
        by_difficulty[result["difficulty"]].append(result)
        by_category_difficulty[f"{result['category']} | {result['difficulty']}"].append(result)

    numeric = _aggregate_numeric(results)
    label = _aggregate_label(results)
    grounding = _aggregate_grounding(results)
    structure = _aggregate_structure(results)

    def category_summary(items: list[dict[str, Any]]) -> dict[str, Any]:
        result = {
            "examples": len(items),
            "grounding": _aggregate_grounding(items),
            "numerical": _aggregate_numeric(items),
            "structure": _aggregate_structure(items),
            "classification": _aggregate_label(items),
        }
        return result

    return {
        "examples": len(results),
        "grounding": grounding,
        "numerical": numeric,
        "classification": label,
        "structure": structure,
        "by_category": {
            category: category_summary(items)
            for category, items in sorted(by_category.items())
        },
        "by_difficulty": {
            difficulty: category_summary(items)
            for difficulty, items in sorted(by_difficulty.items())
        },
        "by_category_and_difficulty": {
            key: category_summary(items)
            for key, items in sorted(by_category_difficulty.items())
        },
        "classification_metrics": classification_metrics(_label_pairs(results)),
        "classification_breakdown": _classification_breakdown(results),
        "reference_exact_match_rate": (
            sum(result["reference_exact_match"] for result in results) / len(results)
            if results else None
        ),
        "failure_breakdown": _failure_breakdown(results),
        "semantic_evaluation": SEMANTIC_EVALUATION_STATUS,
    }


def build_report(rows: list[dict[str, Any]], predictions_by_id: dict[str, Any]) -> dict[str, Any]:
    missing = [row["example_id"] for row in rows if row["example_id"] not in predictions_by_id]
    extra = [example_id for example_id in predictions_by_id if example_id not in {row["example_id"] for row in rows}]

    if missing:
        raise ValueError(f"Missing predictions: {missing[:5]}")
    if extra:
        raise ValueError(f"Unknown prediction IDs: {extra[:5]}")

    results = [
        evaluate_example(row, predictions_by_id[row["example_id"]])
        for row in rows
    ]

    return {
        "evaluation_config": {
            "framework": "Finding-based deterministic evaluators",
            "evaluators": [evaluator.name for evaluator in EVALUATORS],
            "semantic_evaluation": SEMANTIC_EVALUATION_STATUS,
            "number_validation": "recompute-from-input",
            "section_validation": "reference-template coverage with canonical aliases",
        },
        "summary": _summarize(results),
        "examples": results,
    }


def format_report(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "============================================================",
        "                  FINEXPERT EVALUATION",
        "============================================================",
        f"\nExamples: {summary['examples']}",
    ]

    grounding = summary["grounding"]
    if grounding and grounding["figure_fidelity"] is not None:
        lines.append(f"Figure fidelity:      {grounding['figure_fidelity'] * 100:.2f}%")

    numerical = summary["numerical"]
    if numerical["numeric_precision"] is not None:
        lines.append(f"Numeric precision:    {numerical['numeric_precision'] * 100:.2f}%")
    if numerical["numeric_recall"] is not None:
        lines.append(f"Numeric recall:       {numerical['numeric_recall'] * 100:.2f}%")

    classification = summary["classification"]
    if classification:
        lines.append(f"Classification acc.:  {classification['accuracy'] * 100:.2f}%")

    structure = summary["structure"]
    if structure:
        lines.append(f"Section coverage:     {structure['section_coverage'] * 100:.2f}%")

    lines.append("Semantic evaluation:  deferred")
    if summary.get("reference_exact_match_rate") is not None:
        lines.append(
            f"Verbatim ref. match: {summary['reference_exact_match_rate'] * 100:.2f}%  (diagnostic, not a quality score)"
        )

    metrics = summary.get("classification_metrics")
    if metrics:
        low, high = metrics["accuracy_ci95"]
        lines.append("\n------------ CLASSIFICATION ------------")
        lines.append(
            f"Accuracy:     {metrics['accuracy'] * 100:.2f}%  ({metrics['correct']}/{metrics['n']}, "
            f"95% CI {low * 100:.1f}-{high * 100:.1f}%)"
        )
        lines.append(
            "Macro    P/R/F1: "
            + " / ".join(f"{metrics['macro'][m]:.3f}" for m in ("precision", "recall", "f1"))
        )
        lines.append(
            "Weighted P/R/F1: "
            + " / ".join(f"{metrics['weighted'][m]:.3f}" for m in ("precision", "recall", "f1"))
        )
        lines.append(f"\n  {'label':<15}{'P':>7}{'R':>7}{'F1':>7}{'support':>9}")
        for label, values in metrics["per_label"].items():
            lines.append(
                f"  {label:<15}{values['precision']:>7.3f}{values['recall']:>7.3f}"
                f"{values['f1']:>7.3f}{values['support']:>9}"
            )
        matrix = metrics["confusion_matrix"]
        short = {"Healthy": "Healthy", "Moderate Risk": "Moderate", "High Risk": "High", "<missing>": "Missing"}
        lines.append("\n  Confusion matrix (rows = expected, cols = predicted)")
        lines.append("  " + " " * 15 + "".join(f"{short[c]:>10}" for c in matrix["columns_predicted"]))
        for label, row in zip(matrix["rows_expected"], matrix["counts"]):
            lines.append(f"  {label:<15}" + "".join(f"{count:>10}" for count in row))

    lines.append("\n---------------- BY TASK ----------------")
    for category, values in summary["by_category"].items():
        lines.append(f"\n{category}")
        lines.append(f"  Examples:            {values['examples']}")
        if values["grounding"]["figure_fidelity"] is not None:
            lines.append(f"  Figure fidelity:     {values['grounding']['figure_fidelity'] * 100:.2f}%")
        if values["numerical"]["numeric_precision"] is not None:
            lines.append(f"  Numeric precision:   {values['numerical']['numeric_precision'] * 100:.2f}%")
        if values["numerical"]["numeric_recall"] is not None:
            lines.append(f"  Numeric recall:      {values['numerical']['numeric_recall'] * 100:.2f}%")
        if values["classification"]:
            lines.append(f"  Classification acc.: {values['classification']['accuracy'] * 100:.2f}%")
        if values["structure"]:
            lines.append(f"  Section coverage:    {values['structure']['section_coverage'] * 100:.2f}%")

    lines.append("\n------------- BY DIFFICULTY -------------")
    for difficulty, values in summary["by_difficulty"].items():
        parts = [f"n={values['examples']}"]
        if values["grounding"]["figure_fidelity"] is not None:
            parts.append(f"fidelity={values['grounding']['figure_fidelity'] * 100:.1f}%")
        if values["numerical"]["numeric_recall"] is not None:
            parts.append(f"num_recall={values['numerical']['numeric_recall'] * 100:.1f}%")
        if values["classification"]:
            parts.append(f"cls_acc={values['classification']['accuracy'] * 100:.1f}%")
        lines.append(f"{difficulty:<8}" + "  ".join(parts))

    breakdown = summary.get("classification_breakdown") or {}
    if breakdown.get("by_difficulty_and_label"):
        lines.append("\n------- CLASSIFICATION: DIFFICULTY x LABEL -------")
        for key, values in breakdown["by_difficulty_and_label"].items():
            lines.append(f"{key:<26}{values['correct']}/{values['n']}")

    failures = summary["failure_breakdown"]
    lines.append("\n------------- ERROR BREAKDOWN -------------")
    if failures["finding_codes"]:
        for code, count in sorted(failures["finding_codes"].items()):
            lines.append(f"{code:<40}{count}")
    else:
        lines.append("No failing detail findings.")

    if failures["missing_expected_metrics"]:
        lines.append("\nMissing expected quantitative metrics:")
        for metric, count in sorted(failures["missing_expected_metrics"].items()):
            lines.append(f"{metric:<30}{count}")

    if failures["classification_errors"]:
        lines.append("\nClassification errors:")
        for error in failures["classification_errors"]:
            lines.append(
                f"{error['example_id']}: {error['expected']} -> {error['generated']}"
            )

    if failures["structural_errors"]:
        lines.append("\nStructural errors:")
        for error in failures["structural_errors"]:
            lines.append(
                f"{error['example_id']}: missing={error['missing_sections']} "
                f"coverage={error['coverage']:.2f}"
            )

    lines.append("\n============================================================")
    return "\n".join(lines)


def evaluate(test_file: str | Path, predictions_file: str | Path, report_file: str | Path) -> dict[str, Any]:
    def load_jsonl(path: str | Path) -> list[dict[str, Any]]:
        rows = []
        with Path(path).open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    raise ValueError(f"Invalid JSON at {path}:{line_number}") from exc
        return rows

    rows = load_jsonl(test_file)
    prediction_rows = load_jsonl(predictions_file)
    predictions = {}
    for row in prediction_rows:
        example_id = row["example_id"]
        if example_id in predictions:
            raise ValueError(f"Duplicate prediction ID: {example_id}")
        predictions[example_id] = row

    report = build_report(rows, predictions)
    output = Path(report_file)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report
