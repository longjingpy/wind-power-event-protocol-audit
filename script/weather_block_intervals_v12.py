"""Calendar-block uncertainty for the existing observational weather contrasts."""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "outputs/dynamic_events_v6/weather_mechanism"
OUT = ROOT / "outputs/weather_uncertainty_v12"

def main():
    data = pd.read_csv(SOURCE / "weather_mechanism_panel.csv.gz", dtype={"turbine": str})
    data["time"] = pd.to_datetime(data.time, utc=True)
    origin = pd.Timestamp("1970-01-05", tz="UTC")
    rows = []
    for source, exposure, subset in [
        ("ERA5", "treatment", data),
        ("NOAA", "noaa_treatment", data[data.noaa_match.eq(True)]),
    ]:
        for horizon in [1, 2, 4]:
            d = subset.dropna(subset=[exposure, f"outcome_{horizon}h"]).copy()
            a = d[exposure].astype(bool).to_numpy()
            y = d[f"outcome_{horizon}h"].astype(float).to_numpy()
            estimate = y[a].mean() - y[~a].mean()
            for days in [3, 7, 14]:
                block = ((d.time - origin).dt.total_seconds() // (86400 * days)).astype(int)
                counts = pd.DataFrame({"block": block.to_numpy(), "nt": a.astype(int),
                                       "nc": (~a).astype(int), "yt": y*a, "yc": y*(~a)})
                aggregate = counts.groupby("block")[["nt", "nc", "yt", "yc"]].sum()
                rng = np.random.default_rng(20260914 + days + horizon)
                weights = rng.multinomial(len(aggregate), np.full(len(aggregate), 1/len(aggregate)), size=2000)
                total = weights @ aggregate.to_numpy()
                keep = (total[:, 0] > 0) & (total[:, 1] > 0)
                draws = total[keep, 2]/total[keep, 0] - total[keep, 3]/total[keep, 1]
                low, high = np.quantile(draws, [.025, .975])
                rows.append({"source": source, "horizon_h": horizon, "block_days": days,
                             "treated_n": int(a.sum()), "control_n": int((~a).sum()),
                             "occupied_blocks": len(aggregate), "risk_difference": estimate,
                             "ci95_low": low, "ci95_high": high, "defined_resamples": int(keep.sum())})
    result = pd.DataFrame(rows)
    for source, filename in [("ERA5", "risk_by_horizon.csv"), ("NOAA", "noaa_ground_proxy_risk.csv")]:
        archived = pd.read_csv(SOURCE / filename).sort_values("horizon_h")
        observed = result[(result.source == source) & (result.block_days == 7)].sort_values("horizon_h")
        np.testing.assert_allclose(archived.risk_difference, observed.risk_difference, atol=1e-12)
    OUT.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUT / "risk_block_intervals.csv", index=False)
    print(result[result.block_days == 7].to_string(index=False))

if __name__ == "__main__":
    main()
