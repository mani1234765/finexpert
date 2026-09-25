import random


# ============================================================
# SCENARIO TYPES
# ============================================================

SCENARIO_TYPES = [
    # Existing 10
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

    # Advanced 40
    "earnings_quality",
    "profit_to_cash_conversion",
    "receivables_revenue_divergence",
    "inventory_buildup",
    "cfo_net_income_divergence",
    "aggressive_revenue_recognition",
    "one_time_gain_distortion",
    "ebitda_quality",
    "cash_conversion_cycle",
    "working_capital_release",
    "supplier_financing",
    "negative_working_capital",
    "seasonal_working_capital",
    "working_capital_stress",
    "debt_maturity_wall",
    "interest_coverage_stress",
    "floating_rate_debt_sensitivity",
    "debt_covenant_headroom",
    "refinancing_liquidity_risk",
    "debt_reduction_equity_dilution",
    "debt_restructuring",
    "eps_share_count_dilution",
    "buyback_eps_growth",
    "stock_based_compensation",
    "roe_buyback_distortion",
    "capital_allocation",
    "depreciation_policy_change",
    "impairment_cash_flow",
    "deferred_tax_distortion",
    "lease_accounting",
    "foreign_exchange_distortion",
    "inflation_distortion",
    "valuation_growth_profitability",
    "multiple_expansion",
    "dcf_sensitivity",
    "wacc_growth_tradeoff",
    "enterprise_value_bridge",
    "customer_acquisition_economics",
    "rule_of_40",
    "cohort_economics",
]


# ============================================================
# COMMON HELPERS
# ============================================================


def calculate_percentage_change(old_value, new_value):
    """
    Calculate percentage change between two values.
    """

    if old_value == 0:
        raise ValueError(
            "Cannot calculate percentage change from zero."
        )

    return (
        (new_value - old_value)
        / old_value
    ) * 100


def _scaled_value(value, percentage):
    """
    Apply a percentage change to a value.
    """

    return value * (1 + percentage / 100)


# ============================================================
# EXISTING 10 SCENARIOS
# ============================================================


def generate_revenue_growth_scenario(rng):
    previous_revenue = rng.choice(
        [100, 150, 200, 250, 300, 400, 500]
    )

    growth_rate = rng.choice(
        [5, 8, 10, 12, 15, 20, 25, 30]
    )

    current_revenue = _scaled_value(
        previous_revenue,
        growth_rate,
    )

    return {
        "scenario_type": "revenue_growth",
        "metrics": {
            "previous_revenue": previous_revenue,
            "current_revenue": current_revenue,
        },
        "expected_signals": [
            "revenue_growth",
        ],
    }


def generate_profitability_scenario(rng):
    previous_revenue = rng.choice(
        [200, 300, 400, 500, 600]
    )

    revenue_growth = rng.choice(
        [5, 10, 15, 20]
    )

    current_revenue = _scaled_value(
        previous_revenue,
        revenue_growth,
    )

    previous_profit = rng.choice(
        [30, 40, 50, 60, 80, 100]
    )

    profit_change = rng.choice(
        [-25, -20, -15, -10, 10, 15, 20, 25]
    )

    current_profit = _scaled_value(
        previous_profit,
        profit_change,
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
    revenue = rng.choice(
        [200, 300, 400, 500, 600]
    )

    previous_expenses = rng.choice(
        [80, 100, 120, 150, 180]
    )

    expense_change = rng.choice(
        [-10, 5, 10, 15, 20, 25]
    )

    current_expenses = _scaled_value(
        previous_expenses,
        expense_change,
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
    previous_debt = rng.choice(
        [100, 150, 200, 250, 300]
    )

    debt_change = rng.choice(
        [-20, -10, 10, 20, 30, 40]
    )

    current_debt = _scaled_value(
        previous_debt,
        debt_change,
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
    Generate a diverse liquidity scenario.

    The previous generator had only 25 possible
    current-assets/current-liabilities combinations.
    This version provides hundreds of combinations so
    the pipeline can generate 30 valid examples reliably.
    """

    current_assets = rng.choice(
        [
            90,
            100,
            110,
            120,
            130,
            140,
            150,
            165,
            175,
            185,
            200,
            220,
            240,
            260,
            280,
            300,
            325,
            350,
            375,
            400,
        ]
    )

    current_liabilities = rng.choice(
        [
            70,
            80,
            90,
            100,
            110,
            120,
            130,
            140,
            150,
            165,
            175,
            185,
            200,
            220,
            240,
            260,
            280,
            300,
            325,
            350,
        ]
    )

    return {
        "scenario_type": "liquidity",
        "metrics": {
            "current_assets": current_assets,
            "current_liabilities": current_liabilities,
        },
        "expected_signals": [
            "current_ratio",
        ],
    }


def generate_cash_flow_scenario(rng):
    previous_cash_flow = rng.choice(
        [20, 30, 40, 50, 60]
    )

    cash_flow_change = rng.choice(
        [-30, -20, -10, 10, 20, 30]
    )

    current_cash_flow = _scaled_value(
        previous_cash_flow,
        cash_flow_change,
    )

    return {
        "scenario_type": "cash_flow",
        "metrics": {
            "previous_cash_flow": previous_cash_flow,
            "current_cash_flow": current_cash_flow,
        },
        "expected_signals": [
            "cash_flow_change",
        ],
    }


def generate_efficiency_scenario(rng):
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
    previous_revenue = rng.choice(
        [300, 400, 500, 600]
    )

    revenue_change = rng.choice(
        [5, 10, 15, 20]
    )

    current_revenue = _scaled_value(
        previous_revenue,
        revenue_change,
    )

    previous_profit = rng.choice(
        [40, 50, 60, 80]
    )

    profit_change = rng.choice(
        [-20, -10, 10, 20]
    )

    current_profit = _scaled_value(
        previous_profit,
        profit_change,
    )

    previous_debt = rng.choice(
        [150, 200, 250]
    )

    debt_change = rng.choice(
        [10, 20, 30]
    )

    current_debt = _scaled_value(
        previous_debt,
        debt_change,
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
    previous_revenue = rng.choice(
        [400, 500, 600, 800]
    )

    revenue_change = rng.choice(
        [5, 10, 15, 20]
    )

    current_revenue = _scaled_value(
        previous_revenue,
        revenue_change,
    )

    previous_profit = rng.choice(
        [60, 80, 100, 120]
    )

    profit_change = rng.choice(
        [-20, -10, 10, 20]
    )

    current_profit = _scaled_value(
        previous_profit,
        profit_change,
    )

    previous_debt = rng.choice(
        [150, 200, 250, 300]
    )

    debt_change = rng.choice(
        [-10, 10, 20, 30]
    )

    current_debt = _scaled_value(
        previous_debt,
        debt_change,
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


# ============================================================
# ADVANCED 40 SCENARIOS
# ============================================================


def generate_earnings_quality_scenario(rng):
    revenue = rng.choice([500, 700, 900, 1200])
    net_income = rng.choice([60, 80, 100, 120])

    net_income_growth = rng.choice([15, 20, 25, 30])
    cfo_change = rng.choice([-30, -20, -10, 5])
    receivables_growth = rng.choice([30, 40, 50, 70])
    inventory_growth = rng.choice([20, 30, 40, 50])

    return {
        "scenario_type": "earnings_quality",
        "metrics": {
            "revenue": revenue,
            "net_income": net_income,
            "net_income_growth": net_income_growth,
            "cfo_change": cfo_change,
            "receivables_growth": receivables_growth,
            "inventory_growth": inventory_growth,
        },
        "expected_signals": [
            "earnings_quality",
            "profit_cash_divergence",
            "working_capital_pressure",
        ],
    }


def generate_profit_to_cash_conversion_scenario(rng):
    ebitda = rng.choice([150, 200, 250, 300])
    net_income = rng.choice([80, 100, 120, 150])
    operating_cash_flow = rng.choice([30, 40, 50, 60])
    capital_expenditure = rng.choice([80, 100, 120, 150])

    return {
        "scenario_type": "profit_to_cash_conversion",
        "metrics": {
            "ebitda": ebitda,
            "net_income": net_income,
            "operating_cash_flow": operating_cash_flow,
            "capital_expenditure": capital_expenditure,
        },
        "expected_signals": [
            "cash_conversion",
            "free_cash_flow",
            "earnings_quality",
        ],
    }


def generate_receivables_revenue_divergence_scenario(rng):
    revenue = rng.choice([500, 700, 900, 1200])
    receivables = rng.choice([80, 100, 120, 150])

    revenue_growth = rng.choice([10, 20, 30])
    receivables_growth = rng.choice([35, 50, 70, 90])

    return {
        "scenario_type": "receivables_revenue_divergence",
        "metrics": {
            "revenue": revenue,
            "receivables": receivables,
            "revenue_growth": revenue_growth,
            "receivables_growth": receivables_growth,
        },
        "expected_signals": [
            "receivables_growth",
            "revenue_quality",
            "collection_risk",
        ],
    }


def generate_inventory_buildup_scenario(rng):
    revenue = rng.choice([500, 700, 900, 1200])
    inventory = rng.choice([70, 100, 130, 160])

    revenue_growth = rng.choice([-5, 0, 5, 10])
    inventory_growth = rng.choice([30, 40, 55, 70])

    return {
        "scenario_type": "inventory_buildup",
        "metrics": {
            "revenue": revenue,
            "inventory": inventory,
            "revenue_growth": revenue_growth,
            "inventory_growth": inventory_growth,
        },
        "expected_signals": [
            "inventory_pressure",
            "working_capital",
            "demand_risk",
        ],
    }


def generate_cfo_net_income_divergence_scenario(rng):
    net_income = rng.choice([100, 150, 200, 250])
    operating_cash_flow = rng.choice([20, 40, 60, 80])

    return {
        "scenario_type": "cfo_net_income_divergence",
        "metrics": {
            "net_income": net_income,
            "operating_cash_flow": operating_cash_flow,
        },
        "expected_signals": [
            "cash_conversion",
            "earnings_quality",
        ],
    }


def generate_aggressive_revenue_recognition_scenario(rng):
    revenue_growth = rng.choice([25, 35, 45, 60])
    receivables_growth = rng.choice([50, 70, 90, 120])
    contract_assets_growth = rng.choice([40, 60, 80, 100])

    return {
        "scenario_type": "aggressive_revenue_recognition",
        "metrics": {
            "revenue_growth": revenue_growth,
            "receivables_growth": receivables_growth,
            "contract_assets_growth": contract_assets_growth,
        },
        "expected_signals": [
            "revenue_quality",
            "receivables",
            "contract_assets",
            "investigation_required",
        ],
    }


def generate_one_time_gain_distortion_scenario(rng):
    operating_profit = rng.choice([80, 100, 120, 150])
    reported_net_income = rng.choice([180, 220, 260, 300])
    one_time_gain = rng.choice([80, 100, 120, 150])

    return {
        "scenario_type": "one_time_gain_distortion",
        "metrics": {
            "operating_profit": operating_profit,
            "reported_net_income": reported_net_income,
            "one_time_gain": one_time_gain,
        },
        "expected_signals": [
            "recurring_profit",
            "non_recurring_gain",
            "earnings_quality",
        ],
    }


def generate_ebitda_quality_scenario(rng):
    reported_ebitda = rng.choice([200, 250, 300, 400])
    restructuring = rng.choice([20, 30, 40, 50])
    stock_compensation = rng.choice([15, 25, 35, 45])
    acquisition_costs = rng.choice([10, 20, 30, 40])

    return {
        "scenario_type": "ebitda_quality",
        "metrics": {
            "reported_ebitda": reported_ebitda,
            "restructuring": restructuring,
            "stock_compensation": stock_compensation,
            "acquisition_costs": acquisition_costs,
        },
        "expected_signals": [
            "adjusted_ebitda",
            "recurring_costs",
            "non_gaap_quality",
        ],
    }


def generate_cash_conversion_cycle_scenario(rng):
    dso = rng.choice([30, 45, 60, 75])
    dio = rng.choice([30, 45, 60, 90])
    dpo = rng.choice([20, 30, 45, 60])

    return {
        "scenario_type": "cash_conversion_cycle",
        "metrics": {
            "dso": dso,
            "dio": dio,
            "dpo": dpo,
        },
        "expected_signals": [
            "cash_conversion_cycle",
            "working_capital",
        ],
    }


def generate_working_capital_release_scenario(rng):
    previous_receivables = rng.choice([100, 150, 200])
    current_receivables = rng.choice([60, 90, 120])

    previous_inventory = rng.choice([100, 150, 200])
    current_inventory = rng.choice([70, 100, 130])

    return {
        "scenario_type": "working_capital_release",
        "metrics": {
            "previous_receivables": previous_receivables,
            "current_receivables": current_receivables,
            "previous_inventory": previous_inventory,
            "current_inventory": current_inventory,
        },
        "expected_signals": [
            "working_capital_release",
            "temporary_cash_flow",
        ],
    }


def generate_supplier_financing_scenario(rng):
    previous_payables = rng.choice([100, 150, 200])
    current_payables = rng.choice([160, 220, 280])
    operating_cash_flow = rng.choice([100, 150, 200])

    return {
        "scenario_type": "supplier_financing",
        "metrics": {
            "previous_payables": previous_payables,
            "current_payables": current_payables,
            "operating_cash_flow": operating_cash_flow,
        },
        "expected_signals": [
            "supplier_financing",
            "working_capital",
            "cash_flow_quality",
        ],
    }


def generate_negative_working_capital_scenario(rng):
    current_assets = rng.choice([100, 150, 200])
    current_liabilities = rng.choice([180, 220, 280])
    operating_cash_flow = rng.choice([80, 120, 160])

    return {
        "scenario_type": "negative_working_capital",
        "metrics": {
            "current_assets": current_assets,
            "current_liabilities": current_liabilities,
            "operating_cash_flow": operating_cash_flow,
        },
        "expected_signals": [
            "negative_working_capital",
            "cash_generation",
        ],
    }


def generate_seasonal_working_capital_scenario(rng):
    peak_current_assets = rng.choice([250, 300, 400])
    peak_current_liabilities = rng.choice([180, 220, 280])

    trough_current_assets = rng.choice([120, 150, 180])
    trough_current_liabilities = rng.choice([140, 170, 210])

    return {
        "scenario_type": "seasonal_working_capital",
        "metrics": {
            "peak_current_assets": peak_current_assets,
            "peak_current_liabilities": peak_current_liabilities,
            "trough_current_assets": trough_current_assets,
            "trough_current_liabilities": trough_current_liabilities,
        },
        "expected_signals": [
            "seasonality",
            "liquidity",
            "point_in_time_bias",
        ],
    }


def generate_working_capital_stress_scenario(rng):
    revenue = rng.choice([500, 700, 900])
    receivables = rng.choice([100, 140, 180])
    inventory = rng.choice([100, 140, 180])
    payables = rng.choice([80, 100, 120])

    revenue_shock = rng.choice([-10, -20])
    receivables_shock = rng.choice([20, 30, 40])
    inventory_shock = rng.choice([15, 25, 35])
    payables_shock = rng.choice([-10, 0, 10])

    return {
        "scenario_type": "working_capital_stress",
        "metrics": {
            "revenue": revenue,
            "receivables": receivables,
            "inventory": inventory,
            "payables": payables,
            "revenue_shock": revenue_shock,
            "receivables_shock": receivables_shock,
            "inventory_shock": inventory_shock,
            "payables_shock": payables_shock,
        },
        "expected_signals": [
            "stress_testing",
            "working_capital",
            "cash_requirement",
        ],
    }


def generate_debt_maturity_wall_scenario(rng):
    debt_2027 = rng.choice([50, 75, 100])
    debt_2028 = rng.choice([50, 100, 150])
    debt_2029 = rng.choice([250, 350, 450, 500])
    debt_2030 = rng.choice([25, 50, 75])

    cash = rng.choice([100, 150, 200])
    operating_cash_flow = rng.choice([80, 120, 160])

    return {
        "scenario_type": "debt_maturity_wall",
        "metrics": {
            "debt_2027": debt_2027,
            "debt_2028": debt_2028,
            "debt_2029": debt_2029,
            "debt_2030": debt_2030,
            "cash": cash,
            "operating_cash_flow": operating_cash_flow,
        },
        "expected_signals": [
            "maturity_concentration",
            "refinancing_risk",
            "liquidity",
        ],
    }


def generate_interest_coverage_stress_scenario(rng):
    ebit = rng.choice([150, 200, 250, 300])
    interest = rng.choice([40, 50, 60, 75])
    earnings_shock = rng.choice([-20, -40, -60])

    stressed_ebit = _scaled_value(
        ebit,
        earnings_shock,
    )

    return {
        "scenario_type": "interest_coverage_stress",
        "metrics": {
            "ebit": ebit,
            "interest_expense": interest,
            "earnings_shock": earnings_shock,
            "stressed_ebit": stressed_ebit,
        },
        "expected_signals": [
            "interest_coverage",
            "stress_testing",
            "default_risk",
        ],
    }


def generate_floating_rate_debt_sensitivity_scenario(rng):
    total_debt = rng.choice([300, 500, 700, 1000])
    floating_percentage = rng.choice([40, 60, 80])
    current_rate = rng.choice([6, 7, 8])
    rate_shock_bps = rng.choice([100, 200, 300])

    return {
        "scenario_type": "floating_rate_debt_sensitivity",
        "metrics": {
            "total_debt": total_debt,
            "floating_percentage": floating_percentage,
            "current_rate": current_rate,
            "rate_shock_bps": rate_shock_bps,
        },
        "expected_signals": [
            "interest_sensitivity",
            "floating_rate_exposure",
        ],
    }


def generate_debt_covenant_headroom_scenario(rng):
    debt = rng.choice([400, 500, 600])
    ebitda = rng.choice([130, 150, 180, 200])
    maximum_leverage = rng.choice([3.5, 4.0, 4.5])
    ebitda_shock = rng.choice([-20, -30, -40])

    stressed_ebitda = _scaled_value(
        ebitda,
        ebitda_shock,
    )

    return {
        "scenario_type": "debt_covenant_headroom",
        "metrics": {
            "debt": debt,
            "ebitda": ebitda,
            "maximum_leverage": maximum_leverage,
            "ebitda_shock": ebitda_shock,
            "stressed_ebitda": stressed_ebitda,
        },
        "expected_signals": [
            "covenant_headroom",
            "leverage",
            "stress_testing",
        ],
    }


def generate_refinancing_liquidity_risk_scenario(rng):
    cash = rng.choice([400, 500, 600])
    total_debt = rng.choice([400, 500, 600])
    debt_due_soon = rng.choice([300, 400, 500])
    restricted_cash = rng.choice([200, 300, 350])

    return {
        "scenario_type": "refinancing_liquidity_risk",
        "metrics": {
            "cash": cash,
            "total_debt": total_debt,
            "debt_due_soon": debt_due_soon,
            "restricted_cash": restricted_cash,
        },
        "expected_signals": [
            "available_liquidity",
            "refinancing_risk",
            "restricted_cash",
        ],
    }


def generate_debt_reduction_equity_dilution_scenario(rng):
    initial_debt = rng.choice([500, 700, 900])
    debt_repayment = rng.choice([200, 300])
    equity_issued = debt_repayment
    existing_shares = rng.choice([100, 150, 200])
    new_shares = rng.choice([20, 30, 40])

    return {
        "scenario_type": "debt_reduction_equity_dilution",
        "metrics": {
            "initial_debt": initial_debt,
            "debt_repayment": debt_repayment,
            "equity_issued": equity_issued,
            "existing_shares": existing_shares,
            "new_shares": new_shares,
        },
        "expected_signals": [
            "leverage_reduction",
            "equity_dilution",
            "capital_structure",
        ],
    }


def generate_debt_restructuring_scenario(rng):
    old_interest_rate = rng.choice([9, 10, 11, 12])
    new_interest_rate = old_interest_rate - rng.choice([1, 2, 3])
    debt = rng.choice([400, 600, 800])
    old_maturity = rng.choice([2, 3])
    new_maturity = old_maturity + rng.choice([2, 3])

    return {
        "scenario_type": "debt_restructuring",
        "metrics": {
            "debt": debt,
            "old_interest_rate": old_interest_rate,
            "new_interest_rate": new_interest_rate,
            "old_maturity_years": old_maturity,
            "new_maturity_years": new_maturity,
        },
        "expected_signals": [
            "interest_savings",
            "maturity_extension",
            "refinancing_risk",
        ],
    }


def generate_eps_share_count_dilution_scenario(rng):
    net_income = rng.choice([100, 150, 200, 250])
    income_growth = rng.choice([5, 10, 15])
    share_growth = rng.choice([15, 20, 25])

    return {
        "scenario_type": "eps_share_count_dilution",
        "metrics": {
            "net_income": net_income,
            "income_growth": income_growth,
            "share_growth": share_growth,
        },
        "expected_signals": [
            "eps",
            "share_dilution",
            "per_share_growth",
        ],
    }


def generate_buyback_eps_growth_scenario(rng):
    net_income = rng.choice([100, 150, 200])
    share_count_reduction = rng.choice([10, 15, 20])

    return {
        "scenario_type": "buyback_eps_growth",
        "metrics": {
            "net_income": net_income,
            "share_count_reduction": share_count_reduction,
        },
        "expected_signals": [
            "eps_growth",
            "buybacks",
            "underlying_earnings",
        ],
    }


def generate_stock_based_compensation_scenario(rng):
    net_income = rng.choice([150, 200, 250])
    stock_compensation = rng.choice([20, 30, 40, 50])
    basic_shares = rng.choice([100, 150, 200])
    diluted_shares = basic_shares + rng.choice([10, 20, 30])

    return {
        "scenario_type": "stock_based_compensation",
        "metrics": {
            "net_income": net_income,
            "stock_compensation": stock_compensation,
            "basic_shares": basic_shares,
            "diluted_shares": diluted_shares,
        },
        "expected_signals": [
            "stock_based_compensation",
            "dilution",
            "shareholder_economics",
        ],
    }


def generate_roe_buyback_distortion_scenario(rng):
    net_income = rng.choice([100, 150, 200])
    pre_buyback_equity = rng.choice([600, 800, 1000])
    post_buyback_equity = rng.choice([350, 450, 550])

    return {
        "scenario_type": "roe_buyback_distortion",
        "metrics": {
            "net_income": net_income,
            "pre_buyback_equity": pre_buyback_equity,
            "post_buyback_equity": post_buyback_equity,
        },
        "expected_signals": [
            "roe",
            "buyback_effect",
            "capital_structure",
        ],
    }


def generate_capital_allocation_scenario(rng):
    excess_cash = rng.choice([200, 300, 400])
    debt_cost = rng.choice([8, 10, 12])
    reinvestment_return = rng.choice([6, 10, 14, 18])
    acquisition_return = rng.choice([5, 12, 16, 20])

    return {
        "scenario_type": "capital_allocation",
        "metrics": {
            "excess_cash": excess_cash,
            "debt_cost": debt_cost,
            "reinvestment_return": reinvestment_return,
            "acquisition_return": acquisition_return,
        },
        "expected_signals": [
            "capital_allocation",
            "opportunity_cost",
            "return_comparison",
        ],
    }


def generate_depreciation_policy_change_scenario(rng):
    asset_base = rng.choice([500, 700, 900])
    old_useful_life = rng.choice([5, 6, 8])
    new_useful_life = old_useful_life + rng.choice([2, 3, 4])

    return {
        "scenario_type": "depreciation_policy_change",
        "metrics": {
            "asset_base": asset_base,
            "old_useful_life": old_useful_life,
            "new_useful_life": new_useful_life,
        },
        "expected_signals": [
            "depreciation",
            "reported_profit",
            "cash_flow",
            "accounting_policy",
        ],
    }


def generate_impairment_cash_flow_scenario(rng):
    impairment = rng.choice([200, 300, 400, 500])
    pre_impairment_assets = rng.choice([1000, 1500, 2000])

    return {
        "scenario_type": "impairment_cash_flow",
        "metrics": {
            "impairment": impairment,
            "pre_impairment_assets": pre_impairment_assets,
        },
        "expected_signals": [
            "impairment",
            "non_cash_expense",
            "asset_value",
        ],
    }


def generate_deferred_tax_distortion_scenario(rng):
    pretax_income = rng.choice([150, 200, 250])
    current_tax = rng.choice([30, 40, 50])
    deferred_tax_expense = rng.choice([-20, 20, 40, 60])

    return {
        "scenario_type": "deferred_tax_distortion",
        "metrics": {
            "pretax_income": pretax_income,
            "current_tax": current_tax,
            "deferred_tax_expense": deferred_tax_expense,
        },
        "expected_signals": [
            "deferred_tax",
            "cash_tax",
            "reported_profit",
        ],
    }


def generate_lease_accounting_scenario(rng):
    lease_expense = rng.choice([50, 70, 90])
    depreciation = rng.choice([25, 35, 45])
    lease_interest = rng.choice([15, 20, 25])

    return {
        "scenario_type": "lease_accounting",
        "metrics": {
            "lease_expense": lease_expense,
            "depreciation": depreciation,
            "lease_interest": lease_interest,
        },
        "expected_signals": [
            "lease_accounting",
            "ebitda",
            "depreciation",
            "interest",
        ],
    }


def generate_foreign_exchange_distortion_scenario(rng):
    reported_revenue_growth = rng.choice([15, 20, 25, 30])
    constant_currency_growth = rng.choice([5, 8, 10, 12])
    reported_margin = rng.choice([12, 14, 16])
    constant_currency_margin = rng.choice([10, 12, 14])

    return {
        "scenario_type": "foreign_exchange_distortion",
        "metrics": {
            "reported_revenue_growth": reported_revenue_growth,
            "constant_currency_growth": constant_currency_growth,
            "reported_margin": reported_margin,
            "constant_currency_margin": constant_currency_margin,
        },
        "expected_signals": [
            "foreign_exchange",
            "constant_currency",
            "reported_vs_underlying",
        ],
    }


def generate_inflation_distortion_scenario(rng):
    nominal_revenue_growth = rng.choice([12, 15, 20, 25])
    inflation_rate = rng.choice([6, 8, 10])
    nominal_profit_growth = rng.choice([10, 15, 20])
    cost_inflation = rng.choice([12, 15, 18])

    return {
        "scenario_type": "inflation_distortion",
        "metrics": {
            "nominal_revenue_growth": nominal_revenue_growth,
            "inflation_rate": inflation_rate,
            "nominal_profit_growth": nominal_profit_growth,
            "cost_inflation": cost_inflation,
        },
        "expected_signals": [
            "nominal_vs_real",
            "inflation",
            "margin_pressure",
        ],
    }


def generate_valuation_growth_profitability_scenario(rng):
    revenue_growth = rng.choice([20, 30, 40])
    margin = rng.choice([5, 10, 15])
    free_cash_flow = rng.choice([-50, -20, 20, 50])
    valuation_multiple = rng.choice([20, 30, 40, 50])

    return {
        "scenario_type": "valuation_growth_profitability",
        "metrics": {
            "revenue_growth": revenue_growth,
            "operating_margin": margin,
            "free_cash_flow": free_cash_flow,
            "valuation_multiple": valuation_multiple,
        },
        "expected_signals": [
            "growth",
            "profitability",
            "valuation",
            "free_cash_flow",
        ],
    }


def generate_multiple_expansion_scenario(rng):
    old_pe = rng.choice([15, 20, 25])
    new_pe = rng.choice([25, 30, 35, 40])
    eps_growth = rng.choice([5, 10, 15])

    return {
        "scenario_type": "multiple_expansion",
        "metrics": {
            "old_pe": old_pe,
            "new_pe": new_pe,
            "eps_growth": eps_growth,
        },
        "expected_signals": [
            "valuation_multiple",
            "eps_growth",
            "share_price_driver",
        ],
    }


def generate_dcf_sensitivity_scenario(rng):
    revenue_growth = rng.choice([8, 10, 12])
    operating_margin = rng.choice([12, 15, 18])
    wacc = rng.choice([8, 10, 12])
    terminal_growth = rng.choice([2, 3, 4])

    return {
        "scenario_type": "dcf_sensitivity",
        "metrics": {
            "revenue_growth": revenue_growth,
            "operating_margin": operating_margin,
            "wacc": wacc,
            "terminal_growth": terminal_growth,
        },
        "expected_signals": [
            "dcf",
            "wacc",
            "terminal_growth",
            "valuation_sensitivity",
        ],
    }


def generate_wacc_growth_tradeoff_scenario(rng):
    company_a_growth = rng.choice([15, 18, 20])
    company_a_wacc = rng.choice([10, 12, 14])

    company_b_growth = rng.choice([10, 12, 14])
    company_b_wacc = rng.choice([6, 7, 8])

    return {
        "scenario_type": "wacc_growth_tradeoff",
        "metrics": {
            "company_a_growth": company_a_growth,
            "company_a_wacc": company_a_wacc,
            "company_b_growth": company_b_growth,
            "company_b_wacc": company_b_wacc,
        },
        "expected_signals": [
            "risk_adjusted_growth",
            "wacc",
            "valuation",
        ],
    }


def generate_enterprise_value_bridge_scenario(rng):
    enterprise_value = rng.choice([1000, 1500, 2000])
    debt = rng.choice([300, 400, 500])
    cash = rng.choice([100, 150, 200])
    minority_interest = rng.choice([0, 20, 40])
    preferred_stock = rng.choice([0, 20, 30])

    return {
        "scenario_type": "enterprise_value_bridge",
        "metrics": {
            "enterprise_value": enterprise_value,
            "debt": debt,
            "cash": cash,
            "minority_interest": minority_interest,
            "preferred_stock": preferred_stock,
        },
        "expected_signals": [
            "enterprise_value",
            "equity_value",
            "valuation_bridge",
        ],
    }


def generate_customer_acquisition_economics_scenario(rng):
    cac = rng.choice([100, 150, 200, 250])
    arpu = rng.choice([30, 40, 50, 60])
    gross_margin = rng.choice([60, 70, 80])
    churn = rng.choice([2, 3, 4, 5])

    return {
        "scenario_type": "customer_acquisition_economics",
        "metrics": {
            "cac": cac,
            "arpu": arpu,
            "gross_margin": gross_margin,
            "monthly_churn": churn,
        },
        "expected_signals": [
            "cac",
            "ltv",
            "unit_economics",
            "payback",
        ],
    }


def generate_rule_of_40_scenario(rng):
    revenue_growth = rng.choice([10, 20, 30, 40])
    ebitda_margin = rng.choice([-10, 0, 5, 10, 20])

    return {
        "scenario_type": "rule_of_40",
        "metrics": {
            "revenue_growth": revenue_growth,
            "ebitda_margin": ebitda_margin,
        },
        "expected_signals": [
            "rule_of_40",
            "growth",
            "profitability",
        ],
    }


def generate_cohort_economics_scenario(rng):
    overall_revenue_growth = rng.choice([20, 30, 40])

    old_cac = rng.choice([100, 120, 150])
    new_cac = old_cac + rng.choice([30, 50, 70])

    old_churn = rng.choice([2, 3, 4])
    new_churn = old_churn + rng.choice([1, 2, 3])

    old_gross_margin = rng.choice([70, 75, 80])
    new_gross_margin = old_gross_margin - rng.choice([5, 10, 15])

    return {
        "scenario_type": "cohort_economics",
        "metrics": {
            "overall_revenue_growth": overall_revenue_growth,
            "old_cac": old_cac,
            "new_cac": new_cac,
            "old_churn": old_churn,
            "new_churn": new_churn,
            "old_gross_margin": old_gross_margin,
            "new_gross_margin": new_gross_margin,
        },
        "expected_signals": [
            "cohort_analysis",
            "cac",
            "churn",
            "gross_margin",
            "underlying_deterioration",
        ],
    }


# ============================================================
# GENERATOR REGISTRY
# ============================================================


GENERATORS = {
    # Existing
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

    # Advanced
    "earnings_quality": generate_earnings_quality_scenario,
    "profit_to_cash_conversion": (
        generate_profit_to_cash_conversion_scenario
    ),
    "receivables_revenue_divergence": (
        generate_receivables_revenue_divergence_scenario
    ),
    "inventory_buildup": (
        generate_inventory_buildup_scenario
    ),
    "cfo_net_income_divergence": (
        generate_cfo_net_income_divergence_scenario
    ),
    "aggressive_revenue_recognition": (
        generate_aggressive_revenue_recognition_scenario
    ),
    "one_time_gain_distortion": (
        generate_one_time_gain_distortion_scenario
    ),
    "ebitda_quality": generate_ebitda_quality_scenario,
    "cash_conversion_cycle": (
        generate_cash_conversion_cycle_scenario
    ),
    "working_capital_release": (
        generate_working_capital_release_scenario
    ),
    "supplier_financing": (
        generate_supplier_financing_scenario
    ),
    "negative_working_capital": (
        generate_negative_working_capital_scenario
    ),
    "seasonal_working_capital": (
        generate_seasonal_working_capital_scenario
    ),
    "working_capital_stress": (
        generate_working_capital_stress_scenario
    ),
    "debt_maturity_wall": (
        generate_debt_maturity_wall_scenario
    ),
    "interest_coverage_stress": (
        generate_interest_coverage_stress_scenario
    ),
    "floating_rate_debt_sensitivity": (
        generate_floating_rate_debt_sensitivity_scenario
    ),
    "debt_covenant_headroom": (
        generate_debt_covenant_headroom_scenario
    ),
    "refinancing_liquidity_risk": (
        generate_refinancing_liquidity_risk_scenario
    ),
    "debt_reduction_equity_dilution": (
        generate_debt_reduction_equity_dilution_scenario
    ),
    "debt_restructuring": (
        generate_debt_restructuring_scenario
    ),
    "eps_share_count_dilution": (
        generate_eps_share_count_dilution_scenario
    ),
    "buyback_eps_growth": (
        generate_buyback_eps_growth_scenario
    ),
    "stock_based_compensation": (
        generate_stock_based_compensation_scenario
    ),
    "roe_buyback_distortion": (
        generate_roe_buyback_distortion_scenario
    ),
    "capital_allocation": (
        generate_capital_allocation_scenario
    ),
    "depreciation_policy_change": (
        generate_depreciation_policy_change_scenario
    ),
    "impairment_cash_flow": (
        generate_impairment_cash_flow_scenario
    ),
    "deferred_tax_distortion": (
        generate_deferred_tax_distortion_scenario
    ),
    "lease_accounting": (
        generate_lease_accounting_scenario
    ),
    "foreign_exchange_distortion": (
        generate_foreign_exchange_distortion_scenario
    ),
    "inflation_distortion": (
        generate_inflation_distortion_scenario
    ),
    "valuation_growth_profitability": (
        generate_valuation_growth_profitability_scenario
    ),
    "multiple_expansion": (
        generate_multiple_expansion_scenario
    ),
    "dcf_sensitivity": (
        generate_dcf_sensitivity_scenario
    ),
    "wacc_growth_tradeoff": (
        generate_wacc_growth_tradeoff_scenario
    ),
    "enterprise_value_bridge": (
        generate_enterprise_value_bridge_scenario
    ),
    "customer_acquisition_economics": (
        generate_customer_acquisition_economics_scenario
    ),
    "rule_of_40": generate_rule_of_40_scenario,
    "cohort_economics": (
        generate_cohort_economics_scenario
    ),
}


# ============================================================
# PUBLIC API
# ============================================================


def generate_scenario(
    scenario_type=None,
    seed=None,
):
    """
    Generate a deterministic financial scenario.

    If scenario_type is not provided, one is selected
    randomly from all 50 available scenario types.
    """

    rng = random.Random(seed)

    if scenario_type is None:
        scenario_type = rng.choice(
            SCENARIO_TYPES
        )

    if scenario_type not in GENERATORS:
        raise ValueError(
            f"Unknown scenario type: {scenario_type}"
        )

    scenario = GENERATORS[scenario_type](rng)

    scenario["seed"] = seed

    return scenario