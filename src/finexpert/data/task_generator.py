from .example_generator import generate_explanation_example
from .schema import ReasoningType
from .scenario_generator import generate_scenario


TASKS = (
    "financial_explanation",
    "financial_classification",
    "financial_report_generation",
)

CLASSIFICATION_LABELS = (
    "Healthy",
    "Moderate Risk",
    "High Risk",
)


# Medium and hard examples add a second related financial signal.
# This prevents difficulty from being only a metadata label.
RELATED_SCENARIOS = {
    "revenue_growth": "profitability",
    "profitability": "cash_flow",
    "operating_expenses": "revenue_growth",
    "debt_leverage": "liquidity",
    "liquidity": "debt_leverage",
    "cash_flow": "profitability",
    "efficiency": "profitability",
    "risk_analysis": "liquidity",
    "multi_metric_comparison": "comprehensive_performance",
    "comprehensive_performance": "risk_analysis",
}


SCENARIO_LABELS = {
    "revenue_growth": "Revenue",
    "profitability": "Profitability",
    "operating_expenses": "Operating expenses",
    "debt_leverage": "Debt and leverage",
    "liquidity": "Liquidity",
    "cash_flow": "Operating cash flow",
    "efficiency": "Operating efficiency",
    "risk_analysis": "Financial risk",
    "multi_metric_comparison": "Multi-metric performance",
    "comprehensive_performance": "Comprehensive performance",
}


def _percentage(old_value, new_value):
    if old_value == 0:
        return None
    return ((new_value - old_value) / old_value) * 100


def _classification_for(scenario_type, metrics):
    """Return a deterministic, conservative dataset label."""

    if scenario_type == "revenue_growth":
        change = _percentage(
            metrics["previous_revenue"],
            metrics["current_revenue"],
        )
        if change is None or change == 0:
            return "Moderate Risk"
        return "Healthy" if change > 0 else "High Risk"

    if scenario_type == "profitability":
        revenue_growth = _percentage(
            metrics["previous_revenue"],
            metrics["current_revenue"],
        )
        profit_growth = _percentage(
            metrics["previous_profit"],
            metrics["current_profit"],
        )
        old_margin = (
            metrics["previous_profit"]
            / metrics["previous_revenue"]
        )
        new_margin = (
            metrics["current_profit"]
            / metrics["current_revenue"]
        )

        if (
            revenue_growth is not None
            and profit_growth is not None
        ):
            if (
                revenue_growth > 0
                and profit_growth > 0
                and new_margin >= old_margin
            ):
                return "Healthy"
            if (
                profit_growth < 0
                and new_margin < old_margin
            ):
                return "High Risk"
        return "Moderate Risk"

    if scenario_type == "operating_expenses":
        ratio = (
            metrics["current_operating_expenses"]
            / metrics["revenue"]
        )
        change = _percentage(
            metrics["previous_operating_expenses"],
            metrics["current_operating_expenses"],
        )
        if change is not None:
            if ratio <= 0.25 and change <= 10:
                return "Healthy"
            if ratio >= 0.40 or change >= 25:
                return "High Risk"
        return "Moderate Risk"

    if scenario_type == "debt_leverage":
        debt_change = _percentage(
            metrics["previous_debt"],
            metrics["current_debt"],
        )
        leverage = (
            metrics["current_debt"]
            / metrics["equity"]
        )
        if debt_change is not None:
            if leverage < 1.0 and debt_change <= 10:
                return "Healthy"
            if leverage >= 2.0 or debt_change >= 30:
                return "High Risk"
        return "Moderate Risk"

    if scenario_type == "liquidity":
        ratio = (
            metrics["current_assets"]
            / metrics["current_liabilities"]
        )
        if ratio >= 1.5:
            return "Healthy"
        if ratio < 1.0:
            return "High Risk"
        return "Moderate Risk"

    if scenario_type == "cash_flow":
        change = _percentage(
            metrics["previous_cash_flow"],
            metrics["current_cash_flow"],
        )
        if (
            metrics["current_cash_flow"] > 0
            and change is not None
            and change >= 0
        ):
            return "Healthy"
        if (
            metrics["current_cash_flow"] <= 0
            or (
                change is not None
                and change <= -20
            )
        ):
            return "High Risk"
        return "Moderate Risk"

    if scenario_type == "efficiency":
        asset_turnover = (
            metrics["revenue"]
            / metrics["total_assets"]
        )
        roa = (
            metrics["net_income"]
            / metrics["total_assets"]
        ) * 100
        if asset_turnover >= 1.5 and roa >= 10:
            return "Healthy"
        if asset_turnover < 0.75 or roa < 5:
            return "High Risk"
        return "Moderate Risk"

    if scenario_type == "risk_analysis":
        leverage = (
            metrics["debt"]
            / metrics["revenue"]
        )
        cash_debt = (
            metrics["cash"]
            / metrics["debt"]
        )
        margin = (
            metrics["operating_profit"]
            / metrics["revenue"]
        )
        risk_points = int(leverage >= 1.0)
        risk_points += int(cash_debt < 0.20)
        risk_points += int(margin < 0.10)
        if risk_points >= 2:
            return "High Risk"
        if risk_points == 0:
            return "Healthy"
        return "Moderate Risk"

    if scenario_type in {
        "multi_metric_comparison",
        "comprehensive_performance",
    }:
        revenue_growth = _percentage(
            metrics["previous_revenue"],
            metrics["current_revenue"],
        )
        profit_growth = _percentage(
            metrics["previous_profit"],
            metrics["current_profit"],
        )
        debt_growth = _percentage(
            metrics["previous_debt"],
            metrics["current_debt"],
        )

        if (
            profit_growth is not None
            and debt_growth is not None
            and profit_growth < 0
            and debt_growth >= 20
        ):
            return "High Risk"

        if (
            revenue_growth is not None
            and profit_growth is not None
            and revenue_growth > 0
            and profit_growth > 0
            and (
                debt_growth is None
                or debt_growth <= 20
            )
        ):
            return "Healthy"

        return "Moderate Risk"

    return "Moderate Risk"


def _reasoning_types(base, task, difficulty):
    values = [
        item.value
        for item in base["reasoning_type"]
    ]

    if task == "financial_classification":
        if "risk_analysis" not in values:
            values.append("risk_analysis")

    elif task == "financial_report_generation":
        if "comparison" not in values:
            values.append("comparison")
        if difficulty == "hard":
            if "risk_analysis" not in values:
                values.append("risk_analysis")

    if difficulty == "hard":
        if "numerical_reasoning" not in values:
            values.append("numerical_reasoning")
        if "comparison" not in values:
            values.append("comparison")

    ordered = []
    for value in values:
        if value not in ordered:
            ordered.append(value)

    return [ReasoningType(value) for value in ordered]


def _task_instruction(task, base_instruction, difficulty):
    if task == "financial_explanation":
        if difficulty == "easy":
            return base_instruction

        if difficulty == "medium":
            return (
                base_instruction
                + " Quantify the key changes and explain how the reported "
                "financial signals relate to one another."
            )

        return (
            base_instruction
            + " Quantify the key changes, connect the financial signals, "
            "identify the principal risk or opportunity, and state what "
            "additional information would be needed before drawing a causal conclusion."
        )

    if task == "financial_classification":
        return (
            "Classify the company's overall financial health as Healthy, "
            "Moderate Risk, or High Risk using the provided financial figures. "
            "Show the key calculations, compare the relevant signals, and cite "
            "the evidence supporting the classification."
        )

    return (
        "Generate a structured financial performance report from the provided "
        "figures. Include an executive summary, quantitative analysis, key "
        "observations, risks or opportunities, areas requiring further "
        "investigation, and a conclusion."
    )


def _append_related_context(
    base,
    related,
    related_example,
    difficulty,
):
    """Add genuinely additional financial information for medium/hard cases."""

    if difficulty == "easy":
        return

    base["input"] = (
        base["input"].strip()
        + " Additional related financial information: "
        + related_example["input"].strip()
    )

    base["expected_output"] = (
        base["expected_output"].strip()
        + " Related analysis: "
        + related_example["expected_output"].strip()
    )


def _classification_output(
    primary_label,
    related_label,
    base_output,
    related_output,
    difficulty,
):
    if difficulty == "easy":
        final_label = primary_label
        evidence = base_output
    else:
        # When two independent signals disagree, use the conservative
        # middle class rather than inventing a stronger conclusion.
        if primary_label == related_label:
            final_label = primary_label
        else:
            final_label = "Moderate Risk"

        evidence = (
            f"Primary analysis: {base_output} "
            f"Related analysis: {related_output}"
        )

    return (
        f"Classification: {final_label}\n"
        f"Evidence: {evidence}\n"
        "Basis: The classification uses only the supplied financial figures "
        "and deterministic dataset-labeling rules. It is not a complete "
        "credit, investment, or solvency assessment."
    )


def _report_output(
    base_output,
    related_output,
    difficulty,
):
    if difficulty == "easy":
        return (
            f"Executive Summary: {base_output}\n\n"
            "Key Observations: The reported figures provide the primary "
            "financial signal for this scenario.\n\n"
            "Conclusion: Further context may be required for a complete assessment."
        )

    if difficulty == "medium":
        return (
            f"Executive Summary: {base_output}\n\n"
            f"Quantitative Analysis: {related_output}\n\n"
            "Key Observations: The primary and related metrics should be "
            "interpreted together rather than in isolation.\n\n"
            "Risks and Opportunities: The observed pattern identifies areas "
            "that warrant attention.\n\n"
            "Areas Requiring Further Investigation: Additional historical "
            "periods and supporting financial detail would improve the assessment.\n\n"
            "Conclusion: The available figures support a directional assessment "
            "but not a complete judgment."
        )

    return (
        f"Executive Summary: {base_output}\n\n"
        f"Quantitative Analysis: {related_output}\n\n"
        "Key Observations: Multiple financial signals may reinforce or offset "
        "one another, so no single metric should determine the overall conclusion.\n\n"
        "Potential Risks and Opportunities: The combined pattern identifies "
        "areas requiring closer financial review, but the supplied figures do "
        "not establish a specific causal explanation.\n\n"
        "Areas Requiring Further Investigation: Review historical trends, "
        "cash-flow statements, balance-sheet composition, accounting policies, "
        "and relevant management disclosures.\n\n"
        "Conclusion: The scenario supports a structured financial assessment "
        "while retaining appropriate qualification where the available data are incomplete."
    )


def _normalize_legacy_input(base, scenario_type, scenario):
    # NOTE: debt_leverage input text intentionally keeps the neutral
    # "moved from X to Y" wording. Rewriting it to "increased/declined
    # from" makes the claim parser treat debt as a value-change claim,
    # which then requires a matching *output* growth claim in a
    # supported metric -- but "debt" is deliberately excluded from
    # SUPPORTED_GROWTH_METRICS (see example_validator.py). That
    # combination made every debt_leverage example unconditionally
    # fail financial validation. Do not "fix" this by re-adding a
    # debt-specific rewrite here without also revisiting
    # SUPPORTED_GROWTH_METRICS.

    if scenario_type in {
        "multi_metric_comparison",
        "comprehensive_performance",
    }:
        base["input"] = base["input"].replace(
            "Total debt moved from",
            "Total debt increased from",
        )


def _append_debt_claim(base, scenario):
    previous_debt = scenario["metrics"]["previous_debt"]
    current_debt = scenario["metrics"]["current_debt"]
    debt_change = _percentage(
        previous_debt,
        current_debt,
    )

    if debt_change is None:
        return

    if debt_change > 0:
        direction = "increased"
    elif debt_change < 0:
        direction = "declined"
    else:
        direction = "remained unchanged"

    base["expected_output"] += (
        f" Total debt {direction} by approximately "
        f"{abs(debt_change):.1f} percent."
    )


def generate_training_example(
    scenario_type,
    task,
    difficulty,
    example_id,
    company,
    seed,
):
    """Generate one task-specific FinExpert training example."""

    if task not in TASKS:
        raise ValueError(
            f"Unsupported task: {task}"
        )

    base = generate_explanation_example(
        scenario_type=scenario_type,
        difficulty=difficulty,
        example_id=example_id,
        company=company,
        seed=seed,
    )

    primary_scenario = generate_scenario(
        scenario_type=scenario_type,
        seed=seed,
    )

    _normalize_legacy_input(
        base,
        scenario_type,
        primary_scenario,
    )

    if scenario_type == "debt_leverage":
        _append_debt_claim(
            base,
            primary_scenario,
        )

    related_scenario_type = RELATED_SCENARIOS.get(
        scenario_type
    )

    related_example = None
    related_label = None

    if (
        difficulty in {"medium", "hard"}
        and related_scenario_type is not None
    ):
        related_example = generate_explanation_example(
            scenario_type=related_scenario_type,
            difficulty=difficulty,
            example_id=f"{example_id}_related",
            company=company,
            seed=seed + 10000,
        )

        related_scenario = generate_scenario(
            scenario_type=related_scenario_type,
            seed=seed + 10000,
        )

        _normalize_legacy_input(
            related_example,
            related_scenario_type,
            related_scenario,
        )

        if related_scenario_type == "debt_leverage":
            _append_debt_claim(
                related_example,
                related_scenario,
            )

        related_label = _classification_for(
            related_scenario_type,
            related_scenario["metrics"],
        )

    base_output = base["expected_output"].strip()

    base["instruction"] = _task_instruction(
        task,
        base["instruction"],
        difficulty,
    )

    primary_label = _classification_for(
        scenario_type,
        primary_scenario["metrics"],
    )

    if task == "financial_explanation":
        if related_example is not None:
            _append_related_context(
                base,
                related_scenario_type,
                related_example,
                difficulty,
            )
        elif difficulty == "medium":
            base["expected_output"] = (
                base_output
                + " The key financial implication should be interpreted "
                "in the context of the reported metrics."
            )
        elif difficulty == "hard":
            base["expected_output"] = (
                base_output
                + " Taken together, the reported signals should be evaluated "
                "jointly. The available figures do not establish a specific "
                "causal explanation, so supporting disclosures should be reviewed."
            )

    elif task == "financial_classification":
        related_output = (
            related_example["expected_output"].strip()
            if related_example is not None
            else ""
        )
        base["expected_output"] = _classification_output(
            primary_label=primary_label,
            related_label=related_label,
            base_output=base_output,
            related_output=related_output,
            difficulty=difficulty,
        )

    else:
        related_output = (
            related_example["expected_output"].strip()
            if related_example is not None
            else ""
        )
        base["expected_output"] = _report_output(
            base_output=base_output,
            related_output=related_output,
            difficulty=difficulty,
        )

    if task == "financial_explanation" and related_example is None:
        # Keep the existing base output for easy examples.
        base["expected_output"] = base["expected_output"].strip()

    base["category"] = task
    base["reasoning_type"] = _reasoning_types(
        base,
        task,
        difficulty,
    )

    return base