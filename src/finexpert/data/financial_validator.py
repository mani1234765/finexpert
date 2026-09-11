def percentage_change(old_value, new_value):
    if old_value == 0:
        return {
            "success": False,
            "reason": "percentage_change_undefined"
        }

    percentage_change_value = (new_value - old_value) / old_value * 100

    return {
        "success": True,
        "calculated_value": percentage_change_value
    }


def profit_margin(revenue, profit):
    if revenue == 0:
        return {
            "success": False,
            "reason": "profit_margin_undefined"
        }

    profit_margin_value = (profit / revenue) * 100

    return {
        "success": True,
        "calculated_value": profit_margin_value
    }


def operating_margin(revenue, operating_income):
    if revenue == 0:
        return {
            "success": False,
            "reason": "operating_margin_undefined"
        }

    operating_margin_value = (operating_income / revenue) * 100

    return {
        "success": True,
        "calculated_value": operating_margin_value
    }


def net_profit_margin(revenue, net_income):
    if revenue == 0:
        return {
            "success": False,
            "reason": "net_profit_margin_undefined"
        }

    net_profit_margin_value = (net_income / revenue) * 100

    return {
        "success": True,
        "calculated_value": net_profit_margin_value
    }


def debt_to_equity(total_debt, total_equity):
    if total_equity == 0:
        return {
            "success": False,
            "reason": "debt_to_equity_undefined"
        }

    debt_to_equity_value = total_debt / total_equity

    return {
        "success": True,
        "calculated_value": debt_to_equity_value
    }


def current_ratio(current_assets, current_liabilities):
    if current_liabilities == 0:
        return {
            "success": False,
            "reason": "current_ratio_undefined"
        }

    current_ratio_value = current_assets / current_liabilities

    return {
        "success": True,
        "calculated_value": current_ratio_value
    }


def debt_to_revenue(total_debt, revenue):
    if revenue == 0:
        return {
            "success": False,
            "reason": "debt_to_revenue_undefined"
        }

    debt_to_revenue_value = total_debt / revenue

    return {
        "success": True,
        "calculated_value": debt_to_revenue_value
    }


def return_on_assets(net_income, total_assets):
    if total_assets == 0:
        return {
            "success": False,
            "reason": "return_on_assets_undefined"
        }

    return_on_assets_value = (net_income / total_assets) * 100

    return {
        "success": True,
        "calculated_value": return_on_assets_value
    }


def return_on_equity(net_income, total_equity):
    if total_equity == 0:
        return {
            "success": False,
            "reason": "return_on_equity_undefined"
        }

    return_on_equity_value = (net_income / total_equity) * 100

    return {
        "success": True,
        "calculated_value": return_on_equity_value
    }


def earning_growth_rate(previous_earnings, current_earnings):
    if previous_earnings == 0:
        return {
            "success": False,
            "reason": "earning_growth_rate_undefined"
        }

    earning_growth_rate_value = (
        (current_earnings - previous_earnings) / previous_earnings
    ) * 100

    return {
        "success": True,
        "calculated_value": earning_growth_rate_value
    }


def revenue_growth_rate(previous_revenue, current_revenue):
    if previous_revenue == 0:
        return {
            "success": False,
            "reason": "revenue_growth_rate_undefined"
        }

    revenue_growth_rate_value = (
        (current_revenue - previous_revenue) / previous_revenue
    ) * 100

    return {
        "success": True,
        "calculated_value": revenue_growth_rate_value
    }


def operating_expense_ratio(operating_expenses, revenue):
    if revenue == 0:
        return {
            "success": False,
            "reason": "operating_expense_ratio_undefined"
        }

    operating_expense_ratio_value = (
        operating_expenses / revenue
    ) * 100

    return {
        "success": True,
        "calculated_value": operating_expense_ratio_value
    }