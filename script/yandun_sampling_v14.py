"""Physical-horizon sampling sensitivity; complete windows and no gap filling."""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/whole-SCADA-data/wind_power/xinjiang/yandun"
OUT = ROOT / "outputs/yandun_sampling_v14"

def threshold_anchors(power, valid, minutes, horizon_h):
    """A fixed physical lag needs every intervening aggregate bin."""
    lag = int(horizon_h * 60 // minutes)
    if lag * minutes != horizon_h * 60:
        raise ValueError("Horizon must be divisible by grid resolution")
    eligible = valid.rolling(lag + 1, min_periods=lag + 1).sum().eq(lag + 1)
    change = power - power.shift(lag)
    return eligible, change, eligible & change.abs().ge(.2)

def main():
    meta = pd.read_csv(BASE / "machine_meta.csv").set_index("machine_num")
    raw = pd.read_csv(BASE / "scadas_20240216-20240824_single.csv")
    raw["pow_fan_id"] = pd.to_numeric(raw.pow_fan_id, errors="raise")
    raw = raw[raw.pow_fan_id.isin(meta.index)].copy()
    raw["time"] = pd.to_datetime(raw.timestamp).dt.tz_localize("Asia/Shanghai").dt.tz_convert("UTC")
    rows = []
    for turbine, source in raw.groupby("pow_fan_id", sort=True):
        source = source.sort_values("time")
        if source.time.duplicated().any():
            repeated = source[source.time.duplicated(keep=False)]
            assert repeated.groupby("time").real_power.nunique(dropna=False).le(1).all()
            source = source.drop_duplicates("time")
        source = source.set_index("time")
        capacity = float(meta.loc[turbine, "rated_power"])
        valid_native = source.real_power.between(0, 1.2 * capacity) & np.isfinite(source.real_power)
        for minutes in [15, 30, 60]:
            rule = f"{minutes}min"
            mean = source.real_power.where(valid_native).resample(rule).mean()/capacity
            valid = valid_native.resample(rule).sum().eq(minutes//15) & mean.notna()
            for horizon in [1, 4]:
                eligible, change, hit = threshold_anchors(mean, valid, minutes, horizon)
                for clock in ["native_grid", "common_hourly_clock"]:
                    selected = pd.Series(True, index=mean.index) if clock == "native_grid" else pd.Series(mean.index.minute == 0, index=mean.index)
                    opportunity = eligible & selected
                    rows.append({"site": "yandun", "turbine": int(turbine), "minutes": minutes,
                                 "horizon_h": horizon, "clock": clock, "grid_rows": len(mean),
                                 "usable_rows": int(valid.sum()), "eligible_anchors": int(opportunity.sum()),
                                 "positive_anchors": int((hit & selected).sum()),
                                 "median_abs_change": float(change[opportunity].abs().median())})
    OUT.mkdir(parents=True, exist_ok=True)
    data = pd.DataFrame(rows)
    data.to_csv(OUT / "turbine_anchor_counts.csv", index=False)
    summary = data.groupby(["minutes", "horizon_h", "clock"])[["eligible_anchors", "positive_anchors"]].sum().reset_index()
    summary["positive_rate"] = summary.positive_anchors/summary.eligible_anchors
    summary.to_csv(OUT / "anchor_detection_summary.csv", index=False)
    print(summary.to_string(index=False))

if __name__ == "__main__":
    main()
