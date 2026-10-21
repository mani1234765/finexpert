"""Standard corporate-finance formulas, written out explicitly.

Definitions follow common analyst / CFA-curriculum conventions. Where conventions differ between textbooks, the
choice is stated in the docstring, and questions in the regression set always state the inputs needed so the
expected answer is unambiguous. Rates are fractions (0.25 = 25%); percent helpers return percentages.
"""

from __future__ import annotations


def pct(fraction: float) -> float:
    """0.1707 -> 17.07"""
    return fraction * 100


def ebitda(ebit: float, depreciation_and_amortisation: float) -> float:
    return ebit + depreciation_and_amortisation


def nopat(ebit: float, tax_rate: float) -> float:
    """Net operating profit after tax = EBIT x (1 - tax rate). Uses EBIT, never EBITDA."""
    return ebit * (1 - tax_rate)


def invested_capital(total_debt: float, total_equity: float, cash: float = 0.0,
                     non_operating_investments: float = 0.0) -> float:
    """Financing view: debt + equity - cash - non-operating investments."""
    return total_debt + total_equity - cash - non_operating_investments


def roic(ebit: float, tax_rate: float, capital: float) -> float:
    """Return on invested capital = NOPAT / invested capital (fraction)."""
    return nopat(ebit, tax_rate) / capital


def fcff(ebit: float, tax_rate: float, depreciation_and_amortisation: float, capex: float,
         increase_in_net_working_capital: float) -> float:
    """Free cash flow to the firm = EBIT(1 - t) + D&A - capex - increase in NWC."""
    return nopat(ebit, tax_rate) + depreciation_and_amortisation - capex - increase_in_net_working_capital


def fcfe(fcff_value: float, interest_expense: float, tax_rate: float, net_borrowing: float) -> float:
    """Free cash flow to equity = FCFF - interest x (1 - t) + net borrowing."""
    return fcff_value - interest_expense * (1 - tax_rate) + net_borrowing


def margin(numerator: float, revenue: float) -> float:
    """Any margin as a fraction of revenue (gross profit, operating profit, net profit ...)."""
    return numerator / revenue


def cagr(begin: float, end: float, years: float) -> float:
    return (end / begin) ** (1 / years) - 1


def wacc(equity_value: float, debt_value: float, cost_of_equity: float, cost_of_debt: float,
         tax_rate: float) -> float:
    total = equity_value + debt_value
    return equity_value / total * cost_of_equity + debt_value / total * cost_of_debt * (1 - tax_rate)


def roe(net_income: float, equity: float) -> float:
    return net_income / equity


def interest_coverage(ebit: float, interest_expense: float) -> float:
    return ebit / interest_expense


def days_sales_outstanding(receivables: float, revenue: float, days: int = 365) -> float:
    return receivables / revenue * days
