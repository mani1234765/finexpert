from .scenario_generator import generate_scenario


def _percentage(old_value, new_value):
    if old_value == 0:
        return None

    return (
        (new_value - old_value)
        / old_value
    ) * 100


def _direction(change):
    if change > 0:
        return "increased"

    if change < 0:
        return "declined"

    return "remained unchanged"


def _format_percentage(value):
    return f"{abs(value):.1f}%"


# ============================================================
# SCENARIO ENRICHERS
# ============================================================

def _enrich_revenue_growth(
    metrics,
    difficulty,
):
    previous_revenue = metrics[
        "previous_revenue"
    ]

    current_revenue = metrics[
        "current_revenue"
    ]

    if difficulty in {"medium", "hard"}:
        metrics[
            "previous_operating_profit"
        ] = round(
            previous_revenue * 0.20,
            2,
        )

        metrics[
            "current_operating_profit"
        ] = round(
            current_revenue * 0.17,
            2,
        )

    if difficulty == "hard":
        metrics[
            "previous_debt"
        ] = round(
            previous_revenue * 0.30,
            2,
        )

        metrics[
            "current_debt"
        ] = round(
            current_revenue * 0.40,
            2,
        )

        metrics[
            "previous_cash"
        ] = round(
            previous_revenue * 0.12,
            2,
        )

        metrics[
            "current_cash"
        ] = round(
            current_revenue * 0.09,
            2,
        )


def _enrich_profitability(
    metrics,
    difficulty,
):
    previous_revenue = metrics[
        "previous_revenue"
    ]

    current_revenue = metrics[
        "current_revenue"
    ]

    if difficulty in {"medium", "hard"}:
        metrics[
            "previous_debt"
        ] = round(
            previous_revenue * 0.30,
            2,
        )

        metrics[
            "current_debt"
        ] = round(
            current_revenue * 0.45,
            2,
        )

    if difficulty == "hard":
        metrics[
            "previous_cash"
        ] = round(
            previous_revenue * 0.12,
            2,
        )

        metrics[
            "current_cash"
        ] = round(
            current_revenue * 0.08,
            2,
        )


def _enrich_operating_expenses(
    metrics,
    difficulty,
):
    revenue = metrics["revenue"]

    previous_expenses = metrics[
        "previous_operating_expenses"
    ]

    current_expenses = metrics[
        "current_operating_expenses"
    ]

    if difficulty in {"medium", "hard"}:
        metrics[
            "previous_operating_profit"
        ] = round(
            revenue - previous_expenses,
            2,
        )

        metrics[
            "current_operating_profit"
        ] = round(
            revenue - current_expenses,
            2,
        )

    if difficulty == "hard":
        metrics["debt"] = round(
            revenue * 0.35,
            2,
        )

        metrics["cash"] = round(
            revenue * 0.10,
            2,
        )


def _enrich_debt_leverage(
    metrics,
    difficulty,
):
    previous_debt = metrics[
        "previous_debt"
    ]

    current_debt = metrics[
        "current_debt"
    ]

    if difficulty in {"medium", "hard"}:
        metrics[
            "previous_revenue"
        ] = round(
            previous_debt * 2.5,
            2,
        )

        metrics[
            "current_revenue"
        ] = round(
            current_debt * 2.2,
            2,
        )

    if difficulty == "hard":
        metrics[
            "previous_operating_profit"
        ] = round(
            metrics["previous_revenue"]
            * 0.15,
            2,
        )

        metrics[
            "current_operating_profit"
        ] = round(
            metrics["current_revenue"]
            * 0.12,
            2,
        )

        metrics[
            "previous_cash"
        ] = round(
            previous_debt * 0.25,
            2,
        )

        metrics[
            "current_cash"
        ] = round(
            current_debt * 0.18,
            2,
        )


def _enrich_liquidity(
    metrics,
    difficulty,
):
    current_assets = metrics[
        "current_assets"
    ]

    current_liabilities = metrics[
        "current_liabilities"
    ]

    if difficulty in {"medium", "hard"}:
        metrics["debt"] = round(
            current_liabilities * 1.4,
            2,
        )

        metrics["cash"] = round(
            current_assets * 0.25,
            2,
        )

    if difficulty == "hard":
        metrics[
            "operating_cash_flow"
        ] = round(
            current_assets * 0.18,
            2,
        )


def _enrich_cash_flow(
    metrics,
    difficulty,
):
    previous_cash_flow = metrics[
        "previous_cash_flow"
    ]

    current_cash_flow = metrics[
        "current_cash_flow"
    ]

    revenue = round(
        max(
            abs(previous_cash_flow),
            abs(current_cash_flow),
        ) * 5,
        2,
    )

    if difficulty in {"medium", "hard"}:
        metrics["revenue"] = revenue

        metrics[
            "operating_profit"
        ] = round(
            revenue * 0.15,
            2,
        )

    if difficulty == "hard":
        metrics["debt"] = round(
            revenue * 0.40,
            2,
        )

        metrics["cash"] = round(
            revenue * 0.10,
            2,
        )


def _enrich_efficiency(
    metrics,
    difficulty,
):
    total_assets = metrics[
        "total_assets"
    ]

    revenue = metrics[
        "revenue"
    ]

    net_income = metrics[
        "net_income"
    ]

    # Easy:
    # Keep the original three metrics.
    #
    # Efficiency requires:
    #   Asset Turnover = Revenue / Total Assets
    #   ROA = Net Income / Total Assets
    #
    # Therefore revenue, total_assets and
    # net_income are all required for an
    # easy efficiency example.

    if difficulty in {"medium", "hard"}:
        metrics["debt"] = round(
            total_assets * 0.45,
            2,
        )

    if difficulty == "hard":
        metrics["cash"] = round(
            total_assets * 0.10,
            2,
        )

        metrics[
            "previous_revenue"
        ] = round(
            revenue * 0.90,
            2,
        )

        metrics[
            "previous_total_assets"
        ] = round(
            total_assets * 1.10,
            2,
        )

        metrics[
            "previous_net_income"
        ] = round(
            net_income * 0.85,
            2,
        )


def _enrich_multi_metric(
    metrics,
    difficulty,
):
    if difficulty != "hard":
        return

    previous_revenue = metrics[
        "previous_revenue"
    ]

    current_revenue = metrics[
        "current_revenue"
    ]

    metrics[
        "previous_cash"
    ] = round(
        previous_revenue * 0.15,
        2,
    )

    metrics[
        "current_cash"
    ] = round(
        current_revenue * 0.10,
        2,
    )


def _enrich_comprehensive(
    metrics,
    difficulty,
):
    if difficulty != "hard":
        return

    previous_revenue = metrics[
        "previous_revenue"
    ]

    current_revenue = metrics[
        "current_revenue"
    ]

    metrics[
        "previous_cash"
    ] = round(
        previous_revenue * 0.15,
        2,
    )

    metrics[
        "current_cash"
    ] = round(
        current_revenue * 0.09,
        2,
    )


# ============================================================
# ENRICHER REGISTRY
# ============================================================

ENRICHERS = {
    "revenue_growth": (
        _enrich_revenue_growth
    ),
    "profitability": (
        _enrich_profitability
    ),
    "operating_expenses": (
        _enrich_operating_expenses
    ),
    "debt_leverage": (
        _enrich_debt_leverage
    ),
    "liquidity": _enrich_liquidity,
    "cash_flow": _enrich_cash_flow,
    "efficiency": _enrich_efficiency,
    "multi_metric_comparison": (
        _enrich_multi_metric
    ),
    "comprehensive_performance": (
        _enrich_comprehensive
    ),
}


# ============================================================
# INPUT BUILDERS
# ============================================================

def _build_revenue_input(
    company,
    metrics,
    difficulty,
):
    text = (
        f"{company} reported revenue "
        f"increasing from "
        f"₹{metrics['previous_revenue']:g} Cr "
        f"to "
        f"₹{metrics['current_revenue']:g} Cr."
    )

    if difficulty in {"medium", "hard"}:
        text += (
            f" Operating profit changed from "
            f"₹{metrics['previous_operating_profit']:g} Cr "
            f"to "
            f"₹{metrics['current_operating_profit']:g} Cr."
        )

    if difficulty == "hard":
        text += (
            f" Total debt changed from "
            f"₹{metrics['previous_debt']:g} Cr "
            f"to "
            f"₹{metrics['current_debt']:g} Cr."
            f" Cash changed from "
            f"₹{metrics['previous_cash']:g} Cr "
            f"to "
            f"₹{metrics['current_cash']:g} Cr."
        )

    return text


def _build_profitability_input(
    company,
    metrics,
    difficulty,
):
    text = (
        f"{company} reported revenue changing "
        f"from "
        f"₹{metrics['previous_revenue']:g} Cr "
        f"to "
        f"₹{metrics['current_revenue']:g} Cr. "
        f"Profit changed from "
        f"₹{metrics['previous_profit']:g} Cr "
        f"to "
        f"₹{metrics['current_profit']:g} Cr."
    )

    if difficulty in {"medium", "hard"}:
        text += (
            f" Debt changed from "
            f"₹{metrics['previous_debt']:g} Cr "
            f"to "
            f"₹{metrics['current_debt']:g} Cr."
        )

    if difficulty == "hard":
        text += (
            f" Cash changed from "
            f"₹{metrics['previous_cash']:g} Cr "
            f"to "
            f"₹{metrics['current_cash']:g} Cr."
        )

    return text


def _build_opex_input(
    company,
    metrics,
    difficulty,
):
    text = (
        f"{company} reported revenue of "
        f"₹{metrics['revenue']:g} Cr. "
        f"Operating expenses changed from "
        f"₹{metrics['previous_operating_expenses']:g} Cr "
        f"to "
        f"₹{metrics['current_operating_expenses']:g} Cr."
    )

    if difficulty in {"medium", "hard"}:
        text += (
            f" Operating profit changed from "
            f"₹{metrics['previous_operating_profit']:g} Cr "
            f"to "
            f"₹{metrics['current_operating_profit']:g} Cr."
        )

    if difficulty == "hard":
        text += (
            f" Debt is "
            f"₹{metrics['debt']:g} Cr "
            f"and cash is "
            f"₹{metrics['cash']:g} Cr."
        )

    return text


def _build_debt_input(
    company,
    metrics,
    difficulty,
):
    text = (
        f"{company} reported total debt "
        f"changing from "
        f"₹{metrics['previous_debt']:g} Cr "
        f"to "
        f"₹{metrics['current_debt']:g} Cr. "
        f"Equity is "
        f"₹{metrics['equity']:g} Cr."
    )

    if difficulty in {"medium", "hard"}:
        text += (
            f" Revenue changed from "
            f"₹{metrics['previous_revenue']:g} Cr "
            f"to "
            f"₹{metrics['current_revenue']:g} Cr."
        )

    if difficulty == "hard":
        text += (
            f" Operating profit changed from "
            f"₹{metrics['previous_operating_profit']:g} Cr "
            f"to "
            f"₹{metrics['current_operating_profit']:g} Cr."
            f" Cash changed from "
            f"₹{metrics['previous_cash']:g} Cr "
            f"to "
            f"₹{metrics['current_cash']:g} Cr."
        )

    return text


def _build_liquidity_input(
    company,
    metrics,
    difficulty,
):
    text = (
        f"{company} reported current assets "
        f"of ₹{metrics['current_assets']:g} Cr "
        f"and current liabilities of "
        f"₹{metrics['current_liabilities']:g} Cr."
    )

    if difficulty in {"medium", "hard"}:
        text += (
            f" Total debt is "
            f"₹{metrics['debt']:g} Cr "
            f"and cash is "
            f"₹{metrics['cash']:g} Cr."
        )

    if difficulty == "hard":
        text += (
            f" Operating cash flow is "
            f"₹{metrics['operating_cash_flow']:g} Cr."
        )

    return text


def _build_cash_flow_input(
    company,
    metrics,
    difficulty,
):
    text = (
        f"{company} reported cash flow "
        f"changing from "
        f"₹{metrics['previous_cash_flow']:g} Cr "
        f"to "
        f"₹{metrics['current_cash_flow']:g} Cr."
    )

    if difficulty in {"medium", "hard"}:
        text += (
            f" Revenue is "
            f"₹{metrics['revenue']:g} Cr "
            f"and operating profit is "
            f"₹{metrics['operating_profit']:g} Cr."
        )

    if difficulty == "hard":
        text += (
            f" Total debt is "
            f"₹{metrics['debt']:g} Cr "
            f"and cash is "
            f"₹{metrics['cash']:g} Cr."
        )

    return text


def _build_efficiency_input(
    company,
    metrics,
    difficulty,
):
    text = (
        f"{company} reported revenue of "
        f"₹{metrics['revenue']:g} Cr "
        f"and total assets of "
        f"₹{metrics['total_assets']:g} Cr. "
        f"Net income is "
        f"₹{metrics['net_income']:g} Cr."
    )

    if difficulty in {"medium", "hard"}:
        text += (
            f" Debt is "
            f"₹{metrics['debt']:g} Cr."
        )

    if difficulty == "hard":
        text += (
            f" Cash is "
            f"₹{metrics['cash']:g} Cr."
            f" Previous-period revenue was "
            f"₹{metrics['previous_revenue']:g} Cr, "
            f"previous-period total assets were "
            f"₹{metrics['previous_total_assets']:g} Cr, "
            f"and previous-period net income was "
            f"₹{metrics['previous_net_income']:g} Cr."
        )

    return text


def _build_risk_input(
    company,
    metrics,
):
    return (
        f"{company} reported debt of "
        f"₹{metrics['debt']:g} Cr, "
        f"revenue of "
        f"₹{metrics['revenue']:g} Cr, "
        f"cash of "
        f"₹{metrics['cash']:g} Cr, "
        f"and operating profit of "
        f"₹{metrics['operating_profit']:g} Cr."
    )


def _build_multi_input(
    company,
    metrics,
    difficulty,
):
    text = (
        f"{company} reported revenue changing "
        f"from "
        f"₹{metrics['previous_revenue']:g} Cr "
        f"to "
        f"₹{metrics['current_revenue']:g} Cr. "
        f"Profit changed from "
        f"₹{metrics['previous_profit']:g} Cr "
        f"to "
        f"₹{metrics['current_profit']:g} Cr. "
        f"Debt changed from "
        f"₹{metrics['previous_debt']:g} Cr "
        f"to "
        f"₹{metrics['current_debt']:g} Cr."
    )

    if difficulty == "hard":
        text += (
            f" Cash changed from "
            f"₹{metrics['previous_cash']:g} Cr "
            f"to "
            f"₹{metrics['current_cash']:g} Cr."
        )

    return text


INPUT_BUILDERS = {
    "revenue_growth": _build_revenue_input,
    "profitability": _build_profitability_input,
    "operating_expenses": _build_opex_input,
    "debt_leverage": _build_debt_input,
    "liquidity": _build_liquidity_input,
    "cash_flow": _build_cash_flow_input,
    "efficiency": _build_efficiency_input,
    "risk_analysis": _build_risk_input,
    "multi_metric_comparison": _build_multi_input,
    "comprehensive_performance": _build_multi_input,
}


# ============================================================
# CLAIM GENERATION
# ============================================================

def _build_claims(
    scenario_type,
    metrics,
    difficulty,
):
    if difficulty == "easy":
        return ""

    claims = []

    if scenario_type == "revenue_growth":
        revenue_change = _percentage(
            metrics["previous_revenue"],
            metrics["current_revenue"],
        )

        profit_change = _percentage(
            metrics[
                "previous_operating_profit"
            ],
            metrics[
                "current_operating_profit"
            ],
        )

        claims.append(
            "Revenue "
            f"{_direction(revenue_change)} by "
            f"{_format_percentage(revenue_change)}."
        )

        claims.append(
            "Operating profit "
            f"{_direction(profit_change)} by "
            f"{_format_percentage(profit_change)}."
        )

        if difficulty == "hard":
            debt_change = _percentage(
                metrics["previous_debt"],
                metrics["current_debt"],
            )

            cash_change = _percentage(
                metrics["previous_cash"],
                metrics["current_cash"],
            )

            claims.append(
                "Debt "
                f"{_direction(debt_change)} by "
                f"{_format_percentage(debt_change)}."
            )

            claims.append(
                "Cash "
                f"{_direction(cash_change)} by "
                f"{_format_percentage(cash_change)}."
            )

    elif scenario_type == "profitability":
        revenue_change = _percentage(
            metrics["previous_revenue"],
            metrics["current_revenue"],
        )

        profit_change = _percentage(
            metrics["previous_profit"],
            metrics["current_profit"],
        )

        claims.append(
            "Revenue "
            f"{_direction(revenue_change)} by "
            f"{_format_percentage(revenue_change)}."
        )

        claims.append(
            "Profit "
            f"{_direction(profit_change)} by "
            f"{_format_percentage(profit_change)}."
        )

        if difficulty in {"medium", "hard"}:
            debt_change = _percentage(
                metrics["previous_debt"],
                metrics["current_debt"],
            )

            claims.append(
                "Debt "
                f"{_direction(debt_change)} by "
                f"{_format_percentage(debt_change)}."
            )

        if difficulty == "hard":
            cash_change = _percentage(
                metrics["previous_cash"],
                metrics["current_cash"],
            )

            claims.append(
                "Cash "
                f"{_direction(cash_change)} by "
                f"{_format_percentage(cash_change)}."
            )

    elif scenario_type == "operating_expenses":
        expense_change = _percentage(
            metrics[
                "previous_operating_expenses"
            ],
            metrics[
                "current_operating_expenses"
            ],
        )

        profit_change = _percentage(
            metrics[
                "previous_operating_profit"
            ],
            metrics[
                "current_operating_profit"
            ],
        )

        claims.append(
            "Operating expenses "
            f"{_direction(expense_change)} by "
            f"{_format_percentage(expense_change)}."
        )

        claims.append(
            "Operating profit "
            f"{_direction(profit_change)} by "
            f"{_format_percentage(profit_change)}."
        )

    elif scenario_type == "debt_leverage":
        debt_change = _percentage(
            metrics["previous_debt"],
            metrics["current_debt"],
        )

        revenue_change = _percentage(
            metrics["previous_revenue"],
            metrics["current_revenue"],
        )

        claims.append(
            "Debt "
            f"{_direction(debt_change)} by "
            f"{_format_percentage(debt_change)}."
        )

        claims.append(
            "Revenue "
            f"{_direction(revenue_change)} by "
            f"{_format_percentage(revenue_change)}."
        )

        if difficulty == "hard":
            profit_change = _percentage(
                metrics[
                    "previous_operating_profit"
                ],
                metrics[
                    "current_operating_profit"
                ],
            )

            cash_change = _percentage(
                metrics["previous_cash"],
                metrics["current_cash"],
            )

            claims.append(
                "Operating profit "
                f"{_direction(profit_change)} by "
                f"{_format_percentage(profit_change)}."
            )

            claims.append(
                "Cash "
                f"{_direction(cash_change)} by "
                f"{_format_percentage(cash_change)}."
            )

    elif scenario_type == "efficiency":
        if difficulty == "hard":
            revenue_change = _percentage(
                metrics["previous_revenue"],
                metrics["revenue"],
            )

            asset_change = _percentage(
                metrics["previous_total_assets"],
                metrics["total_assets"],
            )

            income_change = _percentage(
                metrics["previous_net_income"],
                metrics["net_income"],
            )

            claims.append(
                "Revenue "
                f"{_direction(revenue_change)} by "
                f"{_format_percentage(revenue_change)}."
            )

            claims.append(
                "Total assets "
                f"{_direction(asset_change)} by "
                f"{_format_percentage(asset_change)}."
            )

            claims.append(
                "Net income "
                f"{_direction(income_change)} by "
                f"{_format_percentage(income_change)}."
            )

    elif scenario_type in {
        "multi_metric_comparison",
        "comprehensive_performance",
    }:
        revenue_change = _percentage(
            metrics["previous_revenue"],
            metrics["current_revenue"],
        )

        profit_change = _percentage(
            metrics["previous_profit"],
            metrics["current_profit"],
        )

        debt_change = _percentage(
            metrics["previous_debt"],
            metrics["current_debt"],
        )

        claims.extend(
            [
                "Revenue "
                f"{_direction(revenue_change)} by "
                f"{_format_percentage(revenue_change)}.",

                "Profit "
                f"{_direction(profit_change)} by "
                f"{_format_percentage(profit_change)}.",

                "Debt "
                f"{_direction(debt_change)} by "
                f"{_format_percentage(debt_change)}.",
            ]
        )

        if difficulty == "hard":
            cash_change = _percentage(
                metrics["previous_cash"],
                metrics["current_cash"],
            )

            claims.append(
                "Cash "
                f"{_direction(cash_change)} by "
                f"{_format_percentage(cash_change)}."
            )

    return " ".join(claims)


# ============================================================
# MAIN BUILDER
# ============================================================

def build_difficulty_scenario(
    scenario_type,
    difficulty,
    seed,
    company,
):
    """
    Generate a scenario and construct the
    difficulty-specific input directly from
    its metrics.
    """

    scenario = generate_scenario(
        scenario_type=scenario_type,
        seed=seed,
    )

    metrics = scenario["metrics"]

    enricher = ENRICHERS.get(
        scenario_type
    )

    if enricher is not None:
        enricher(
            metrics,
            difficulty,
        )

    builder = INPUT_BUILDERS.get(
        scenario_type
    )

    if builder is None:
        raise ValueError(
            "No difficulty input builder "
            f"exists for scenario: "
            f"{scenario_type}"
        )

    if scenario_type == "risk_analysis":
        difficulty_input = builder(
            company,
            metrics,
        )
    else:
        difficulty_input = builder(
            company,
            metrics,
            difficulty,
        )

    claims = _build_claims(
        scenario_type=scenario_type,
        metrics=metrics,
        difficulty=difficulty,
    )

    return {
        "scenario": scenario,
        "input": difficulty_input,
        "claims": claims,
    }