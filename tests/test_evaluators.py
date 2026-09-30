import pytest

from finexpert.evaluation.context import EvaluationContext
from finexpert.evaluation.evaluators import (
    GroundingEvaluator,
    LabelEvaluator,
    NumericalEvaluator,
    StructuralEvaluator,
)


def ctx(category, source, expected, prediction, difficulty="easy"):
    return EvaluationContext(
        example_id="test-1",
        category=category,
        difficulty=difficulty,
        source_text=source,
        expected_text=expected,
        prediction_text=prediction,
    )


def summary(findings, evaluator):
    return next(
        finding for finding in findings
        if finding.evaluator == evaluator and finding.level == "summary"
    )


def test_label_correct_and_incorrect_use_same_finding_contract():
    evaluator = LabelEvaluator()

    good = evaluator.evaluate(ctx(
        "financial_classification",
        "Revenue is ₹500 Cr.",
        "Classification: Healthy\nEvidence: Revenue is ₹500 Cr.",
        "Classification: Healthy\nEvidence: Revenue is ₹500 Cr.",
    ))
    assert summary(good, "label").code == "LABEL_CORRECT"
    assert summary(good, "label").passed is True

    bad = evaluator.evaluate(ctx(
        "financial_classification",
        "Revenue is ₹500 Cr.",
        "Classification: Healthy\nEvidence: Revenue is ₹500 Cr.",
        "Classification: High Risk\nEvidence: ...",
    ))
    assert summary(bad, "label").code == "LABEL_INCORRECT"
    assert summary(bad, "label").passed is False


def test_grounding_uses_finding_contract():
    evaluator = GroundingEvaluator()

    good = evaluator.evaluate(ctx(
        "financial_explanation",
        "Revenue increased from ₹500 Cr to ₹575 Cr.",
        "Revenue increased by 15%, from ₹500 Cr to ₹575 Cr.",
        "Revenue increased by 15%, from ₹500 Cr to ₹575 Cr.",
    ))
    assert summary(good, "grounding").code == "FIGURES_GROUNDED"

    bad = evaluator.evaluate(ctx(
        "financial_explanation",
        "Revenue increased from ₹500 Cr to ₹575 Cr.",
        "Revenue increased by 15%, from ₹500 Cr to ₹575 Cr.",
        "Revenue increased by 15%. Operating profit is ₹999 Cr.",
    ))
    assert summary(bad, "grounding").code == "INVENTED_FIGURE"
    assert bad[0].details["unsupported_figures"][0]["value"] == 999.0


def test_numerical_recomputes_percentage_from_source():
    findings = NumericalEvaluator().evaluate(ctx(
        "financial_explanation",
        "Revenue increased from ₹150 Cr to ₹172.5 Cr.",
        "Revenue increased by 15%, from ₹150 Cr to ₹172.5 Cr.",
        "Revenue increased by 14.3%, from ₹150 Cr to ₹172.5 Cr.",
    ))

    summary_finding = summary(findings, "numerical")
    assert summary_finding.passed is False
    assert any(f.code == "PERCENTAGE_MATH_ERROR" for f in findings)


def test_numerical_recomputes_ratio_from_source():
    findings = NumericalEvaluator().evaluate(ctx(
        "financial_explanation",
        "Debt is ₹40 Cr and revenue is ₹100 Cr.",
        "Debt-to-revenue is 0.40.",
        "Debt-to-revenue is 0.040.",
    ))

    summary_finding = summary(findings, "numerical")
    assert summary_finding.passed is False
    detail = next(f for f in findings if f.code == "RATIO_MATH_ERROR")
    assert detail.details["details"]["recomputed"] == [0.4]


def test_numerical_allows_small_percentage_rounding_difference():
    findings = NumericalEvaluator().evaluate(ctx(
        "financial_explanation",
        "Cash decreased from ₹29 Cr to ₹25 Cr.",
        "Cash decreased by 13.8%, from ₹29 Cr to ₹25 Cr.",
        "Cash decreased by 13.79%, from ₹29 Cr to ₹25 Cr.",
    ))

    summary_finding = summary(findings, "numerical")
    assert summary_finding.passed is True


def test_structural_section_coverage_is_explicit():
    expected = (
        "Executive Summary: x\n\n"
        "Quantitative Analysis: y\n\n"
        "Key Observations: z\n\n"
        "Risks and Opportunities: r\n\n"
        "Areas Requiring Further Investigation: a\n\n"
        "Conclusion: c"
    )
    prediction = (
        "Executive Summary: x\n\n"
        "Quantitative Analysis: y\n\n"
        "Key Observations: z\n\n"
        "Potential Risks and Opportunities: r\n\n"
        "Conclusion: c"
    )

    findings = StructuralEvaluator().evaluate(ctx(
        "financial_report_generation",
        "Revenue is ₹100 Cr.",
        expected,
        prediction,
        difficulty="medium",
    ))

    result = summary(findings, "structural")
    assert result.passed is False
    # The alias is canonicalized, so the risk section is considered present.
    assert result.details["missing_sections"] == [
        "areas requiring further investigation"
    ]
    assert result.details["coverage"] == pytest.approx(5 / 6)
