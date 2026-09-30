"""Report-structure evaluator."""

import re

from ..context import EvaluationContext
from ..finding import Finding


SECTION_RE = re.compile(
    r"(?im)^\s*(Executive Summary|Quantitative Analysis|Key Observations|"
    r"Potential Risks and Opportunities|Risks and Opportunities|"
    r"Areas Requiring Further Investigation|Conclusion|"
    r"Classification|Evidence|Basis)\s*:"
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
        # Required sections are derived from the REFERENCE text itself,
        # not a hardcoded per-category/per-difficulty list. This
        # generalizes across all three task types for free:
        #   - financial_classification always has Classification/
        #     Evidence/Basis, so it's always checked.
        #   - financial_report_generation has 3-5 sections depending
        #     on difficulty; whatever the reference actually contains
        #     is what gets required.
        #   - financial_explanation is unstructured prose at "easy"
        #     difficulty (the reference has zero labeled sections), so
        #     expected comes back empty and this evaluator correctly
        #     imposes no structural requirement there -- only
        #     medium/hard, which open with "Quantitative Analysis:",
        #     get a real check. No difficulty branching needed here;
        #     it falls out of reading the reference.
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
