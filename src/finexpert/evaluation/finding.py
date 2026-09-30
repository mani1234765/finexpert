"""Shared evaluation finding contract.

Every evaluator returns Finding objects.  The report layer only consumes
findings and does not know how an evaluator arrived at them.
"""

from dataclasses import dataclass, field
from typing import Any, Literal


FindingLevel = Literal["summary", "detail"]


@dataclass(frozen=True)
class Finding:
    """A single structured evaluation result."""

    evaluator: str
    code: str
    passed: bool
    message: str
    level: FindingLevel = "summary"
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "evaluator": self.evaluator,
            "code": self.code,
            "passed": self.passed,
            "message": self.message,
            "level": self.level,
            "details": self.details,
        }
