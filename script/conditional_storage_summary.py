from pathlib import Path
import pandas as pd

root = Path(__file__).resolve().parents[1]
data = pd.read_csv(root / "outputs/storage_policy_v15/capacity_price_surface.csv")
keys = ["site", "model", "price_case", "tail_premium", "storage_fraction", "duration_h", "seed"]
mse = data[data.training == "mse"].set_index(keys).total_cny_per_installed_mw.rename("mse")
weighted = data[data.training == "event_weighted"].set_index(keys).total_cny_per_installed_mw.rename("event_weighted")
merged = pd.concat([mse, weighted], axis=1).dropna().reset_index()
merged["difference"] = merged.event_weighted - merged.mse
merged["event_weighted_better"] = merged.difference < 0
summary = (merged.groupby(["site", "model", "price_case", "tail_premium", "storage_fraction", "duration_h"])
           .agg(mean_difference=("difference", "mean"), sd_difference=("difference", "std"),
                seeds=("difference", "size"), better_seeds=("event_weighted_better", "sum"))
           .reset_index())
summary["better_fraction"] = summary.better_seeds / summary.seeds
out = root / "outputs/storage_policy_v15/conditional_advantage.csv"
summary.to_csv(out, index=False)
print(f"cells_mean_better={(summary.mean_difference < 0).sum()} of {len(summary)}")
print(summary.sort_values("mean_difference").head(15).to_string(index=False))
print("fixed10/2")
print(summary[(summary.storage_fraction == .1) & (summary.duration_h == 2)]
      .sort_values("mean_difference").to_string(index=False))
