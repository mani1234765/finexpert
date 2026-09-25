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



def _advanced_metric_text(metrics):
    """
    Render advanced scenario metrics without using
    period-over-period phrasing that can be mistaken for
    a validator growth claim.
    """

    labels = {
        "revenue": "Revenue",
        "previous_revenue": "Previous-period revenue",
        "current_revenue": "Current-period revenue",
        "profit": "Profit",
        "previous_profit": "Previous-period profit",
        "current_profit": "Current-period profit",
        "net_income": "Net income",
        "operating_profit": "Operating profit",
        "operating_income": "Operating income",
        "debt": "Total debt",
        "total_debt": "Total debt",
        "cash": "Cash",
        "total_assets": "Total assets",
        "total_equity": "Total equity",
        "ebitda": "EBITDA",
        "reported_ebitda": "Reported EBITDA",
        "operating_cash_flow": "Operating cash flow",
        "previous_cash_flow": "Previous-period operating cash flow",
        "current_cash_flow": "Current-period operating cash flow",
        "capex": "Capital expenditure",
        "previous_operating_expenses": "Previous-period operating expenses",
        "current_operating_expenses": "Current-period operating expenses",
        "receivables": "Receivables",
        "previous_receivables": "Previous-period receivables",
        "current_receivables": "Current-period receivables",
        "inventory": "Inventory",
        "previous_inventory": "Previous-period inventory",
        "current_inventory": "Current-period inventory",
        "payables": "Payables",
        "previous_payables": "Previous-period payables",
        "current_payables": "Current-period payables",
        "current_assets": "Current assets",
        "current_liabilities": "Current liabilities",
    }

    parts = []
    for key, value in metrics.items():
        if key in labels and isinstance(value, (int, float)):
            parts.append(f"{labels[key]}: {format_value(value)}.")
    return " ".join(parts)


def _advanced_percentage(numerator, denominator):
    if denominator == 0:
        return None
    return (numerator / denominator) * 100


def _advanced_ratio(numerator, denominator):
    if denominator == 0:
        return None
    return numerator / denominator


def _generate_advanced_explanation(
    scenario_type,
    difficulty,
    example_id,
    company,
    metrics,
):
    """
    Generate explanation examples for the 40 advanced
    financial-analysis scenarios.

    The advanced layer intentionally emphasizes calculated
    relationships and qualified interpretation rather than
    unsupported causal claims.
    """

    instructions = {
        "earnings_quality": "Assess the quality of reported earnings using the provided profit, cash-flow, and working-capital indicators.",
        "profit_to_cash_conversion": "Assess how effectively reported profit is converting into operating cash flow.",
        "receivables_revenue_divergence": "Assess the relationship between revenue and receivables and identify any financial-analysis warning signs.",
        "inventory_buildup": "Assess inventory levels relative to revenue and identify whether the balance-sheet pattern warrants investigation.",
        "cfo_net_income_divergence": "Compare net income with operating cash flow and explain what the relationship may indicate.",
        "aggressive_revenue_recognition": "Assess revenue-recognition warning signals using revenue, receivables, and contract assets.",
        "one_time_gain_distortion": "Assess how a one-time gain affects reported profitability and the quality of recurring earnings.",
        "ebitda_quality": "Assess reported EBITDA after considering potentially non-recurring or non-cash adjustments.",
        "cash_conversion_cycle": "Calculate and interpret the company's cash conversion cycle from the provided operating metrics.",
        "working_capital_release": "Assess the effect of changes in working capital on operating cash generation.",
        "supplier_financing": "Assess the relationship between payables and operating cash flow and identify supplier-financing considerations.",
        "negative_working_capital": "Assess the company's negative working-capital structure and its implications for liquidity.",
        "seasonal_working_capital": "Compare peak and trough working-capital requirements and assess the seasonal funding need.",
        "working_capital_stress": "Assess working-capital stress using receivables, inventory, payables, and revenue.",
        "debt_maturity_wall": "Assess near-term refinancing exposure using the debt maturity schedule and available liquidity.",
        "interest_coverage_stress": "Assess interest-coverage resilience under the provided earnings stress scenario.",
        "floating_rate_debt_sensitivity": "Estimate the interest-cost sensitivity to the provided floating-rate shock.",
        "debt_covenant_headroom": "Assess debt-covenant headroom under the provided leverage and earnings assumptions.",
        "refinancing_liquidity_risk": "Assess refinancing liquidity risk using cash, restricted cash, total debt, and near-term maturities.",
        "debt_reduction_equity_dilution": "Compare debt reduction with the equity dilution required to fund it.",
        "debt_restructuring": "Assess the financial effect of the proposed debt restructuring using the provided terms.",
        "eps_share_count_dilution": "Assess the effect of earnings and share-count changes on EPS.",
        "buyback_eps_growth": "Assess how a share repurchase changes EPS when net income is held constant.",
        "stock_based_compensation": "Assess the effect of stock-based compensation on reported earnings and share dilution.",
        "roe_buyback_distortion": "Assess how a share buyback can affect ROE through changes in equity.",
        "capital_allocation": "Compare the expected returns from debt reduction, reinvestment, and acquisitions.",
        "depreciation_policy_change": "Assess the earnings effect of changing the useful life assumption for depreciable assets.",
        "impairment_cash_flow": "Explain the distinction between an impairment charge and operating cash flow.",
        "deferred_tax_distortion": "Explain how deferred tax expense affects reported net income without representing the same-period cash tax burden.",
        "lease_accounting": "Assess lease economics using lease expense, depreciation, and lease interest.",
        "foreign_exchange_distortion": "Separate reported performance from constant-currency performance using the provided FX information.",
        "inflation_distortion": "Assess nominal growth versus inflation-adjusted business performance using the provided assumptions.",
        "valuation_growth_profitability": "Assess valuation implications when growth, profitability, and free cash flow signals differ.",
        "multiple_expansion": "Separate earnings growth from valuation-multiple expansion in explaining the change in equity value.",
        "dcf_sensitivity": "Assess how DCF value changes under the provided growth, margin, and discount-rate assumptions.",
        "wacc_growth_tradeoff": "Compare the valuation effect of different growth and WACC assumptions.",
        "enterprise_value_bridge": "Bridge enterprise value to equity value using debt, cash, and other claims.",
        "customer_acquisition_economics": "Assess customer-acquisition economics using CAC, ARPU, gross margin, and churn.",
        "rule_of_40": "Calculate the Rule of 40 score and interpret the balance between growth and profitability.",
        "cohort_economics": "Assess customer economics using CAC, churn, gross margin, and revenue performance.",
    }

    instruction = instructions.get(
        scenario_type,
        "Analyze the provided financial scenario using the available financial metrics.",
    )

    input_parts = [
        f"{company} financial-analysis scenario.",
        _advanced_metric_text(metrics),
    ]

    calculations = []
    interpretation = ""

    # Working-capital and cash-flow scenarios.
    if scenario_type == "profit_to_cash_conversion":
        ni = metrics["net_income"]
        cfo = metrics["operating_cash_flow"]
        conversion = _advanced_percentage(cfo, ni)
        calculations.append(
            f"Operating cash-flow conversion of net income: {conversion:.1f}%."
        )
        interpretation = (
            "This compares cash generated from operations with reported net income. "
            "A lower conversion rate can warrant investigation of working capital, "
            "non-cash items, and earnings quality."
        )

    elif scenario_type == "cfo_net_income_divergence":
        ni = metrics["net_income"]
        cfo = metrics["operating_cash_flow"]
        gap = cfo - ni
        calculations.append(
            f"Operating cash flow minus net income: {format_value(gap)}."
        )
        interpretation = (
            "A positive gap means operating cash flow exceeds reported net income, "
            "while a negative gap means cash generation is below reported profit. "
            "The figures alone do not establish the underlying cause."
        )

    elif scenario_type == "earnings_quality":
        ni = metrics["net_income"]
        cfo = metrics["operating_cash_flow"]
        receivables_growth = metrics["receivables_growth"]
        inventory_growth = metrics["inventory_growth"]
        conversion = _advanced_percentage(cfo, ni)
        calculations.extend([
            f"Operating cash-flow conversion of net income: {conversion:.1f}%.",
            f"Receivables change indicator: {receivables_growth:.1f}%.",
            f"Inventory change indicator: {inventory_growth:.1f}%.",
        ])
        interpretation = (
            "Cash conversion and working-capital movements should be considered "
            "together when assessing earnings quality. These indicators can flag "
            "areas for investigation but do not by themselves prove aggressive accounting."
        )

    elif scenario_type == "receivables_revenue_divergence":
        calculations.extend([
            f"Revenue change indicator: {metrics['revenue_growth']:.1f}%.",
            f"Receivables change indicator: {metrics['receivables_growth']:.1f}%.",
        ])
        interpretation = (
            "Receivables growing materially faster than revenue can be a warning "
            "signal that warrants investigation of collections, credit terms, and "
            "revenue recognition. It is not proof of improper recognition."
        )

    elif scenario_type == "inventory_buildup":
        calculations.extend([
            f"Revenue change indicator: {metrics['revenue_growth']:.1f}%.",
            f"Inventory change indicator: {metrics['inventory_growth']:.1f}%.",
        ])
        interpretation = (
            "Inventory rising faster than revenue can indicate weaker inventory "
            "turnover or demand pressure and should be investigated alongside "
            "inventory composition and future sales."
        )

    elif scenario_type == "aggressive_revenue_recognition":
        calculations.extend([
            f"Revenue change indicator: {metrics['revenue_growth']:.1f}%.",
            f"Receivables change indicator: {metrics['receivables_growth']:.1f}%.",
            f"Contract-assets change indicator: {metrics['contract_assets_growth']:.1f}%.",
        ])
        interpretation = (
            "A divergence between revenue and receivables or contract assets is a "
            "potential revenue-quality warning sign. The available figures do not "
            "establish that revenue recognition was improper."
        )

    elif scenario_type == "one_time_gain_distortion":
        reported = metrics["reported_net_income"]
        gain = metrics["one_time_gain"]
        recurring = reported - gain
        calculations.extend([
            f"Reported net income: {format_value(reported)}.",
            f"One-time gain: {format_value(gain)}.",
            f"Net income excluding the identified one-time gain: {format_value(recurring)}.",
        ])
        interpretation = (
            "The adjusted figure provides a view of reported earnings excluding "
            "the specified one-time gain. It should not be treated as a complete "
            "measure of recurring earnings without considering other adjustments."
        )

    elif scenario_type == "ebitda_quality":
        reported = metrics["reported_ebitda"]
        adjustments = (
            metrics["restructuring"]
            + metrics["stock_based_compensation"]
            + metrics["acquisition_costs"]
        )
        calculations.extend([
            f"Reported EBITDA: {format_value(reported)}.",
            f"Specified adjustments: {format_value(adjustments)}.",
            f"EBITDA after removing the specified adjustments: {format_value(reported - adjustments)}.",
        ])
        interpretation = (
            "The adjusted figure shows how much reported EBITDA depends on the "
            "specified add-backs. Whether those costs are genuinely non-recurring "
            "requires historical and business-context review."
        )

    elif scenario_type == "cash_conversion_cycle":
        dso = metrics["dso"]
        dio = metrics["dio"]
        dpo = metrics["dpo"]
        ccc = dso + dio - dpo
        calculations.append(
            f"Cash conversion cycle: {ccc:.1f} days ({dso:.1f} DSO + {dio:.1f} DIO - {dpo:.1f} DPO)."
        )
        interpretation = (
            "A longer cash conversion cycle generally means more operating cash "
            "is tied up before sales convert back into cash."
        )

    elif scenario_type == "working_capital_release":
        old_wc = (
            metrics["previous_receivables"]
            + metrics["previous_inventory"]
            - metrics["previous_payables"]
        )
        new_wc = (
            metrics["current_receivables"]
            + metrics["current_inventory"]
            - metrics["current_payables"]
        )
        release = old_wc - new_wc
        calculations.append(
            f"Estimated working-capital release: {format_value(release)}."
        )
        interpretation = (
            "A reduction in operating working capital represents a release of "
            "cash from the operating cycle, assuming the listed components are representative."
        )

    elif scenario_type == "supplier_financing":
        old_p = metrics["previous_payables"]
        new_p = metrics["current_payables"]
        cfo = metrics["operating_cash_flow"]
        change = new_p - old_p
        calculations.extend([
            f"Payables change: {format_value(change)}.",
            f"Operating cash flow: {format_value(cfo)}.",
        ])
        interpretation = (
            "Higher payables can support operating cash flow by delaying supplier "
            "payments, but the sustainability of that funding depends on supplier "
            "terms, payment practices, and business conditions."
        )

    elif scenario_type == "negative_working_capital":
        wc = metrics["current_assets"] - metrics["current_liabilities"]
        calculations.append(
            f"Net working capital: {format_value(wc)}."
        )
        interpretation = (
            "Negative working capital means current liabilities exceed current assets. "
            "This can be structurally efficient in some business models, but liquidity "
            "risk depends on the timing and stability of cash inflows and obligations."
        )

    elif scenario_type == "seasonal_working_capital":
        peak = metrics["peak_current_assets"] - metrics["peak_current_liabilities"]
        trough = metrics["trough_current_assets"] - metrics["trough_current_liabilities"]
        need = peak - trough
        calculations.append(
            f"Peak-to-trough working-capital funding swing: {format_value(need)}."
        )
        interpretation = (
            "The difference represents the additional working-capital requirement "
            "at the peak point in the provided seasonal cycle."
        )

    elif scenario_type == "working_capital_stress":
        current_wc = (
            metrics["receivables"]
            + metrics["inventory"]
            - metrics["payables"]
        )
        calculations.append(
            f"Operating working capital in the scenario: {format_value(current_wc)}."
        )
        interpretation = (
            "Working-capital stress should be assessed by considering receivables, "
            "inventory, payables, and revenue together rather than relying on one metric."
        )

    # Debt and capital-structure scenarios.
    elif scenario_type == "debt_maturity_wall":
        near_term = metrics["debt_2027"] + metrics["debt_2028"]
        coverage = _advanced_ratio(
            metrics["cash"] + metrics["operating_cash_flow"],
            near_term,
        )
        calculations.extend([
            f"Debt maturing in the first two listed years: {format_value(near_term)}.",
            f"Illustrative cash-plus-CFO coverage of that amount: {coverage:.2f}x.",
        ])
        interpretation = (
            "The maturity concentration highlights refinancing exposure. Cash-flow "
            "coverage is only an illustrative comparison and does not replace a "
            "full liquidity and refinancing analysis."
        )

    elif scenario_type == "interest_coverage_stress":
        current = _advanced_ratio(metrics["ebit"], metrics["interest_expense"])
        stressed = _advanced_ratio(metrics["stressed_ebit"], metrics["interest_expense"])
        calculations.extend([
            f"Current interest coverage: {current:.2f}x.",
            f"Stressed interest coverage: {stressed:.2f}x.",
        ])
        interpretation = (
            "Lower interest coverage under the stress case indicates reduced "
            "capacity to absorb earnings pressure while servicing interest."
        )

    elif scenario_type == "floating_rate_debt_sensitivity":
        floating_debt = metrics["debt"] * metrics["floating_rate_percentage"] / 100
        annual_interest_change = floating_debt * metrics["rate_shock_bps"] / 10000
        calculations.append(
            f"Estimated annual interest-cost increase: {format_value(annual_interest_change)}."
        )
        interpretation = (
            "The calculation isolates the mechanical effect of the stated rate shock "
            "on the floating-rate portion of debt; actual interest expense can differ "
            "because of repricing dates and hedging."
        )

    elif scenario_type == "debt_covenant_headroom":
        current_leverage = _advanced_ratio(metrics["debt"], metrics["ebitda"])
        stressed_leverage = _advanced_ratio(metrics["debt"], metrics["stressed_ebitda"])
        calculations.extend([
            f"Current debt-to-EBITDA: {current_leverage:.2f}x.",
            f"Stressed debt-to-EBITDA: {stressed_leverage:.2f}x.",
            f"Stated maximum leverage: {metrics['maximum_leverage']:.2f}x.",
        ])
        interpretation = (
            "The difference between stressed leverage and the stated covenant "
            "threshold indicates how much deterioration could be absorbed before "
            "the specified limit is reached."
        )

    elif scenario_type == "refinancing_liquidity_risk":
        available_cash = metrics["cash"] - metrics["restricted_cash"]
        coverage = _advanced_ratio(available_cash, metrics["debt_due_soon"])
        calculations.extend([
            f"Unrestricted cash proxy: {format_value(available_cash)}.",
            f"Unrestricted-cash coverage of debt due soon: {coverage:.2f}x.",
        ])
        interpretation = (
            "A low coverage ratio indicates greater reliance on operating cash flow, "
            "asset sales, refinancing, or other funding sources."
        )

    elif scenario_type == "debt_reduction_equity_dilution":
        debt_reduction = metrics["debt_repaid"]
        dilution = _advanced_percentage(
            metrics["new_shares"],
            metrics["existing_shares"],
        )
        calculations.extend([
            f"Debt repayment funded: {format_value(debt_reduction)}.",
            f"New shares relative to existing shares: {dilution:.1f}%.",
        ])
        interpretation = (
            "The transaction trades lower debt for equity issuance. The analysis "
            "should consider both reduced financial leverage and shareholder dilution."
        )

    elif scenario_type == "debt_restructuring":
        old_interest = metrics["debt"] * metrics["old_interest_rate"] / 100
        new_interest = metrics["debt"] * metrics["new_interest_rate"] / 100
        savings = old_interest - new_interest
        calculations.extend([
            f"Illustrative annual interest before restructuring: {format_value(old_interest)}.",
            f"Illustrative annual interest after restructuring: {format_value(new_interest)}.",
            f"Illustrative annual interest saving: {format_value(savings)}.",
        ])
        interpretation = (
            "The mechanical interest saving improves debt-service economics, while "
            "the longer maturity changes refinancing timing. Fees and other restructuring terms "
            "would also need to be considered."
        )

    # Equity and accounting scenarios.
    elif scenario_type == "eps_share_count_dilution":
        old_eps = metrics["net_income"] / metrics["previous_shares"]
        new_eps = metrics["current_net_income"] / metrics["current_shares"]
        calculations.extend([
            f"Previous-period EPS proxy: {old_eps:.2f}.",
            f"Current-period EPS proxy: {new_eps:.2f}.",
        ])
        interpretation = (
            "EPS reflects both earnings and the number of shares outstanding, so "
            "share-count changes can materially affect per-share performance."
        )

    elif scenario_type == "buyback_eps_growth":
        old_eps = metrics["net_income"] / metrics["previous_shares"]
        new_eps = metrics["net_income"] / metrics["current_shares"]
        calculations.extend([
            f"EPS before buyback: {old_eps:.2f}.",
            f"EPS after buyback, assuming unchanged net income: {new_eps:.2f}.",
        ])
        interpretation = (
            "A lower share count mechanically increases EPS when net income is unchanged. "
            "This does not by itself indicate improved underlying operating performance."
        )

    elif scenario_type == "stock_based_compensation":
        adjusted_income = metrics["net_income"] + metrics["stock_based_compensation"]
        basic_eps = metrics["net_income"] / metrics["basic_shares"]
        diluted_eps = metrics["net_income"] / metrics["diluted_shares"]
        calculations.extend([
            f"Net income plus specified SBC add-back: {format_value(adjusted_income)}.",
            f"Basic EPS proxy: {basic_eps:.2f}.",
            f"Diluted EPS proxy: {diluted_eps:.2f}.",
        ])
        interpretation = (
            "Stock-based compensation is generally non-cash when granted but can "
            "represent an economic cost through dilution. Both cash-flow and per-share "
            "effects should therefore be considered."
        )

    elif scenario_type == "roe_buyback_distortion":
        pre = _advanced_percentage(metrics["net_income"], metrics["pre_buyback_equity"])
        post = _advanced_percentage(metrics["net_income"], metrics["post_buyback_equity"])
        calculations.extend([
            f"ROE before buyback: {pre:.1f}%.",
            f"ROE after buyback: {post:.1f}%.",
        ])
        interpretation = (
            "A buyback can increase ROE mechanically by reducing the equity denominator, "
            "even when operating profitability has not changed."
        )

    elif scenario_type == "capital_allocation":
        calculations.extend([
            f"Debt cost: {metrics['debt_cost']:.1f}%.",
            f"Expected reinvestment return: {metrics['reinvestment_return']:.1f}%.",
            f"Expected acquisition return: {metrics['acquisition_return']:.1f}%.",
        ])
        interpretation = (
            "A simplified allocation framework favors uses of capital whose expected "
            "returns exceed the relevant financing cost, subject to risk, certainty, "
            "liquidity, and strategic considerations."
        )

    elif scenario_type == "depreciation_policy_change":
        old_dep = metrics["asset_base"] / metrics["old_useful_life"]
        new_dep = metrics["asset_base"] / metrics["new_useful_life"]
        calculations.extend([
            f"Illustrative annual depreciation under old life: {format_value(old_dep)}.",
            f"Illustrative annual depreciation under new life: {format_value(new_dep)}.",
        ])
        interpretation = (
            "A longer useful life reduces annual depreciation mechanically and can "
            "increase reported operating profit, assuming the asset base is unchanged. "
            "The accounting estimate must still reflect expected asset usage."
        )

    elif scenario_type == "impairment_cash_flow":
        calculations.extend([
            f"Impairment charge: {format_value(metrics['impairment'])}.",
            f"Pre-impairment asset base: {format_value(metrics['pre_impairment_assets'])}.",
        ])
        interpretation = (
            "An impairment is an accounting charge that reduces carrying value and "
            "reported earnings but is not itself a current-period cash outflow."
        )

    elif scenario_type == "deferred_tax_distortion":
        cash_tax = metrics["current_tax"]
        tax_expense = metrics["current_tax"] + metrics["deferred_tax_expense"]
        calculations.extend([
            f"Current cash-tax component: {format_value(cash_tax)}.",
            f"Reported tax expense including deferred tax: {format_value(tax_expense)}.",
        ])
        interpretation = (
            "Deferred tax expense changes reported tax expense without representing "
            "the same amount of current-period cash tax. Cash taxes and accounting tax "
            "expense should therefore be distinguished."
        )

    elif scenario_type == "lease_accounting":
        combined = metrics["lease_depreciation"] + metrics["lease_interest"]
        calculations.extend([
            f"Lease depreciation: {format_value(metrics['lease_depreciation'])}.",
            f"Lease interest: {format_value(metrics['lease_interest'])}.",
            f"Combined depreciation-plus-interest: {format_value(combined)}.",
        ])
        interpretation = (
            "Lease economics can be viewed through both the depreciation of the "
            "right-of-use asset and the financing component represented by lease interest."
        )

    # Macro / valuation scenarios.
    elif scenario_type == "foreign_exchange_distortion":
        calculations.extend([
            f"Reported revenue change indicator: {metrics['reported_growth']:.1f}%.",
            f"Constant-currency revenue change indicator: {metrics['constant_currency_growth']:.1f}%.",
            f"Reported operating margin: {metrics['reported_margin']:.1f}%.",
            f"Constant-currency operating margin: {metrics['constant_currency_margin']:.1f}%.",
        ])
        interpretation = (
            "The gap between reported and constant-currency measures shows the "
            "extent to which exchange-rate movements affect the reported comparison."
        )

    elif scenario_type == "inflation_distortion":
        real_growth = (
            (1 + metrics["nominal_revenue_growth"] / 100)
            / (1 + metrics["inflation_rate"] / 100)
            - 1
        ) * 100
        calculations.extend([
            f"Nominal revenue growth indicator: {metrics['nominal_revenue_growth']:.1f}%.",
            f"Inflation assumption: {metrics['inflation_rate']:.1f}%.",
            f"Approximate inflation-adjusted revenue growth: {real_growth:.1f}%.",
        ])
        interpretation = (
            "Nominal growth can overstate underlying volume or real growth when "
            "prices are rising materially."
        )

    elif scenario_type == "valuation_growth_profitability":
        calculations.extend([
            f"Revenue growth assumption: {metrics['growth_rate']:.1f}%.",
            f"Operating margin: {metrics['operating_margin']:.1f}%.",
            f"Free cash flow: {format_value(metrics['free_cash_flow'])}.",
            f"Valuation multiple: {metrics['valuation_multiple']:.1f}x.",
        ])
        interpretation = (
            "Valuation should reflect the interaction between growth, profitability, "
            "cash generation, and the multiple investors are willing to pay."
        )

    elif scenario_type == "multiple_expansion":
        old_value = metrics["old_pe"] * metrics["old_eps"]
        new_value = metrics["new_pe"] * metrics["new_eps"]
        calculations.extend([
            f"Illustrative old equity value per share: {old_value:.2f}.",
            f"Illustrative new equity value per share: {new_value:.2f}.",
            f"EPS change indicator: {metrics['eps_growth']:.1f}%.",
            f"P/E multiple change: {metrics['new_pe'] - metrics['old_pe']:.1f}x.",
        ])
        interpretation = (
            "The change in value can be decomposed into earnings growth and multiple "
            "expansion. A higher multiple represents a change in valuation expectations, "
            "not operating earnings by itself."
        )

    elif scenario_type == "dcf_sensitivity":
        calculations.extend([
            f"Base growth assumption: {metrics['growth_rate']:.1f}%.",
            f"Operating margin assumption: {metrics['operating_margin']:.1f}%.",
            f"WACC assumption: {metrics['wacc']:.1f}%.",
            f"Terminal growth assumption: {metrics['terminal_growth']:.1f}%.",
        ])
        interpretation = (
            "DCF output is highly sensitive to growth, margins, and the discount rate. "
            "The provided assumptions should therefore be treated as a sensitivity framework "
            "rather than a precise valuation."
        )

    elif scenario_type == "wacc_growth_tradeoff":
        calculations.extend([
            f"Case A growth: {metrics['growth_a']:.1f}%.",
            f"Case A WACC: {metrics['wacc_a']:.1f}%.",
            f"Case B growth: {metrics['growth_b']:.1f}%.",
            f"Case B WACC: {metrics['wacc_b']:.1f}%.",
        ])
        interpretation = (
            "Higher growth can support valuation, while a higher WACC reduces the "
            "present value of future cash flows. A complete numerical comparison requires "
            "the underlying cash-flow assumptions."
        )

    elif scenario_type == "enterprise_value_bridge":
        equity_value = (
            metrics["enterprise_value"]
            - metrics["debt"]
            - metrics["minority_interest"]
            - metrics["preferred_stock"]
            + metrics["cash"]
        )
        calculations.append(
            f"Illustrative equity value from the EV bridge: {format_value(equity_value)}."
        )
        interpretation = (
            "Equity value is derived by adjusting enterprise value for debt and other "
            "senior claims, while adding cash. The exact bridge depends on the definition "
            "of each balance-sheet item."
        )

    elif scenario_type == "customer_acquisition_economics":
        lifetime_months = 1 / metrics["monthly_churn"]
        gross_profit_ltv = (
            metrics["arpu"]
            * metrics["gross_margin"]
            / metrics["monthly_churn"]
        )
        ltv_cac = gross_profit_ltv / metrics["cac"]
        calculations.extend([
            f"Illustrative customer lifetime: {lifetime_months:.1f} months.",
            f"Illustrative gross-profit LTV: ₹{gross_profit_ltv:.2f}.",
            f"Illustrative LTV/CAC: {ltv_cac:.2f}x.",
        ])
        interpretation = (
            "The LTV calculation uses the simplified constant-churn assumption "
            "embedded in the scenario. Real customer economics can differ because "
            "retention, pricing, margins, and acquisition costs change over time."
        )

    elif scenario_type == "rule_of_40":
        score = metrics["revenue_growth"] + metrics["ebitda_margin"]
        calculations.append(
            f"Rule of 40 score: {score:.1f}%."
        )
        interpretation = (
            "The Rule of 40 combines growth and EBITDA margin into a single heuristic. "
            "It is a screening metric rather than a complete measure of software-company quality."
        )

    elif scenario_type == "cohort_economics":
        lifetime_months = 1 / metrics["churn_rate"]
        gross_profit_ltv = (
            metrics["arpu"]
            * metrics["gross_margin"]
            / metrics["churn_rate"]
        )
        ltv_cac = gross_profit_ltv / metrics["cac"]
        calculations.extend([
            f"Illustrative customer lifetime: {lifetime_months:.1f} months.",
            f"Illustrative gross-profit LTV: ₹{gross_profit_ltv:.2f}.",
            f"Illustrative LTV/CAC: {ltv_cac:.2f}x.",
            f"Revenue change indicator: {metrics['revenue_growth']:.1f}%.",
        ])
        interpretation = (
            "Cohort economics should be assessed through retention, gross-profit "
            "generation, acquisition cost, and the trajectory of revenue together."
        )

    else:
        # Fallback keeps the function safe if a new advanced scenario
        # is added before a dedicated analytical treatment exists.
        interpretation = (
            "The scenario contains multiple financial indicators that should be "
            "evaluated together. The available figures alone do not establish a "
            "specific causal explanation."
        )

    expected_output = " ".join(calculations)
    if interpretation:
        expected_output += " " + interpretation

    return {
        "example_id": example_id,
        "instruction": instruction,
        "input": " ".join(input_parts).strip(),
        "expected_output": expected_output.strip(),
        "category": "financial_explanation",
        "difficulty": difficulty,
        "reasoning_type": [
            ReasoningType.NUMERICAL_REASONING,
            ReasoningType.RISK_ANALYSIS,
        ],
        "source_type": "synthetic",
        "company": company,
    }

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
            f"{company} reported that total debt moved "
            f"from {format_value(previous_debt)} "
            f"to {format_value(current_debt)}, "
            f"while total equity was "
            f"{format_value(equity)}."
        )

        if debt_change > 0:
            debt_change_noun = "an increase"
        elif debt_change < 0:
            debt_change_noun = "a decline"
        else:
            debt_change_noun = "no change"

        expected_output = (
            f"Total debt moved from "
            f"{format_value(previous_debt)} to "
            f"{format_value(current_debt)}, "
            f"{debt_change_noun} of "
            f"{format_percentage(abs(debt_change))}. "
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

        working_capital = (
            current_assets - current_liabilities
        )

        working_capital_margin = (
            working_capital / current_liabilities
        ) * 100

        variant_hash = (
            int(current_assets) * 7
            + int(current_liabilities) * 13
        )

        variant_instruction = variant_hash % 4
        variant_input = (variant_hash // 4) % 4
        variant_open = (variant_hash // 16) % 4
        variant_wc = (variant_hash // 64) % 4
        variant_close = (variant_hash // 256) % 4

        instruction = [
            "Explain the company's liquidity position "
            "based on the provided current assets and "
            "current liabilities.",
            "Assess the company's short-term liquidity "
            "using the current assets and current "
            "liabilities provided.",
            "Interpret what the company's current assets "
            "and current liabilities imply about its "
            "liquidity position.",
            "Review the company's balance-sheet liquidity "
            "given its current assets and current "
            "liabilities.",
        ][variant_instruction]

        input_text = [
            f"{company} reported current assets of "
            f"{format_value(current_assets)} and "
            f"current liabilities of "
            f"{format_value(current_liabilities)}.",
            f"{company}'s balance sheet shows current "
            f"assets of {format_value(current_assets)} "
            f"against current liabilities of "
            f"{format_value(current_liabilities)}.",
            f"As of the latest reporting period, "
            f"{company} held current assets of "
            f"{format_value(current_assets)} and carried "
            f"current liabilities of "
            f"{format_value(current_liabilities)}.",
            f"{company} listed current assets of "
            f"{format_value(current_assets)} alongside "
            f"current liabilities of "
            f"{format_value(current_liabilities)} on its "
            f"balance sheet.",
        ][variant_input]

        expected_output = [
            f"The current ratio is "
            f"{current_ratio:.2f}, calculated as current "
            f"assets of {format_value(current_assets)} "
            f"divided by current liabilities of "
            f"{format_value(current_liabilities)}. ",
            f"Dividing current assets of "
            f"{format_value(current_assets)} by current "
            f"liabilities of "
            f"{format_value(current_liabilities)} gives a "
            f"current ratio of {current_ratio:.2f}. ",
            f"With current assets of "
            f"{format_value(current_assets)} set against "
            f"current liabilities of "
            f"{format_value(current_liabilities)}, the "
            f"resulting current ratio works out to "
            f"{current_ratio:.2f}. ",
            f"Comparing current assets of "
            f"{format_value(current_assets)} with current "
            f"liabilities of "
            f"{format_value(current_liabilities)} produces "
            f"a current ratio of {current_ratio:.2f}. ",
        ][variant_open]

        if working_capital > 0:
            expected_output += [
                f"This leaves the company with positive "
                f"working capital of "
                f"{format_value(working_capital)}. ",
                f"As a result, net working capital stands "
                f"at a positive "
                f"{format_value(working_capital)}. ",
                f"That translates into a working capital "
                f"surplus of {format_value(working_capital)}. ",
                f"Net of liabilities, working capital comes "
                f"to a positive "
                f"{format_value(working_capital)}. ",
            ][variant_wc]

        elif working_capital < 0:
            expected_output += [
                f"This leaves the company with a working "
                f"capital shortfall of "
                f"{format_value(abs(working_capital))}. ",
                f"As a result, net working capital is "
                f"negative, at "
                f"{format_value(abs(working_capital))}. ",
                f"That translates into a working capital "
                f"deficit of "
                f"{format_value(abs(working_capital))}. ",
                f"Net of liabilities, the company runs a "
                f"working capital gap of "
                f"{format_value(abs(working_capital))}. ",
            ][variant_wc]

        else:
            expected_output += (
                "This leaves the company with zero net "
                "working capital. "
            )

        expected_output += (
            f"This working capital position is equivalent "
            f"to {format_percentage(abs(working_capital_margin))} "
            f"of current liabilities. "
        )

        if current_ratio >= 2.0:
            expected_output += [
                "A ratio at this level points to a strong "
                "liquidity buffer, with current assets "
                "comfortably exceeding current liabilities.",
                "This is a robust liquidity cushion, well "
                "above what is typically needed to meet "
                "near-term obligations.",
                "Such a high ratio suggests ample short-term "
                "resources relative to upcoming obligations.",
                "This points to a very comfortable liquidity "
                "margin against short-term obligations.",
            ][variant_close]

        elif current_ratio >= 1.0:
            expected_output += [
                "The ratio indicates that current assets "
                "are sufficient to cover current liabilities "
                "on a basic balance-sheet basis.",
                "This suggests the company can comfortably "
                "meet its short-term obligations as they "
                "come due.",
                "This reflects an adequate short-term "
                "liquidity position relative to obligations.",
                "This indicates the company is on solid "
                "footing to cover near-term liabilities.",
            ][variant_close]

        elif current_ratio >= 0.7:
            expected_output += [
                "The ratio indicates that current assets "
                "are somewhat lower than current "
                "liabilities, suggesting mild liquidity "
                "pressure that is worth monitoring.",
                "This points to modest liquidity pressure, "
                "as short-term obligations slightly outpace "
                "short-term resources.",
                "This suggests a manageable but noticeable "
                "gap between short-term resources and "
                "obligations.",
                "This warrants some caution, since current "
                "liabilities run ahead of current assets.",
            ][variant_close]

        else:
            expected_output += [
                "The ratio indicates that current assets "
                "are well below current liabilities, "
                "pointing to a more significant liquidity "
                "concern.",
                "This signals a meaningful liquidity "
                "concern, with obligations well ahead of "
                "available short-term resources.",
                "This raises a notable liquidity flag, as "
                "short-term resources fall well short of "
                "obligations.",
                "This suggests real liquidity strain that "
                "would merit closer attention.",
            ][variant_close]

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

        variant_hash = (
            int(revenue) * 5
            + int(total_assets) * 11
            + int(net_income) * 17
        )

        variant_instruction = variant_hash % 4
        variant_input = (variant_hash // 4) % 4
        variant_open = (variant_hash // 16) % 4
        variant_close = (variant_hash // 64) % 3

        instruction = [
            "Explain the company's asset efficiency "
            "and return on assets based on the provided "
            "financial figures.",
            "Assess how efficiently the company is using "
            "its assets based on the revenue, total "
            "assets, and net income provided.",
            "Interpret the company's asset utilization "
            "and profitability based on the figures "
            "provided.",
            "Review the company's efficiency and returns "
            "using the provided revenue, total assets, "
            "and net income.",
        ][variant_instruction]

        input_text = [
            f"{company} reported revenue of "
            f"{format_value(revenue)}, total assets of "
            f"{format_value(total_assets)}, and net "
            f"income of {format_value(net_income)}.",
            f"{company}'s financials show revenue of "
            f"{format_value(revenue)}, total assets of "
            f"{format_value(total_assets)}, and net "
            f"income of {format_value(net_income)}.",
            f"For the period, {company} generated revenue "
            f"of {format_value(revenue)} on total assets "
            f"of {format_value(total_assets)}, with net "
            f"income of {format_value(net_income)}.",
            f"{company} posted revenue of "
            f"{format_value(revenue)} against total assets "
            f"of {format_value(total_assets)}, along with "
            f"net income of {format_value(net_income)}.",
        ][variant_input]

        expected_output = [
            f"Asset turnover is "
            f"{asset_turnover:.2f}x, calculated as revenue "
            f"divided by total assets. Return on assets is "
            f"{return_on_assets:.1f}%, calculated as net "
            f"income divided by total assets. ",
            f"Revenue divided by total assets gives an "
            f"asset turnover of {asset_turnover:.2f}x, "
            f"while net income divided by total assets "
            f"gives a return on assets of "
            f"{return_on_assets:.1f}%. ",
            f"The company's asset turnover works out to "
            f"{asset_turnover:.2f}x (revenue over total "
            f"assets), and its return on assets works out "
            f"to {return_on_assets:.1f}% (net income over "
            f"total assets). ",
            f"Dividing revenue by total assets yields an "
            f"asset turnover of {asset_turnover:.2f}x; "
            f"dividing net income by total assets yields a "
            f"return on assets of {return_on_assets:.1f}%. ",
        ][variant_open]

        if asset_turnover >= 1.5:
            expected_output += [
                "These metrics indicate the company is "
                "generating a large multiple of revenue "
                "relative to its asset base, alongside a "
                "solid return on those assets.",
                "This points to highly efficient use of the "
                "asset base, with revenue well in excess of "
                "the assets deployed to generate it.",
                "This suggests the company is squeezing a "
                "strong amount of revenue and profit out of "
                "a comparatively lean asset base.",
            ][variant_close]

        elif asset_turnover >= 0.8:
            expected_output += [
                "These metrics provide an indication of how "
                "efficiently the company uses its asset "
                "base to generate revenue and earnings.",
                "This reflects a reasonably balanced "
                "relationship between the assets deployed "
                "and the revenue and profit they generate.",
                "This suggests moderate efficiency, with "
                "revenue and earnings roughly in line with "
                "the scale of the asset base.",
            ][variant_close]

        else:
            expected_output += [
                "These metrics suggest the company is "
                "generating relatively modest revenue and "
                "earnings for the size of its asset base.",
                "This points to a heavier asset base relative "
                "to the revenue and profit it is currently "
                "generating.",
                "This suggests there may be room to improve "
                "how effectively the asset base is being "
                "put to use.",
            ][variant_close]

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

        variant_hash = (
            int(revenue) * 3
            + int(debt) * 7
            + int(cash) * 11
            + int(operating_profit) * 13
        )

        variant_instruction = variant_hash % 4
        variant_input = (variant_hash // 4) % 4
        variant_open = (variant_hash // 16) % 4
        variant_close = (variant_hash // 64) % 3

        instruction = [
            "Assess the company's financial risk based "
            "on revenue, debt, cash, and operating "
            "profit.",
            "Evaluate the company's financial risk profile "
            "using the revenue, debt, cash, and operating "
            "profit provided.",
            "Review the company's leverage, liquidity, and "
            "profitability signals based on the figures "
            "provided.",
            "Analyze the company's overall financial risk "
            "given its revenue, debt, cash position, and "
            "operating profit.",
        ][variant_instruction]

        input_text = [
            f"{company} reported revenue of "
            f"{format_value(revenue)}, total debt of "
            f"{format_value(debt)}, cash of "
            f"{format_value(cash)}, and operating profit "
            f"of {format_value(operating_profit)}.",
            f"{company}'s figures show revenue of "
            f"{format_value(revenue)}, total debt of "
            f"{format_value(debt)}, cash on hand of "
            f"{format_value(cash)}, and operating profit "
            f"of {format_value(operating_profit)}.",
            f"For the period, {company} posted revenue of "
            f"{format_value(revenue)} against total debt "
            f"of {format_value(debt)}, with cash of "
            f"{format_value(cash)} and operating profit of "
            f"{format_value(operating_profit)}.",
            f"{company} disclosed revenue of "
            f"{format_value(revenue)}, debt of "
            f"{format_value(debt)}, cash reserves of "
            f"{format_value(cash)}, and operating profit "
            f"of {format_value(operating_profit)}.",
        ][variant_input]

        expected_output = [
            f"Debt-to-revenue is "
            f"{debt_to_revenue:.2f}, while cash represents "
            f"{cash_to_debt:.2f} of total debt. "
            f"Operating margin is "
            f"{operating_margin:.1f}%. ",
            f"The debt-to-revenue ratio comes to "
            f"{debt_to_revenue:.2f}, and cash covers "
            f"{cash_to_debt:.2f} of total debt. Operating "
            f"margin stands at {operating_margin:.1f}%. ",
            f"Total debt equals "
            f"{debt_to_revenue:.2f} times revenue, cash "
            f"equals {cash_to_debt:.2f} times total debt, "
            f"and operating margin is "
            f"{operating_margin:.1f}%. ",
            f"Relative to revenue, debt comes to "
            f"{debt_to_revenue:.2f}; relative to debt, cash "
            f"comes to {cash_to_debt:.2f}; and operating "
            f"margin is {operating_margin:.1f}%. ",
        ][variant_open]

        if debt_to_revenue >= 1.0:
            expected_output += [
                "These metrics should be considered together "
                "when assessing leverage, liquidity, and "
                "operating profitability. The available data "
                "alone is not sufficient to determine the "
                "company's overall financial risk, though the "
                "elevated debt relative to revenue stands out.",
                "Taken together, these figures point to "
                "leverage that is high relative to revenue, "
                "which is worth weighing alongside the "
                "company's liquidity and profitability.",
                "The debt load relative to revenue is on the "
                "higher side here, and should be assessed "
                "together with the company's cash position "
                "and operating profitability.",
            ][variant_close]

        else:
            expected_output += [
                "These metrics should be considered together "
                "when assessing leverage, liquidity, and "
                "operating profitability. The available data "
                "alone is not sufficient to determine the "
                "company's overall financial risk.",
                "Taken together, these figures suggest debt "
                "is at a more manageable level relative to "
                "revenue, though liquidity and profitability "
                "should still be assessed together.",
                "The debt load relative to revenue looks "
                "reasonable here, but should still be viewed "
                "alongside the company's cash position and "
                "operating profitability.",
            ][variant_close]

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
            f"{company} reported revenue "
            f"{revenue_direction} from "
            f"{format_value(previous_revenue)} to "
            f"{format_value(current_revenue)}. Operating "
            f"profit {profit_direction} from "
            f"{format_value(previous_profit)} to "
            f"{format_value(current_profit)}. Total debt "
            f"moved from {format_value(previous_debt)} to "
            f"{format_value(current_debt)}."
        )

        expected_output = (
            f"Revenue {revenue_direction} by "
            f"{format_percentage(abs(revenue_change))}, "
            f"and operating profit {profit_direction} by "
            f"{format_percentage(abs(profit_change))}. "
            f"Total debt also {debt_direction} over the "
            f"same period, moving from "
            f"{format_value(previous_debt)} to "
            f"{format_value(current_debt)}. "
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
            f"{company} reported revenue "
            f"{direction_word(revenue_change)} from "
            f"{format_value(previous_revenue)} to "
            f"{format_value(current_revenue)}. Operating "
            f"profit {direction_word(profit_change)} from "
            f"{format_value(previous_profit)} to "
            f"{format_value(current_profit)}. Total debt "
            f"moved from {format_value(previous_debt)} to "
            f"{format_value(current_debt)}, while current "
            f"cash was {format_value(cash)}."
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
            f"Total debt also "
            f"{direction_word(debt_change)} over the same "
            f"period, moving from "
            f"{format_value(previous_debt)} to "
            f"{format_value(current_debt)}, and current "
            f"cash is {format_value(cash)}. "
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
        return _generate_advanced_explanation(
            scenario_type=scenario_type,
            difficulty=difficulty,
            example_id=example_id,
            company=company,
            metrics=metrics,
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