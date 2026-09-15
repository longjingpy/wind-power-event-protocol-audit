from pathlib import Path
import json
import sys
import numpy as np
import pandas as pd

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "script"))
import benchmark_detection_v9 as bench

rows = []
for model in ["timesnet", "kanad"]:
    candidates = []
    for directory in sorted((root / "outputs/detection_hpo_v16").glob("h*")):
        if not directory.is_dir():
            continue
        config = json.loads((directory / "calibration.json").read_text())
        data = np.load(directory / "dataset.npz")
        validation = []
        for seed in [41, 42, 43]:
            score = np.load(directory / f"scores_{model}_{seed}.npz")["validation"]
            cfg = config[f"{model}-{seed}"]["calibrated"]
            validation.append(bench.evaluate(score, data["validation_mask"], cfg, .3)["f1"])
        candidates.append((float(np.mean(validation)), directory, validation))
    value, directory, validation = max(candidates, key=lambda x: (x[0], x[1].name))
    test = pd.read_csv(directory / "metrics.csv")
    test = test[(test.model == model) & (test.split == "test") &
                (test.protocol == "calibrated") & (test.iou_cutoff == .3)]
    rows.append({"model": model, "selected_config": directory.name,
                 "validation_f1_mean": value, "validation_f1_sd": np.std(validation, ddof=1),
                 "test_f1_mean": test.f1.mean(), "test_f1_sd": test.f1.std(ddof=1),
                 "test_precision_mean": test.precision.mean(), "test_recall_mean": test.recall.mean(),
                 "test_delay_mean_steps": test.mean_delay_steps.mean(), "seeds": len(test)})
baseline = pd.read_csv(root / "outputs/detection_benchmark_v9_100/metrics.csv")
baseline = baseline[(baseline.model == "mean_rule") & (baseline.split == "test") &
                    (baseline.protocol == "calibrated") & (baseline.iou_cutoff == .3)].iloc[0]
rows.append({"model": "mean_rule", "selected_config": "analytic",
             "validation_f1_mean": np.nan, "validation_f1_sd": np.nan,
             "test_f1_mean": baseline.f1, "test_f1_sd": np.nan,
             "test_precision_mean": baseline.precision, "test_recall_mean": baseline.recall,
             "test_delay_mean_steps": baseline.mean_delay_steps, "seeds": 1})
out = root / "outputs/detection_hpo_v16/selected_summary.csv"
pd.DataFrame(rows).to_csv(out, index=False)
print(pd.DataFrame(rows).to_string(index=False))
