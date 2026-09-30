"""Common input object passed to all evaluators."""

from dataclasses import dataclass


@dataclass(frozen=True)
class EvaluationContext:
    example_id: str
    category: str
    difficulty: str
    source_text: str
    expected_text: str
    prediction_text: str
