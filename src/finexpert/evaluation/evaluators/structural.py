"""Report-structure evaluator."""

import re

from ..context import EvaluationContext
from ..finding import Finding


SECTION_RE = re.compile(
    r"(?im)^\s*(Executive Summary|Quantitative Analysis|Key Observations|"
    r"Potential Risks and Opportunities|Risks and Opportunities|"
    r"Areas Requiring Further Investigation|Conclusion)\s*:"
)

ALIASES = {
    "potential risks and opportunities": "risks and opportunities",
    "risks and opportunities": "risks and opportunities",
}


class StructuralEvaluator:
    name = "structural"

    @classmethod
    def extract_sections(cls, text: str) -> set[str]:
        sections = set()
        for raw in SECTION_RE.findall(text):
            normalized = re.sub(r"\s+", " ", raw.strip().lower())
            normalized = ALIASES.get(normalized, normalized)
            sections.add(normalized)
        return sections

    def evaluate(self, context: EvaluationContext) -> list[Finding]:
        if context.category != "financial_report_generation":
            return []

        expected = self.extract_sections(context.expected_text)
        generated = self.extract_sections(context.prediction_text)
        present = expected & generated
        missing = expected - generated
        extra = generated - expected
        coverage = len(present) / len(expected) if expected else 1.0

        details = {
            "expected_sections": sorted(expected),
            "present_sections": sorted(present),
            "missing_sections": sorted(missing),
            "extra_sections": sorted(extra),
            "coverage": coverage,
        }

        if missing:
            return [
                Finding(
                    evaluator=self.name,
                    code="SECTION_MISSING",
                    passed=False,
                    message=f"Report covers {len(present)}/{len(expected)} expected sections.",
                    details=details,
                )
            ]

        return [
            Finding(
                evaluator=self.name,
                code="SECTION_COVERAGE_COMPLETE",
                passed=True,
                message="Report contains every expected section.",
                details=details,
            )
        ]
