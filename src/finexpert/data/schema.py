from pydantic import BaseModel, Field
from enum import Enum
class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
class Category(str, Enum):
    FINANCIAL_EXPLANATION = "financial_explanation"
    FINANCIAL_CLASSIFICATION = "financial_classification"
    FINANCIAL_REPORT_GENERATION = "financial_report_generation"
class SourceType(str, Enum):
    SYNTHETIC = "synthetic"
    ANNUAL_REPORT = "annual_report"
    FINANCIAL_STATEMENT = "financial_statement"
    EARNINGS_CALL = "earnings_call"
class ReasoningType(str, Enum):
    NUMERICAL_REASONING = "numerical_reasoning"
    TREND_ANALYSIS = "trend_analysis"
    RISK_ANALYSIS = "risk_analysis"
    COMPARISON = "comparison"
    CAUSAL_REASONING = "causal_reasoning"
reasoning_type: list[ReasoningType] = Field(min_length=1)
class FinancialExample(BaseModel):
    example_id: str
    instruction: str
    input: str
    expected_output: str
    category: Category
    difficulty: Difficulty
    reasoning_type: list[ReasoningType] = Field(min_length=1)
    source_type: SourceType | None = None
    company: str | None = None


example = FinancialExample(
    example_id="fin_exp_1",
    instruction="Explain the change in revenue and operating profit.",
    input="Revenue increased from ₹100 Cr to ₹130 Cr, while operating profit decreased from ₹20 Cr to ₹15 Cr.",
    expected_output="Revenue increased by 30%, while operating profit decreased by 25%, indicating pressure on profitability.",
    category=Category.FINANCIAL_EXPLANATION,
    difficulty=Difficulty.EASY,
    reasoning_type=[ReasoningType.TREND_ANALYSIS],
    source_type=SourceType.SYNTHETIC,
    company="ABC Industries"
)
