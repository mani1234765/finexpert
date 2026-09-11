import re


def extract_percentage_claims(text):
    """
    Extract percentage values from financial text.
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
        value = float(match.group("value"))
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

            if direction in negative_words and value > 0:
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

    Example:
        Revenue increased from ₹100 Cr to ₹130 Cr.
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
        value = float(match.group("value"))
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
        Operating profit decreased by 25%.
    """

    claims = []

    pattern = (
        r"(?P<metric>"
        r"operating profit|"
        r"net profit|"
        r"revenue|"
        r"profit|"
        r"earnings|"
        r"debt|"
        r"cash reserves|"
        r"cash|"
        r"expenses"
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
        metric = match.group("metric").lower()
        direction = match.group("direction").lower()
        value = float(match.group("value"))

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

    Example:
        Revenue increased from ₹100 Cr to ₹130 Cr.
        Operating profit decreased from ₹20 Cr to ₹15 Cr.
    """

    claims = []

    pattern = (
        r"(?P<metric>"
        r"operating profit|"
        r"net profit|"
        r"revenue|"
        r"profit|"
        r"earnings|"
        r"debt|"
        r"cash reserves|"
        r"cash|"
        r"expenses"
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
        metric = match.group("metric").lower()

        previous_value = float(
            match.group("previous_value")
        )

        current_value = float(
            match.group("current_value")
        )

        previous_unit = match.group("previous_unit")
        current_unit = match.group("current_unit")

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