"""Regression tests for evaluator bugs found in the v1 baseline review.

The key invariant: a prediction identical to the reference must score
perfectly on every deterministic evaluator.  Before these fixes the
committed reference answers scored ~76% numeric precision/recall against
themselves.
"""

import json
from pathlib import Path

import pytest

from finexpert.evaluation.classification_metrics import (
    classification_metrics,
    wilson_interval,
)
from finexpert.evaluation.context import EvaluationContext
from finexpert.evaluation.evaluators import GroundingEvaluator, NumericalEvaluator
from finexpert.evaluation.report import build_report

SFT_DIR = Path(__file__).resolve().parents[1] / "data" / "sft"


def _context(source, expected, prediction, category="financial_explanation"):
    return EvaluationContext(
        example_id="x_001",
        category=category,
        difficulty="easy",
        source_text=source,
        expected_text=expected,
        prediction_text=prediction,
    )


def _summary(findings, evaluator):
    return next(f for f in findings if f.evaluator == evaluator and f.level == "summary")


@pytest.mark.parametrize("split", ["train", "validation", "test"])
def test_reference_answers_score_perfectly(split):
    path = SFT_DIR / f"{split}.jsonl"
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    predictions = {row["example_id"]: row["messages"][2]["content"] for row in rows}

    summary = build_report(rows, predictions)["summary"]

    assert summary["numerical"]["numeric_precision"] == 1.0
    assert summary["numerical"]["numeric_recall"] == 1.0
    assert summary["grounding"]["figure_fidelity"] == 1.0
    assert summary["classification"]["accuracy"] == 1.0
    assert summary["structure"]["section_coverage"] == 1.0
    assert summary["failure_breakdown"]["finding_codes"] == {}
    assert summary["reference_exact_match_rate"] == 1.0


@pytest.mark.parametrize("verb", ["changing", "increasing", "rising", "growing"])
def test_source_participles_are_parsed(verb):
    source = f"ABC reported revenue {verb} from ₹100 Cr to ₹120 Cr."
    text = "Revenue increased by 20.0%, from ₹100 Cr to ₹120 Cr."
    summary = _summary(NumericalEvaluator().evaluate(_context(source, text, text)), "numerical")
    assert summary.passed
    assert summary.details["numeric_recall"] == 1.0


@pytest.mark.parametrize("verb", ["decreasing", "declining", "falling"])
def test_negative_participles_keep_direction(verb):
    source = f"ABC reported cash flow {verb} from ₹50 Cr to ₹40 Cr."
    ok = "Cash flow declined by 20.0%, from ₹50 Cr to ₹40 Cr."
    wrong_sign = "Cash flow increased by 20.0%, from ₹50 Cr to ₹40 Cr."

    assert _summary(NumericalEvaluator().evaluate(_context(source, ok, ok)), "numerical").passed
    assert not _summary(NumericalEvaluator().evaluate(_context(source, ok, wrong_sign)), "numerical").passed


def test_one_decimal_percent_ratio_is_accepted():
    source = "ABC reported revenue of ₹400 Cr and total assets of ₹300 Cr. Net income is ₹40 Cr."
    text = "Return on assets is 13.3%, based on net income of ₹40 Cr and total assets of ₹300 Cr."
    assert _summary(NumericalEvaluator().evaluate(_context(source, text, text)), "numerical").passed


def test_wrong_percent_ratio_is_still_rejected():
    source = "ABC reported revenue of ₹400 Cr and total assets of ₹300 Cr. Net income is ₹40 Cr."
    expected = "Return on assets is 13.3%, based on net income of ₹40 Cr and total assets of ₹300 Cr."
    wrong = "Return on assets is 13.5%, based on net income of ₹40 Cr and total assets of ₹300 Cr."
    assert not _summary(NumericalEvaluator().evaluate(_context(source, expected, wrong)), "numerical").passed


def test_repeating_a_supported_figure_is_not_invented():
    source = "ABC reported cash flow changing from ₹40 Cr to ₹32 Cr."
    expected = "Cash flow declined by 20.0%, from ₹40 Cr to ₹32 Cr."
    prediction = expected + " Cash flow ended at ₹32 Cr, down from ₹40 Cr."
    finding = _summary(GroundingEvaluator().evaluate(_context(source, expected, prediction)), "grounding")
    assert finding.passed


def test_unsupported_figure_is_still_flagged():
    source = "ABC reported cash flow changing from ₹40 Cr to ₹32 Cr."
    expected = "Cash flow declined by 20.0%, from ₹40 Cr to ₹32 Cr."
    prediction = expected + " Reserves stand at ₹75 Cr."
    finding = _summary(GroundingEvaluator().evaluate(_context(source, expected, prediction)), "grounding")
    assert not finding.passed
    assert finding.details["unsupported_figures"] == [{"value": 75.0, "unit": "cr", "count": 1}]


def test_classification_metrics_match_sklearn():
    sklearn_metrics = pytest.importorskip("sklearn.metrics")
    labels = ["Healthy", "Moderate Risk", "High Risk"]
    expected = ["Healthy", "Healthy", "Moderate Risk", "Moderate Risk", "High Risk", "High Risk", "High Risk"]
    predicted = ["Healthy", "Moderate Risk", "Moderate Risk", "Healthy", "High Risk", "Moderate Risk", "High Risk"]

    ours = classification_metrics(list(zip(expected, predicted)))
    for average in ("macro", "weighted"):
        p, r, f, _ = sklearn_metrics.precision_recall_fscore_support(
            expected, predicted, labels=labels, average=average, zero_division=0
        )
        assert ours[average]["precision"] == pytest.approx(p)
        assert ours[average]["recall"] == pytest.approx(r)
        assert ours[average]["f1"] == pytest.approx(f)
    assert ours["confusion_matrix"]["counts"] == sklearn_metrics.confusion_matrix(
        expected, predicted, labels=labels
    ).tolist()


def test_missing_label_counts_as_error_column():
    metrics = classification_metrics([("Healthy", "Healthy"), ("High Risk", None)])
    assert metrics["accuracy"] == 0.5
    assert metrics["missing_predictions"] == 1
    assert metrics["confusion_matrix"]["columns_predicted"][-1] == "<missing>"
    assert metrics["confusion_matrix"]["counts"][2] == [0, 0, 0, 1]


def test_wilson_interval_known_value():
    low, high = wilson_interval(8, 10)
    assert low == pytest.approx(0.4902, abs=1e-3)
    assert high == pytest.approx(0.9433, abs=1e-3)
    assert wilson_interval(0, 0) is None
