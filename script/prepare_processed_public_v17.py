"""Export frozen study inputs as pseudonymized processed SCADA.

Original identities and clock origins stay private. Per-turbine Parquet
output and four-column SDWPF batch reads bound memory. Raw files stay local.
"""
from collections import defaultdict
from pathlib import Path
import gc
import json
import zipfile
import argparse
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from common_event_experiment import series
from matched_composition_v16 import wind_sources

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/processed_public_v17"
PRIVATE = ROOT / "temp/processed_public_v17_private"
SITE_IDS = dict(zip(["pizhou", "suining", "yandun", "hill", "lahaute", "greece", "sdwpf"], [f"WF{i:02d}" for i in range(1, 8)]))
EXPECTED = dict(zip(SITE_IDS.values(), [33, 14, 117, 21, 4, 10, 134]))
COLUMNS = ["site_id", "turbine_id", "time_index", "interval_minutes", "relative_day", "source_hour", "month",
           "split", "power_norm", "power_valid", "wind_speed_ms", "wind_valid"]


def regular(values, stamps, minutes, required=1):
    index = pd.DatetimeIndex(pd.to_datetime(stamps, utc=True, errors="coerce")).as_unit("ns")
    data = pd.Series(np.asarray(values, dtype=float), index=index)
    data = data[~index.isna()]
    duplicate = data.index.duplicated(keep=False)
    data = data[~duplicate].sort_index()
    means = data.resample(f"{minutes}min").mean()
    count = data.resample(f"{minutes}min").count()
    return means, count.ge(required), int(duplicate.sum())


def make_frame(site, turbine, index, power, power_valid, wind, wind_valid, scale, minutes, origin, boundaries=None):
    index = pd.DatetimeIndex(index).as_unit("ns")
    assert index.is_unique and index.is_monotonic_increasing
    assert np.all(np.diff(index.asi8) == pd.Timedelta(minutes=minutes).value)
    assert np.isfinite(scale) and scale > 0
    boundaries = boundaries or [index[0] + .6 * (index[-1] - index[0]), index[0] + .8 * (index[-1] - index[0])]
    p, w = np.asarray(power, dtype=float), np.asarray(wind, dtype=float)
    pv = np.asarray(power_valid, dtype=bool) & np.isfinite(p)
    wv = np.asarray(wind_valid, dtype=bool) & np.isfinite(w) & (w >= 0) & (w <= 60)
    frame = pd.DataFrame({"site_id": site, "turbine_id": turbine,
        "time_index": ((index.asi8 - origin.value) // pd.Timedelta(minutes=minutes).value).astype(np.int64),
        "interval_minutes": minutes, "relative_day": ((index.floor("D") - origin.floor("D")).days).astype(np.int32),
        "source_hour": index.hour.astype(np.int8), "month": index.month.astype(np.int8),
        "split": np.where(index < boundaries[0], "train", np.where(index < boundaries[1], "validation", "test")),
        "power_norm": np.where(pv, p / scale, np.nan), "power_valid": pv,
        "wind_speed_ms": np.where(wv, w, np.nan), "wind_valid": wv})
    assert list(frame.columns) == COLUMNS and not frame.duplicated(["site_id", "turbine_id", "time_index"]).any()
    assert pv.any(), f"No usable power for {site}/{turbine}"
    np.testing.assert_allclose(frame.loc[pv, "power_norm"].to_numpy() * scale, p[pv], rtol=1e-12, atol=1e-9)
    return frame


def write_turbine(frame, source_site, source_turbine, origin, scale, basis, records, private):
    sid, tid = frame.site_id.iloc[0], frame.turbine_id.iloc[0]
    folder = OUT / "tables" / sid
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{tid}.parquet"
    frame.to_parquet(path, index=False, compression="zstd")
    pd.testing.assert_frame_equal(frame, pd.read_parquet(path))
    assert pq.ParquetFile(path).schema.names == COLUMNS
    records.append({"site_id": sid, "turbine_id": tid, "file": path.relative_to(OUT).as_posix(),
                    "rows": len(frame), "power_valid_rows": int(frame.power_valid.sum()),
                    "wind_valid_rows": int(frame.wind_valid.sum()), "interval_minutes": int(frame.interval_minutes.iloc[0]),
                    "first_index": int(frame.time_index.iloc[0]), "last_index": int(frame.time_index.iloc[-1]),
                    "scale_basis": basis, "file_bytes": path.stat().st_size})
    private.append({"site_id": sid, "turbine_id": tid, "original_site": source_site, "original_turbine": str(source_turbine),
                    "clock_origin": str(origin), "scale_source_units": float(scale)})


def primary(records, private):
    ref = pd.read_csv(ROOT / "outputs/dynamic_events_v6/source_series.csv", dtype={"turbine": str})
    for col in ["start", "end", "b1", "b2"]:
        ref[col] = pd.to_datetime(ref[col], utc=True)
    lookup = ref.set_index(["site", "turbine"])
    identifiers = {(site, tid): f"T{i:03d}" for site, group in ref.groupby("site")
                   for i, tid in enumerate(sorted(group.turbine), 1)}
    origins = ref.groupby("site").start.min().to_dict()
    winds = {}
    for site, tid, stamps, values, _ in wind_sources():
        if (site, tid) in identifiers:
            winds[site, tid] = regular(values, stamps, 30, 1 if site in ["pizhou", "yandun"] else 3)[:2]
    seen = set()
    for site, tid, stamps, power, valid, _ in series(audit_dir=PRIVATE, exclude_hill_shutdown=False):
        key = (site, str(tid))
        if key not in identifiers:
            continue
        assert key not in seen, key
        seen.add(key)
        source = lookup.loc[key]
        index = pd.DatetimeIndex(pd.to_datetime(stamps, utc=True))
        assert len(index) == source.rows and index[0] == source.start and index[-1] == source.end
        assert int(np.asarray(valid, dtype=bool).sum()) == source.valid_rows
        w, ok = winds[key]
        frame = make_frame(SITE_IDS[site], identifiers[key], index, power, valid,
                           w.reindex(index).to_numpy(), ok.reindex(index, fill_value=False).to_numpy(),
                           source.scale, 30, origins[site], [source.b1, source.b2])
        write_turbine(frame, site, tid, origins[site], source.scale, "frozen_primary_analysis_scale", records, private)
    assert seen == set(identifiers)
    del winds
    gc.collect()
    print("primary 189 turbines complete", flush=True)


def greek(records, private):
    paths = sorted((ROOT / "data/external_samples/greece_smd10towfgr/clean_native").glob("WT*_data.csv.gz"))
    columns = ["Timestamp", "Grid Production Power Avg. [W]", "Ambient WindSpeed Avg. [m/s]"]
    sources = [pd.read_csv(path, usecols=columns) for path in paths]
    origin = min(pd.to_datetime(data.Timestamp, utc=True).min() for data in sources).floor("10min")
    for i, (path, data) in enumerate(zip(paths, sources), 1):
        timestamps = pd.to_datetime(data.Timestamp, utc=True, errors="coerce")
        values = pd.to_numeric(data[columns[1]], errors="coerce")
        scale = abs(float(np.quantile(values[timestamps.notna() & np.isfinite(values)], .995)))
        p, pv, _ = regular(values, timestamps, 10)
        w, wv, _ = regular(data[columns[2]], timestamps, 10)
        frame = make_frame("WF06", f"T{i:03d}", p.index, p.to_numpy(), pv.to_numpy(),
                           w.reindex(p.index).to_numpy(), wv.reindex(p.index, fill_value=False).to_numpy(), scale, 10, origin)
        write_turbine(frame, "greece", path.name.split("_")[0], origin, scale,
                      "whole_archive_q995_unknown_power_units_source_clock_unverified", records, private)
    print("Greek 10 turbines complete", flush=True)


def sdwpf(records, private):
    path = ROOT / "data/external_public/sdwpf/sdwpf_2001_2112_full.parquet"
    chunks, origin = defaultdict(list), None
    for batch in pq.ParquetFile(path).iter_batches(batch_size=131072, columns=["TurbID", "Tmstamp", "Patv", "Wspd"]):
        data = batch.to_pandas()
        data["Tmstamp"] = pd.to_datetime(data.Tmstamp, utc=True, errors="coerce")
        minimum = data.Tmstamp.min()
        origin = minimum if origin is None or minimum < origin else origin
        for tid, group in data.groupby("TurbID", sort=False):
            chunks[tid].append(group[["Tmstamp", "Patv", "Wspd"]].copy())
    origin = origin.floor("30min")
    for i, tid in enumerate(sorted(chunks), 1):
        data = pd.concat(chunks.pop(tid), ignore_index=True)
        p, pv, duplicate = regular(data.Patv, data.Tmstamp, 30, 1)
        assert duplicate == 0
        w, wv, _ = regular(data.Wspd, data.Tmstamp, 30, 1)
        scale = abs(float(np.quantile(p[pv], .995)))
        frame = make_frame("WF07", f"T{i:03d}", p.index, p.to_numpy(), pv.to_numpy(), w.to_numpy(), wv.to_numpy(), scale, 30, origin)
        write_turbine(frame, "sdwpf", tid, origin, scale, "whole_archive_q995_halfhour_available_mean", records, private)
        if i % 20 == 0:
            print("SDWPF", i, "complete", flush=True)
    print("SDWPF 134 turbines complete", flush=True)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    PRIVATE.mkdir(parents=True, exist_ok=True)
    records, private = [], []
    primary(records, private)
    greek(records, private)
    sdwpf(records, private)
    index = pd.DataFrame(records)
    counts = index.groupby("site_id").turbine_id.nunique().to_dict()
    assert counts == EXPECTED and len(index) == 333, counts
    index.to_csv(OUT / "file_index.csv", index=False)
    (PRIVATE / "identity_and_clock_map.json").write_text(json.dumps(private, indent=2))
    metadata = {"status": "PROCESSED_TABLES_VERIFIED", "version": "v17", "turbines": 333, "sites": 7,
        "rows": int(index.rows.sum()), "site_turbine_counts": counts, "columns": COLUMNS,
        "deidentification": "pseudonymous identifiers; original IDs, coordinates, absolute dates and clock origins excluded",
        "time": "common relative time index within site; no interpolation; month/source-hour retained for context",
        "clock_caution": "WF06/WF07 timezone is unverified; hour follows the source clock",
        "power": "unitless archived analysis normalization; primary reference scales frozen, external q995 uses each archive",
        "quality": "primary source time spans, row counts, usable-power counts and Parquet numeric round trips checked",
        "scope": "processed SCADA only; original files, private maps, free-text logs and personal material excluded"}
    (OUT / "metadata.json").write_text(json.dumps(metadata, indent=2))
    (OUT / "README.md").write_text("# Processed wind-power research dataset\n\nSeven study archives and 333 pseudonymous turbines. Complete inventory and normalization are in metadata.json and file_index.csv. Each Parquet file contains a regular relative clock, normalized power, wind, validity flags and chronological split. Missing measurements remain null; no interpolation is performed. Original turbine names, locations and absolute dates are excluded. Month and source-clock hour support seasonal context. Pseudonymization is not a guarantee against inference from previously public data.\n\nPrimary validity and scales follow the archived analysis. WF06 retains 10-minute source-clock sampling with unknown absolute power units; WF07 uses available 30-minute means. Use power_valid and wind_valid independently.\n\nThe provider authorizes processed contributions under study MIT terms. Original source attribution and conditions remain applicable: Greek monitoring archive doi:10.5281/zenodo.14546480; SDWPF doi:10.6084/m9.figshare.24798654; La Haute Borne/OpenOA and Hill of Towie.\n")
    package()
    print(json.dumps(metadata, indent=2))


def package():
    (OUT / "LICENSE").write_text((ROOT / "public_release/LICENSE").read_text())
    dictionary = {"site_id": "Pseudonymous study archive ID", "turbine_id": "Pseudonymous turbine ID within archive",
        "time_index": "Integer interval offset from a common site origin, retained only in the private map",
        "interval_minutes": "10 or 30; multiply time-index differences by this value for physical durations",
        "relative_day": "Calendar-day difference from the site origin; preserves same-site day grouping",
        "source_hour": "UTC hour for primary archives; unverified source-clock hour for WF06/WF07",
        "month": "Calendar month 1-12; absolute year and date are omitted",
        "split": "Archived chronological train/validation/test assignment at 60% and 80% of each turbine span",
        "power_norm": "Unitless power divided by the archived analysis reference; null when power_valid is false",
        "power_valid": "Eligibility under the stated archive-specific power protocol",
        "wind_speed_ms": "Processed turbine wind speed in m/s; null when wind_valid is false",
        "wind_valid": "Available wind meeting source completeness and the 0-60 m/s range check"}
    (OUT / "data_dictionary.json").write_text(json.dumps(dictionary, indent=2))
    names = ["metadata.json", "file_index.csv", "README.md", "LICENSE", "data_dictionary.json"]
    members = [*[OUT / name for name in names], *sorted((OUT / "tables").rglob("*.parquet"))]
    archive = ROOT / "outputs/processed_scada_v17.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_STORED) as package:
        for member in members:
            package.write(member, member.relative_to(OUT).as_posix())
    with zipfile.ZipFile(archive) as package:
        assert len(package.namelist()) == 338 and package.testzip() is None
        assert all(name.startswith("tables/WF") or name in names for name in package.namelist())
    print(json.dumps({"zip_bytes": archive.stat().st_size, "members": len(members)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--package-only", action="store_true")
    args = parser.parse_args()
    package() if args.package_only else main()
