from .difficulty_scenarios import build_difficulty_scenario

from .classification_rules import (
    classify_financial_health,
)


from .schema import ReasoningType



TASKS = (
    "financial_explanation",
    "financial_classification",
    "financial_report_generation",
)


def _percentage(old_value, new_value):
    if old_value == 0:
        return None

    return (
        (new_value - old_value)
        / old_value
    ) * 100


def _format_number(value):
    if float(value).is_integer():
        return f"{int(value)}"

    return f"{value:.2f}"


def _build_period_change_claim(
    label,
    previous_value,
    current_value,
):
    change = _percentage(
        previous_value,
        current_value,
    )

    if change is None:
        return None

    if change > 0:
        direction = "increased"
    elif change < 0:
        direction = "declined"
    else:
        direction = "remained unchanged"

    return (
        f"{label} {direction} by "
        f"{abs(change):.1f}%, from "
        f"₹{_format_number(previous_value)} Cr to "
        f"₹{_format_number(current_value)} Cr."
    )


def _build_enriched_claims(metrics):
    """
    Build factual claims only from metrics present
    in the actual generated scenario.
    """

    claims = []

    metric_pairs = [
        (
            "previous_revenue",
            "current_revenue",
            "Revenue",
        ),
        (
            "previous_profit",
            "current_profit",
            "Profit",
        ),
        (
            "previous_operating_profit",
            "current_operating_profit",
            "Operating profit",
        ),
        (
            "previous_net_profit",
            "current_net_profit",
            "Net profit",
        ),
        (
            "previous_operating_expenses",
            "current_operating_expenses",
            "Operating expenses",
        ),
        (
            "previous_debt",
            "current_debt",
            "Total debt",
        ),
        (
            "previous_cash",
            "current_cash",
            "Cash",
        ),
        (
            "previous_cash_flow",
            "current_cash_flow",
            "Cash flow",
        ),
        (
            "previous_equity",
            "current_equity",
            "Equity",
        ),
        (
            "previous_assets",
            "current_assets",
            "Assets",
        ),
        (
            "previous_liabilities",
            "current_liabilities",
            "Liabilities",
        ),
    ]

    for (
        previous_key,
        current_key,
        label,
    ) in metric_pairs:

        if (
            previous_key not in metrics
            or current_key not in metrics
        ):
            continue

        claim = _build_period_change_claim(
            label=label,
            previous_value=metrics[previous_key],
            current_value=metrics[current_key],
        )

        if claim is not None:
            claims.append(claim)

    return claims


def _build_static_metric_claims(metrics):
    """
    Build factual claims for scenarios whose metrics
    are single-period values rather than previous/current
    pairs.
    """

    claims = []

    if (
        "current_assets" in metrics
        and "current_liabilities" in metrics
    ):
        current_assets = metrics["current_assets"]
        current_liabilities = metrics["current_liabilities"]

        if current_liabilities != 0:
            ratio = (
                current_assets
                / current_liabilities
            )

            claims.append(
                f"Current ratio is {ratio:.2f}, "
                f"based on current assets of "
                f"₹{_format_number(current_assets)} Cr "
                f"and current liabilities of "
                f"₹{_format_number(current_liabilities)} Cr."
            )

    if (
        "revenue" in metrics
        and "total_assets" in metrics
    ):
        total_assets = metrics["total_assets"]

        if total_assets != 0:
            asset_turnover = (
                metrics["revenue"]
                / total_assets
            )

            claims.append(
                f"Asset turnover is {asset_turnover:.2f}, "
                f"based on revenue of "
                f"₹{_format_number(metrics['revenue'])} Cr "
                f"and total assets of "
                f"₹{_format_number(total_assets)} Cr."
            )

    if (
        "net_income" in metrics
        and "total_assets" in metrics
    ):
        total_assets = metrics["total_assets"]

        if total_assets != 0:
            roa = (
                metrics["net_income"]
                / total_assets
            ) * 100

            claims.append(
                f"Return on assets is {roa:.1f}%, "
                f"based on net income of "
                f"₹{_format_number(metrics['net_income'])} Cr "
                f"and total assets of "
                f"₹{_format_number(total_assets)} Cr."
            )

    if (
        "debt" in metrics
        and "revenue" in metrics
    ):
        revenue = metrics["revenue"]

        if revenue != 0:
            leverage = (
                metrics["debt"]
                / revenue
            )

            claims.append(
                f"Debt-to-revenue is {leverage:.2f}, "
                f"based on debt of "
                f"₹{_format_number(metrics['debt'])} Cr "
                f"and revenue of "
                f"₹{_format_number(revenue)} Cr."
            )

    if (
        "cash" in metrics
        and "debt" in metrics
    ):
        debt = metrics["debt"]

        if debt != 0:
            cash_debt = (
                metrics["cash"]
                / debt
            )

            claims.append(
                f"Cash-to-debt is {cash_debt:.2f}, "
                f"based on cash of "
                f"₹{_format_number(metrics['cash'])} Cr "
                f"and debt of "
                f"₹{_format_number(debt)} Cr."
            )

    if (
        "operating_profit" in metrics
        and "revenue" in metrics
    ):
        revenue = metrics["revenue"]

        if revenue != 0:
            margin = (
                metrics["operating_profit"]
                / revenue
            ) * 100

            claims.append(
                f"Operating margin is {margin:.1f}%, "
                f"based on operating profit of "
                f"₹{_format_number(metrics['operating_profit'])} Cr "
                f"and revenue of "
                f"₹{_format_number(revenue)} Cr."
            )

    return claims


def _build_all_claims(metrics):
    claims = _build_enriched_claims(metrics)

    claims.extend(
        _build_static_metric_claims(metrics)
    )

    return claims


def _build_enriched_analysis(metrics):
    claims = _build_all_claims(metrics)

    if not claims:
        return (
            "The reported financial figures "
            "should be interpreted together."
        )

    return " ".join(claims)


def _build_easy_explanation(metrics):
    claims = _build_all_claims(metrics)

    if not claims:
        return (
            "The reported financial figures "
            "provide the basis for a financial assessment."
        )

    return " ".join(claims)


def _build_medium_explanation(metrics):
    analysis = _build_enriched_analysis(
        metrics
    )

    return (
        f"Quantitative analysis: {analysis} "
        "These reported signals should be interpreted "
        "together rather than in isolation."
    )


def _build_hard_explanation(metrics):
    analysis = _build_enriched_analysis(
        metrics
    )

    return (
        f"Quantitative analysis: {analysis} "
        "Taken together, the reported signals should be "
        "evaluated jointly rather than in isolation. "
        "The available figures do not establish a specific "
        "causal explanation, so supporting financial "
        "disclosures would be required before drawing "
        "a causal conclusion."
    )


# ============================================================
# CLASSIFICATION
# ============================================================


def _add_change_signal(
    metrics,
    previous_key,
    current_key,
    positive_points,
    risk_points,
    positive_weight=1,
    negative_weight=1,
    strong_negative_threshold=None,
    strong_negative_weight=None,
):
    """
    Add a classification signal from a previous/current metric pair.

    Returns updated:
        positive_points
        risk_points
    """

    if (
        previous_key not in metrics
        or current_key not in metrics
    ):
        return (
            positive_points,
            risk_points,
        )

    previous_value = metrics[previous_key]
    current_value = metrics[current_key]

    change = _percentage(
        previous_value,
        current_value,
    )

    if change is None:
        return (
            positive_points,
            risk_points,
        )

    if change > 0:

        positive_points += positive_weight

    elif change < 0:

        if (
            strong_negative_threshold is not None
            and change <= strong_negative_threshold
            and strong_negative_weight is not None
        ):
            risk_points += strong_negative_weight
        else:
            risk_points += negative_weight

    return (
        positive_points,
        risk_points,
    )


def _classification_from_all_metrics(metrics):
    """
    Classify overall financial health using every
    relevant financial signal available in the scenario.

    This function is specifically used for the
    financial_classification task.

    The important principle is:

        classification should reflect the full
        information provided in the input.

    Signals considered when available:

        Revenue
        Operating profit
        Net profit
        Generic profit
        Debt
        Cash
        Cash flow
        Operating expenses
        Current ratio
        Asset turnover
        ROA
        Debt-to-revenue
        Cash-to-debt
        Operating margin

    Scoring:

        Positive signals add positive points.

        Risk signals add risk points.

        Large negative signals receive higher risk weight.

    Final labels:

        risk >= positive + 2
            -> High Risk

        positive >= risk + 2
            -> Healthy

        otherwise
            -> Moderate Risk
    """

    positive_points = 0
    risk_points = 0

    # --------------------------------------------------------
    # REVENUE
    # --------------------------------------------------------

    (
        positive_points,
        risk_points,
    ) = _add_change_signal(
        metrics=metrics,
        previous_key="previous_revenue",
        current_key="current_revenue",
        positive_points=positive_points,
        risk_points=risk_points,
        positive_weight=1,
        negative_weight=1,
    )

    # --------------------------------------------------------
    # OPERATING PROFIT
    # --------------------------------------------------------

    (
        positive_points,
        risk_points,
    ) = _add_change_signal(
        metrics=metrics,
        previous_key="previous_operating_profit",
        current_key="current_operating_profit",
        positive_points=positive_points,
        risk_points=risk_points,
        positive_weight=2,
        negative_weight=2,
        strong_negative_threshold=-20,
        strong_negative_weight=3,
    )

    # --------------------------------------------------------
    # NET PROFIT
    # --------------------------------------------------------

    (
        positive_points,
        risk_points,
    ) = _add_change_signal(
        metrics=metrics,
        previous_key="previous_net_profit",
        current_key="current_net_profit",
        positive_points=positive_points,
        risk_points=risk_points,
        positive_weight=2,
        negative_weight=2,
        strong_negative_threshold=-20,
        strong_negative_weight=3,
    )

    # --------------------------------------------------------
    # GENERIC PROFIT
    #
    # Only use this when net profit and operating profit
    # are not already available.
    # --------------------------------------------------------

    if (
        "previous_net_profit" not in metrics
        and "current_net_profit" not in metrics
        and "previous_operating_profit" not in metrics
        and "current_operating_profit" not in metrics
    ):
        (
            positive_points,
            risk_points,
        ) = _add_change_signal(
            metrics=metrics,
            previous_key="previous_profit",
            current_key="current_profit",
            positive_points=positive_points,
            risk_points=risk_points,
            positive_weight=2,
            negative_weight=2,
            strong_negative_threshold=-20,
            strong_negative_weight=3,
        )

    # --------------------------------------------------------
    # DEBT
    # --------------------------------------------------------

    if (
        "previous_debt" in metrics
        and "current_debt" in metrics
    ):

        debt_change = _percentage(
            metrics["previous_debt"],
            metrics["current_debt"],
        )

        if debt_change is not None:

            if debt_change >= 30:
                risk_points += 3

            elif debt_change > 10:
                risk_points += 1

            elif debt_change <= 0:
                positive_points += 1

    # --------------------------------------------------------
    # CASH
    # --------------------------------------------------------

    if (
        "previous_cash" in metrics
        and "current_cash" in metrics
    ):

        cash_change = _percentage(
            metrics["previous_cash"],
            metrics["current_cash"],
        )

        if cash_change is not None:

            if cash_change <= -10:
                risk_points += 2

            elif cash_change < 0:
                risk_points += 1

            elif cash_change > 0:
                positive_points += 1

    # --------------------------------------------------------
    # CASH FLOW
    # --------------------------------------------------------

    if (
        "previous_cash_flow" in metrics
        and "current_cash_flow" in metrics
    ):

        previous_cash_flow = metrics[
            "previous_cash_flow"
        ]

        current_cash_flow = metrics[
            "current_cash_flow"
        ]

        cash_flow_change = _percentage(
            previous_cash_flow,
            current_cash_flow,
        )

        if current_cash_flow <= 0:

            risk_points += 3

        elif (
            cash_flow_change is not None
            and cash_flow_change <= -20
        ):

            risk_points += 2

        elif (
            cash_flow_change is not None
            and cash_flow_change < 0
        ):

            risk_points += 1

        elif (
            cash_flow_change is not None
            and cash_flow_change > 0
        ):

            positive_points += 1

    # --------------------------------------------------------
    # OPERATING EXPENSES
    # --------------------------------------------------------

    if (
        "previous_operating_expenses" in metrics
        and "current_operating_expenses" in metrics
    ):

        expense_change = _percentage(
            metrics[
                "previous_operating_expenses"
            ],
            metrics[
                "current_operating_expenses"
            ],
        )

        if expense_change is not None:

            if expense_change >= 25:
                risk_points += 2

            elif expense_change > 10:
                risk_points += 1

            elif expense_change <= 0:
                positive_points += 1

    # --------------------------------------------------------
    # CURRENT RATIO
    # --------------------------------------------------------

    if (
        "current_assets" in metrics
        and "current_liabilities" in metrics
    ):

        current_liabilities = metrics[
            "current_liabilities"
        ]

        if current_liabilities != 0:

            current_ratio = (
                metrics["current_assets"]
                / current_liabilities
            )

            if current_ratio >= 1.5:

                positive_points += 2

            elif current_ratio < 1:

                risk_points += 2

    # --------------------------------------------------------
    # ASSET TURNOVER
    # --------------------------------------------------------

    if (
        "revenue" in metrics
        and "total_assets" in metrics
    ):

        total_assets = metrics[
            "total_assets"
        ]

        if total_assets != 0:

            asset_turnover = (
                metrics["revenue"]
                / total_assets
            )

            if asset_turnover >= 1.5:

                positive_points += 2

            elif asset_turnover < 0.75:

                risk_points += 2

    # --------------------------------------------------------
    # RETURN ON ASSETS
    # --------------------------------------------------------

    if (
        "net_income" in metrics
        and "total_assets" in metrics
    ):

        total_assets = metrics[
            "total_assets"
        ]

        if total_assets != 0:

            roa = (
                metrics["net_income"]
                / total_assets
            ) * 100

            if roa >= 10:

                positive_points += 2

            elif roa < 5:

                risk_points += 2

    # --------------------------------------------------------
    # DEBT-TO-REVENUE
    # --------------------------------------------------------

    if (
        "debt" in metrics
        and "revenue" in metrics
    ):

        revenue = metrics["revenue"]

        if revenue != 0:

            debt_to_revenue = (
                metrics["debt"]
                / revenue
            )

            if debt_to_revenue >= 1:

                risk_points += 2

            elif debt_to_revenue >= 0.75:

                risk_points += 1

            elif debt_to_revenue < 0.5:

                positive_points += 1

    # --------------------------------------------------------
    # CASH-TO-DEBT
    # --------------------------------------------------------

    if (
        "cash" in metrics
        and "debt" in metrics
    ):

        debt = metrics["debt"]

        if debt != 0:

            cash_to_debt = (
                metrics["cash"]
                / debt
            )

            if cash_to_debt < 0.20:

                risk_points += 2

            elif cash_to_debt < 0.50:

                risk_points += 1

            else:

                positive_points += 1

    # --------------------------------------------------------
    # OPERATING MARGIN
    # --------------------------------------------------------

    if (
        "operating_profit" in metrics
        and "revenue" in metrics
    ):

        revenue = metrics["revenue"]

        if revenue != 0:

            operating_margin = (
                metrics["operating_profit"]
                / revenue
            ) * 100

            if operating_margin < 10:

                risk_points += 2

            elif operating_margin >= 20:

                positive_points += 1

    # --------------------------------------------------------
    # PERIOD-BASED OPERATING MARGIN CHANGE
    # --------------------------------------------------------

    if (
        "previous_operating_profit" in metrics
        and "current_operating_profit" in metrics
        and "previous_revenue" in metrics
        and "current_revenue" in metrics
    ):

        previous_revenue = metrics[
            "previous_revenue"
        ]

        current_revenue = metrics[
            "current_revenue"
        ]

        if (
            previous_revenue != 0
            and current_revenue != 0
        ):

            previous_margin = (
                metrics["previous_operating_profit"]
                / previous_revenue
            ) * 100

            current_margin = (
                metrics["current_operating_profit"]
                / current_revenue
            ) * 100

            margin_change = (
                current_margin
                - previous_margin
            )

            if margin_change <= -5:

                risk_points += 1

            elif margin_change >= 5:

                positive_points += 1

    # --------------------------------------------------------
    # FINAL CLASSIFICATION
    # --------------------------------------------------------

    if risk_points >= positive_points + 2:
        return "High Risk"

    if positive_points >= risk_points + 2:
        return "Healthy"

    return "Moderate Risk"


def _classification_for(
    scenario_type,
    metrics,
):
    """
    Return the dataset classification label.

    For training classification tasks, use ALL available
    financial signals instead of allowing the scenario type
    to determine the label.

    The scenario-specific classification rules remain
    available in classification_rules.py for testing and
    future scenario-level validation, but the training
    classification target represents overall financial health.
    """

    return _classification_from_all_metrics(
        metrics
    )


# ============================================================
# REASONING TYPES
# ============================================================


def _reasoning_types(
    base_reasoning,
    task,
    difficulty,
):
    values = [
        item.value
        if isinstance(item, ReasoningType)
        else str(item)
        for item in base_reasoning
    ]

    # --------------------------------------------------
    # Medium examples
    # --------------------------------------------------

    if difficulty == "medium":

        if "trend_analysis" not in values:
            values.append(
                "trend_analysis"
            )

        if "comparison" not in values:
            values.append(
                "comparison"
            )

    # --------------------------------------------------
    # Classification
    # --------------------------------------------------

    if task == "financial_classification":

        if "risk_analysis" not in values:
            values.append(
                "risk_analysis"
            )

    # --------------------------------------------------
    # Report generation
    # --------------------------------------------------

    if task == "financial_report_generation":

        if "comparison" not in values:
            values.append(
                "comparison"
            )

        if difficulty in {
            "medium",
            "hard",
        }:

            if "risk_analysis" not in values:
                values.append(
                    "risk_analysis"
                )

    # --------------------------------------------------
    # Hard examples
    # --------------------------------------------------

    if difficulty == "hard":

        if "numerical_reasoning" not in values:
            values.append(
                "numerical_reasoning"
            )

        if "comparison" not in values:
            values.append(
                "comparison"
            )

        if "risk_analysis" not in values:
            values.append(
                "risk_analysis"
            )

    # --------------------------------------------------
    # Preserve order and remove duplicates
    # --------------------------------------------------

    ordered = []

    for value in values:

        if value not in ordered:
            ordered.append(
                value
            )

    return [
        ReasoningType(value)
        for value in ordered
    ]


# ============================================================
# INSTRUCTIONS
# ============================================================


def _task_instruction(
    task,
    difficulty,
    scenario_type,
):
    if task == "financial_explanation":

        if difficulty == "easy":
            return (
                "Explain the company's financial performance "
                "based on the provided financial figures."
            )

        if difficulty == "medium":
            return (
                "Explain the company's financial performance "
                "based on the provided financial figures. "
                "Quantify the key changes and explain how "
                "the reported financial signals relate to "
                "one another."
            )

        return (
            "Explain the company's financial performance "
            "based on the provided financial figures. "
            "Quantify the key changes, connect the reported "
            "financial signals, identify the principal risk "
            "or opportunity, and state what additional "
            "information would be needed before drawing "
            "a causal conclusion."
        )

    if task == "financial_classification":
        return (
            "Classify the company's overall financial health "
            "as Healthy, Moderate Risk, or High Risk using "
            "only the provided financial figures. Show the "
            "key calculations and cite the evidence supporting "
            "the classification."
        )

    return (
        "Generate a structured financial performance report "
        "using only the provided financial figures. Include "
        "an executive summary, quantitative analysis, key "
        "observations, risks or opportunities, areas "
        "requiring further investigation, and a conclusion."
    )


# ============================================================
# REPORT GENERATION
# ============================================================


def _build_executive_summary(metrics):
    claims = _build_all_claims(metrics)

    if not claims:
        return (
            "The available financial figures provide "
            "the basis for a structured assessment."
        )

    return (
        "The company reported the following key financial "
        "developments: "
        + " ".join(claims)
        + " Overall interpretation should consider these "
        "signals together."
    )


def _report_output(
    difficulty,
    metrics,
):
    executive_summary = _build_executive_summary(
        metrics
    )

    if difficulty == "easy":
        analysis = _build_easy_explanation(
            metrics
        )

        return (
            f"Executive Summary: {analysis}\n\n"
            "Key Observations: The reported figures provide "
            "the primary financial signal for this scenario.\n\n"
            "Conclusion: Further context may be required for "
            "a complete assessment."
        )

    if difficulty == "medium":
        analysis = _build_medium_explanation(
            metrics
        )

        return (
            f"Executive Summary: {executive_summary}\n\n"
            f"{analysis}\n\n"
            "Key Observations: The reported metrics should be "
            "interpreted together rather than in isolation.\n\n"
            "Risks and Opportunities: The observed financial "
            "pattern identifies areas that warrant attention.\n\n"
            "Areas Requiring Further Investigation: Additional "
            "historical periods and supporting financial detail "
            "would improve the assessment.\n\n"
            "Conclusion: The available figures support a "
            "directional assessment but not a complete judgment."
        )

    analysis = _build_hard_explanation(
        metrics
    )

    return (
        f"Executive Summary: {executive_summary}\n\n"
        f"{analysis}\n\n"
        "Key Observations: Multiple reported financial signals "
        "should be considered jointly rather than allowing one "
        "metric to determine the overall conclusion.\n\n"
        "Potential Risks and Opportunities: The combined "
        "reported pattern identifies areas requiring closer "
        "financial review.\n\n"
        "Areas Requiring Further Investigation: Review historical "
        "trends, cash-flow statements, balance-sheet composition, "
        "accounting policies, and relevant management disclosures.\n\n"
        "Conclusion: The scenario supports a structured financial "
        "assessment while retaining appropriate qualification "
        "where the available data are incomplete."
    )


# ============================================================
# MAIN GENERATOR
# ============================================================


def generate_training_example(
    scenario_type,
    task,
    difficulty,
    example_id,
    company,
    seed,
):
    """
    Generate one task-specific FinExpert training example.

    Single source of truth:

        build_difficulty_scenario()
                |
                +-- scenario metrics
                |
                +-- input
                |
                +-- claims
                |
                +-- expected output

    No second financial scenario is generated here.
    """

    if task not in TASKS:
        raise ValueError(
            f"Unsupported task: {task}"
        )

    # --------------------------------------------------
    # Generate the ONE authoritative scenario.
    # --------------------------------------------------

    difficulty_result = build_difficulty_scenario(
        scenario_type=scenario_type,
        difficulty=difficulty,
        seed=seed,
        company=company,
    )

    scenario = difficulty_result["scenario"]
    difficulty_input = difficulty_result["input"]

    metrics = scenario["metrics"]

    # --------------------------------------------------
    # Build instruction.
    # --------------------------------------------------

    instruction = _task_instruction(
        task=task,
        difficulty=difficulty,
        scenario_type=scenario_type,
    )

    # --------------------------------------------------
    # Classification.
    # --------------------------------------------------

    primary_label = _classification_for(
        scenario_type,
        metrics,
    )

    # --------------------------------------------------
    # Expected output.
    # --------------------------------------------------

    if task == "financial_explanation":

        if difficulty == "easy":
            expected_output = _build_easy_explanation(
                metrics
            )

        elif difficulty == "medium":
            expected_output = _build_medium_explanation(
                metrics
            )

        else:
            expected_output = _build_hard_explanation(
                metrics
            )

    elif task == "financial_classification":

        if difficulty == "easy":
            evidence = _build_easy_explanation(
                metrics
            )

        elif difficulty == "medium":
            evidence = _build_medium_explanation(
                metrics
            )

        else:
            evidence = _build_hard_explanation(
                metrics
            )

        expected_output = (
            f"Classification: {primary_label}\n"
            f"Evidence: {evidence}\n"
            "Basis: The classification uses only the supplied "
            "financial figures and deterministic dataset-labeling "
            "rules. It is not a complete credit, investment, or "
            "solvency assessment."
        )

    else:
        expected_output = _report_output(
            difficulty=difficulty,
            metrics=metrics,
        )

    # --------------------------------------------------
    # Metadata.
    # --------------------------------------------------

    base_reasoning = scenario.get(
        "reasoning_type",
        [],
    )
    if not base_reasoning:
        base_reasoning = [
            "numerical_reasoning"
        ]

    # scenario_generator uses strings for reasoning types.
    reasoning_types = _reasoning_types(
        base_reasoning=base_reasoning,
        task=task,
        difficulty=difficulty,
    )

    return {
        "example_id": example_id,
        "instruction": instruction,
        "input": difficulty_input,
        "expected_output": expected_output.strip(),
        "category": task,
        "difficulty": difficulty,
        "reasoning_type": reasoning_types,
        "source_type": "synthetic",
        "company": company,
    }