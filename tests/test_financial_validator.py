from finexpert.data.financial_validator import percentage_change

def test_percentage_change_decrease():
    result = percentage_change(20, 15)

    assert result["success"] is True
    assert result["calculated_value"] == -25.0
    print(result)

def test_percentage_change_increase():
    result = percentage_change(70, 130) 

    assert result["success"] is True
    assert result["calculated_value"] == 85.71428571428571
    print(result)

def test_percentage_change_old_value_zero():
    result = percentage_change(0, 50)

    assert result["success"] is False
    assert result["reason"] == "percentage_change_undefined"
    print(result)

def test_profit_margin():
    from finexpert.data.financial_validator import profit_margin

    result = profit_margin(1000, 200)

    assert result["success"] is True
    assert result["calculated_value"] == 20.0
    print(result)
def test_profit_margin_revenue_zero():
    from finexpert.data.financial_validator import profit_margin

    result = profit_margin(0, 200)

    assert result["success"] is False
    assert result["reason"] == "profit_margin_undefined"
    print(result)

def test_debt_to_equity():
    from finexpert.data.financial_validator import debt_to_equity

    result = debt_to_equity(5000, 10000)

    assert result["success"] is True
    assert result["calculated_value"] == 0.5
    print(result)

def test_debt_to_equity_total_equity_zero():   
    from finexpert.data.financial_validator import debt_to_equity

    result = debt_to_equity(5000, 0)

    assert result["success"] is False
    assert result["reason"] == "debt_to_equity_undefined"
    print(result)

def test_current_ratio():
    from finexpert.data.financial_validator import current_ratio

    result = current_ratio(8000, 4000)

    assert result["success"] is True
    assert result["calculated_value"] == 2.0
    print(result)

def test_current_ratio_current_liabilities_zero():
    from finexpert.data.financial_validator import current_ratio

    result = current_ratio(8000, 0)

    assert result["success"] is False
    assert result["reason"] == "current_ratio_undefined"
    print(result)

def test_net_profit_margin():
    from finexpert.data.financial_validator import net_profit_margin

    result = net_profit_margin(1000, 200)

    assert result["success"] is True
    assert result["calculated_value"] == 20.0
    print(result)


def test_net_profit_margin_revenue_zero():
    from finexpert.data.financial_validator import net_profit_margin

    result = net_profit_margin(0, 200)

    assert result["success"] is False
    assert result["reason"] == "net_profit_margin_undefined"
    print(result)

def test_debt_to_revenue():
    from finexpert.data.financial_validator import debt_to_revenue

    result = debt_to_revenue(5000, 10000)

    assert result["success"] is True
    assert result["calculated_value"] == 0.5
    print(result)

def test_debt_to_revenue_revenue_zero():
    from finexpert.data.financial_validator import debt_to_revenue

    result = debt_to_revenue(5000, 0)

    assert result["success"] is False
    assert result["reason"] == "debt_to_revenue_undefined"
    print(result)

def test_return_on_assets():
    from finexpert.data.financial_validator import return_on_assets

    result = return_on_assets(2000, 10000)

    assert result["success"] is True
    assert result["calculated_value"] == 20.0
    print(result)

def test_return_on_assets_total_assets_zero():
    from finexpert.data.financial_validator import return_on_assets

    result = return_on_assets(2000, 0)

    assert result["success"] is False
    assert result["reason"] == "return_on_assets_undefined"
    print(result)

def test_return_on_equity():
    from finexpert.data.financial_validator import return_on_equity

    result = return_on_equity(2000, 10000)

    assert result["success"] is True
    assert result["calculated_value"] == 20.0
    print(result)

def test_return_on_equity_total_equity_zero():
    from finexpert.data.financial_validator import return_on_equity

    result = return_on_equity(2000, 0)

    assert result["success"] is False
    assert result["reason"] == "return_on_equity_undefined"
    print(result)

def test_earning_growth_rate():
    from finexpert.data.financial_validator import earning_growth_rate

    result = earning_growth_rate(1000, 2000)

    assert result["success"] is True
    assert result["calculated_value"] == 100.0
    print(result)

def test_earning_growth_rate_negative():
    from finexpert.data.financial_validator import earning_growth_rate

    result = earning_growth_rate(2000, 1000)

    assert result["success"] is True
    assert result["calculated_value"] == -50.0
    print(result)

def test_earning_growth_rate_previous_earnings_zero():
    from finexpert.data.financial_validator import earning_growth_rate

    result = earning_growth_rate(0, 1000)

    assert result["success"] is False
    assert result["reason"] == "earning_growth_rate_undefined"
    print(result)

def test_revenue_growth_rate():
    from finexpert.data.financial_validator import revenue_growth_rate

    result = revenue_growth_rate(1000, 2000)

    assert result["success"] is True
    assert result["calculated_value"] == 100.0
    print(result)

def test_revenue_growth_rate_negative():
    from finexpert.data.financial_validator import revenue_growth_rate

    result = revenue_growth_rate(2000, 1000)

    assert result["success"] is True
    assert result["calculated_value"] == -50.0
    print(result)

def test_revenue_growth_rate_previous_revenue_zero():
    from finexpert.data.financial_validator import revenue_growth_rate

    result = revenue_growth_rate(0, 1000)

    assert result["success"] is False
    assert result["reason"] == "revenue_growth_rate_undefined"
    print(result)

def test_operating_expense_ratio():
    from finexpert.data.financial_validator import operating_expense_ratio

    result = operating_expense_ratio(500, 2000)

    assert result["success"] is True
    assert result["calculated_value"] == 25.0
    print(result)

def test_operating_expense_ratio_revenue_zero():
    from finexpert.data.financial_validator import operating_expense_ratio

    result = operating_expense_ratio(500, 0)

    assert result["success"] is False
    assert result["reason"] == "operating_expense_ratio_undefined"
    print(result)