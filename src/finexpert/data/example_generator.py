from .scenario_generator import generate_scenario
from .schema import ReasoningType


def format_value(value):
    """
    Format a financial value for human-readable text.
    """

    if value == int(value):
        return f"₹{int(value)} Cr"

    return f"₹{value:.2f} Cr"


def format_percentage(value):
    """
    Format a percentage value for human-readable text.
    """

    return f"{value:.1f}%"


def direction_word(change):
    """
    Convert a numerical change into a financial direction.
    """

    if change > 0:
        return "increased"

    if change < 0:
        return "declined"

    return "remained unchanged"


def generate_explanation_example(
    scenario_type,
    difficulty,
    example_id,
    company,
    seed,
):
    """
    Convert a financial scenario into a
    financial explanation training example.
    """

    scenario = generate_scenario(
        scenario_type=scenario_type,
        seed=seed,
    )

    metrics = scenario["metrics"]

    # --------------------------------------------------
    # 1. REVENUE GROWTH
    # --------------------------------------------------

    if scenario_type == "revenue_growth":

        previous_revenue = metrics["previous_revenue"]
        current_revenue = metrics["current_revenue"]

        revenue_change = (
            (current_revenue - previous_revenue)
            / previous_revenue
        ) * 100

        instruction = (
            "Explain the company's revenue performance "
            "based on the provided financial figures."
        )

        input_text = (
            f"{company} reported that revenue "
            f"{direction_word(revenue_change)} "
            f"from {format_value(previous_revenue)} "
            f"to {format_value(current_revenue)}."
        )

        expected_output = (
            f"Revenue {direction_word(revenue_change)} "
            f"by {format_percentage(abs(revenue_change))}, "
            f"from {format_value(previous_revenue)} to "
            f"{format_value(current_revenue)}."
        )

        if revenue_change > 0:
            expected_output += (
                " This indicates positive revenue growth "
                "between the two periods."
            )

        elif revenue_change < 0:
            expected_output += (
                " This indicates a decline in revenue "
                "between the two periods."
            )

        else:
            expected_output += (
                " This indicates that revenue remained "
                "stable between the two periods."
            )

        reasoning_type = [
            ReasoningType.NUMERICAL_REASONING,
            ReasoningType.TREND_ANALYSIS,
        ]

    # --------------------------------------------------
    # 2. PROFITABILITY
    # --------------------------------------------------

    elif scenario_type == "profitability":

        previous_revenue = metrics["previous_revenue"]
        current_revenue = metrics["current_revenue"]
        previous_profit = metrics["previous_profit"]
        current_profit = metrics["current_profit"]

        revenue_change = (
            (current_revenue - previous_revenue)
            / previous_revenue
        ) * 100

        profit_change = (
            (current_profit - previous_profit)
            / previous_profit
        ) * 100

        previous_margin = (
            previous_profit / previous_revenue
        ) * 100

        current_margin = (
            current_profit / current_revenue
        ) * 100

        margin_change = (
            current_margin - previous_margin
        )

        instruction = (
            "Explain the company's revenue and "
            "profitability performance based on the "
            "provided financial figures."
        )

        input_text = (
            f"{company} reported that revenue "
            f"{direction_word(revenue_change)} "
            f"from {format_value(previous_revenue)} "
            f"to {format_value(current_revenue)}. "
            f"Operating profit "
            f"{direction_word(profit_change)} "
            f"from {format_value(previous_profit)} "
            f"to {format_value(current_profit)}."
        )

        expected_output = (
            f"Revenue {direction_word(revenue_change)} "
            f"by {format_percentage(abs(revenue_change))}, "
            f"while operating profit "
            f"{direction_word(profit_change)} "
            f"by {format_percentage(abs(profit_change))}. "
            f"Operating profit margin "
            f"{direction_word(margin_change)} "
            f"from {format_percentage(previous_margin)} "
            f"to {format_percentage(current_margin)}. "
        )

        if (
            revenue_change > 0
            and profit_change < 0
        ):
            expected_output += (
                "This indicates that revenue growth was "
                "accompanied by pressure on profitability. "
                "Further analysis would be required to "
                "identify the underlying causes."
            )

        elif (
            revenue_change > 0
            and profit_change > 0
        ):
            expected_output += (
                "This indicates that the company improved "
                "both revenue and operating profitability."
            )

        elif (
            revenue_change < 0
            and profit_change < 0
        ):
            expected_output += (
                "This indicates deterioration in both "
                "revenue and operating profitability."
            )

        else:
            expected_output += (
                "The changes indicate a shift in operating "
                "performance that requires further analysis."
            )

        reasoning_type = [
            ReasoningType.NUMERICAL_REASONING,
            ReasoningType.TREND_ANALYSIS,
            ReasoningType.COMPARISON,
        ]

    # --------------------------------------------------
    # 3. OPERATING EXPENSES
    # --------------------------------------------------

    elif scenario_type == "operating_expenses":

        revenue = metrics["revenue"]
        previous_expenses = metrics[
            "previous_operating_expenses"
        ]
        current_expenses = metrics[
            "current_operating_expenses"
        ]

        expense_change = (
            (current_expenses - previous_expenses)
            / previous_expenses
        ) * 100

        previous_expense_ratio = (
            previous_expenses / revenue
        ) * 100

        current_expense_ratio = (
            current_expenses / revenue
        ) * 100

        instruction = (
            "Explain the company's operating expense "
            "performance based on the provided "
            "financial figures."
        )

        input_text = (
            f"{company} reported operating expenses "
            f"{direction_word(expense_change)} "
            f"from {format_value(previous_expenses)} "
            f"to {format_value(current_expenses)}, "
            f"with revenue of {format_value(revenue)}."
        )

        expected_output = (
            f"Operating expenses "
            f"{direction_word(expense_change)} "
            f"by {format_percentage(abs(expense_change))}, "
            f"from {format_value(previous_expenses)} to "
            f"{format_value(current_expenses)}. "
            f"Operating expenses represented "
            f"{format_percentage(previous_expense_ratio)} "
            f"of revenue previously and "
            f"{format_percentage(current_expense_ratio)} "
            f"currently. "
        )

        if expense_change > 0:
            expected_output += (
                "The increase in expenses may place "
                "pressure on operating efficiency, "
                "although further analysis is required "
                "to determine the underlying cause."
            )

        elif expense_change < 0:
            expected_output += (
                "The decline in expenses may indicate "
                "improved cost control."
            )

        else:
            expected_output += (
                "Operating expenses remained stable "
                "relative to the previous period."
            )

        reasoning_type = [
            ReasoningType.NUMERICAL_REASONING,
            ReasoningType.TREND_ANALYSIS,
            ReasoningType.COMPARISON,
        ]

    # --------------------------------------------------
    # 4. DEBT / LEVERAGE
    # --------------------------------------------------

    elif scenario_type == "debt_leverage":

        previous_debt = metrics["previous_debt"]
        current_debt = metrics["current_debt"]
        equity = metrics["equity"]

        debt_change = (
            (current_debt - previous_debt)
            / previous_debt
        ) * 100

        debt_to_equity = (
            current_debt / equity
        )

        instruction = (
            "Explain the company's debt and leverage "
            "position based on the provided financial "
            "figures."
        )

        input_text = (
            f"{company} reported that total debt "
            f"{direction_word(debt_change)} "
            f"from {format_value(previous_debt)} "
            f"to {format_value(current_debt)}, "
            f"while total equity was "
            f"{format_value(equity)}."
        )

        expected_output = (
            f"Total debt {direction_word(debt_change)} "
            f"by {format_percentage(abs(debt_change))}, "
            f"from {format_value(previous_debt)} to "
            f"{format_value(current_debt)}. "
            f"The resulting debt-to-equity ratio is "
            f"{debt_to_equity:.2f}."
        )

        if debt_change > 0:
            expected_output += (
                " The increase in debt indicates higher "
                "financial leverage and may increase "
                "financial risk."
            )

        elif debt_change < 0:
            expected_output += (
                " The decline in debt indicates a "
                "reduction in financial leverage."
            )

        else:
            expected_output += (
                " Debt remained stable relative to "
                "the previous period."
            )

        reasoning_type = [
            ReasoningType.NUMERICAL_REASONING,
            ReasoningType.TREND_ANALYSIS,
            ReasoningType.RISK_ANALYSIS,
        ]

    # --------------------------------------------------
    # 5. LIQUIDITY
    # --------------------------------------------------

    elif scenario_type == "liquidity":

        current_assets = metrics["current_assets"]
        current_liabilities = metrics[
            "current_liabilities"
        ]

        current_ratio = (
            current_assets / current_liabilities
        )

        instruction = (
            "Explain the company's liquidity position "
            "based on the provided current assets and "
            "current liabilities."
        )

        input_text = (
            f"{company} reported current assets of "
            f"{format_value(current_assets)} and "
            f"current liabilities of "
            f"{format_value(current_liabilities)}."
        )

        expected_output = (
            f"The current ratio is "
            f"{current_ratio:.2f}, calculated as current "
            f"assets of {format_value(current_assets)} "
            f"divided by current liabilities of "
            f"{format_value(current_liabilities)}. "
        )

        if current_ratio >= 1:
            expected_output += (
                "The ratio indicates that current assets "
                "are sufficient to cover current liabilities "
                "on a basic balance-sheet basis."
            )

        else:
            expected_output += (
                "The ratio indicates that current assets "
                "are lower than current liabilities, "
                "which may indicate liquidity pressure."
            )

        reasoning_type = [
            ReasoningType.NUMERICAL_REASONING,
            ReasoningType.RISK_ANALYSIS,
        ]

    # --------------------------------------------------
    # 6. CASH FLOW
    # --------------------------------------------------

    elif scenario_type == "cash_flow":

        previous_cash_flow = metrics[
            "previous_cash_flow"
        ]
        current_cash_flow = metrics[
            "current_cash_flow"
        ]

        cash_flow_change = (
            (current_cash_flow - previous_cash_flow)
            / previous_cash_flow
        ) * 100

        instruction = (
            "Explain the company's operating cash flow "
            "performance based on the provided financial "
            "figures."
        )

        input_text = (
            f"{company} reported operating cash flow "
            f"{direction_word(cash_flow_change)} "
            f"from {format_value(previous_cash_flow)} "
            f"to {format_value(current_cash_flow)}."
        )

        expected_output = (
            f"Operating cash flow "
            f"{direction_word(cash_flow_change)} "
            f"by {format_percentage(abs(cash_flow_change))}, "
            f"from {format_value(previous_cash_flow)} to "
            f"{format_value(current_cash_flow)}. "
        )

        if cash_flow_change > 0:
            expected_output += (
                "The increase indicates improved operating "
                "cash generation."
            )

        elif cash_flow_change < 0:
            expected_output += (
                "The decline indicates weaker operating "
                "cash generation and warrants further "
                "investigation."
            )

        else:
            expected_output += (
                "Operating cash flow remained stable "
                "between the two periods."
            )

        reasoning_type = [
            ReasoningType.NUMERICAL_REASONING,
            ReasoningType.TREND_ANALYSIS,
        ]

    # --------------------------------------------------
    # 7. EFFICIENCY
    # --------------------------------------------------

    elif scenario_type == "efficiency":

        revenue = metrics["revenue"]
        total_assets = metrics["total_assets"]
        net_income = metrics["net_income"]

        asset_turnover = (
            revenue / total_assets
        )

        return_on_assets = (
            net_income / total_assets
        ) * 100

        instruction = (
            "Explain the company's asset efficiency "
            "and return on assets based on the provided "
            "financial figures."
        )

        input_text = (
            f"{company} reported revenue of "
            f"{format_value(revenue)}, total assets of "
            f"{format_value(total_assets)}, and net "
            f"income of {format_value(net_income)}."
        )

        expected_output = (
            f"Asset turnover is "
            f"{asset_turnover:.2f}x, calculated as revenue "
            f"divided by total assets. Return on assets is "
            f"{return_on_assets:.1f}%, calculated as net "
            f"income divided by total assets. "
            f"These metrics provide an indication of how "
            f"efficiently the company uses its asset base "
            f"to generate revenue and earnings."
        )

        reasoning_type = [
            ReasoningType.NUMERICAL_REASONING,
            ReasoningType.COMPARISON,
        ]

    # --------------------------------------------------
    # 8. RISK ANALYSIS
    # --------------------------------------------------

    elif scenario_type == "risk_analysis":

        revenue = metrics["revenue"]
        debt = metrics["debt"]
        cash = metrics["cash"]
        operating_profit = metrics[
            "operating_profit"
        ]

        debt_to_revenue = debt / revenue
        cash_to_debt = cash / debt
        operating_margin = (
            operating_profit / revenue
        ) * 100

        instruction = (
            "Assess the company's financial risk based "
            "on revenue, debt, cash, and operating profit."
        )

        input_text = (
            f"{company} reported revenue of "
            f"{format_value(revenue)}, total debt of "
            f"{format_value(debt)}, cash of "
            f"{format_value(cash)}, and operating profit "
            f"of {format_value(operating_profit)}."
        )

        expected_output = (
            f"Debt-to-revenue is "
            f"{debt_to_revenue:.2f}, while cash represents "
            f"{cash_to_debt:.2f} of total debt. "
            f"Operating margin is "
            f"{operating_margin:.1f}%. "
        )

        expected_output += (
            "These metrics should be considered together "
            "when assessing leverage, liquidity, and "
            "operating profitability. The available data "
            "alone is not sufficient to determine the "
            "company's overall financial risk."
        )

        reasoning_type = [
            ReasoningType.NUMERICAL_REASONING,
            ReasoningType.RISK_ANALYSIS,
            ReasoningType.COMPARISON,
        ]

    # --------------------------------------------------
    # 9. MULTI-METRIC COMPARISON
    # --------------------------------------------------

    elif scenario_type == "multi_metric_comparison":

        previous_revenue = metrics["previous_revenue"]
        current_revenue = metrics["current_revenue"]

        previous_profit = metrics["previous_profit"]
        current_profit = metrics["current_profit"]

        previous_debt = metrics["previous_debt"]
        current_debt = metrics["current_debt"]

        revenue_change = (
            (current_revenue - previous_revenue)
            / previous_revenue
        ) * 100

        profit_change = (
            (current_profit - previous_profit)
            / previous_profit
        ) * 100

        debt_change = (
            (current_debt - previous_debt)
            / previous_debt
        ) * 100

        instruction = (
            "Compare the company's revenue, operating "
            "profit, and debt performance across the "
            "two periods."
        )

        revenue_direction = direction_word(
            revenue_change
        )

        profit_direction = direction_word(
            profit_change
        )

        debt_direction = direction_word(
            debt_change
        )

        input_text = (
            f"{company} reported revenue of "
            f"{format_value(previous_revenue)} in the "
            f"previous period and "
            f"{format_value(current_revenue)} in the "
            f"current period. Operating profit was "
            f"{format_value(previous_profit)} previously "
            f"and {format_value(current_profit)} currently. "
            f"Total debt was "
            f"{format_value(previous_debt)} previously "
            f"and {format_value(current_debt)} currently."
        )

        expected_output = (
            f"Revenue {revenue_direction} by "
            f"{format_percentage(abs(revenue_change))}, "
            f"operating profit {profit_direction} by "
            f"{format_percentage(abs(profit_change))}, "
            f"and debt {debt_direction} by "
            f"{format_percentage(abs(debt_change))}. "
        )

        expected_output += (
            "These changes should be evaluated together "
            "to understand the company's growth, "
            "profitability, and leverage position."
        )

        reasoning_type = [
            ReasoningType.NUMERICAL_REASONING,
            ReasoningType.TREND_ANALYSIS,
            ReasoningType.COMPARISON,
            ReasoningType.RISK_ANALYSIS,
        ]

    # --------------------------------------------------
    # 10. COMPREHENSIVE PERFORMANCE
    # --------------------------------------------------

    elif scenario_type == "comprehensive_performance":

        previous_revenue = metrics["previous_revenue"]
        current_revenue = metrics["current_revenue"]

        previous_profit = metrics["previous_profit"]
        current_profit = metrics["current_profit"]

        previous_debt = metrics["previous_debt"]
        current_debt = metrics["current_debt"]

        cash = metrics["cash"]

        revenue_change = (
            (current_revenue - previous_revenue)
            / previous_revenue
        ) * 100

        profit_change = (
            (current_profit - previous_profit)
            / previous_profit
        ) * 100

        debt_change = (
            (current_debt - previous_debt)
            / previous_debt
        ) * 100

        previous_margin = (
            previous_profit / previous_revenue
        ) * 100

        current_margin = (
            current_profit / current_revenue
        ) * 100

        debt_to_revenue = (
            current_debt / current_revenue
        )

        instruction = (
            "Provide a comprehensive explanation of the "
            "company's financial performance based on "
            "revenue, operating profit, debt, and cash."
        )

        input_text = (
            f"{company} reported revenue of "
            f"{format_value(previous_revenue)} in the "
            f"previous period and "
            f"{format_value(current_revenue)} in the "
            f"current period. Operating profit was "
            f"{format_value(previous_profit)} previously "
            f"and {format_value(current_profit)} currently. "
            f"Total debt was "
            f"{format_value(previous_debt)} previously "
            f"and {format_value(current_debt)} currently, "
            f"while current cash was "
            f"{format_value(cash)}."
        )

        expected_output = (
            f"Revenue {direction_word(revenue_change)} "
            f"by {format_percentage(abs(revenue_change))}, "
            f"while operating profit "
            f"{direction_word(profit_change)} by "
            f"{format_percentage(abs(profit_change))}. "
            f"Operating profit margin changed from "
            f"{format_percentage(previous_margin)} to "
            f"{format_percentage(current_margin)}. "
            f"Debt {direction_word(debt_change)} by "
            f"{format_percentage(abs(debt_change))}, "
            f"and current cash is "
            f"{format_value(cash)}. "
            f"Current debt-to-revenue is "
            f"{debt_to_revenue:.2f}. "
        )

        expected_output += (
            "Taken together, these metrics provide a "
            "broader view of growth, profitability, "
            "leverage, and liquidity. Additional financial "
            "information would be required for a complete "
            "assessment."
        )

        reasoning_type = [
            ReasoningType.NUMERICAL_REASONING,
            ReasoningType.TREND_ANALYSIS,
            ReasoningType.COMPARISON,
            ReasoningType.RISK_ANALYSIS,
        ]

    else:
        raise ValueError(
            f"Explanation generation is not yet supported "
            f"for scenario type: {scenario_type}"
        )

    return {
        "example_id": example_id,
        "instruction": instruction,
        "input": input_text,
        "expected_output": expected_output.strip(),
        "category": "financial_explanation",
        "difficulty": difficulty,
        "reasoning_type": reasoning_type,
        "source_type": "synthetic",
        "company": company,
    }