HEALTHY = "Healthy"
MODERATE_RISK = "Moderate Risk"
HIGH_RISK = "High Risk"

VALID_LABELS = {
    HEALTHY,
    MODERATE_RISK,
    HIGH_RISK,
}


def _percentage(old_value, new_value):
    """
    Calculate percentage change.

    Returns None when the previous value is zero.
    """

    if old_value == 0:
        return None

    return (
        (new_value - old_value)
        / old_value
    ) * 100


def _classify_revenue_growth(metrics):
    """
    Revenue growth classification.

    Positive growth -> Healthy
    Zero / undefined -> Moderate Risk
    Negative growth -> High Risk
    """

    previous_revenue = metrics.get(
        "previous_revenue"
    )
    current_revenue = metrics.get(
        "current_revenue"
    )

    if (
        previous_revenue is None
        or current_revenue is None
    ):
        return MODERATE_RISK

    growth = _percentage(
        previous_revenue,
        current_revenue,
    )

    if growth is None:
        return MODERATE_RISK

    if growth > 0:
        return HEALTHY

    if growth < 0:
        return HIGH_RISK

    return MODERATE_RISK


def _classify_profitability(metrics):
    """
    Profitability classification.

    Healthy:
        revenue grows
        profit grows
        margin does not decline

    High Risk:
        profit declines
        margin declines

    Otherwise:
        Moderate Risk
    """

    previous_revenue = metrics.get(
        "previous_revenue"
    )
    current_revenue = metrics.get(
        "current_revenue"
    )
    previous_profit = metrics.get(
        "previous_profit"
    )
    current_profit = metrics.get(
        "current_profit"
    )

    if (
        previous_revenue is None
        or current_revenue is None
        or previous_profit is None
        or current_profit is None
    ):
        return MODERATE_RISK

    revenue_growth = _percentage(
        previous_revenue,
        current_revenue,
    )

    profit_growth = _percentage(
        previous_profit,
        current_profit,
    )

    if (
        revenue_growth is None
        or profit_growth is None
        or previous_revenue == 0
        or current_revenue == 0
    ):
        return MODERATE_RISK

    previous_margin = (
        previous_profit
        / previous_revenue
    )

    current_margin = (
        current_profit
        / current_revenue
    )

    if (
        revenue_growth > 0
        and profit_growth > 0
        and current_margin >= previous_margin
    ):
        return HEALTHY

    if (
        profit_growth < 0
        and current_margin < previous_margin
    ):
        return HIGH_RISK

    return MODERATE_RISK


def _classify_operating_expenses(metrics):
    """
    Operating expense classification.

    Healthy:
        expense ratio <= 25%
        and expense growth <= 10%

    High Risk:
        expense ratio >= 40%
        or expense growth >= 25%

    Otherwise:
        Moderate Risk
    """

    revenue = metrics.get(
        "revenue"
    )

    previous_expenses = metrics.get(
        "previous_operating_expenses"
    )

    current_expenses = metrics.get(
        "current_operating_expenses"
    )

    if (
        revenue is None
        or previous_expenses is None
        or current_expenses is None
    ):
        return MODERATE_RISK

    if revenue == 0:
        return MODERATE_RISK

    expense_ratio = (
        current_expenses
        / revenue
    )

    expense_growth = _percentage(
        previous_expenses,
        current_expenses,
    )

    if expense_growth is None:
        return MODERATE_RISK

    if (
        expense_ratio <= 0.25
        and expense_growth <= 10
    ):
        return HEALTHY

    if (
        expense_ratio >= 0.40
        or expense_growth >= 25
    ):
        return HIGH_RISK

    return MODERATE_RISK


def _classify_debt_leverage(metrics):
    """
    Debt/leverage classification.

    Uses the debt change and debt-to-equity ratio.

    Healthy:
        debt decreases or remains controlled
        and leverage is below 1

    High Risk:
        debt growth >= 30%
        or debt-to-equity >= 2

    Otherwise:
        Moderate Risk
    """

    previous_debt = metrics.get(
        "previous_debt"
    )

    current_debt = metrics.get(
        "current_debt"
    )

    equity = metrics.get(
        "equity"
    )

    if (
        previous_debt is None
        or current_debt is None
        or equity is None
    ):
        return MODERATE_RISK

    if previous_debt == 0:
        return MODERATE_RISK

    if equity == 0:
        return HIGH_RISK

    debt_growth = _percentage(
        previous_debt,
        current_debt,
    )

    debt_to_equity = (
        current_debt
        / equity
    )

    if (
        debt_growth is not None
        and debt_growth >= 30
    ):
        return HIGH_RISK

    if debt_to_equity >= 2:
        return HIGH_RISK

    if (
        debt_growth is not None
        and debt_growth <= 10
        and debt_to_equity < 1
    ):
        return HEALTHY

    return MODERATE_RISK


def _classify_liquidity(metrics):
    """
    Liquidity classification.

    Healthy:
        current ratio >= 1.5

    High Risk:
        current ratio < 1

    Otherwise:
        Moderate Risk
    """

    current_assets = metrics.get(
        "current_assets"
    )

    current_liabilities = metrics.get(
        "current_liabilities"
    )

    if (
        current_assets is None
        or current_liabilities is None
    ):
        return MODERATE_RISK

    if current_liabilities == 0:
        return HEALTHY

    current_ratio = (
        current_assets
        / current_liabilities
    )

    if current_ratio >= 1.5:
        return HEALTHY

    if current_ratio < 1:
        return HIGH_RISK

    return MODERATE_RISK


def _classify_cash_flow(metrics):
    """
    Cash-flow classification.

    Healthy:
        positive cash flow
        and no decline

    High Risk:
        cash flow <= 0
        or decline >= 20%

    Otherwise:
        Moderate Risk
    """

    previous_cash_flow = metrics.get(
        "previous_cash_flow"
    )

    current_cash_flow = metrics.get(
        "current_cash_flow"
    )

    if current_cash_flow is None:
        return MODERATE_RISK

    if current_cash_flow <= 0:
        return HIGH_RISK

    if previous_cash_flow is None:
        return MODERATE_RISK

    change = _percentage(
        previous_cash_flow,
        current_cash_flow,
    )

    if change is None:
        return MODERATE_RISK

    if change <= -20:
        return HIGH_RISK

    if change >= 0:
        return HEALTHY

    return MODERATE_RISK


def _classify_efficiency(metrics):
    """
    Efficiency classification.

    Healthy:
        asset turnover >= 1.5
        and ROA >= 10%

    High Risk:
        asset turnover < 0.75
        or ROA < 5%

    Otherwise:
        Moderate Risk
    """

    asset_turnover = metrics.get(
        "asset_turnover"
    )

    roa = metrics.get(
        "roa"
    )

    total_assets = metrics.get("total_assets")

    if total_assets:
        if asset_turnover is None and "revenue" in metrics:
            asset_turnover = metrics["revenue"] / total_assets

        if roa is None and "net_income" in metrics:
            roa = metrics["net_income"] / total_assets * 100

    if (
        asset_turnover is None
        or roa is None
    ):
        return MODERATE_RISK

    if (
        asset_turnover >= 1.5
        and roa >= 10
    ):
        return HEALTHY

    if (
        asset_turnover < 0.75
        or roa < 5
    ):
        return HIGH_RISK

    return MODERATE_RISK


def _classify_risk_analysis(metrics):
    """
    Multi-signal risk classification.

    Risk indicators:

        debt / revenue >= 1
        cash / debt < 0.20
        operating margin < 10%

    0 risk indicators -> Healthy
    1 risk indicator  -> Moderate Risk
    2+ risk indicators -> High Risk
    """

    revenue = metrics.get(
        "revenue"
    )

    debt = metrics.get(
        "debt"
    )

    cash = metrics.get(
        "cash"
    )

    operating_profit = metrics.get(
        "operating_profit"
    )

    if (
        revenue is None
        or debt is None
        or cash is None
        or operating_profit is None
    ):
        return MODERATE_RISK

    risk_points = 0

    if revenue != 0:
        debt_to_revenue = (
            debt / revenue
        )

        if debt_to_revenue >= 1:
            risk_points += 1

    if debt != 0:
        cash_to_debt = (
            cash / debt
        )

        if cash_to_debt < 0.20:
            risk_points += 1

    if revenue != 0:
        operating_margin = (
            operating_profit
            / revenue
        ) * 100

        if operating_margin < 10:
            risk_points += 1

    if risk_points >= 2:
        return HIGH_RISK

    if risk_points == 0:
        return HEALTHY

    return MODERATE_RISK


def _classify_multi_metric_comparison(metrics):
    """
    Multi-metric comparison classification.

    High Risk:
        profit declines AND debt grows by >= 20%

    Healthy:
        revenue grows
        profit grows
        debt growth <= 20%

    Otherwise:
        Moderate Risk
    """

    revenue_growth = metrics.get(
        "revenue_growth"
    )

    profit_growth = metrics.get(
        "profit_growth"
    )

    debt_growth = metrics.get(
        "debt_growth"
    )

    # Some callers provide previous/current values
    # instead of precomputed growth values.
    if revenue_growth is None:
        previous_revenue = metrics.get(
            "previous_revenue"
        )
        current_revenue = metrics.get(
            "current_revenue"
        )

        if (
            previous_revenue is not None
            and current_revenue is not None
        ):
            revenue_growth = _percentage(
                previous_revenue,
                current_revenue,
            )

    if profit_growth is None:
        previous_profit = metrics.get(
            "previous_profit"
        )
        current_profit = metrics.get(
            "current_profit"
        )

        if (
            previous_profit is not None
            and current_profit is not None
        ):
            profit_growth = _percentage(
                previous_profit,
                current_profit,
            )

    if debt_growth is None:
        previous_debt = metrics.get(
            "previous_debt"
        )
        current_debt = metrics.get(
            "current_debt"
        )

        if (
            previous_debt is not None
            and current_debt is not None
        ):
            debt_growth = _percentage(
                previous_debt,
                current_debt,
            )

    if (
        revenue_growth is None
        or profit_growth is None
        or debt_growth is None
    ):
        return MODERATE_RISK

    if (
        profit_growth < 0
        and debt_growth >= 20
    ):
        return HIGH_RISK

    if (
        revenue_growth > 0
        and profit_growth > 0
        and debt_growth <= 20
    ):
        return HEALTHY

    return MODERATE_RISK


def _classify_comprehensive_performance(metrics):
    """
    Comprehensive performance classification.

    Uses the enriched multi-period metrics when available.
    """

    risk_score = 0
    positive_score = 0

    # Revenue
    if (
        "previous_revenue" in metrics
        and "current_revenue" in metrics
    ):
        growth = _percentage(
            metrics["previous_revenue"],
            metrics["current_revenue"],
        )

        if growth is not None:
            if growth > 0:
                positive_score += 1
            elif growth < 0:
                risk_score += 1

    # Operating profit
    if (
        "previous_operating_profit" in metrics
        and "current_operating_profit" in metrics
    ):
        growth = _percentage(
            metrics["previous_operating_profit"],
            metrics["current_operating_profit"],
        )

        if growth is not None:
            if growth > 0:
                positive_score += 2
            elif growth < 0:
                risk_score += 2

    # Net profit
    if (
        "previous_net_profit" in metrics
        and "current_net_profit" in metrics
    ):
        growth = _percentage(
            metrics["previous_net_profit"],
            metrics["current_net_profit"],
        )

        if growth is not None:
            if growth > 0:
                positive_score += 2
            elif growth < 0:
                risk_score += 2

    # Generic profit
    elif (
        "previous_profit" in metrics
        and "current_profit" in metrics
    ):
        growth = _percentage(
            metrics["previous_profit"],
            metrics["current_profit"],
        )

        if growth is not None:
            if growth > 0:
                positive_score += 2
            elif growth < 0:
                risk_score += 2

    # Debt
    if (
        "previous_debt" in metrics
        and "current_debt" in metrics
    ):
        growth = _percentage(
            metrics["previous_debt"],
            metrics["current_debt"],
        )

        if growth is not None:
            if growth >= 30:
                risk_score += 2
            elif growth > 10:
                risk_score += 1
            elif growth <= 0:
                positive_score += 1

    # Cash
    if (
        "previous_cash" in metrics
        and "current_cash" in metrics
    ):
        growth = _percentage(
            metrics["previous_cash"],
            metrics["current_cash"],
        )

        if growth is not None:
            if growth <= -10:
                risk_score += 2
            elif growth < 0:
                risk_score += 1
            elif growth > 0:
                positive_score += 1

    # Cash flow
    if (
        "previous_cash_flow" in metrics
        and "current_cash_flow" in metrics
    ):
        current_cash_flow = metrics[
            "current_cash_flow"
        ]

        growth = _percentage(
            metrics["previous_cash_flow"],
            current_cash_flow,
        )

        if current_cash_flow <= 0:
            risk_score += 2
        elif growth is not None:
            if growth <= -20:
                risk_score += 2
            elif growth < 0:
                risk_score += 1
            elif growth > 0:
                positive_score += 1

    # Operating expenses
    if (
        "previous_operating_expenses" in metrics
        and "current_operating_expenses" in metrics
    ):
        growth = _percentage(
            metrics["previous_operating_expenses"],
            metrics["current_operating_expenses"],
        )

        if growth is not None:
            if growth >= 25:
                risk_score += 2
            elif growth > 10:
                risk_score += 1
            elif growth <= 0:
                positive_score += 1

    if risk_score >= positive_score + 2:
        return HIGH_RISK

    if positive_score >= risk_score + 2:
        return HEALTHY

    return MODERATE_RISK


CLASSIFIERS = {
    "revenue_growth": _classify_revenue_growth,
    "profitability": _classify_profitability,
    "operating_expenses": _classify_operating_expenses,
    "debt_leverage": _classify_debt_leverage,
    "liquidity": _classify_liquidity,
    "cash_flow": _classify_cash_flow,
    "efficiency": _classify_efficiency,
    "risk_analysis": _classify_risk_analysis,
    "multi_metric_comparison": (
        _classify_multi_metric_comparison
    ),
    "comprehensive_performance": (
        _classify_comprehensive_performance
    ),
}


def classify_financial_health(
    scenario_type,
    metrics,
):
    """
    Return a deterministic financial-health label.

    Unknown scenarios intentionally default to
    Moderate Risk so the generation pipeline does not
    crash merely because a new scenario has not yet
    received a dedicated classifier.
    """

    classifier = CLASSIFIERS.get(
        scenario_type
    )

    if classifier is None:
        return MODERATE_RISK

    label = classifier(metrics)

    if label not in VALID_LABELS:
        return MODERATE_RISK

    return label