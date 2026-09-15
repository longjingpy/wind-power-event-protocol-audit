"""Freeze validation choices, then evaluate untouched synthetic draws.

This tests the score-to-interval protocol on the same generator family, not
field SCADA accuracy. Bootstrap draws resample complete synthetic sequences;
the same draws are shared by every fixed trained model and the simple rule.
"""
from pathlib import Path
from datetime import datetime, timezone
import json
import argparse
import re
import time
import numpy as np
import pandas as pd
import torch

import benchmark_detection_v9 as b

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "outputs/detection_hpo_v16"
OUT = ROOT / "outputs/detection_confirmation_v16"
SELECTION_FILE = SRC / "selected_summary.csv"
RULE_FILE = SRC / "simple_rule_selected.json"


def rule_scores(x, window):
    prefix = np.pad(np.cumsum(x, axis=1, dtype=np.float64), ((0, 0), (1, 0)))
    average = (prefix[:, window:] - prefix[:, :-window]) / window
    score = np.zeros(x.shape, dtype=np.float64)
    score[:, 2 * window - 1:] = np.abs(average[:, window:] - average[:, :-window])
    return score


def f1(counts):
    tp, fp, fn = np.moveaxis(counts, -1, 0)
    denominator = 2 * tp + fp + fn
    return np.divide(2 * tp, denominator, out=np.zeros_like(denominator, dtype=float), where=denominator > 0)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    torch.set_num_threads(2)
    selection = pd.read_csv(SELECTION_FILE)
    rule = json.loads(RULE_FILE.read_text())
    choices = {}
    for row in selection[selection.model != "mean_rule"].itertuples():
        directory = SRC / row.selected_config
        calibration = json.loads((directory / "calibration.json").read_text())
        size, latent = map(int, re.search(r"h(\d+)_z(\d+)", row.selected_config).groups())
        choices[row.model] = {"directory": row.selected_config, "size": size, "latent": latent,
                              "calibration": {str(seed): calibration[f"{row.model}-{seed}"]["calibrated"]
                                              for seed in [41, 42, 43]}}
    protocol = {"created_utc": datetime.now(timezone.utc).isoformat(), "selection": choices,
                "simple_rule": rule, "new_generator_seeds": [2026091501, 2026091502],
                "sequences_per_condition": 1600, "training_seeds": [41, 42, 43],
                "iou_cutoff": .3, "scope": "post-selection synthetic confirmation; same generator family",
                "bootstrap": "2000 paired sequence resamples, conditional on frozen trained models"}
    freeze = OUT / "frozen_selection.json"
    if freeze.exists():
        old = json.loads(freeze.read_text())
        assert old["selection"] == choices and old["simple_rule"] == rule, "Frozen selection changed"
    else:
        freeze.write_text(json.dumps(protocol, indent=2))
    # Fresh samples are generated only after the choices have been saved.
    datasets = {}
    for condition, seed, shifted in [("same_family", 2026091501, False), ("higher_noise", 2026091502, True)]:
        x, truth, meta = b.generate(1600, seed, shifted=shifted)
        datasets[condition] = (x, truth)
        np.savez_compressed(OUT / f"dataset_{condition}.npz", x=x, truth=truth)
        meta.to_csv(OUT / f"meta_{condition}.csv", index=False)
    details = {}
    metrics = []
    timing = []
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    for condition, (x, truth) in datasets.items():
        score = rule_scores(x, rule["selected_window"])
        metric, rows = b.evaluate(score, truth, rule["config"], .3, detailed=True)
        metrics.append(dict(condition=condition, model="mean_rule", seed=0, **metric))
        details[condition, "mean_rule", 0] = pd.DataFrame(rows)[["tp", "fp", "fn"]].to_numpy()
    for name, spec in choices.items():
        for seed in [41, 42, 43]:
            model = (b.UpstreamAE(name, spec["size"]) if name in ["timesnet", "kanad"]
                     else b.SequenceAE(name, spec["size"], spec["latent"]))
            checkpoint = torch.load(SRC / spec["directory"] / f"model_{name}_{seed}.pt", map_location="cpu", weights_only=True)
            model.load_state_dict(checkpoint["state_dict"], strict=True)
            model.to(device)
            for condition, (x, truth) in datasets.items():
                score = b.infer(model, x, checkpoint["mean"], checkpoint["std"], device)
                metric, rows = b.evaluate(score, truth, spec["calibration"][str(seed)], .3, detailed=True)
                metrics.append(dict(condition=condition, model=name, seed=seed, **metric))
                details[condition, name, seed] = pd.DataFrame(rows)[["tp", "fp", "fn"]].to_numpy()
            if seed == 41:
                cpu = torch.device("cpu")
                model.to(cpu)
                sample = datasets["same_family"][0][:800]
                b.infer(model, sample, checkpoint["mean"], checkpoint["std"], cpu)
                measured = []
                for _ in range(5):
                    start = time.perf_counter()
                    b.infer(model, sample, checkpoint["mean"], checkpoint["std"], cpu)
                    measured.append((time.perf_counter() - start) * 1000 / len(sample))
                timing.append({"model": name, "parameters": sum(p.numel() for p in model.parameters()),
                               "cpu_ms_per_sequence_median": float(np.median(measured)),
                               "cpu_ms_per_sequence_min": min(measured), "cpu_ms_per_sequence_max": max(measured),
                               "batch_size": 64, "timed_sequences": 800, "repeats": 5, "cpu_threads": 2})
            print(name, seed, "evaluated", flush=True)
    sample = datasets["same_family"][0][:800]
    measured = []
    rule_scores(sample, rule["selected_window"])
    for _ in range(5):
        start = time.perf_counter()
        rule_scores(sample, rule["selected_window"])
        measured.append((time.perf_counter() - start) * 1000 / len(sample))
    timing.append({"model": "mean_rule", "parameters": 0,
                   "cpu_ms_per_sequence_median": float(np.median(measured)),
                   "cpu_ms_per_sequence_min": min(measured), "cpu_ms_per_sequence_max": max(measured),
                   "batch_size": 800, "timed_sequences": 800, "repeats": 5, "cpu_threads": 2})
    (OUT / "timing_environment.json").write_text(json.dumps({
        "cpu": "AMD Ryzen 7 9700X 8-Core Processor", "os": "Ubuntu 24.04 under WSL2",
        "torch": torch.__version__, "cpu_threads": 2, "warmup_runs": 1, "timed_runs": 5,
        "scope": "CPU reconstruction/score generation including array normalization; postprocessing excluded",
        "simple_implementation": "NumPy cumulative-sum adjacent-window means"}, indent=2))
    frame = pd.DataFrame(metrics)
    frame.to_csv(OUT / "metrics.csv", index=False)
    frame.groupby(["condition", "model"])[["f1", "precision", "recall", "mean_delay_steps"]].agg(["mean", "std"]).to_csv(OUT / "summary.csv")
    pd.DataFrame(timing).to_csv(OUT / "compute.csv", index=False)
    rng = np.random.default_rng(2026091503)
    gains = []
    for condition in datasets:
        draws = rng.integers(0, 1600, size=(2000, 1600))
        base = f1(details[condition, "mean_rule", 0][draws].sum(axis=1))
        for name in choices:
            values = np.mean([f1(details[condition, name, seed][draws].sum(axis=1)) for seed in [41, 42, 43]], axis=0) - base
            point = frame[(frame.condition == condition) & (frame.model == name)].f1.mean() - frame[(frame.condition == condition) & (frame.model == "mean_rule")].f1.iloc[0]
            gains.append({"condition": condition, "model": name, "mean_f1_gain_vs_mean_rule": point,
                          "ci95_low": np.quantile(values, .025), "ci95_high": np.quantile(values, .975),
                          "resamples": 2000, "unit": "independent synthetic sequence; frozen models"})
    pd.DataFrame(gains).to_csv(OUT / "paired_gain_intervals.csv", index=False)
    print(pd.DataFrame(gains).to_string(index=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-root", type=Path, default=SRC)
    parser.add_argument("--selection-file", type=Path, default=SELECTION_FILE)
    parser.add_argument("--simple-rule-file", type=Path, default=RULE_FILE)
    parser.add_argument("--output-dir", type=Path, default=OUT)
    arguments = parser.parse_args()
    SRC, SELECTION_FILE, RULE_FILE, OUT = arguments.model_root, arguments.selection_file, arguments.simple_rule_file, arguments.output_dir
    main()
