from finexpert.evaluation.metrics import (
    extract_label,
    figures_are_grounded,
    is_correct_label,
    is_format_ok,
    numeric_mismatch,
)


def test_extract_label_variants():
    assert extract_label("Classification: Healthy\nEvidence: ...") == "Healthy"
    assert extract_label("classification: moderate risk") == "moderate risk"
    assert extract_label("No label here") is None


def test_is_correct_label():
    ref = "Classification: High Risk\nEvidence: ..."
    assert is_correct_label(ref, "Classification: High Risk\nBecause X.")
    assert not is_correct_label(ref, "Classification: Healthy\nBecause X.")


def test_is_correct_label_requires_labelled_reference():
    import pytest

    with pytest.raises(ValueError):
        is_correct_label("no label in reference", "Classification: Healthy")


def test_is_format_ok():
    assert is_format_ok("Classification: Healthy\n...")
    assert not is_format_ok("The company looks Healthy overall.")


def test_figures_are_grounded_true_when_figures_come_from_prompt_or_reference():
    prompt = "Revenue is ₹500 Cr."
    reference = "Revenue increased from ₹500 Cr to ₹575 Cr."
    prediction = "Revenue increased by 15%, from ₹500 Cr to ₹575 Cr."

    assert figures_are_grounded(prediction, reference, prompt)


def test_figures_are_grounded_false_for_invented_figure():
    prompt = "Revenue is ₹500 Cr."
    reference = "Revenue increased from ₹500 Cr to ₹575 Cr."
    prediction = "Revenue increased by 15%. Operating profit is ₹999 Cr."

    assert not figures_are_grounded(prediction, reference, prompt)


def test_numeric_mismatch_catches_digit_drift_not_seen_by_currency_check():
    # The real bug this caught: reference says 0.40, model wrote 0.040.
    # Neither number has Rs/Cr around it, so the currency-only check
    # (figures_are_grounded) can't see this -- numeric_mismatch can.
    reference = "Debt-to-revenue is 0.40, based on debt of ₹40 Cr and revenue of ₹100 Cr."
    prediction = "Debt-to-revenue is 0.040, based on debt of ₹40 Cr and revenue of ₹100 Cr."

    mismatch = numeric_mismatch(reference, prediction)
    assert "0.040" in mismatch


def test_numeric_mismatch_empty_when_prediction_reuses_only_reference_numbers():
    reference = "Revenue increased by 15%, from ₹500 Cr to ₹575 Cr."
    prediction = "Revenue increased by 15%, from ₹500 Cr to ₹575 Cr."

    assert numeric_mismatch(reference, prediction) == []
