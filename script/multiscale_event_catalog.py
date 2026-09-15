"""Versioned retrospective intervals, preserving detector and scale provenance.

Threshold/tail/mean-shift definitions extend this project's v3 contract across
three declared horizons. They are study-defined comparators, not calibrated VaR.
Ahn & Hur (2022), DOI 10.3390/en15072676, pp.2,16, motivates SDA comparisons;
it does not specify the endpoint-corridor implementation below. That baseline
is explicitly SDA-style, NOT a reproduction of published OpSDA. Its defining
max-error invariant is checked against an independent exhaustive implementation.
"""
from pathlib import Path
from itertools import combinations
import hashlib
import json
import numpy as np
import pandas as pd
from common_event_experiment import series
from pizhou_component_matching import shutdown_mask

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/dynamic_events_v4"
HORIZONS = (2, 4, 8)
EPSILONS = (.025, .05, .10)
CONFIGS = [f"{method}_{h//2}h" for method in ["threshold", "financial_tail", "mean_shift"] for h in HORIZONS] + [f"endpoint_corridor_{eps:.3f}" for eps in EPSILONS]


def sha256(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def source_files():
    paths = list((ROOT / "data/event_clean_v2/pizhou").glob("*.csv.gz"))
    paths += list((ROOT / "data/external_samples/hill_of_towie/clean_native").glob("T[0-9][0-9].csv.gz"))
    paths += list((ROOT / "data/whole-SCADA-data/wind_power/jiangsu/xuzhou/suining").rglob("*.csv"))
    paths += [ROOT / "data/external_samples/la_haute_borne/la-haute-borne-data-2014-2015.csv"]
    paths += [p for p in (ROOT / "data/event_clean_v2/yandun").glob("*.csv.gz") if p.name != "unmatched_ids.csv.gz"]
    return sorted(paths)


def valid_runs(mask):
    edges = np.diff(np.r_[False, mask, False].astype(int))
    return list(zip(np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)))


def endpoint_corridor(x, epsilon):
    """Greedy actual-endpoint chords; every accepted chord has max error <=eps.

    Prior point k permits endpoint slopes [(x[k]-x[a]-eps)/(k-a),
    (x[k]-x[a]+eps)/(k-a)]. Intersect these intervals, test each new actual
    endpoint, and close at the preceding point on failure. This is a declared
    endpoint-constrained variant, not an inferred equation from the cited paper.
    """
    if epsilon <= 0 or not np.isfinite(x).all():
        raise ValueError("Positive tolerance and finite contiguous input required")
    if len(x) < 2:
        return []
    segments, start = [], 0
    low, high = -np.inf, np.inf
    for end in range(1, len(x)):
        slope = (x[end]-x[start])/(end-start)
        if slope < low-1e-12 or slope > high+1e-12:
            segments.append((start, end-1))
            start = end-1
            low, high = -np.inf, np.inf
        low = max(low, (x[end]-x[start]-epsilon)/(end-start))
        high = min(high, (x[end]-x[start]+epsilon)/(end-start))
    segments.append((start, len(x)-1))
    return segments


def merge_signed(intervals):
    """Merge consecutive intersecting intervals only when detector signs agree."""
    merged = []
    for start, end, sign in intervals:
        if merged and sign == merged[-1][2] and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(end, merged[-1][1]), sign)
        else:
            merged.append((start, end, sign))
    return merged


def sliding_candidates(x, method, lag):
    p = pd.Series(x)
    if method == "mean_shift":
        movement = p.rolling(lag).mean()-p.shift(lag).rolling(lag).mean()
        hit = movement.abs().ge(.20).to_numpy()
        span = 2*lag-1
    else:
        movement = p.diff(lag)
        if method == "threshold":
            hit = movement.abs().ge(.20).to_numpy()
        elif method == "financial_tail":
            history = movement.shift(1).rolling(48, min_periods=48)
            hit = ((movement.lt(history.quantile(.05)) | movement.gt(history.quantile(.95))) & movement.abs().ge(.10)).to_numpy()
        else:
            raise ValueError(method)
        span = lag
    ids = np.flatnonzero(hit)
    return merge_signed([(int(i-span), int(i), int(np.sign(movement.iloc[i]))) for i in ids])


def configurations(x):
    result = {}
    for method in ["threshold", "financial_tail", "mean_shift"]:
        for lag in HORIZONS:
            result[f"{method}_{lag//2}h"] = sliding_candidates(x, method, lag)
    for epsilon in EPSILONS:
        result[f"endpoint_corridor_{epsilon:.3f}"] = [(a,b,int(np.sign(x[b]-x[a]))) for a,b in endpoint_corridor(x,epsilon) if abs(x[b]-x[a]) >= .20]
    return result


def describe_interval(x, a, b, shutdown):
    values = x[a:b+1]
    delta = np.diff(values)
    context_ok = a >= 4 and b+4 < len(x)
    support = slice(a-4,b+5) if context_ok else slice(a,b+1)
    suspect_context = bool(shutdown[support].any())
    eligible = context_ok and not suspect_context
    curve = values-np.linspace(values[0], values[-1], len(values))
    row = {"duration_hours":(b-a)*.5, "amplitude":float(values[-1]-values[0]),
        "direction":int(np.sign(values[-1]-values[0])), "min_offset":int(values.argmin()), "max_offset":int(values.argmax()),
        "power_start":float(values[0]), "power_end":float(values[-1]),
        "power_range":float(np.ptp(values)), "total_variation":float(np.abs(delta).sum()),
        "max_abs_rate_per_hour":float(np.abs(delta).max()*2),
        "max_abs_chord_residual":float(np.abs(curve).max()),
        "curvature_l1":float(np.abs(np.diff(values, n=2)).sum()),
        "pre_mean":float(x[a-4:a].mean()) if context_ok else None,
        "post_mean":float(x[b+1:b+5].mean()) if context_ok else None,
        "left_boundary":a == 0, "right_boundary":b == len(x)-1,
        "suspected_shutdown_event":bool(shutdown[a:b+1].any()),
        "suspected_shutdown_available_support":suspect_context,
        "context_complete":context_ok, "representation_eligible":eligible}
    shape = None
    if eligible:
        resampled = np.interp(np.linspace(0,b-a,17),np.arange(b-a+1),values)
        path = np.r_[x[a-4:a],resampled,x[b+1:b+5]]-values[0]
        denominator = np.abs(path).max()
        assert denominator > 0
        shape = (path/denominator).astype(np.float32)
        row["shape_normalizer"] = float(denominator)
    else:
        row["shape_normalizer"] = None
    return row, shape


def main():
    OUT.mkdir(exist_ok=True)
    files = source_files()
    inputs = {str(p.relative_to(ROOT)):sha256(p) for p in files}
    rows, shapes, audit = [], [], []
    intersections, unions, opportunities = {}, {}, {}
    for site, turbine, time, power, quality, capacity in series(audit_dir=OUT, exclude_hill_shutdown=False):
        time = pd.DatetimeIndex(time)
        assert time.is_unique and np.all(np.diff(time.asi8) == 1_800_000_000_000)
        raw = np.asarray(power,float)
        valid = np.asarray(quality,bool) & np.isfinite(raw)
        b1, b2 = time[0]+.6*(time[-1]-time[0]), time[0]+.8*(time[-1]-time[0])
        calibration = raw[valid & (time < b1)]
        scale = float(capacity) if capacity is not None else float(np.quantile(calibration,.995)) if len(calibration) else np.nan
        assert np.isfinite(scale) and scale > 0, (site,turbine)
        x = raw/scale
        split_ids = np.where(time < b1,"train",np.where(time < b2,"validation","test"))
        turbine_count = 0
        for split in ["train","validation","test"]:
            masks = {config:np.zeros(len(x)-1,bool) for config in CONFIGS}
            common = np.zeros(len(x)-1,bool)
            for lo, hi in valid_runs(valid & (split_ids == split)):
                if hi-lo < 2:
                    continue
                values = x[lo:hi]
                shutdown = shutdown_mask(values,np.ones(len(values),bool))
                # Same comparison interior for all detectors; exclude 48+maxlag
                # edges at each run start to avoid financial-history warmup.
                common[lo+56:hi-1] = True
                for config, intervals in configurations(values).items():
                    for a,b,detector_sign in intervals:
                        assert 0 <= a < b < len(values)
                        row, shape = describe_interval(values,a,b,shutdown)
                        start, end = int(lo+a),int(lo+b)
                        key = f"{site}|{turbine}|{split}|{config}|{time[start]}|{time[end]}"
                        row.update({"event_id":hashlib.sha256(key.encode()).hexdigest()[:24],
                            "site":site,"turbine":str(turbine),"split":split,"config":config,
                            "start_index":start,"end_index":end,"time_start":time[start],"time_end":time[end],
                            "time_min":time[start+row.pop("min_offset")],"time_max":time[start+row.pop("max_offset")],
                            "detector_direction":detector_sign,"scale":scale,"scale_basis":"nameplate" if capacity is not None else "early_60pct_q995",
                            "shape_row":len(shapes) if shape is not None else -1})
                        rows.append(row)
                        if shape is not None:
                            shapes.append(shape)
                        masks[config][start:end] = True
                        turbine_count += 1
            key = (site,split)
            opportunities[key] = opportunities.get(key,0)+int(common.sum())
            for a,b in combinations(CONFIGS,2):
                key = (site,split,a,b)
                intersections[key] = intersections.get(key,0)+int((masks[a] & masks[b] & common).sum())
                unions[key] = unions.get(key,0)+int(((masks[a] | masks[b]) & common).sum())
        audit.append({"site":site,"turbine":str(turbine),"start":str(time[0]),"end":str(time[-1]),
            "rows":len(time),"valid_rows":int(valid.sum()),"scale":scale,"scale_basis":"nameplate" if capacity is not None else "early_60pct_q995",
            "b1":str(b1),"b2":str(b2),"candidates":turbine_count})
        print(site,turbine,turbine_count,flush=True)
    table = pd.DataFrame(rows)
    assert table.event_id.is_unique and not table.duplicated(["site","turbine","split","config","start_index","end_index"]).any()
    array = np.stack(shapes)
    assert array.shape == (int(table.representation_eligible.sum()),25) and np.isfinite(array).all()
    table.to_csv(OUT / "candidate_intervals.csv.gz",index=False)
    np.save(OUT / "context_shapes.npy",array)
    pd.DataFrame(audit).to_csv(OUT / "source_series.csv",index=False)
    summaries = []
    for key, group in table.groupby(["site","split","config"]):
        summaries.append(dict(zip(["site","split","config"],key)) | {"candidates":len(group),
            "eligible":int(group.representation_eligible.sum()),"duration_median_h":float(group.duration_hours.median()),
            "duration_q95_h":float(group.duration_hours.quantile(.95)),"shutdown_event_fraction":float(group.suspected_shutdown_event.mean()),
            "boundary_fraction":float((group.left_boundary | group.right_boundary).mean())})
    pd.DataFrame(summaries).to_csv(OUT / "interval_summary.csv",index=False)
    comparisons = []
    for key, inter in intersections.items():
        union = unions[key]
        comparisons.append(dict(zip(["site","split","config_a","config_b"],key)) | {"intersection_edges":inter,
            "union_edges":union,"common_valid_edges":opportunities[key[:2]],"temporal_iou":inter/union if union else None})
    pd.DataFrame(comparisons).to_csv(OUT / "detector_temporal_overlap.csv",index=False)
    # Ensure source files stayed unchanged throughout the run.
    assert all(sha256(ROOT/path) == value for path,value in inputs.items())
    manifest = {"status":"CANDIDATE_INTERVALS_NOT_PHYSICAL_LIFECYCLES", "configurations":CONFIGS,
        "candidate_rows":len(table),"shape_rows":len(array),"source_series":len(audit),"input_sha256":inputs,
        "script_sha256":sha256(Path(__file__)),"dependency_sha256":{name:sha256(ROOT / "script" / name) for name in ["common_event_experiment.py","pizhou_component_matching.py"]},
        "protocol_sha256":sha256(ROOT / "temp/multiscale_event_protocol.md"),
        "outputs_sha256":{name:sha256(OUT / name) for name in ["candidate_intervals.csv.gz","context_shapes.npy","source_series.csv","interval_summary.csv","detector_temporal_overlap.csv"]},
        "limits":["retrospective boundaries not onset/recovery truth","source interval semantics unresolved at some sites","early-site calibration not zero-shot","endpoint corridor not verified published SDA/OpSDA reproduction","cross-detector/context overlaps remain","shutdown heuristic not fault truth","no model or weather findings certified","long interval/interpolation effects require downstream sensitivity"]}
    (OUT / "catalog_manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf8")
    print(table.groupby("site").size().to_string())


if __name__ == "__main__":
    main()

