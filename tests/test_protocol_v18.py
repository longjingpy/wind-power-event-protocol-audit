"""Scientific invariants, including physical time, gaps and train isolation."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"script"))
from wind_events import Protocol, regularize, fit_scale, describe, detect, build_catalog
from wind_events.catalog import corridor, composite_intervals
from wind_events.literature import original_sda, opsda_2015
from wind_events.matching import match_intervals, pair_catalog
import literature_detectors_v5 as legacy


def test_train_only_scale():
    power = np.arange(1., 101.)
    split = np.array(["train"]*60+["validation"]*20+["test"]*20)
    before = fit_scale(power, np.ones(100, bool), split)
    power[80:] = 1e9
    assert fit_scale(power, np.ones(100, bool), split) == before


def test_missing_and_duplicate_bins_remain_invalid():
    t = pd.date_range("2020-01-01", periods=12, freq="10min", tz="UTC")
    keep = [0, 1, 2, 3, 4, 6, 7, 7, 8, 9, 10, 11]
    _, x, valid, audit = regularize(t[keep], np.ones(12), np.ones(12, bool), 10, 30)
    assert valid.tolist() == [True, False, False, True]
    assert np.isnan(x[1:3]).all()
    assert audit["duplicate_source_rows"] == 2


def test_source_end_labels_are_shifted():
    t = pd.date_range("2020-01-01 00:10", periods=3, freq="10min", tz="UTC")
    t2, x, valid, _ = regularize(t, [1, 2, 3], [True]*3, 10, 30, "end")
    assert t2[0] == pd.Timestamp("2020-01-01", tz="UTC")
    assert valid.tolist() == [True] and x[0] == 2


def test_context_locations_and_duration_are_resolution_invariant():
    results = []
    for cadence in (10, 15, 30, 60):
        minutes = np.arange(0, 1441, cadence)
        x = minutes/1440
        row, shape = describe(x, 240//cadence, 480//cadence, Protocol(resolution_minutes=cadence))
        results.append(shape)
        assert row["duration_hours"] == 4
        assert row["max_abs_rate_per_hour"] == pytest.approx(1/24)
    for result in results[1:]:
        np.testing.assert_allclose(result, results[0], atol=1e-7)


def test_literature_kernels_equal_archived_source():
    rng = np.random.default_rng(41)
    x = np.cumsum(rng.normal(0, .15, 100))
    assert original_sda(x, .025) == legacy.original_sda(x, .025)
    for lag in (2, 4, 8, 24):
        assert opsda_2015(x, .025, lag) == legacy.opsda_2015(x, .025, lag)


def test_seventeen_configs_and_physical_lags():
    x = np.linspace(0, 1, 100)
    configs = detect(x, Protocol(resolution_minutes=10))
    assert len(configs) == 17
    assert "threshold_60min" in configs and "opsda_cui2015_240min_0.025" in configs


def test_adaptive_width_is_past_only():
    rng = np.random.default_rng(4)
    x = np.cumsum(rng.normal(0, .1, 180))
    prefix = corridor(x, None, 48)
    x[120:] += 20
    modified = corridor(x, None, 48)
    assert [r for r in prefix if r[1] < 119] == [r for r in modified if r[1] < 119]


def test_v_and_inverted_v_keep_turning_points():
    for sign, kind in ((1, "inverted_v"), (-1, "v")):
        x = sign*np.r_[np.linspace(0, 1, 5), np.linspace(.75, 0, 4)]
        found = composite_intervals(x, [(0, 4, sign), (4, 8, -sign)])
        assert found == [(0, 8, 4, kind, 0, 1)]


def test_catalog_does_not_cross_missing_or_split_boundaries():
    t = pd.date_range("2020-01-01", periods=500, freq="30min", tz="UTC")
    x = .5+.4*np.sin(np.arange(500)/3)
    valid = np.ones(500, bool)
    valid[240:255] = False
    table, shapes, audit = build_catalog("toy", "T1", t, x, valid)
    assert len(table) and len(shapes)
    for row in table.itertuples():
        assert valid[row.start_index:row.end_index+1].all()
        if row.representation_eligible:
            assert row.start_index-4 >= row.run_start
            assert row.end_index+4 < row.run_end_exclusive
    assert table.event_id.is_unique and shapes.shape[1] == 25
    assert audit["scale_basis"] == "training_q995"


def test_bad_cadence_and_nonfinite_run_fail():
    with pytest.raises(ValueError):
        Protocol(resolution_minutes=45)
    with pytest.raises(ValueError):
        detect([0, np.nan, 1])


def test_matching_is_one_to_one_and_deterministic():
    left = [("a", 0, 10), ("b", 8, 20)]
    right = [("c", 0, 12), ("d", 8, 21)]
    for method in ("greedy", "maximum_iou"):
        pairs = match_intervals(left, right, .3, method)
        assert len(pairs) == 2
        assert pairs == match_intervals(left[::-1], right[::-1], .3, method)
        assert len({r[0] for r in pairs}) == len({r[1] for r in pairs}) == 2


def test_pairs_cannot_cross_turbines_or_splits():
    base = {"site": "toy", "event_level": "primitive", "time_start": "2020-01-01", "time_end": "2020-01-01 02:00"}
    table = pd.DataFrame([base | {"event_id": "a", "config": "A", "turbine": "1", "split": "test"},
                          base | {"event_id": "b", "config": "B", "turbine": "2", "split": "test"},
                          base | {"event_id": "c", "config": "B", "turbine": "1", "split": "validation"}])
    pairs, coverage = pair_catalog(table, configurations=["A", "B"])
    assert not len(pairs) and coverage.pairs.sum() == 0


def test_external_test_never_fits_target_scale():
    t = pd.date_range("2021-01-01", periods=300, freq="30min", tz="UTC")
    x = .5+.4*np.sin(np.arange(300)/3)
    with pytest.raises(ValueError):
        build_catalog("holdout", "T1", t, x, np.ones(300, bool), external_test=True)
    table, shapes, audit = build_catalog("holdout", "T1", t, x, np.ones(300, bool), external_test=True,
        scale_override=(2., "frozen_reference_training_q995"))
    assert table.split.eq("test").all() and audit["scale"] == 2
    assert audit["b1"] is None and audit["b2"] is None
