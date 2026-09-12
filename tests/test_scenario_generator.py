import pytest

from finexpert.data.scenario_generator import (
    SCENARIO_TYPES,
    generate_scenario,
)


def test_all_scenario_types_are_supported():
    for scenario_type in SCENARIO_TYPES:
        scenario = generate_scenario(
            scenario_type=scenario_type,
            seed=42,
        )

        assert scenario["scenario_type"] == scenario_type
        assert "metrics" in scenario
        assert "expected_signals" in scenario
        assert scenario["metrics"]
        assert scenario["expected_signals"]


def test_same_seed_produces_same_scenario():
    scenario_a = generate_scenario(
        scenario_type="profitability",
        seed=42,
    )

    scenario_b = generate_scenario(
        scenario_type="profitability",
        seed=42,
    )

    assert scenario_a == scenario_b


def test_different_seed_can_produce_different_scenarios():
    scenario_a = generate_scenario(
        scenario_type="profitability",
        seed=42,
    )

    scenario_b = generate_scenario(
        scenario_type="profitability",
        seed=100,
    )

    assert scenario_a != scenario_b


def test_unknown_scenario_type_raises_error():
    with pytest.raises(ValueError):
        generate_scenario(
            scenario_type="unknown",
            seed=42,
        )


def test_random_scenario_type_is_supported():
    scenario = generate_scenario(seed=42)

    assert scenario["scenario_type"] in SCENARIO_TYPES