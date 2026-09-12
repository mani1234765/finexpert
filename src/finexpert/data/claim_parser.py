import re


def extract_percentage_claims(text):
    """
    Extract percentage values from financial text.

    Examples:
        Revenue increased by 15%.
        Profit declined by 8.5%.
        Margin increased to 16.4%.
    """

    claims = []

    pattern = (
        r"(?P<direction>"
        r"increased|increases|grew|growth|rose|"
        r"declined|decreased|decreases|fell|drop|dropped"
        r")?"
        r"\s*"
        r"(?:by\s*)?"
        r"(?P<value>-?\d+(?:\.\d+)?)"
        r"\s*%"
    )

    matches = re.finditer(
        pattern,
        text,
        re.IGNORECASE,
    )

    for match in matches:
        value = float(
            match.group("value")
        )

        direction = match.group("direction")

        if direction:
            direction = direction.lower()

            negative_words = {
                "declined",
                "decreased",
                "decreases",
                "fell",
                "drop",
                "dropped",
            }

            if (
                direction in negative_words
                and value > 0
            ):
                value = -value

        claims.append(
            {
                "value": value,
                "text": match.group(0).strip(),
            }
        )

    return claims


def extract_money_values(text):
    """
    Extract financial values from text.

    Examples:
        ₹100 Cr
        ₹25.5 Cr
        100 crore
        50 Million
    """

    values = []

    pattern = (
        r"₹?\s*"
        r"(?P<value>\d+(?:\.\d+)?)"
        r"\s*"
        r"(?P<unit>"
        r"Cr|crore|crores|Lakh|Lakhs|Million|Billion"
        r")?"
    )

    matches = re.finditer(
        pattern,
        text,
        re.IGNORECASE,
    )

    for match in matches:
        value = float(
            match.group("value")
        )

        unit = match.group("unit")

        if unit:
            unit = unit.lower()

        values.append(
            {
                "value": value,
                "unit": unit,
                "text": match.group(0).strip(),
            }
        )

    return values


def extract_growth_claims(text):
    """
    Extract financial growth claims.

    Examples:
        Revenue increased by 15%.
        Net profit declined by 8.6%.
        Operating expenses increased by 10%.
    """

    claims = []

    # IMPORTANT:
    # Longer metric names must come before shorter
    # metric names. Otherwise "expenses" would match
    # inside "operating expenses".
    pattern = (
        r"(?P<metric>"
        r"operating expenses|"
        r"operating profit|"
        r"net profit|"
        r"cash reserves|"
        r"cash flow|"
        r"revenue|"
        r"profit|"
        r"earnings|"
        r"expenses|"
        r"debt|"
        r"cash"
        r")"
        r"\s+"
        r"(?P<direction>"
        r"increased|increases|grew|rose|"
        r"declined|decreased|decreases|fell|"
        r"dropped|drop"
        r")"
        r"\s+"
        r"(?:by\s+)?"
        r"(?P<value>\d+(?:\.\d+)?)"
        r"\s*%"
    )

    matches = re.finditer(
        pattern,
        text,
        re.IGNORECASE,
    )

    for match in matches:
        metric = match.group(
            "metric"
        ).lower()

        direction = match.group(
            "direction"
        ).lower()

        value = float(
            match.group("value")
        )

        negative_words = {
            "declined",
            "decreased",
            "decreases",
            "fell",
            "dropped",
            "drop",
        }

        if direction in negative_words:
            value = -value

        claims.append(
            {
                "metric": metric,
                "change": value,
                "text": match.group(0).strip(),
            }
        )

    return claims


def extract_value_change_claims(text):
    """
    Extract financial value changes.

    Examples:
        Revenue increased from ₹100 Cr to ₹130 Cr.
        Operating profit declined from ₹20 Cr to ₹15 Cr.
        Operating expenses increased from ₹40 Cr to ₹50 Cr.
    """

    claims = []

    # Longer metric names must come first.
    pattern = (
        r"(?P<metric>"
        r"operating expenses|"
        r"operating profit|"
        r"net profit|"
        r"cash reserves|"
        r"cash flow|"
        r"revenue|"
        r"profit|"
        r"earnings|"
        r"expenses|"
        r"debt|"
        r"cash"
        r")"
        r"\s+"
        r"(?P<direction>"
        r"increased|increases|grew|rose|"
        r"declined|decreased|decreases|fell|"
        r"dropped|drop"
        r")"
        r"\s+"
        r"from\s+"
        r"₹?\s*"
        r"(?P<previous_value>\d+(?:\.\d+)?)"
        r"\s*"
        r"(?P<previous_unit>"
        r"Cr|crore|crores|Lakh|Lakhs|Million|Billion"
        r")?"
        r"\s+to\s+"
        r"₹?\s*"
        r"(?P<current_value>\d+(?:\.\d+)?)"
        r"\s*"
        r"(?P<current_unit>"
        r"Cr|crore|crores|Lakh|Lakhs|Million|Billion"
        r")?"
    )

    matches = re.finditer(
        pattern,
        text,
        re.IGNORECASE,
    )

    for match in matches:
        metric = match.group(
            "metric"
        ).lower()

        previous_value = float(
            match.group("previous_value")
        )

        current_value = float(
            match.group("current_value")
        )

        previous_unit = match.group(
            "previous_unit"
        )

        current_unit = match.group(
            "current_unit"
        )

        if previous_unit:
            previous_unit = previous_unit.lower()

        if current_unit:
            current_unit = current_unit.lower()

        claims.append(
            {
                "metric": metric,
                "previous_value": previous_value,
                "current_value": current_value,
                "previous_unit": previous_unit,
                "current_unit": current_unit,
                "text": match.group(0).strip(),
            }
        )

    return claims


def extract_margin_claims(text):
    """
    Extract financial margin claims.

    Examples:
        Operating profit margin increased from 15% to 16.4%.
        Operating profit margin decreased from 20% to 14.8%.
        Net profit margin increased from 8% to 10%.
    """

    claims = []

    pattern = (
        r"(?P<metric>"
        r"operating profit margin|"
        r"net profit margin|"
        r"profit margin"
        r")"
        r"\s+"
        r"(?P<direction>"
        r"increased|increases|grew|rose|"
        r"declined|decreased|decreases|fell|"
        r"dropped|drop|changed"
        r")?"
        r"\s*"
        r"(?:from\s+)?"
        r"(?P<previous_value>\d+(?:\.\d+)?)"
        r"\s*%"
        r"\s+to\s+"
        r"(?P<current_value>\d+(?:\.\d+)?)"
        r"\s*%"
    )

    matches = re.finditer(
        pattern,
        text,
        re.IGNORECASE,
    )

    for match in matches:
        claims.append(
            {
                "metric": match.group(
                    "metric"
                ).lower(),
                "previous_value": float(
                    match.group("previous_value")
                ),
                "current_value": float(
                    match.group("current_value")
                ),
                "text": match.group(0).strip(),
            }
        )

    return claims


def extract_ratio_claims(text):
    """
    Extract financial ratio claims.

    Supports ratios expressed using 'x' or
    plain decimal values.

    Examples:
        Debt-to-equity ratio is 1.50.
        Current ratio is 1.25.
        Asset turnover is 1.75x.
        Debt-to-revenue is 0.65.
    """

    claims = []

    pattern = (
        r"(?P<metric>"
        r"debt-to-equity|"
        r"debt-to-revenue|"
        r"current ratio|"
        r"asset turnover|"
        r"cash-to-debt|"
        r"return on assets|"
        r"return on equity"
        r")"
        r"(?:\s+ratio)?"
        r"\s+"
        r"(?:is|was|equals|of)"
        r"\s+"
        r"(?P<value>\d+(?:\.\d+)?)"
        r"\s*(?P<unit>x)?"
    )

    matches = re.finditer(
        pattern,
        text,
        re.IGNORECASE,
    )

    for match in matches:
        metric = match.group(
            "metric"
        ).lower()

        value = float(
            match.group("value")
        )

        unit = match.group("unit")

        claims.append(
            {
                "metric": metric,
                "value": value,
                "unit": unit,
                "text": match.group(0).strip(),
            }
        )

    return claims