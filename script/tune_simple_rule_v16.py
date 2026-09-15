from pathlib import Path
import json
import sys
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "script"))
import benchmark_detection_v9 as b

OUT = ROOT / "outputs/detection_hpo_v16"
data = np.load(OUT / "h08_z08/dataset.npz")
rows = []
configs = {}
for window in [2, 4, 8, 16]:
    def score(x):
        frame = pd.DataFrame(x.T)
        return (frame.rolling(window, min_periods=window).mean()
                - frame.shift(window).rolling(window, min_periods=window).mean()).abs().fillna(0).to_numpy().T
    validation = score(data["validation"])
    config = b.calibrate(validation, data["validation_mask"])
    val_metrics = b.evaluate(validation, data["validation_mask"], config, .3)
    rows.append({"window": window, "validation_f1": val_metrics["f1"],
                 "validation_precision": val_metrics["precision"]})
    configs[window] = config
choice = max(rows, key=lambda row: (row["validation_f1"], row["validation_precision"], -row["window"]))
window = choice["window"]
frame = pd.DataFrame(data["test"].T)
test_score = (frame.rolling(window, min_periods=window).mean()
              - frame.shift(window).rolling(window, min_periods=window).mean()).abs().fillna(0).to_numpy().T
result = b.evaluate(test_score, data["test_mask"], configs[window], .3)
result.update(selected_window=window, validation_f1=choice["validation_f1"], config=configs[window])
pd.DataFrame(rows).to_csv(OUT / "simple_rule_candidates.csv", index=False)
(OUT / "simple_rule_selected.json").write_text(json.dumps(result, indent=2))
print(json.dumps(result, indent=2))
