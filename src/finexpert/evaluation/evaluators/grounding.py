"""Currency-figure grounding evaluator."""

import re
from collections import Counter

from ..context import EvaluationContext
from ..finding import Finding


CURRENCY_RE = re.compile(
    r"₹\s*(?P<value>\d+(?:\.\d+)?)\s*(?P<unit>Cr|crore|crores|Lakh|Lakhs|Million|Billion)",
    re.IGNORECASE,
)


class GroundingEvaluator:
    """Check that generated currency figures are supported by known text.

    Grounding intentionally remains separate from mathematical correctness.
    A figure can be grounded yet still be the wrong derived calculation.
    """

    name = "grounding"

    @staticmethod
    def _figures(text: str) -> Counter[tuple[float, str]]:
        # Counts are kept for reporting only. Grounding itself is a set check:
        # repeating a supported figure (e.g. in both an executive summary and a
        # quantitative section) is not an invented figure.
        figures: Counter[tuple[float, str]] = Counter()
        for match in CURRENCY_RE.finditer(text):
            figures[(float(match.group("value")), match.group("unit").lower())] += 1
        return figures

    def evaluate(self, context: EvaluationContext) -> list[Finding]:
        # We preserve the existing grounding idea: figures may be supported
        # by either the source prompt or the reference target. Mathematical
        # correctness is handled independently by NumericalEvaluator.
        allowed = self._figures(context.source_text) | self._figures(context.expected_text)
        predicted = self._figures(context.prediction_text)

        unsupported = Counter(
            {figure: count for figure, count in predicted.items() if figure not in allowed}
        )

        details = {
            "predicted_figures": [
                {"value": value, "unit": unit, "count": count}
                for (value, unit), count in sorted(predicted.items())
            ],
            "unsupported_figures": [
                {"value": value, "unit": unit, "count": count}
                for (value, unit), count in sorted(unsupported.items())
            ],
        }

        if unsupported:
            return [
                Finding(
                    evaluator=self.name,
                    code="INVENTED_FIGURE",
                    passed=False,
                    message="One or more generated currency figures are not present in the source or reference evidence.",
                    details=details,
                )
            ]

        return [
            Finding(
                evaluator=self.name,
                code="FIGURES_GROUNDED",
                passed=True,
                message="All generated currency figures are grounded in the source or reference evidence.",
                details=details,
            )
        ]
