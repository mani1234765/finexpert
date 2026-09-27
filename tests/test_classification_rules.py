from finexpert.data.classification_rules import (
    HEALTHY,
    MODERATE_RISK,
    HIGH_RISK,
    classify_financial_health,
)


def test_revenue_growth_healthy():
    metrics = {
        "previous_revenue": 100,
        "current_revenue": 120,
    }

    assert (
        classify_financial_health(
            "revenue_growth",
            metrics,
        )
        == HEALTHY
    )


def test_revenue_growth_high_risk():
    metrics = {
        "previous_revenue": 100,
        "current_revenue": 80,
    }

    assert (
        classify_financial_health(
            "revenue_growth",
            metrics,
        )
        == HIGH_RISK
    )


def test_revenue_growth_moderate_risk():
    metrics = {
        "previous_revenue": 100,
        "current_revenue": 100,
    }

    assert (
        classify_financial_health(
            "revenue_growth",
            metrics,
        )
        == MODERATE_RISK
    )


def test_profitability_healthy():
    metrics = {
        "previous_revenue": 100,
        "current_revenue": 120,
        "previous_profit": 20,
        "current_profit": 30,
    }

    assert (
        classify_financial_health(
            "profitability",
            metrics,
        )
        == HEALTHY
    )


def test_profitability_high_risk():
    metrics = {
        "previous_revenue": 100,
        "current_revenue": 110,
        "previous_profit": 20,
        "current_profit": 15,
    }

    assert (
        classify_financial_health(
            "profitability",
            metrics,
        )
        == HIGH_RISK
    )


def test_liquidity_healthy():
    metrics = {
        "current_assets": 200,
        "current_liabilities": 100,
    }

    assert (
        classify_financial_health(
            "liquidity",
            metrics,
        )
        == HEALTHY
    )


def test_liquidity_moderate_risk():
    metrics = {
        "current_assets": 120,
        "current_liabilities": 100,
    }

    assert (
        classify_financial_health(
            "liquidity",
            metrics,
        )
        == MODERATE_RISK
    )


def test_liquidity_high_risk():
    metrics = {
        "current_assets": 80,
        "current_liabilities": 100,
    }

    assert (
        classify_financial_health(
            "liquidity",
            metrics,
        )
        == HIGH_RISK
    )


def test_debt_leverage_healthy():
    metrics = {
        "previous_debt": 100,
        "current_debt": 105,
        "equity": 200,
    }

    assert (
        classify_financial_health(
            "debt_leverage",
            metrics,
        )
        == HEALTHY
    )


def test_debt_leverage_high_risk():
    metrics = {
        "previous_debt": 100,
        "current_debt": 140,
        "equity": 100,
    }

    assert (
        classify_financial_health(
            "debt_leverage",
            metrics,
        )
        == HIGH_RISK
    )


def test_cash_flow_healthy():
    metrics = {
        "previous_cash_flow": 100,
        "current_cash_flow": 110,
    }

    assert (
        classify_financial_health(
            "cash_flow",
            metrics,
        )
        == HEALTHY
    )


def test_cash_flow_high_risk():
    metrics = {
        "previous_cash_flow": 100,
        "current_cash_flow": 70,
    }

    assert (
        classify_financial_health(
            "cash_flow",
            metrics,
        )
        == HIGH_RISK
    )


def test_risk_analysis_healthy():
    metrics = {
        "debt": 50,
        "revenue": 100,
        "cash": 30,
        "operating_profit": 20,
    }

    assert (
        classify_financial_health(
            "risk_analysis",
            metrics,
        )
        == HEALTHY
    )


def test_risk_analysis_high_risk():
    metrics = {
        "debt": 120,
        "revenue": 100,
        "cash": 10,
        "operating_profit": 5,
    }

    assert (
        classify_financial_health(
            "risk_analysis",
            metrics,
        )
        == HIGH_RISK
    )


def test_multi_metric_high_risk():
    metrics = {
        "previous_revenue": 100,
        "current_revenue": 110,
        "previous_profit": 20,
        "current_profit": 15,
        "previous_debt": 100,
        "current_debt": 130,
    }

    assert (
        classify_financial_health(
            "multi_metric_comparison",
            metrics,
        )
        == HIGH_RISK
    )


def test_multi_metric_healthy():
    metrics = {
        "previous_revenue": 100,
        "current_revenue": 110,
        "previous_profit": 20,
        "current_profit": 25,
        "previous_debt": 100,
        "current_debt": 110,
    }

    assert (
        classify_financial_health(
            "multi_metric_comparison",
            metrics,
        )
        == HEALTHY
    )


def test_unknown_scenario_defaults_to_moderate_risk():
    assert (
        classify_financial_health(
            "unknown_scenario",
            {},
        )
        == MODERATE_RISK
    )