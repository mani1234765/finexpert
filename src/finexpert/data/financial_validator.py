def percentage_change(old_value, new_value):
    """
    Calculate percentage change between two values.

    Formula:
        ((new - old) / old) * 100

    Returns:
        success=True with calculated_value
        or success=False when the calculation is undefined.
    """

    if old_value == 0:
        return {
            "success": False,
            "reason": "percentage_change_undefined",
        }

    percentage_change_value = (
        (new_value - old_value)
        / old_value
    ) * 100

    return {
        "success": True,
        "calculated_value": percentage_change_value,
    }


def profit_margin(revenue, profit):
    """
    Calculate profit margin.

    Formula:
        (profit / revenue) * 100
    """

    if revenue == 0:
        return {
            "success": False,
            "reason": "profit_margin_undefined",
        }

    profit_margin_value = (
        profit / revenue
    ) * 100

    return {
        "success": True,
        "calculated_value": profit_margin_value,
    }


def operating_margin(revenue, operating_income):
    """
    Calculate operating profit margin.

    Formula:
        (operating income / revenue) * 100
    """

    if revenue == 0:
        return {
            "success": False,
            "reason": "operating_margin_undefined",
        }

    operating_margin_value = (
        operating_income / revenue
    ) * 100

    return {
        "success": True,
        "calculated_value": operating_margin_value,
    }


def net_profit_margin(revenue, net_income):
    """
    Calculate net profit margin.

    Formula:
        (net income / revenue) * 100
    """

    if revenue == 0:
        return {
            "success": False,
            "reason": "net_profit_margin_undefined",
        }

    net_profit_margin_value = (
        net_income / revenue
    ) * 100

    return {
        "success": True,
        "calculated_value": net_profit_margin_value,
    }


def debt_to_equity(total_debt, total_equity):
    """
    Calculate debt-to-equity ratio.

    Formula:
        total debt / total equity
    """

    if total_equity == 0:
        return {
            "success": False,
            "reason": "debt_to_equity_undefined",
        }

    debt_to_equity_value = (
        total_debt / total_equity
    )

    return {
        "success": True,
        "calculated_value": debt_to_equity_value,
    }


def current_ratio(
    current_assets,
    current_liabilities,
):
    """
    Calculate current ratio.

    Formula:
        current assets / current liabilities
    """

    if current_liabilities == 0:
        return {
            "success": False,
            "reason": "current_ratio_undefined",
        }

    current_ratio_value = (
        current_assets
        / current_liabilities
    )

    return {
        "success": True,
        "calculated_value": current_ratio_value,
    }


def debt_to_revenue(total_debt, revenue):
    """
    Calculate debt-to-revenue ratio.

    Formula:
        total debt / revenue
    """

    if revenue == 0:
        return {
            "success": False,
            "reason": "debt_to_revenue_undefined",
        }

    debt_to_revenue_value = (
        total_debt / revenue
    )

    return {
        "success": True,
        "calculated_value": debt_to_revenue_value,
    }


def return_on_assets(net_income, total_assets):
    """
    Calculate return on assets (ROA).

    Formula:
        (net income / total assets) * 100
    """

    if total_assets == 0:
        return {
            "success": False,
            "reason": "return_on_assets_undefined",
        }

    return_on_assets_value = (
        net_income / total_assets
    ) * 100

    return {
        "success": True,
        "calculated_value": return_on_assets_value,
    }


def return_on_equity(net_income, total_equity):
    """
    Calculate return on equity (ROE).

    Formula:
        (net income / total equity) * 100
    """

    if total_equity == 0:
        return {
            "success": False,
            "reason": "return_on_equity_undefined",
        }

    return_on_equity_value = (
        net_income / total_equity
    ) * 100

    return {
        "success": True,
        "calculated_value": return_on_equity_value,
    }


def earning_growth_rate(
    previous_earnings,
    current_earnings,
):
    """
    Calculate earnings growth rate.

    Formula:
        ((current - previous) / previous) * 100

    Kept as a dedicated function for compatibility
    with the existing validation layer.
    """

    if previous_earnings == 0:
        return {
            "success": False,
            "reason": "earning_growth_rate_undefined",
        }

    earning_growth_rate_value = (
        (current_earnings - previous_earnings)
        / previous_earnings
    ) * 100

    return {
        "success": True,
        "calculated_value": earning_growth_rate_value,
    }


def revenue_growth_rate(
    previous_revenue,
    current_revenue,
):
    """
    Calculate revenue growth rate.

    Formula:
        ((current - previous) / previous) * 100
    """

    if previous_revenue == 0:
        return {
            "success": False,
            "reason": "revenue_growth_rate_undefined",
        }

    revenue_growth_rate_value = (
        (current_revenue - previous_revenue)
        / previous_revenue
    ) * 100

    return {
        "success": True,
        "calculated_value": revenue_growth_rate_value,
    }


def operating_expense_ratio(
    operating_expenses,
    revenue,
):
    """
    Calculate operating expense ratio.

    Formula:
        (operating expenses / revenue) * 100
    """

    if revenue == 0:
        return {
            "success": False,
            "reason": "operating_expense_ratio_undefined",
        }

    operating_expense_ratio_value = (
        operating_expenses / revenue
    ) * 100

    return {
        "success": True,
        "calculated_value": operating_expense_ratio_value,
    }


def asset_turnover(
    revenue,
    total_assets,
):
    """
    Calculate asset turnover.

    Formula:
        revenue / total assets
    """

    if total_assets == 0:
        return {
            "success": False,
            "reason": "asset_turnover_undefined",
        }

    asset_turnover_value = (
        revenue / total_assets
    )

    return {
        "success": True,
        "calculated_value": asset_turnover_value,
    }


def cash_to_debt(
    cash,
    total_debt,
):
    """
    Calculate cash-to-debt ratio.

    Formula:
        cash / total debt
    """

    if total_debt == 0:
        return {
            "success": False,
            "reason": "cash_to_debt_undefined",
        }

    cash_to_debt_value = (
        cash / total_debt
    )

    return {
        "success": True,
        "calculated_value": cash_to_debt_value,
    }


def margin_change(
    previous_margin,
    current_margin,
):
    """
    Calculate the absolute change in a margin.

    Example:
        Previous margin = 15%
        Current margin = 16.4%

        Margin change = 1.4 percentage points

    Note:
        This is NOT percentage growth.
        It is a percentage-point change.
    """

    margin_change_value = (
        current_margin - previous_margin
    )

    return {
        "success": True,
        "calculated_value": margin_change_value,
    }