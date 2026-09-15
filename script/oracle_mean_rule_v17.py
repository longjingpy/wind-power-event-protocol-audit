"""Test-label oracle ceilings for a declared adjacent-mean rule search.

Oracle choices deliberately use the evaluated labels and are not deployable
policies. Ordinary validation-selected settings and every candidate remain
separate. This bounds the tested rule family, not every simple detector.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from benchmark_detection_v9 import calibrate, evaluate
from confirm_detection_v16 import rule_scores

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "outputs/detection_confirmation_v16"
OUT = ROOT / "outputs/oracle_mean_rule_v17"
WINDOWS = [1, 2, 3, 4, 5, 6, 8, 10, 12, 16, 24, 32]
ORIGINAL = [2, 4, 8, 16]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    original = np.load(ROOT / "outputs/detection_hpo_v16/h08_z08/dataset.npz")
    validation_configs = {}
    validation_metrics = {}
    for window in WINDOWS:
        scores = rule_scores(original["validation"], window)
        config = calibrate(scores, original["validation_mask"])
        validation_configs[window] = config
        validation_metrics[window] = evaluate(scores, original["validation_mask"], config, .3)
    rows = []
    selected = []
    for condition in ["same_family", "higher_noise"]:
        data = np.load(SRC / f"dataset_{condition}.npz")
        for window in WINDOWS:
            scores = rule_scores(data["x"], window)
            frozen = evaluate(scores, data["truth"], validation_configs[window], .3)
            oracle_config = calibrate(scores, data["truth"])
            oracle = evaluate(scores, data["truth"], oracle_config, .3)
            # Test-quantile thresholds and source-quantile thresholds differ.
            # Include the frozen choice so the oracle set contains the baseline.
            if (frozen["f1"], frozen["precision"]) > (oracle["f1"], oracle["precision"]):
                oracle_config, oracle = validation_configs[window], frozen
            assert oracle["f1"] >= frozen["f1"]
            rows.append({"condition": condition, "window": window,
                         "original_candidate": window in ORIGINAL,
                         "validation_f1": validation_metrics[window]["f1"],
                         "frozen_test_f1": frozen["f1"], "frozen_precision": frozen["precision"], "frozen_recall": frozen["recall"],
                         "oracle_test_f1": oracle["f1"], "oracle_precision": oracle["precision"], "oracle_recall": oracle["recall"],
                         "frozen_config": json.dumps(validation_configs[window]), "oracle_config": json.dumps(oracle_config)})
        current = [row for row in rows if row["condition"] == condition]
        for grid, eligible in [("original_four_windows", [r for r in current if r["original_candidate"]]), ("expanded_twelve_windows", current)]:
            for mode, column in [("oracle_window_only", "frozen_test_f1"), ("oracle_window_and_protocol", "oracle_test_f1")]:
                best = max(eligible, key=lambda r: (r[column], -r["window"]))
                selected.append({"condition": condition, "grid": grid, "mode": mode,
                                 "window": best["window"], "f1": best[column],
                                 "label_access": "TEST_LABEL_ORACLE_NOT_DEPLOYABLE"})
        print(condition, selected[-4:], flush=True)
        pd.DataFrame(rows).to_csv(OUT / "all_rule_candidates.csv", index=False)
    pd.DataFrame(selected).to_csv(OUT / "oracle_summary.csv", index=False)
    (OUT / "protocol.json").write_text(json.dumps({
        "primary_windows": ORIGINAL, "expanded_windows": WINDOWS,
        "evaluated_sequences_per_condition": 1600, "scope": "same fixed post-selection synthetic samples as v16",
        "window_only": "choose test-best window with each window's original-validation output calibration",
        "window_and_protocol": "choose both window and complete output calibration on the test labels",
        "comparison": "oracle ceilings are separate from frozen trained-model performance"}, indent=2))


if __name__ == "__main__":
    main()
