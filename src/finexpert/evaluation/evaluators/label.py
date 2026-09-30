"""Classification-label evaluator."""

import re

from ..context import EvaluationContext
from ..finding import Finding


LABEL_RE = re.compile(
    r"^\s*Classification\s*:\s*(Healthy|Moderate\s+Risk|High\s+Risk)",
    re.IGNORECASE,
)


class LabelEvaluator:
    name = "label"

    @staticmethod
    def extract_label(text: str) -> str | None:
        match = LABEL_RE.match(text.strip())
        if not match:
            return None

        value = re.sub(r"\s+", " ", match.group(1).strip()).lower()
        return {
            "healthy": "Healthy",
            "moderate risk": "Moderate Risk",
            "high risk": "High Risk",
        }[value]

    def evaluate(self, context: EvaluationContext) -> list[Finding]:
        if context.category != "financial_classification":
            return []

        expected = self.extract_label(context.expected_text)
        predicted = self.extract_label(context.prediction_text)

        if expected is None:
            return [
                Finding(
                    evaluator=self.name,
                    code="REFERENCE_LABEL_MISSING",
                    passed=False,
                    message="Classification example has no valid reference label.",
                    details={"predicted_label": predicted},
                )
            ]

        if predicted is None:
            summary = Finding(
                evaluator=self.name,
                code="LABEL_MISSING",
                passed=False,
                message="Model output does not contain a valid classification label.",
                details={"expected_label": expected, "predicted_label": None},
            )
        elif predicted == expected:
            summary = Finding(
                evaluator=self.name,
                code="LABEL_CORRECT",
                passed=True,
                message=f"Classification label matches: {expected}.",
                details={"expected_label": expected, "predicted_label": predicted},
            )
        else:
            summary = Finding(
                evaluator=self.name,
                code="LABEL_INCORRECT",
                passed=False,
                message=f"Expected {expected}; model predicted {predicted}.",
                details={"expected_label": expected, "predicted_label": predicted},
            )

        return [summary]
