"""Cross-resolution raw25 correspondence on Yandun native SCADA.

Each resolution fits its own training standardizer and k=4 prototype. Test
events are matched one-to-one across resolutions within turbine and split.
The experiment reports physical-lag event intervals, complete-shape counts,
and both directional coverage fractions.
"""
from itertools import combinations
from pathlib import Path
import json
import hashlib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score

from multiscale_event_catalog import describe_interval, valid_runs

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/whole-SCADA-data/wind_power/xinjiang/yandun"
OUT = ROOT / "outputs/yandun_resolution_v17"


def intervals(mask):
    edge = np.diff(np.r_[False, mask, False].astype(np.int8))
    return list(zip(np.flatnonzero(edge == 1), np.flatnonzero(edge == -1)))


def iou(a, b, step_minutes):
    s = max(a[0], b[0]); e = min(a[1], b[1])
    inter = max(0, (e - s).total_seconds())
    union = (max(a[1], b[1]) - min(a[0], b[0])).total_seconds()
    return inter / union if union else 0.0


def one_to_one(left, right, cutoff=.5):
    edges = []
    for i, a in enumerate(left):
        for j, b in enumerate(right):
            score = iou(a["interval"], b["interval"], a["minutes"])
            if score >= cutoff:
                edges.append((-score, a["interval"][0], b["interval"][0], a["event_id"], b["event_id"], i, j))
    used_left, used_right, pairs = set(), set(), []
    for *_, i, j in sorted(edges):
        if i in used_left or j in used_right:
            continue
        used_left.add(i); used_right.add(j); pairs.append((i, j))
    return pairs


def load_native():
    meta = pd.read_csv(BASE / "machine_meta.csv").set_index("machine_num")
    columns = ["pow_fan_id", "timestamp", "real_power"]
    raw = pd.read_csv(BASE / "scadas_20240216-20240824_single.csv", usecols=columns)
    raw["pow_fan_id"] = pd.to_numeric(raw.pow_fan_id, errors="raise")
    raw = raw[raw.pow_fan_id.isin(meta.index)].copy()
    raw["time"] = pd.to_datetime(raw.timestamp).dt.tz_localize("Asia/Shanghai").dt.tz_convert("UTC")
    return raw, meta


def build_resolution(raw, meta, minutes):
    events, train_shapes = [], []
    expected = minutes // 15
    for turbine, source in raw.groupby("pow_fan_id", sort=True):
        source = source.sort_values("time").drop_duplicates("time").set_index("time")
        capacity = float(meta.loc[turbine, "rated_power"])
        native_valid = source.real_power.between(0, 1.2 * capacity) & np.isfinite(source.real_power)
        power = source.real_power.where(native_valid).resample(f"{minutes}min").mean() / capacity
        valid = native_valid.resample(f"{minutes}min").sum().eq(expected) & power.notna()
        time = power.index
        b1 = time[0] + .6 * (time[-1] - time[0]); b2 = time[0] + .8 * (time[-1] - time[0])
        split = np.where(time < b1, "train", np.where(time < b2, "validation", "test"))
        for part in ["train", "validation", "test"]:
            for lo, hi in valid_runs(valid.to_numpy() & (split == part)):
                if hi - lo < 12:
                    continue
                values = power.to_numpy()[lo:hi]
                eligible = valid.to_numpy()[lo:hi]
                lag = int(4 * 60 // minutes)
                change = pd.Series(values).diff(lag).to_numpy()
                hit = eligible & np.isfinite(change) & (np.abs(change) >= .2)
                for a, e in intervals(hit):
                    end = e - 1
                    if end <= a or a < 4 or end + 4 >= len(values):
                        continue
                    try:
                        description, shape = describe_interval(values, a, end, np.zeros(len(values), bool))
                    except AssertionError:
                        # A flat endpoint segment has no finite morphology
                        # normalizer; retain it in the anchor audit, not in
                        # the shape-comparison population.
                        continue
                    if shape is None or len(shape) != 25 or not np.isfinite(shape).all():
                        continue
                    event_id = hashlib.sha1(f"{turbine}|{part}|{minutes}|{time[lo+a]}|{time[lo+end]}".encode()).hexdigest()[:20]
                    row = {"event_id": event_id, "turbine": int(turbine), "minutes": minutes, "split": part,
                           "time_start": time[lo+a], "time_end": time[lo+end] + pd.Timedelta(minutes=minutes),
                           "interval": (time[lo+a], time[lo+end] + pd.Timedelta(minutes=minutes)),
                           "direction": int(np.sign(values[end] - values[a])), "shape": shape}
                    events.append(row)
                    if part == "train":
                        train_shapes.append(shape)
    return pd.DataFrame(events), np.asarray(train_shapes, dtype=np.float32)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    raw, meta = load_native()
    built = {}
    for minutes in [15, 30, 60]:
        event, train = build_resolution(raw, meta, minutes)
        assert len(train) >= 4
        mu, sd = train.mean(0), train.std(0); sd[sd < 1e-6] = 1
        km = KMeans(n_clusters=4, n_init=20, random_state=41).fit((train - mu) / sd)
        event["label"] = km.predict((np.stack(event["shape"]) - mu) / sd)
        built[minutes] = event
        event.drop(columns=["interval", "shape"]).to_csv(OUT / f"events_{minutes}min.csv", index=False)
        np.save(OUT / f"shapes_{minutes}min.npy", np.stack(event["shape"]).astype(np.float32))
        (OUT / f"prototype_{minutes}min.json").write_text(json.dumps({"mean": mu.tolist(), "std": sd.tolist(), "centres": km.cluster_centers_.tolist()}))
        print(minutes, "events", len(event), "train", len(train), flush=True)
    rows = []
    for left_minutes, right_minutes in combinations([15, 30, 60], 2):
        pair_rows = []
        left_all, right_all = built[left_minutes], built[right_minutes]
        for turbine in sorted(set(left_all.turbine) & set(right_all.turbine)):
            left = left_all[(left_all.turbine == turbine) & (left_all.split == "test")].sort_values("time_start").to_dict("records")
            right = right_all[(right_all.turbine == turbine) & (right_all.split == "test")].sort_values("time_start").to_dict("records")
            matched = one_to_one(left, right)
            pair_rows.extend(matched)
        # Recreate labels from the matched row order without using a pooled test fit.
        left_label, right_label = [], []
        for turbine in sorted(set(left_all.turbine) & set(right_all.turbine)):
            left = left_all[(left_all.turbine == turbine) & (left_all.split == "test")].sort_values("time_start").to_dict("records")
            right = right_all[(right_all.turbine == turbine) & (right_all.split == "test")].sort_values("time_start").to_dict("records")
            for i, j in one_to_one(left, right):
                left_label.append(left[i]["label"]); right_label.append(right[j]["label"])
        n = len(left_label)
        rows.append({"left_minutes": left_minutes, "right_minutes": right_minutes,
                     "left_test_events": int(len(left_all[left_all.split == "test"])), "right_test_events": int(len(right_all[right_all.split == "test"])),
                     "matched_pairs": n, "left_coverage": n / max(len(left_all[left_all.split == "test"]), 1),
                     "right_coverage": n / max(len(right_all[right_all.split == "test"]), 1),
                     "nmi": normalized_mutual_info_score(left_label, right_label) if n > 1 else np.nan,
                     "ari": adjusted_rand_score(left_label, right_label) if n > 1 else np.nan,
                     "k": 4, "matching_iou": .5})
    result = pd.DataFrame(rows)
    result.to_csv(OUT / "resolution_pair_summary.csv", index=False)
    source = {"path": str((BASE / "scadas_20240216-20240824_single.csv").relative_to(ROOT)),
              "native_interval_minutes": 15, "resolutions": [15, 30, 60], "physical_lag_h": 4,
              "train_fit": "each resolution standardizer and KMeans k=4 fit on train split only",
              "test_match": "same turbine, test split, one-to-one UTC intervals, IoU >= 0.5",
              "events": {str(m): int(len(e)) for m, e in built.items()}, "summary": "NMI/ARI compare resolution-specific raw25 prototypes"}
    (OUT / "protocol.json").write_text(json.dumps(source, indent=2))
    print(result.to_string(index=False))


if __name__ == "__main__":
    main()
