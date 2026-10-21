"""Hand-checked values for every formula (each computed on paper first)."""

import pytest

from finexpert.finance import formulas as f


def test_roic_uses_ebit_and_net_invested_capital():
    # EBIT 500, tax 30% -> NOPAT 350; capital 1,200 + 1,350 - 400 - 100 = 2,050; 350 / 2,050 = 17.07%
    assert f.nopat(500, 0.30) == pytest.approx(350)
    assert f.invested_capital(1200, 1350, cash=400, non_operating_investments=100) == 2050
    assert f.pct(f.roic(500, 0.30, 2050)) == pytest.approx(17.073, abs=1e-3)
    # the reported failure: EBITDA 630 x 0.7 = 441 over gross capital 2,550 = 17.29%  (wrong definitions)
    assert f.pct(f.nopat(630, 0.30) / 2550) == pytest.approx(17.294, abs=1e-3)


def test_fcff_and_fcfe():
    # 400 x 0.75 = 300; + 80 - 120 - 30 = 230
    assert f.fcff(400, 0.25, 80, 120, 30) == pytest.approx(230)
    # 230 - 40 x 0.75 + 50 = 250
    assert f.fcfe(230, 40, 0.25, 50) == pytest.approx(250)


def test_margins_cagr_wacc_and_ratios():
    assert f.pct(f.margin(75, 500)) == pytest.approx(15)
    assert f.ebitda(500, 130) == 630
    assert f.pct(f.cagr(100, 146.41, 4)) == pytest.approx(10, abs=1e-9)      # 1.1^4 = 1.4641
    # 2/3 x 12% + 1/3 x 8% x 0.75 = 8% + 2% = 10%
    assert f.pct(f.wacc(200, 100, 0.12, 0.08, 0.25)) == pytest.approx(10)
    assert f.pct(f.roe(90, 600)) == pytest.approx(15)
    assert f.interest_coverage(450, 90) == pytest.approx(5)
    assert f.days_sales_outstanding(120, 730) == pytest.approx(60)
