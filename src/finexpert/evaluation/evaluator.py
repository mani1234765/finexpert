"""Evaluator protocol."""

from typing import Protocol

from .context import EvaluationContext
from .finding import Finding


class Evaluator(Protocol):
    """Common interface implemented by all evaluators."""

    name: str

    def evaluate(self, context: EvaluationContext) -> list[Finding]:
        ...
