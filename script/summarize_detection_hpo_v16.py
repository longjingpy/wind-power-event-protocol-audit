from pathlib import Path
import json
import sys
import numpy as np
import pandas as pd

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "script"))
import benchmark_detection_v9 as bench

rows = []
candidate_validation = []
candidate_test = []
for model in ["timesnet", "kanad", "tcn_ae", "transformer_ae"]:
    candidates = []
    for directory in sorted((root / "outputs/detection_hpo_v16").glob("*")):
        if not directory.is_dir() or not (directory / f"scores_{model}_43.npz").is_file():
            continue
        config = json.loads((directory / "calibration.json").read_text())
        data = np.load(directory / "dataset.npz")
        validation = []
        for seed in [41, 42, 43]:
            score = np.load(directory / f"scores_{model}_{seed}.npz")["validation"]
            cfg = config[f"{model}-{seed}"]["calibrated"]
            validation.append(bench.evaluate(score, data["validation_mask"], cfg, .3)["f1"])
        candidates.append((float(np.mean(validation)), directory, validation))
        candidate_validation.append({"config": directory.name, "model": model,
                                     "validation_f1_mean": np.mean(validation), "validation_f1_sd": np.std(validation, ddof=1),
                                     "seed_41_f1": validation[0], "seed_42_f1": validation[1], "seed_43_f1": validation[2]})
        candidate = pd.read_csv(directory / "metrics.csv")
        candidate = candidate[(candidate.model == model) & (candidate.split == "test") &
                              (candidate.protocol == "calibrated") & (candidate.iou_cutoff == .3)]
        candidate_test.append({"config": directory.name, "model": model, "f1": candidate.f1.mean(),
                               "f1_sd": candidate.f1.std(), "precision": candidate.precision.mean(), "recall": candidate.recall.mean()})
    value, directory, validation = max(candidates, key=lambda x: (x[0], x[1].name))
    test = pd.read_csv(directory / "metrics.csv")
    test = test[(test.model == model) & (test.split == "test") &
                (test.protocol == "calibrated") & (test.iou_cutoff == .3)]
    rows.append({"model": model, "selected_config": directory.name,
                 "validation_f1_mean": value, "validation_f1_sd": np.std(validation, ddof=1),
                 "test_f1_mean": test.f1.mean(), "test_f1_sd": test.f1.std(ddof=1),
                 "test_precision_mean": test.precision.mean(), "test_recall_mean": test.recall.mean(),
                 "test_delay_mean_steps": test.mean_delay_steps.mean(), "seeds": len(test)})
rule = json.loads((root / "outputs/detection_hpo_v16/simple_rule_selected.json").read_text())
rows.append({"model": "mean_rule", "selected_config": f"mean_w{rule['selected_window']}",
             "validation_f1_mean": rule["validation_f1"], "validation_f1_sd": np.nan,
             "test_f1_mean": rule["f1"], "test_f1_sd": np.nan,
             "test_precision_mean": rule["precision"], "test_recall_mean": rule["recall"],
             "test_delay_mean_steps": rule["mean_delay_steps"], "seeds": 1})
out = root / "outputs/detection_hpo_v16/selected_summary.csv"
pd.DataFrame(rows).to_csv(out, index=False)
pd.DataFrame(candidate_validation).to_csv(out.parent / "validation_summary.csv", index=False)
pd.DataFrame(candidate_test).to_csv(out.parent / "summary.csv", index=False)
print(pd.DataFrame(rows).to_string(index=False))
