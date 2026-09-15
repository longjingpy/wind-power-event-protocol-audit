"""Describe matched/unmatched populations separately for every detector pair.

The unit is a detector catalogue side within a configuration pair, not the
union of events matched to any detector. Wind is the mean of four valid
half-hour bins strictly preceding event start, using the same turbine clock.
"""
from itertools import combinations
from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "outputs/dynamic_events_v6"
OUT = ROOT / "outputs/matched_composition_v16"


def wind_sources():
    for site in ["pizhou", "yandun"]:
        for path in sorted((ROOT / "data/event_clean_v2" / site).glob("*.csv.gz")):
            if path.name == "unmatched_ids.csv.gz":
                continue
            data = pd.read_csv(path)
            wind = data.wind_speed_ms.where(data.wind_speed_ms.between(0, 60))
            valid = data.wind_valid_count.eq(30) if site == "pizhou" else data.native_count.eq(2)
            yield site, str(data.turbine_id.iloc[0]), data.timestamp_start_utc, wind.where(valid), str(path.relative_to(ROOT))
    for path in sorted((ROOT / "data/external_samples/hill_of_towie/clean_native").glob("T[0-9][0-9].csv.gz")):
        data = pd.read_csv(path)
        wind = data.wind_speed_ms.where(data.wind_valid & data.wind_speed_ms.between(0, 60))
        yield "hill", path.name.split(".")[0], data.timestamp_start_utc, wind, str(path.relative_to(ROOT))
    base = ROOT / "data/whole-SCADA-data/wind_power/jiangsu/xuzhou/suining"
    for path in sorted(base.rglob("*.csv")):
        data = pd.read_csv(path, encoding="gb18030")
        stamp = pd.to_datetime(data["时间"]).dt.tz_localize("Asia/Shanghai").dt.tz_convert("UTC")
        wind = pd.to_numeric(data["风速"], errors="coerce")
        yield "suining", str(data["名称"].iloc[0]), stamp, wind.where(wind.between(0, 60)), str(path.relative_to(ROOT))
    path = ROOT / "data/external_samples/la_haute_borne/la-haute-borne-data-2014-2015.csv"
    data = pd.read_csv(path, usecols=["Wind_turbine_name", "Date_time", "Ws_avg"])
    for turbine, group in data.groupby("Wind_turbine_name"):
        yield "lahaute", str(turbine), group.Date_time, group.Ws_avg.where(group.Ws_avg.between(0, 60)), str(path.relative_to(ROOT))


def prewindow(stamp, values, native_count):
    index = pd.DatetimeIndex(pd.to_datetime(stamp, utc=True))
    series = pd.Series(np.asarray(values, dtype=float), index=index)
    duplicate = series.index.duplicated(keep=False)
    series = series[~duplicate].sort_index()
    binned = series.resample("30min").mean().where(series.resample("30min").count().eq(native_count))
    return binned.shift(1).rolling(4, min_periods=4).mean(), int(duplicate.sum())


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    columns = ["event_id", "site", "turbine", "split", "config", "time_start", "duration_hours",
               "amplitude", "direction", "power_start", "power_range", "representation_eligible"]
    cand = pd.read_csv(SRC / "candidate_intervals.csv.gz", usecols=columns, dtype={"turbine": str})
    cand = cand[cand.split.eq("test") & cand.representation_eligible].copy()
    assert cand.event_id.is_unique
    cand["time_start"] = pd.to_datetime(cand.time_start, utc=True)
    cand["wind_prewindow_ms"] = np.nan
    source_records = []
    found = set()
    for site, turbine, stamp, values, source in wind_sources():
        selected = cand.site.eq(site) & cand.turbine.eq(turbine)
        if not selected.any():
            raise ValueError(f"No event key for source {site}/{turbine}")
        expected = 1 if site in ["pizhou", "yandun"] else 3
        wind, duplicate = prewindow(stamp, values, expected)
        cand.loc[selected, "wind_prewindow_ms"] = wind.reindex(cand.loc[selected, "time_start"]).to_numpy()
        source_records.append({"site": site, "turbine": turbine, "path": source,
                               "duplicate_source_rows_excluded": duplicate, "wind_prewindows": int(wind.notna().sum())})
        found.add((site, turbine))
    expected_keys = set(map(tuple, cand[["site", "turbine"]].drop_duplicates().to_numpy()))
    assert found == expected_keys, expected_keys - found
    pairs = pd.read_csv(SRC / "test_pairs.csv.gz", usecols=["site", "config_a", "config_b", "event_a", "event_b"])
    assert set(pairs.event_a) | set(pairs.event_b) <= set(cand.event_id)
    lookup = {(site, ca, cb): (set(group.event_a), set(group.event_b))
              for (site, ca, cb), group in pairs.groupby(["site", "config_a", "config_b"])}
    cand["absolute_amplitude"] = cand.amplitude.abs()
    cand["upward_fraction"] = cand.direction.gt(0).astype(float)
    features = ["duration_hours", "amplitude", "absolute_amplitude", "power_range", "power_start", "upward_fraction", "wind_prewindow_ms"]
    rows = []
    for site, site_data in cand.groupby("site"):
        catalogues = {config: group for config, group in site_data.groupby("config")}
        for ca, cb in combinations(sorted(catalogues), 2):
            matched = lookup.get((site, ca, cb), (set(), set()))
            for side, config, ids in [("left", ca, matched[0]), ("right", cb, matched[1])]:
                data = catalogues[config]
                hit = data.event_id.isin(ids)
                assert int(hit.sum()) == len(ids)
                for population, flag in [("matched", hit), ("unmatched", ~hit)]:
                    subset = data.loc[flag]
                    for feature in features:
                        values = subset[feature].dropna()
                        rows.append({"site": site, "config_a": ca, "config_b": cb, "side": side,
                                     "population": population, "feature": feature, "events": len(subset),
                                     "valid_feature_events": len(values), "catalogue_events": len(data),
                                     "matched_fraction": float(hit.mean()), "mean": values.mean(),
                                     "q25": values.quantile(.25), "median": values.median(), "q75": values.quantile(.75)})
        print(site, "complete", flush=True)
    result = pd.DataFrame(rows)
    result.to_csv(OUT / "pair_side_composition.csv", index=False)
    keys = ["site", "config_a", "config_b", "side", "feature"]
    m = result[result.population.eq("matched")].set_index(keys)
    u = result[result.population.eq("unmatched")].set_index(keys)
    comparison = m[["mean", "events", "valid_feature_events"]].join(u[["mean", "events", "valid_feature_events"]], lsuffix="_matched", rsuffix="_unmatched")
    comparison["mean_difference"] = comparison.mean_matched - comparison.mean_unmatched
    comparison.to_csv(OUT / "matched_unmatched_differences.csv")
    compared = comparison.reset_index()
    counts = compared.groupby(["site", "feature"]).agg(
        pair_sides=("mean_difference", "size"), supported_pair_sides=("mean_difference", "count"))
    supported = compared.dropna(subset=["mean_matched", "mean_unmatched"])
    summary = counts.join(supported.groupby(["site", "feature"]).agg(
        equal_pair_mean_matched=("mean_matched", "mean"), equal_pair_mean_unmatched=("mean_unmatched", "mean"),
        equal_pair_mean_difference=("mean_difference", "mean")))
    np.testing.assert_allclose(summary.equal_pair_mean_matched - summary.equal_pair_mean_unmatched,
                               summary.equal_pair_mean_difference, atol=1e-12)
    summary.to_csv(OUT / "site_composition_summary.csv")
    cand[["event_id", "site", "turbine", "time_start", "wind_prewindow_ms"]].to_csv(OUT / "event_wind.csv.gz", index=False)
    pd.DataFrame(source_records).to_csv(OUT / "source_records.csv", index=False)
    (OUT / "protocol.json").write_text(json.dumps({"events": len(cand), "sites": int(cand.site.nunique()),
        "turbines": len(found), "pair_side_population_feature_rows": len(result),
        "scope": "complete test events, each detector-pair side considered separately; no union-match substitution",
        "wind": "same-turbine four complete 30-min bins strictly before event start; no interpolation",
        "summary": "equal pair-side feature means; missing wind and empty populations are explicit"}, indent=2))
    print(summary.to_string())


if __name__ == "__main__":
    main()
