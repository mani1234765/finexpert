import re


DIFFICULTY_RULES = {
    "easy": {
        "min_metrics": 1,
        "max_metrics": 3,
        "min_reasoning": 1,
        "min_complexity": 1,
    },
    "medium": {
        "min_metrics": 2,
        "max_metrics": 5,
        "min_reasoning": 1,
        "min_complexity": 2,
    },
    "hard": {
        "min_metrics": 4,
        "max_metrics": None,
        "min_reasoning": 3,
        "min_complexity": 6,
    },
}


METRIC_PATTERNS = {
    "revenue": [
        r"\brevenue\b",
        r"\bsales\b",
    ],
    "operating_profit": [
        r"\boperating profit\b",
        r"\boperating income\b",
        r"\bebit\b",
    ],
    "net_profit": [
        r"\bnet profit\b",
        r"\bnet income\b",
        r"\bearnings\b",
    ],
    "profit": [
        r"(?<!operating )(?<!net )\bprofit\b",
    ],
    "expenses": [
        r"\bexpenses?\b",
        r"\bcosts?\b",
        r"\boperating expenses?\b",
    ],
    "debt": [
        r"\bdebt\b",
        r"\bborrowings?\b",
    ],
    "cash": [
        r"\bcash\b",
        r"\bcash reserves?\b",
    ],
    "assets": [
        r"(?<!current )\bassets?\b",
    ],
    "equity": [
        r"\bequity\b",
    ],
    "receivables": [
        r"\breceivables?\b",
        r"\baccounts receivable\b",
    ],
    "inventory": [
        r"\binventory\b",
    ],
    "payables": [
        r"\bpayables?\b",
        r"\baccounts payable\b",
    ],
    "operating_cash_flow": [
        r"\boperating cash flow\b",
        r"\bcash flow from operations\b",
    ],
    "ebitda": [
        r"\bebitda\b",
    ],
    "interest_expense": [
        r"\binterest expense\b",
        r"\binterest costs?\b",
    ],
    "shares": [
        r"\bshares?\b",
        r"\bshare count\b",
    ],
    "margin": [
        r"\bmargin\b",
    ],
    "current_assets": [
        r"\bcurrent assets?\b",
    ],
    "current_liabilities": [
        r"\bcurrent liabilities?\b",
    ],
    "assest_turnover": [
        r"\bassest turnover\b",
    ],
    "return_on_assests": [
        r"\breturn on assests\b",
        r"\broa\b",
    ],
}


def extract_financial_metrics(text):
    """
    Extract distinct financial metrics mentioned in the text.

    Returns a list of normalized metric names.
    """

    if not text:
        return []

    text_lower = text.lower()

    found = []

    for metric, patterns in METRIC_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                found.append(metric)
                break

    return found


def extract_numbers(text):
    """
    Extract numeric values from financial text.

    Handles values such as:
        100
        100.5
        -10
        20%
        ₹100
        ₹100 Cr
    """

    if not text:
        return []

    matches = re.findall(
        r"(?<![A-Za-z])[-+]?\d+(?:\.\d+)?",
        text,
    )

    return [float(value) for value in matches]


def count_percentage_claims(text):
    """
    Count explicit percentage claims.

    Examples:
        increased by 20%
        declined by 15%
        margin was 12.5%
    """

    if not text:
        return 0

    matches = re.findall(
        r"[-+]?\d+(?:\.\d+)?\s*%",
        text,
    )

    return len(matches)


def count_period_comparisons(text):
    """
    Count explicit comparison structures.

    Examples:
        from 100 to 120
        increased from 100 to 120
        declined from 50 to 40
        compared with
        versus
        year-over-year
    """

    if not text:
        return 0

    text_lower = text.lower()

    count = 0

    comparison_patterns = [
        r"\bfrom\s+[-+]?\d+(?:\.\d+)?\s+(?:to|into)\s+[-+]?\d+(?:\.\d+)?",
        r"\bincreased\s+from\s+[-+]?\d+(?:\.\d+)?\s+to\s+[-+]?\d+(?:\.\d+)?",
        r"\bincrease\s+from\s+[-+]?\d+(?:\.\d+)?\s+to\s+[-+]?\d+(?:\.\d+)?",
        r"\bincreasing\s+from\s+[-+]?\d+(?:\.\d+)?\s+to\s+[-+]?\d+(?:\.\d+)?",
        r"\bdeclined\s+from\s+[-+]?\d+(?:\.\d+)?\s+to\s+[-+]?\d+(?:\.\d+)?",
        r"\bdecline\s+from\s+[-+]?\d+(?:\.\d+)?\s+to\s+[-+]?\d+(?:\.\d+)?",
        r"\bdecreased\s+from\s+[-+]?\d+(?:\.\d+)?\s+to\s+[-+]?\d+(?:\.\d+)?",
        r"\bdecrease\s+from\s+[-+]?\d+(?:\.\d+)?\s+to\s+[-+]?\d+(?:\.\d+)?",
        r"\bgrew\s+from\s+[-+]?\d+(?:\.\d+)?\s+to\s+[-+]?\d+(?:\.\d+)?",
        r"\bgrowing\s+from\s+[-+]?\d+(?:\.\d+)?\s+to\s+[-+]?\d+(?:\.\d+)?",
        r"\brose\s+from\s+[-+]?\d+(?:\.\d+)?\s+to\s+[-+]?\d+(?:\.\d+)?",
        r"\bfell\s+from\s+[-+]?\d+(?:\.\d+)?\s+to\s+[-+]?\d+(?:\.\d+)?",
        r"\bcompared\s+with\b",
        r"\bcompared\s+to\b",
        r"\bversus\b",
        r"\bvs\.?\b",
        r"\byear[- ]over[- ]year\b",
        r"\byoy\b",
    ]

    for pattern in comparison_patterns:
        count += len(re.findall(pattern, text_lower))

    return count


def count_calculation_signals(text):
    """
    Count explicit calculation / quantitative reasoning signals.
    """

    if not text:
        return 0

    text_lower = text.lower()

    patterns = [
        r"\bpercentage\b",
        r"\bpercent\b",
        r"\bmargin\b",
        r"\bratio\b",
        r"\bgrowth\b",
        r"\bchange\b",
        r"\bincreased\b",
        r"\bincrease\b",
        r"\bincreasing\b",
        r"\bgrew\b",
        r"\bgrowing\b",
        r"\brose\b",
        r"\brising\b",
        r"\bdeclined\b",
        r"\bdecline\b",
        r"\bdecreased\b",
        r"\bdecrease\b",
        r"\bdecreasing\b",
        r"\bfell\b",
        r"\bfall\b",
        r"\bfalling\b",
        r"\bdropped\b",
        r"\bdrop\b",
        r"\bprofitability\b",
        r"\bleverage\b",
        r"\bliquidity\b",
    ]

    return sum(
        len(re.findall(pattern, text_lower))
        for pattern in patterns
    )


def count_reasoning_signals(text):
    """
    Count qualitative reasoning signals.

    These signals indicate interpretation beyond simply
    reading a single number.
    """

    if not text:
        return 0

    text_lower = text.lower()

    patterns = [
        r"\bbecause\b",
        r"\bdue to\b",
        r"\bdriven by\b",
        r"\bindicates?\b",
        r"\bsuggests?\b",
        r"\bimplies?\b",
        r"\bhowever\b",
        r"\balthough\b",
        r"\bdespite\b",
        r"\bwhile\b",
        r"\bwhereas\b",
        r"\brisk\b",
        r"\brisk analysis\b",
        r"\bliquidity\b",
        r"\bleverage\b",
        r"\bprofitability\b",
        r"\bpressure\b",
        r"\bconcern\b",
        r"\bconcerns\b",
        r"\bshould investigate\b",
        r"\bfurther analysis\b",
        r"\brequires further\b",
    ]

    return sum(
        len(re.findall(pattern, text_lower))
        for pattern in patterns
    )


def calculate_reasoning_complexity(
    text,
    reasoning_type_count=1,
):
    """
    Calculate a deterministic reasoning-complexity score.

    Design:

    Easy:
        A single financial metric + a simple calculation
        is enough to reach complexity 1.

    Medium:
        Multiple metrics and/or comparisons should reach
        complexity 2+.

    Hard:
        Multiple metrics, calculations, comparisons and
        reasoning signals should produce a substantially
        higher score.
    """

    metrics = extract_financial_metrics(text)
    metric_count = len(metrics)

    period_comparisons = count_period_comparisons(text)
    percentage_claims = count_percentage_claims(text)
    calculation_signals = count_calculation_signals(text)
    reasoning_signals = count_reasoning_signals(text)

    # ---------------------------------------------------------
    # BASE SCORE
    # ---------------------------------------------------------

    # One financial metric itself represents one reasoning unit.
    complexity = metric_count

    # ---------------------------------------------------------
    # SIMPLE CALCULATION
    # ---------------------------------------------------------

    # A percentage or explicit period comparison means the
    # model has to perform/interpret a quantitative calculation.
    if percentage_claims > 0:
        complexity += 1

    if period_comparisons > 0:
        complexity += 1

    # ---------------------------------------------------------
    # MULTI-METRIC REASONING
    # ---------------------------------------------------------

    if metric_count >= 3:
        complexity += 1

    if metric_count >= 5:
        complexity += 1

    # ---------------------------------------------------------
    # MULTIPLE CALCULATION SIGNALS
    # ---------------------------------------------------------

    if calculation_signals >= 3:
        complexity += 1

    if calculation_signals >= 6:
        complexity += 1

    # ---------------------------------------------------------
    # QUALITATIVE REASONING
    # ---------------------------------------------------------

    if reasoning_signals >= 2:
        complexity += 1

    if reasoning_signals >= 5:
        complexity += 1

    # ---------------------------------------------------------
    # REASONING TYPES
    # ---------------------------------------------------------

    if reasoning_type_count >= 2:
        complexity += 1

    if reasoning_type_count >= 4:
        complexity += 1

    return complexity


def validate_difficulty(
    input_text,
    expected_output,
    difficulty,
    reasoning_types=None,
):
    """
    Validate whether an example's actual complexity matches
    its assigned difficulty.

    Returns:

        {
            "success": True/False,
            "reason": ...,
            "details": {...}
        }
    """

    if difficulty not in DIFFICULTY_RULES:
        return {
            "success": False,
            "reason": "unsupported_difficulty",
        }

    if not input_text or not input_text.strip():
        return {
            "success": False,
            "reason": "empty_input",
        }

    if not expected_output or not expected_output.strip():
        return {
            "success": False,
            "reason": "empty_expected_output",
        }

    reasoning_types = reasoning_types or []

    combined_text = f"{input_text}\n{expected_output}"

    metrics = extract_financial_metrics(combined_text)
    metric_count = len(metrics)

    number_count = len(extract_numbers(combined_text))
    percentage_count = count_percentage_claims(combined_text)
    comparison_count = count_period_comparisons(combined_text)
    calculation_signal_count = count_calculation_signals(combined_text)
    reasoning_signal_count = count_reasoning_signals(combined_text)

    complexity = calculate_reasoning_complexity(
        combined_text,
        reasoning_type_count=len(reasoning_types),
    )

    rules = DIFFICULTY_RULES[difficulty]

    # ---------------------------------------------------------
    # METRIC COUNT
    # ---------------------------------------------------------

    if metric_count < rules["min_metrics"]:
        return {
            "success": False,
            "reason": "insufficient_metric_complexity",
            "details": {
                "difficulty": difficulty,
                "metric_count": metric_count,
                "required_minimum": rules["min_metrics"],
                "complexity": complexity,
            },
        }

    if (
        rules["max_metrics"] is not None
        and metric_count > rules["max_metrics"]
    ):
        return {
            "success": False,
            "reason": "excessive_metric_complexity",
            "details": {
                "difficulty": difficulty,
                "metric_count": metric_count,
                "maximum_allowed": rules["max_metrics"],
                "complexity": complexity,
            },
        }

    # ---------------------------------------------------------
    # REASONING TYPE COUNT
    # ---------------------------------------------------------

    if len(reasoning_types) < rules["min_reasoning"]:
        return {
            "success": False,
            "reason": "insufficient_reasoning_types",
            "details": {
                "difficulty": difficulty,
                "reasoning_type_count": len(reasoning_types),
                "required_minimum": rules["min_reasoning"],
                "complexity": complexity,
            },
        }

    # ---------------------------------------------------------
    # COMPLEXITY
    # ---------------------------------------------------------

    if complexity < rules["min_complexity"]:
        return {
            "success": False,
            "reason": "insufficient_reasoning_complexity",
            "details": {
                "difficulty": difficulty,
                "metric_count": metric_count,
                "number_count": number_count,
                "percentage_count": percentage_count,
                "comparison_count": comparison_count,
                "calculation_signal_count": calculation_signal_count,
                "reasoning_signal_count": reasoning_signal_count,
                "reasoning_type_count": len(reasoning_types),
                "complexity": complexity,
                "required_minimum": rules["min_complexity"],
            },
        }

    # ---------------------------------------------------------
    # HARD-SPECIFIC REQUIREMENTS
    # ---------------------------------------------------------

    if difficulty == "hard":

        if len(reasoning_types) < 3:
            return {
                "success": False,
                "reason": "hard_requires_multiple_reasoning_types",
                "details": {
                    "reasoning_type_count": len(reasoning_types),
                    "required_minimum": 3,
                    "complexity": complexity,
                },
            }

        if complexity < 6:
            return {
                "success": False,
                "reason": "hard_requires_high_complexity",
                "details": {
                    "complexity": complexity,
                    "required_minimum": 6,
                },
            }

    return {
        "success": True,
        "reason": None,
        "details": {
            "difficulty": difficulty,
            "metric_count": metric_count,
            "number_count": number_count,
            "percentage_count": percentage_count,
            "comparison_count": comparison_count,
            "calculation_signal_count": calculation_signal_count,
            "reasoning_signal_count": reasoning_signal_count,
            "reasoning_type_count": len(reasoning_types),
            "complexity": complexity,
        },
    }