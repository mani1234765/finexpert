import re

from .claim_parser import extract_value_change_claims


NUMBER_PATTERN = re.compile(
    r"(?<![A-Za-z])[-+]?\d+(?:\.\d+)?"
)

ROUNDING_TOLERANCE = 0.15


def _extract_numbers(text):
    return [
        float(value)
        for value in NUMBER_PATTERN.findall(text)
    ]


def _number_key(value):
    return round(float(value), 6)


def _add_number(values, number):
    values.add(_number_key(number))


def _extract_metric_values(input_text):
    """
    Extract numeric values directly associated with supported
    financial metrics.

    Supports patterns such as:

        Revenue is ₹300 Cr
        Revenue of ₹300 Cr
        Debt is ₹105 Cr
        Cash is ₹30 Cr

    and change patterns such as:

        Operating expenses changed from ₹180 Cr to ₹216 Cr
        Operating profit increased from ₹120 Cr to ₹140 Cr
        Total debt declined from ₹200 Cr to ₹150 Cr

    The extractor intentionally does not scan the entire sentence
    after a metric because that can incorrectly associate numbers
    belonging to other metrics.
    """

    metrics = {}

    metric_patterns = {
        "revenue": r"\brevenue\b",
        "operating_profit": r"\boperating\s+profit\b",
        "net_profit": r"\bnet\s+profit\b",
        "net_income": r"\bnet\s+income\b",
        "debt": r"\b(?:total\s+)?debt\b",
        "cash": r"\bcash(?!\s+flow)(?:\s+reserves?)?\b",
        "current_assets": r"\bcurrent\s+assets\b",
        "current_liabilities": r"\bcurrent\s+liabilities\b",
        "equity": r"\b(?:total\s+)?equity\b",
        "total_assets": r"\btotal\s+assets\b",
        "operating_expenses": r"\boperating\s+expenses?\b",
    }

    number_pattern = (
        r"[-+]?(?:\d+(?:\.\d+)?|\.\d+)"
    )

    unit_pattern = (
        r"(?:\s*(?:Cr|crore|crores|Lakh|Lakhs|"
        r"Million|Billion))?"
    )

    for metric, metric_pattern in metric_patterns.items():

        values = []

        # ---------------------------------------------------------
        # Pattern 1:
        # metric changed from X to Y
        # ---------------------------------------------------------
        change_pattern = (
            metric_pattern
            + r"\s+"
            + r"(?:"
            + r"increased|"
            + r"decreased|"
            + r"declined|"
            + r"grew|"
            + r"rose|"
            + r"fell|"
            + r"changed|"
            + r"changing"
            + r")"
            + r"\s+from\s*"
            + r"(?:₹\s*)?"
            + rf"({number_pattern})"
            + unit_pattern
            + r"\s+to\s*"
            + r"(?:₹\s*)?"
            + rf"({number_pattern})"
            + unit_pattern
        )

        for match in re.finditer(
            change_pattern,
            input_text,
            flags=re.IGNORECASE,
        ):
            values.append(float(match.group(1)))
            values.append(float(match.group(2)))

        # ---------------------------------------------------------
        # Pattern 2:
        # metric is X
        # metric was X
        # metric are X
        # metric of X
        # metric: X
        # ---------------------------------------------------------
        direct_pattern = (
            metric_pattern
            + r"(?:"
            + r"\s+(?:is|was|were|are|of)"
            + r"|\s*[:=]"
            + r")?"
            + r"\s*"
            + r"(?:₹\s*)?"
            + rf"({number_pattern})"
            + unit_pattern
            + r"\b"
        )

        for match in re.finditer(
            direct_pattern,
            input_text,
            flags=re.IGNORECASE,
        ):
            values.append(float(match.group(1)))

        # Remove duplicates while preserving order.
        unique_values = []

        for value in values:
            if value not in unique_values:
                unique_values.append(value)

        if unique_values:
            metrics[metric] = unique_values

    return metrics


def _extract_change_pairs(input_text):
    """
    Extract previous/current values from explicit financial
    change statements.

    Supports forms such as:

        Revenue increased from ₹100 Cr to ₹110 Cr.
        Profit changed from ₹50 Cr to ₹57.5 Cr.
        Cash flow changing from ₹20 Cr to ₹17 Cr.
        Operating profit declined from ₹50 Cr to ₹40 Cr.
    """

    claims = []

    metric_pattern = (
        r"(?P<metric>"
        r"operating\s+expenses|"
        r"operating\s+profit|"
        r"net\s+profit|"
        r"cash\s+reserves|"
        r"cash\s+flow|"
        r"revenue|"
        r"profit|"
        r"earnings|"
        r"expenses|"
        r"debt|"
        r"cash"
        r")"
    )

    direction_pattern = (
        r"(?P<direction>"
        r"increased|"
        r"increases|"
        r"grew|"
        r"rose|"
        r"declined|"
        r"decreased|"
        r"decreases|"
        r"fell|"
        r"dropped|"
        r"drop|"
        r"changed|"
        r"changing"
        r")"
    )

    value_pattern = (
        r"₹?\s*"
        r"(?P<previous_value>"
        r"\d+(?:\.\d+)?"
        r")"
        r"\s*"
        r"(?:Cr|crore|crores|Lakh|Lakhs|Million|Billion)?"
        r"\s+to\s+"
        r"₹?\s*"
        r"(?P<current_value>"
        r"\d+(?:\.\d+)?"
        r")"
        r"\s*"
        r"(?:Cr|crore|crores|Lakh|Lakhs|Million|Billion)?"
    )

    pattern = (
        metric_pattern
        + r"\s+"
        + direction_pattern
        + r"\s+from\s+"
        + value_pattern
    )

    for match in re.finditer(
        pattern,
        input_text,
        flags=re.IGNORECASE,
    ):

        claims.append(
            {
                "metric": match.group(
                    "metric"
                ).lower(),
                "previous_value": float(
                    match.group(
                        "previous_value"
                    )
                ),
                "current_value": float(
                    match.group(
                        "current_value"
                    )
                ),
            }
        )

    return claims


def _extract_generic_change_pairs(input_text):
    """
    Fallback parser for explicit 'from X to Y' expressions.

    This intentionally does not depend on the wording of the
    metric or direction.

    Examples:

        changing from ₹20 Cr to ₹17 Cr
        from ₹100 Cr to ₹110 Cr
        changed from 50 to 45

    These pairs are still explicitly present in the input,
    so any percentage calculated from them is source-grounded.
    """

    claims = []

    pattern = (
        r"from\s+"
        r"₹?\s*"
        r"(?P<previous_value>"
        r"\d+(?:\.\d+)?"
        r")"
        r"\s*"
        r"(?:Cr|crore|crores|Lakh|Lakhs|Million|Billion)?"
        r"\s+to\s+"
        r"₹?\s*"
        r"(?P<current_value>"
        r"\d+(?:\.\d+)?"
        r")"
        r"\s*"
        r"(?:Cr|crore|crores|Lakh|Lakhs|Million|Billion)?"
    )

    for match in re.finditer(
        pattern,
        input_text,
        flags=re.IGNORECASE,
    ):

        claims.append(
            {
                "previous_value": float(
                    match.group(
                        "previous_value"
                    )
                ),
                "current_value": float(
                    match.group(
                        "current_value"
                    )
                ),
            }
        )

    return claims


def _derived_percentages(input_text):
    """
    Calculate all percentage changes that can be derived
    directly from explicit previous/current values in the input.
    """

    values = set()

    claims = []

    # Parser from claim_parser.py.
    claims.extend(
        extract_value_change_claims(
            input_text
        )
    )

    # Metric-aware fallback.
    claims.extend(
        _extract_change_pairs(
            input_text
        )
    )

    # Generic 'from X to Y' fallback.
    claims.extend(
        _extract_generic_change_pairs(
            input_text
        )
    )

    for claim in claims:

        previous = claim[
            "previous_value"
        ]

        current = claim[
            "current_value"
        ]

        if previous == 0:
            continue

        change = (
            (current - previous)
            / previous
        ) * 100

        # Preserve both signed and absolute forms.
        for value in (
            change,
            abs(change),
            round(change, 1),
            round(abs(change), 1),
            round(change, 2),
            round(abs(change), 2),
        ):
            _add_number(
                values,
                value
            )

    return values


def _derived_ratios(input_text):
    """
    Calculate ratios and percentage-based financial metrics
    that can be derived directly from the supplied figures.
    """

    values = set()

    metrics = _extract_metric_values(
        input_text
    )

    def add_ratio(
        numerator,
        denominator,
        as_percent=False,
    ):
        if (
            numerator not in metrics
            or denominator not in metrics
        ):
            return

        for left in metrics[numerator]:

            for right in metrics[denominator]:

                if right == 0:
                    continue

                result = (
                    left / right
                )

                if as_percent:
                    result *= 100

                for value in (
                    result,
                    round(result, 1),
                    round(result, 2),
                ):
                    _add_number(
                        values,
                        value,
                    )

    # ----------------------------------------
    # Percentage-based metrics
    # ----------------------------------------

    # Operating margin
    add_ratio(
        "operating_profit",
        "revenue",
        as_percent=True,
    )

    # Profit margin
    add_ratio(
        "profit",
        "revenue",
        as_percent=True,
    )

    # Net profit margin
    add_ratio(
        "net_profit",
        "revenue",
        as_percent=True,
    )

    # Operating expense ratio
    add_ratio(
        "operating_expenses",
        "revenue",
        as_percent=True,
    )

    # Return on assets
    add_ratio(
        "net_income",
        "total_assets",
        as_percent=True,
    )

    # Return on equity
    add_ratio(
        "net_income",
        "equity",
        as_percent=True,
    )

    # ----------------------------------------
    # Plain ratios
    # ----------------------------------------

    # Debt-to-equity
    add_ratio(
        "debt",
        "equity",
        as_percent=False,
    )

    # Debt-to-revenue
    add_ratio(
        "debt",
        "revenue",
        as_percent=False,
    )

    # Current ratio
    add_ratio(
        "current_assets",
        "current_liabilities",
        as_percent=False,
    )

    # Cash-to-debt
    add_ratio(
        "cash",
        "debt",
        as_percent=False,
    )

    # Asset turnover
    add_ratio(
        "revenue",
        "total_assets",
        as_percent=False,
    )

    return values


def _approximately_present(
    number,
    allowed_values,
):
    return any(
        abs(number - allowed)
        <= ROUNDING_TOLERANCE
        for allowed in allowed_values
    )


def validate_source_consistency(
    input_text,
    expected_output,
):
    """
    Validate that quantitative output claims are grounded
    in the supplied input.

    Accepted output numbers must be:

        1. Explicitly present in the input, or
        2. Derived percentage changes from input values, or
        3. Derived ratios/margins from input values.
    """

    if not input_text.strip():
        return {
            "success": False,
            "reason": "empty_input",
        }

    if not expected_output.strip():
        return {
            "success": False,
            "reason": "empty_expected_output",
        }

    # ---------------------------------------------
    # Explicit input numbers
    # ---------------------------------------------

    input_numbers = {
        _number_key(number)
        for number in _extract_numbers(
            input_text
        )
    }

    allowed_numbers = set(
        input_numbers
    )

    # ---------------------------------------------
    # Derived percentage changes
    # ---------------------------------------------

    derived_percentage_values = (
        _derived_percentages(
            input_text
        )
    )

    allowed_numbers.update(
        derived_percentage_values
    )

    # ---------------------------------------------
    # Derived ratios / margins
    # ---------------------------------------------

    derived_ratio_values = (
        _derived_ratios(
            input_text
        )
    )

    allowed_numbers.update(
        derived_ratio_values
    )

    # ---------------------------------------------
    # Validate output numbers
    # ---------------------------------------------

    output_numbers = _extract_numbers(
        expected_output
    )

    unsupported = []

    for number in output_numbers:

        if not _approximately_present(
            number,
            allowed_numbers,
        ):
            unsupported.append(
                number
            )

    if unsupported:

        unique_unsupported = []

        for number in unsupported:

            if (
                number
                not in unique_unsupported
            ):
                unique_unsupported.append(
                    number
                )

        return {
            "success": False,
            "reason": (
                "unsupported_output_number"
            ),
            "unsupported_numbers": (
                unique_unsupported
            ),
        }

    return {
        "success": True,
        "reason": None,
        "details": {
            "input_number_count": (
                len(input_numbers)
            ),
            "output_number_count": (
                len(output_numbers)
            ),
            "derived_percentage_count": (
                len(
                    derived_percentage_values
                )
            ),
            "derived_ratio_count": (
                len(
                    derived_ratio_values
                )
            ),
        },
    }