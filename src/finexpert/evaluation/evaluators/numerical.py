"""Source-grounded numerical evaluator.

This evaluator independently recomputes supported financial calculations from
the model input.  The reference answer is used only to measure coverage of the
expected quantitative claims; it is not used as the mathematical source of truth.
"""

from __future__ import annotations

import math
import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from ..context import EvaluationContext
from ..finding import Finding


PERCENT_TOLERANCE = 0.15  # percentage points
RATIO_TOLERANCE = 0.015
VALUE_TOLERANCE = 0.01
# Percent-valued ratios (ROA, margins) are written to 1 decimal place, so a
# correct value can differ from the exact recomputation by up to 0.05 pp.
PERCENT_RATIO_TOLERANCE = 0.06
PERCENT_RATIOS = {
    "return_on_assets",
    "return_on_equity",
    "operating_margin",
    "net_profit_margin",
    "profit_margin",
    "operating_expense_ratio",
}

NEGATIVE_DIRECTIONS = {
    "declined",
    "decreased",
    "decreases",
    "fell",
    "dropped",
    "drop",
    "decreasing",
    "declining",
    "falling",
}

# Past-tense verbs appear in answers; present participles appear in the
# dataset inputs ("reported revenue changing/increasing from ... to ...").
DIRECTIONS = (
    "increased|increases|increasing|grew|growing|rose|rising|"
    "declined|declining|decreased|decreases|decreasing|fell|falling|"
    "dropped|drop|changed|changing"
)

METRICS = (
    "operating expenses|operating expense|operating profit|net profit|"
    "cash flow|cash reserves|current assets|current liabilities|total assets|"
    "net income|revenue|profit|earnings|expenses|debt|cash|equity"
)

VALUE_RE = re.compile(
    rf"(?P<metric>{METRICS})\s+"
    rf"(?P<direction>{DIRECTIONS})"
    r"\s+from\s+₹?\s*(?P<old>\d+(?:\.\d+)?)"
    r"(?:\s*(?:Cr|crore|crores|Lakh|Lakhs|Million|Billion))?"
    r"\s+to\s+₹?\s*(?P<new>\d+(?:\.\d+)?)"
    r"(?:\s*(?:Cr|crore|crores|Lakh|Lakhs|Million|Billion))?",
    re.IGNORECASE,
)

STATIC_VALUE_RE = re.compile(
    rf"(?P<metric>{METRICS})\s+(?:is|was|of|=)\s+₹?\s*(?P<value>\d+(?:\.\d+)?)"
    r"(?:\s*(?:Cr|crore|crores|Lakh|Lakhs|Million|Billion))?",
    re.IGNORECASE,
)

PERCENT_RE = re.compile(
    rf"(?P<metric>{METRICS})\s+"
    rf"(?P<direction>{DIRECTIONS})"
    r"\s+(?:by\s+)?(?P<value>-?\d+(?:\.\d+)?)\s*%",
    re.IGNORECASE,
)

GROWTH_RE = re.compile(
    rf"(?P<metric>{METRICS})\s+(?:growth|change|increase|decrease)\s+"
    r"(?:is|was|equals|=)\s+(?P<value>-?\d+(?:\.\d+)?)\s*%",
    re.IGNORECASE,
)

RATIO_RE = re.compile(
    r"(?P<metric>debt-to-equity|debt-to-revenue|current ratio|asset turnover|cash-to-debt|"
    r"return on assets|return on equity|operating margin|net profit margin|profit margin|"
    r"operating expense ratio)"
    r"(?:\s+ratio)?\s+(?:is|was|equals|of|=)\s+(?P<value>-?\d+(?:\.\d+)?)"
    r"\s*(?:x|%)?",
    re.IGNORECASE,
)


ALIASES = {
    "operating expense": "operating_expenses",
    "operating expenses": "operating_expenses",
    "operating profit": "operating_profit",
    "net profit": "net_profit",
    "cash flow": "cash_flow",
    "cash reserves": "cash",
    "current assets": "current_assets",
    "current liabilities": "current_liabilities",
    "total assets": "total_assets",
    "net income": "net_income",
    "revenue": "revenue",
    "profit": "profit",
    "earnings": "earnings",
    "expenses": "expenses",
    "debt": "debt",
    "cash": "cash",
    "equity": "equity",
    "debt-to-equity": "debt_to_equity",
    "debt-to-revenue": "debt_to_revenue",
    "current ratio": "current_ratio",
    "asset turnover": "asset_turnover",
    "cash-to-debt": "cash_to_debt",
    "return on assets": "return_on_assets",
    "return on equity": "return_on_equity",
    "operating margin": "operating_margin",
    "net profit margin": "net_profit_margin",
    "profit margin": "profit_margin",
    "operating expense ratio": "operating_expense_ratio",
}


@dataclass(frozen=True)
class Claim:
    type: str
    metric: str
    value: float | None = None
    old: float | None = None
    new: float | None = None
    direction: str | None = None
    text: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "metric": self.metric,
            "value": self.value,
            "old": self.old,
            "new": self.new,
            "direction": self.direction,
            "text": self.text,
        }


class NumericalEvaluator:
    name = "numerical"

    @staticmethod
    def _normalize_metric(metric: str) -> str:
        metric = re.sub(r"\s+", " ", metric.strip().lower())
        return ALIASES.get(metric, metric.replace("-", "_"))

    @staticmethod
    def _ratio_tolerance(metric: str) -> float:
        return PERCENT_RATIO_TOLERANCE if metric in PERCENT_RATIOS else RATIO_TOLERANCE

    @staticmethod
    def _close(a: float, b: float, tolerance: float) -> bool:
        return math.isclose(float(a), float(b), rel_tol=0.0, abs_tol=tolerance)

    @classmethod
    def extract_claims(cls, text: str) -> list[Claim]:
        claims: list[Claim] = []

        for match in VALUE_RE.finditer(text):
            claims.append(
                Claim(
                    type="value_change",
                    metric=cls._normalize_metric(match.group("metric")),
                    old=float(match.group("old")),
                    new=float(match.group("new")),
                    direction=match.group("direction").lower(),
                    text=match.group(0).strip(),
                )
            )

        for pattern in (PERCENT_RE, GROWTH_RE):
            for match in pattern.finditer(text):
                direction = match.groupdict().get("direction")
                value = float(match.group("value"))
                if direction and direction.lower() in NEGATIVE_DIRECTIONS:
                    value = -abs(value)
                claims.append(
                    Claim(
                        type="percentage_change",
                        metric=cls._normalize_metric(match.group("metric")),
                        value=value,
                        direction=direction.lower() if direction else None,
                        text=match.group(0).strip(),
                    )
                )

        for match in RATIO_RE.finditer(text):
            claims.append(
                Claim(
                    type="ratio",
                    metric=cls._normalize_metric(match.group("metric")),
                    value=float(match.group("value")),
                    text=match.group(0).strip(),
                )
            )

        return cls._deduplicate_claims(claims)

    @staticmethod
    def _claim_key(claim: Claim) -> tuple[Any, ...]:
        return (
            claim.type,
            claim.metric,
            claim.value,
            claim.old,
            claim.new,
            claim.direction,
        )

    @classmethod
    def _deduplicate_claims(cls, claims: list[Claim]) -> list[Claim]:
        seen = set()
        result = []
        for claim in claims:
            key = cls._claim_key(claim)
            if key not in seen:
                seen.add(key)
                result.append(claim)
        return result

    @classmethod
    def source_metrics(cls, source_text: str) -> tuple[dict[str, list[float]], dict[str, float]]:
        """Return source values plus preferred current/latest values.

        For period-change sentences, the latest value is preferred for ratio
        derivation so a ratio such as debt-to-revenue uses the current revenue
        rather than the prior-period revenue when both appear in the input.
        """

        values: defaultdict[str, list[float]] = defaultdict(list)
        latest: dict[str, float] = {}

        for match in VALUE_RE.finditer(source_text):
            metric = cls._normalize_metric(match.group("metric"))
            old = float(match.group("old"))
            new = float(match.group("new"))
            values[metric].extend([old, new])
            latest[metric] = new

        for match in STATIC_VALUE_RE.finditer(source_text):
            metric = cls._normalize_metric(match.group("metric"))
            value = float(match.group("value"))
            values[metric].append(value)
            latest.setdefault(metric, value)

        for metric in list(values):
            deduped: list[float] = []
            for value in values[metric]:
                if not any(cls._close(value, existing, VALUE_TOLERANCE) for existing in deduped):
                    deduped.append(value)
            values[metric] = deduped

        return dict(values), latest

    @classmethod
    def derived_values(cls, source_text: str) -> dict[str, list[float]]:
        values, latest = cls.source_metrics(source_text)
        derived: defaultdict[str, list[float]] = defaultdict(list)

        for claim in cls.extract_claims(source_text):
            if claim.type != "value_change" or claim.old == 0:
                continue
            change = ((claim.new - claim.old) / claim.old) * 100
            derived[f"{claim.metric}_change"].append(change)

        def add_ratio(output: str, numerator: str, denominator: str, multiplier: float = 1.0) -> None:
            left_values = [latest[numerator]] if numerator in latest else values.get(numerator, [])
            right_values = [latest[denominator]] if denominator in latest else values.get(denominator, [])

            for left in left_values:
                for right in right_values:
                    if right == 0:
                        continue
                    derived[output].append((left / right) * multiplier)

        add_ratio("debt_to_equity", "debt", "equity")
        add_ratio("debt_to_revenue", "debt", "revenue")
        add_ratio("current_ratio", "current_assets", "current_liabilities")
        add_ratio("asset_turnover", "revenue", "total_assets")
        add_ratio("cash_to_debt", "cash", "debt")
        add_ratio("return_on_assets", "net_income", "total_assets", 100.0)
        add_ratio("return_on_assets", "net_profit", "total_assets", 100.0)
        add_ratio("return_on_equity", "net_income", "equity", 100.0)
        add_ratio("return_on_equity", "net_profit", "equity", 100.0)
        add_ratio("operating_margin", "operating_profit", "revenue", 100.0)
        add_ratio("net_profit_margin", "net_profit", "revenue", 100.0)
        add_ratio("net_profit_margin", "net_income", "revenue", 100.0)
        add_ratio("profit_margin", "profit", "revenue", 100.0)
        add_ratio("operating_expense_ratio", "operating_expenses", "revenue", 100.0)

        return {key: list(values_) for key, values_ in derived.items()}

    @classmethod
    def validate_claim(cls, claim: Claim, source_text: str) -> tuple[bool, str, dict[str, Any]]:
        derived = cls.derived_values(source_text)

        if claim.type == "value_change":
            source_claims = [c for c in cls.extract_claims(source_text) if c.type == "value_change"]
            for source_claim in source_claims:
                if source_claim.metric != claim.metric:
                    continue
                if source_claim.old is None or source_claim.new is None:
                    continue
                if not cls._close(source_claim.old, claim.old or 0.0, VALUE_TOLERANCE):
                    continue
                if not cls._close(source_claim.new, claim.new or 0.0, VALUE_TOLERANCE):
                    continue

                delta = source_claim.new - source_claim.old
                if delta > VALUE_TOLERANCE and claim.direction in NEGATIVE_DIRECTIONS:
                    continue
                if delta < -VALUE_TOLERANCE and claim.direction not in NEGATIVE_DIRECTIONS:
                    continue
                return True, "VALUE_CHANGE_GROUNDED", {
                    "expected_old": source_claim.old,
                    "expected_new": source_claim.new,
                }

            return False, "VALUE_CHANGE_NOT_GROUNDED", {}

        if claim.type == "percentage_change":
            allowed = derived.get(f"{claim.metric}_change", [])
            if not allowed:
                return False, "PERCENTAGE_SOURCE_NOT_FOUND", {}

            for expected in allowed:
                if cls._close(claim.value or 0.0, expected, PERCENT_TOLERANCE):
                    return True, "PERCENTAGE_MATH_MATCH", {"recomputed": expected}

            return False, "PERCENTAGE_MATH_ERROR", {"recomputed": allowed}

        if claim.type == "ratio":
            allowed = derived.get(claim.metric, [])
            if not allowed:
                return False, "RATIO_SOURCE_NOT_FOUND", {}

            tolerance = cls._ratio_tolerance(claim.metric)
            for expected in allowed:
                if cls._close(claim.value or 0.0, expected, tolerance):
                    return True, "RATIO_MATH_MATCH", {"recomputed": expected}

            return False, "RATIO_MATH_ERROR", {"recomputed": allowed}

        return False, "UNKNOWN_CLAIM_TYPE", {}

    @classmethod
    def _matches_expected(cls, expected: Claim, generated: Claim) -> bool:
        if expected.type != generated.type or expected.metric != generated.metric:
            return False

        if expected.type == "value_change":
            return (
                cls._close(expected.old or 0.0, generated.old or 0.0, VALUE_TOLERANCE)
                and cls._close(expected.new or 0.0, generated.new or 0.0, VALUE_TOLERANCE)
            )

        if expected.type == "percentage_change":
            tolerance = PERCENT_TOLERANCE
        else:
            tolerance = cls._ratio_tolerance(expected.metric)
        return cls._close(expected.value or 0.0, generated.value or 0.0, tolerance)

    def evaluate(self, context: EvaluationContext) -> list[Finding]:
        expected_claims = self.extract_claims(context.expected_text)
        generated_claims = self.extract_claims(context.prediction_text)

        generated_status: list[dict[str, Any]] = []
        valid_indices: list[int] = []
        invalid_count = 0

        for index, claim in enumerate(generated_claims):
            valid, code, details = self.validate_claim(claim, context.source_text)
            item = {
                **claim.as_dict(),
                "valid": valid,
                "code": code,
                "details": details,
            }
            generated_status.append(item)
            if valid:
                valid_indices.append(index)
            else:
                invalid_count += 1

        matched_expected = 0
        used_generated: set[int] = set()
        expected_match_flags: list[bool] = []

        for expected in expected_claims:
            found = None
            for index in valid_indices:
                if index in used_generated:
                    continue
                generated = generated_claims[index]
                if self._matches_expected(expected, generated):
                    found = index
                    break
            if found is None:
                expected_match_flags.append(False)
            else:
                expected_match_flags.append(True)
                used_generated.add(found)
                matched_expected += 1

        # Mark valid generated claims that actually cover an expected claim.
        for index, item in enumerate(generated_status):
            item["matched_expected"] = index in used_generated

        findings: list[Finding] = []
        findings.extend(
            Finding(
                evaluator=self.name,
                code=item["code"],
                passed=item["valid"],
                message=(
                    f"{item['metric']} calculation is source-grounded."
                    if item["valid"]
                    else f"{item['metric']} calculation failed source-grounded validation: {item['code']}."
                ),
                level="detail",
                details=item,
            )
            for item in generated_status
        )

        for index, expected in enumerate(expected_claims):
            if not expected_match_flags[index]:
                findings.append(
                    Finding(
                        evaluator=self.name,
                        code="MISSING_EXPECTED_METRIC",
                        passed=False,
                        message=f"Expected quantitative claim is missing: {expected.metric}.",
                        level="detail",
                        details={"claim": expected.as_dict()},
                    )
                )

        expected_count = len(expected_claims)
        generated_count = len(generated_claims)
        valid_count = sum(1 for item in generated_status if item["valid"])

        precision = valid_count / generated_count if generated_count else None
        recall = matched_expected / expected_count if expected_count else None

        summary_passed = (
            invalid_count == 0
            and (expected_count == 0 or matched_expected == expected_count)
        )

        findings.insert(
            0,
            Finding(
                evaluator=self.name,
                code="NUMERICAL_SUMMARY",
                passed=summary_passed,
                message="Numerical claims were recomputed from the source input.",
                details={
                    "expected_claim_count": expected_count,
                    "generated_claim_count": generated_count,
                    "valid_generated_claim_count": valid_count,
                    "invalid_generated_claim_count": invalid_count,
                    "matched_expected_claim_count": matched_expected,
                    "unmatched_expected_claim_count": expected_count - matched_expected,
                    "numeric_precision": precision,
                    "numeric_recall": recall,
                },
            ),
        )

        return findings
