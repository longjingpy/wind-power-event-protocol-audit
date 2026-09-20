from pathlib import Path
import sys
import numpy as np
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"src"))
from wind_events.economics import imbalance_cashflow, excess_error_energy, Battery, dispatch_step, settlement_opportunity_cost
from wind_events.economics import planned_inventory_step


def test_mw_energy_and_currency_conversion():
    result = imbalance_cashflow(70, 100, 500, 500, 1)
    assert result["deviation_mwh"] == -30
    assert result["net_imbalance_cost_gbp"] == 15000


def test_negative_prices_keep_sign():
    cost = imbalance_cashflow([80, 120], [100, 100], [-50, -50], [-50, -50], .5)
    np.testing.assert_allclose(cost["net_imbalance_cost_gbp"], [-500, 500])


def test_equal_nmae_does_not_determine_tolerance_cost():
    a, b = np.array([20., 0]), np.array([10., 10])
    assert np.abs(a).mean() == np.abs(b).mean()
    assert excess_error_energy(a, np.zeros(2), 10, .5).sum() == 5
    assert excess_error_energy(b, np.zeros(2), 10, .5).sum() == 0


def test_battery_conserves_energy_with_efficiency_and_bounds():
    battery = Battery(5, 10)
    state = dispatch_step(20, 10, 8, battery)
    assert state["stored_mwh"] == pytest.approx(9)
    assert state["discharge_mw"] == 0
    assert state["stored_mwh"]-8 == pytest.approx(state["charge_mw"]*.5*.92)
    state = dispatch_step(0, 20, 2, battery)
    assert state["stored_mwh"] == pytest.approx(1)
    assert state["discharge_mw"]*.5/.92 == pytest.approx(1)


def test_zero_storage_equals_no_action():
    state = dispatch_step(40, 60, 0, Battery(0, 0))
    assert state["metered_mw"] == 40 and state["throughput_mwh"] == 0


def test_contract_revenue_prevents_flat_price_forecast_arbitrage():
    np.testing.assert_allclose(settlement_opportunity_cost([40, 60], [70, 20], 100, 100, 100), 0)
    assert settlement_opportunity_cost(50, 60, 20, 100, 100, 1) == 800


def test_planned_controller_terminal_inventory_and_energy():
    battery=Battery(5,10)
    state=5.
    charged=discharged=0.
    for i in range(48):
        step=planned_inventory_step(20 if i%3 else 0,10,state,battery,47-i,5)
        assert 1-1e-9 <= step['stored_mwh'] <= 9+1e-9
        assert max(step['charge_mw'],step['discharge_mw']) <= 5+1e-9
        assert min(step['charge_mw'],step['discharge_mw']) == 0
        charged+=step['charge_mw']*.5;discharged+=step['discharge_mw']*.5
        state=step['stored_mwh']
    assert state==pytest.approx(5)
    assert charged*.92==pytest.approx(discharged/.92)


def test_fixed_commitment_cashflow_difference_cancels_unknown_baseline():
    for actual in (-2,30,60):
        base=imbalance_cashflow(actual,40,80,80)['net_imbalance_cost_gbp']
        changed=imbalance_cashflow(actual+3,40,80,80)['net_imbalance_cost_gbp']
        assert changed-base==pytest.approx(-3*.5*80)
