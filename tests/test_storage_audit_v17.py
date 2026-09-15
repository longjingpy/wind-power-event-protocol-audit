from pathlib import Path
import sys
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "script"))
import storage_audit_v17 as audit


def test_lp_charge_increases_soc_and_matches_original_objective():
    residual = np.array([.5, -.4, np.nan, .6, -.3])
    trace = audit._lp_trace(residual, .1, .2, 300., 80., 1000., .2)
    expected = audit.v15.ETA * .5 * trace["charge_mw"] - .5 * trace["discharge_mw"] / audit.v15.ETA
    np.testing.assert_allclose(np.diff(trace["soc_mwh"]), expected, atol=1e-9)
    assert trace["charge_mw"][2] == trace["discharge_mw"][2] == 0
    assert trace["charge_mw"].sum() > 0


def test_online_missing_and_future_edits_preserve_prefix():
    residual = np.array([.5, -.2, np.nan, .4, -.8])
    first = audit._online_trace(residual, .1, .2, 0., .2)
    residual[3:] = [-1., 1.]
    second = audit._online_trace(residual, .1, .2, 0., .2)
    assert np.isfinite(first["soc_mwh"]).all()
    np.testing.assert_array_equal(first["soc_mwh"][:4], second["soc_mwh"][:4])


def test_large_future_penalty_gives_lp_foresight_value():
    residual = np.array([-.1, -.6])
    online = audit._online_trace(residual, .2, .2, 0., .2)
    lp = audit._lp_trace(residual, .2, .2, 300., 80., 5000., .2)
    online_cost = audit._trace_cost(online, 300., 80., 5000., 1., .2, .2, 1.)["total_cny"]
    lp_cost = audit._trace_cost(lp, 300., 80., 5000., 1., .2, .2, 1.)["total_cny"]
    np.testing.assert_allclose(online_cost - lp_cost, 250., atol=1e-6)
