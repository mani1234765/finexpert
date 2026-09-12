import random


SCENARIO_TYPES = [
    "revenue_growth",
    "profitability",
    "operating_expenses",
    "debt_leverage",
    "liquidity",
    "cash_flow",
    "efficiency",
    "risk_analysis",
    "multi_metric_comparison",
    "comprehensive_performance",
]


def calculate_percentage_change(old_value, new_value):
    """
    Calculate percentage change between two values.
    """

    if old_value == 0:
        raise ValueError(
            "Cannot calculate percentage change from zero."
        )

    return ((new_value - old_value) / old_value) * 100


def generate_revenue_growth_scenario(rng):
    """
    Generate a simple revenue growth scenario.
    """

    previous_revenue = rng.choice(
        [100, 150, 200, 250, 300, 400, 500]
    )

    growth_rate = rng.choice(
        [5, 8, 10, 12, 15, 20, 25, 30]
    )

    current_revenue = previous_revenue * (
        1 + growth_rate / 100
    )

    return {
        "scenario_type": "revenue_growth",
        "metrics": {
            "previous_revenue": previous_revenue,
            "current_revenue": current_revenue,
        },
        "expected_signals": [
            "revenue_growth"
        ],
    }


def generate_profitability_scenario(rng):
    """
    Generate a scenario where revenue and profit
    change between two periods.
    """

    previous_revenue = rng.choice(
        [200, 300, 400, 500, 600]
    )

    revenue_growth = rng.choice(
        [5, 10, 15, 20]
    )

    current_revenue = previous_revenue * (
        1 + revenue_growth / 100
    )

    previous_profit = rng.choice(
        [30, 40, 50, 60, 80, 100]
    )

    profit_change = rng.choice(
        [-25, -20, -15, -10, 10, 15, 20, 25]
    )

    current_profit = previous_profit * (
        1 + profit_change / 100
    )

    return {
        "scenario_type": "profitability",
        "metrics": {
            "previous_revenue": previous_revenue,
            "current_revenue": current_revenue,
            "previous_profit": previous_profit,
            "current_profit": current_profit,
        },
        "expected_signals": [
            "revenue_change",
            "profit_change",
            "margin_change",
        ],
    }


def generate_operating_expense_scenario(rng):
    """
    Generate an operating expense scenario.
    """

    revenue = rng.choice(
        [200, 300, 400, 500, 600]
    )

    previous_expenses = rng.choice(
        [80, 100, 120, 150, 180]
    )

    expense_change = rng.choice(
        [-10, 5, 10, 15, 20, 25]
    )

    current_expenses = previous_expenses * (
        1 + expense_change / 100
    )

    return {
        "scenario_type": "operating_expenses",
        "metrics": {
            "revenue": revenue,
            "previous_operating_expenses": previous_expenses,
            "current_operating_expenses": current_expenses,
        },
        "expected_signals": [
            "expense_change",
            "expense_ratio",
        ],
    }


def generate_debt_leverage_scenario(rng):
    """
    Generate a debt and leverage scenario.
    """

    previous_debt = rng.choice(
        [100, 150, 200, 250, 300]
    )

    debt_change = rng.choice(
        [-20, -10, 10, 20, 30, 40]
    )

    current_debt = previous_debt * (
        1 + debt_change / 100
    )

    equity = rng.choice(
        [150, 200, 250, 300, 400]
    )

    return {
        "scenario_type": "debt_leverage",
        "metrics": {
            "previous_debt": previous_debt,
            "current_debt": current_debt,
            "equity": equity,
        },
        "expected_signals": [
            "debt_change",
            "debt_to_equity",
        ],
    }


def generate_liquidity_scenario(rng):
    """
    Generate a liquidity scenario.
    """

    current_assets = rng.choice(
        [100, 150, 200, 250, 300]
    )

    current_liabilities = rng.choice(
        [80, 100, 150, 200, 250]
    )

    return {
        "scenario_type": "liquidity",
        "metrics": {
            "current_assets": current_assets,
            "current_liabilities": current_liabilities,
        },
        "expected_signals": [
            "current_ratio"
        ],
    }


def generate_cash_flow_scenario(rng):
    """
    Generate an operating cash flow scenario.
    """

    previous_cash_flow = rng.choice(
        [20, 30, 40, 50, 60]
    )

    cash_flow_change = rng.choice(
        [-30, -20, -10, 10, 20, 30]
    )

    current_cash_flow = previous_cash_flow * (
        1 + cash_flow_change / 100
    )

    return {
        "scenario_type": "cash_flow",
        "metrics": {
            "previous_cash_flow": previous_cash_flow,
            "current_cash_flow": current_cash_flow,
        },
        "expected_signals": [
            "cash_flow_change"
        ],
    }


def generate_efficiency_scenario(rng):
    """
    Generate an asset-efficiency scenario.
    """

    revenue = rng.choice(
        [300, 400, 500, 600, 800]
    )

    total_assets = rng.choice(
        [200, 300, 400, 500]
    )

    net_income = rng.choice(
        [20, 30, 40, 50, 60]
    )

    return {
        "scenario_type": "efficiency",
        "metrics": {
            "revenue": revenue,
            "total_assets": total_assets,
            "net_income": net_income,
        },
        "expected_signals": [
            "asset_turnover",
            "return_on_assets",
        ],
    }


def generate_risk_analysis_scenario(rng):
    """
    Generate a multi-signal financial risk scenario.
    """

    revenue = rng.choice(
        [300, 400, 500, 600]
    )

    debt = rng.choice(
        [200, 300, 400, 500]
    )

    cash = rng.choice(
        [40, 60, 80, 100]
    )

    operating_profit = rng.choice(
        [30, 50, 70, 90]
    )

    return {
        "scenario_type": "risk_analysis",
        "metrics": {
            "revenue": revenue,
            "debt": debt,
            "cash": cash,
            "operating_profit": operating_profit,
        },
        "expected_signals": [
            "leverage",
            "liquidity",
            "profitability",
        ],
    }


def generate_multi_metric_comparison_scenario(rng):
    """
    Generate a scenario containing multiple financial metrics.
    """

    previous_revenue = rng.choice(
        [300, 400, 500, 600]
    )

    revenue_change = rng.choice(
        [5, 10, 15, 20]
    )

    current_revenue = previous_revenue * (
        1 + revenue_change / 100
    )

    previous_profit = rng.choice(
        [40, 50, 60, 80]
    )

    profit_change = rng.choice(
        [-20, -10, 10, 20]
    )

    current_profit = previous_profit * (
        1 + profit_change / 100
    )

    previous_debt = rng.choice(
        [150, 200, 250]
    )

    debt_change = rng.choice(
        [10, 20, 30]
    )

    current_debt = previous_debt * (
        1 + debt_change / 100
    )

    return {
        "scenario_type": "multi_metric_comparison",
        "metrics": {
            "previous_revenue": previous_revenue,
            "current_revenue": current_revenue,
            "previous_profit": previous_profit,
            "current_profit": current_profit,
            "previous_debt": previous_debt,
            "current_debt": current_debt,
        },
        "expected_signals": [
            "revenue_change",
            "profit_change",
            "debt_change",
            "overall_financial_health",
        ],
    }


def generate_comprehensive_performance_scenario(rng):
    """
    Generate a comprehensive financial performance scenario.
    """

    previous_revenue = rng.choice(
        [400, 500, 600, 800]
    )

    revenue_change = rng.choice(
        [5, 10, 15, 20]
    )

    current_revenue = previous_revenue * (
        1 + revenue_change / 100
    )

    previous_profit = rng.choice(
        [60, 80, 100, 120]
    )

    profit_change = rng.choice(
        [-20, -10, 10, 20]
    )

    current_profit = previous_profit * (
        1 + profit_change / 100
    )

    previous_debt = rng.choice(
        [150, 200, 250, 300]
    )

    debt_change = rng.choice(
        [-10, 10, 20, 30]
    )

    current_debt = previous_debt * (
        1 + debt_change / 100
    )

    cash = rng.choice(
        [50, 70, 100, 120]
    )

    return {
        "scenario_type": "comprehensive_performance",
        "metrics": {
            "previous_revenue": previous_revenue,
            "current_revenue": current_revenue,
            "previous_profit": previous_profit,
            "current_profit": current_profit,
            "previous_debt": previous_debt,
            "current_debt": current_debt,
            "cash": cash,
        },
        "expected_signals": [
            "revenue_change",
            "profit_change",
            "margin_change",
            "debt_change",
            "liquidity",
            "overall_financial_health",
        ],
    }


GENERATORS = {
    "revenue_growth": generate_revenue_growth_scenario,
    "profitability": generate_profitability_scenario,
    "operating_expenses": generate_operating_expense_scenario,
    "debt_leverage": generate_debt_leverage_scenario,
    "liquidity": generate_liquidity_scenario,
    "cash_flow": generate_cash_flow_scenario,
    "efficiency": generate_efficiency_scenario,
    "risk_analysis": generate_risk_analysis_scenario,
    "multi_metric_comparison": (
        generate_multi_metric_comparison_scenario
    ),
    "comprehensive_performance": (
        generate_comprehensive_performance_scenario
    ),
}


def generate_scenario(
    scenario_type=None,
    seed=None,
):
    """
    Generate a deterministic financial scenario.

    If scenario_type is not provided, one is selected
    randomly from the available scenario types.
    """

    rng = random.Random(seed)

    if scenario_type is None:
        scenario_type = rng.choice(SCENARIO_TYPES)

    if scenario_type not in GENERATORS:
        raise ValueError(
            f"Unknown scenario type: {scenario_type}"
        )

    scenario = GENERATORS[scenario_type](rng)

    scenario["seed"] = seed

    return scenario