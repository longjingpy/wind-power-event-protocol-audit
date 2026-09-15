"""Compare source-frozen and noise-calibrated rules on new synthetic draws.

Both simple and learned scores receive the same target-validation labels.
Architectures and weights remain frozen. The test draw is generated only
after the target-validation settings have been saved.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import torch

import benchmark_detection_v9 as b
from confirm_detection_v16 import rule_scores, f1
from oracle_mean_rule_v17 import WINDOWS

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "outputs/detection_hpo_v16"
OUT = ROOT / "outputs/noise_calibration_v17"


def restore(name, seed, spec, device):
    model = b.UpstreamAE(name, spec["size"]) if name in ["timesnet", "kanad"] else b.SequenceAE(name, spec["size"], spec["latent"])
    checkpoint = torch.load(SRC / spec["directory"] / f"model_{name}_{seed}.pt", map_location="cpu", weights_only=True)
    model.load_state_dict(checkpoint["state_dict"], strict=True)
    return model.to(device), checkpoint


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    torch.set_num_threads(2)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    prior = json.loads((ROOT / "outputs/detection_confirmation_v16/frozen_selection.json").read_text())
    plan = {"validation_seed": 2026091703, "test_seed": 2026091704, "validation_n": 400, "test_n": 1600,
            "noise_innovation_sd": .027, "windows": WINDOWS, "frozen_models": prior["selection"],
            "training": "no new model fitting; target calibration changes output settings only"}
    plan_file = OUT / "plan.json"
    if plan_file.exists():
        assert json.loads(plan_file.read_text()) == plan
    else:
        plan_file.write_text(json.dumps(plan, indent=2))
    validation, truth, _ = b.generate(plan["validation_n"], plan["validation_seed"], shifted=True)
    rule_candidates = []
    rule_configs = {}
    for window in WINDOWS:
        score = rule_scores(validation, window)
        config = b.calibrate(score, truth)
        metrics = b.evaluate(score, truth, config, .3)
        rule_candidates.append({"window": window, "validation_f1": metrics["f1"], "validation_precision": metrics["precision"]})
        rule_configs[window] = config
    best_rule = max(rule_candidates, key=lambda row: (row["validation_f1"], row["validation_precision"], -row["window"]))
    target_configs = {}
    for name, spec in prior["selection"].items():
        target_configs[name] = {}
        for seed in [41, 42, 43]:
            model, checkpoint = restore(name, seed, spec, device)
            score = b.infer(model, validation, checkpoint["mean"], checkpoint["std"], device)
            target_configs[name][str(seed)] = b.calibrate(score, truth)
        print(name, "target calibration complete", flush=True)
    (OUT / "target_validation_selection.json").write_text(json.dumps({
        "mean_rule_window": best_rule["window"], "mean_rule_config": rule_configs[best_rule["window"]],
        "model_configs": target_configs, "test_labels_used": False}, indent=2))
    # This draw is created after every target-validation choice has been saved.
    test, ytest, metadata = b.generate(plan["test_n"], plan["test_seed"], shifted=True)
    np.savez_compressed(OUT / "dataset.npz", validation=validation, validation_mask=truth, test=test, test_mask=ytest)
    metadata.to_csv(OUT / "test_meta.csv", index=False)
    rows = []
    details = {}
    for policy, window, config in [
        ("source_frozen", prior["simple_rule"]["selected_window"], prior["simple_rule"]["config"]),
        ("target_validation", best_rule["window"], rule_configs[best_rule["window"]])]:
        score = rule_scores(test, window)
        metrics, detail = b.evaluate(score, ytest, config, .3, detailed=True)
        rows.append(dict(model="mean_rule", seed=0, policy=policy, **metrics))
        details["mean_rule", 0, policy] = pd.DataFrame(detail)[["tp", "fp", "fn"]].to_numpy()
    for candidate in rule_candidates:
        window = candidate["window"]
        candidate["test_f1"] = b.evaluate(rule_scores(test, window), ytest, rule_configs[window], .3)["f1"]
        candidate["selected_by_validation"] = window == best_rule["window"]
    for name, spec in prior["selection"].items():
        for seed in [41, 42, 43]:
            model, checkpoint = restore(name, seed, spec, device)
            score = b.infer(model, test, checkpoint["mean"], checkpoint["std"], device)
            for policy, config in [("source_frozen", spec["calibration"][str(seed)]), ("target_validation", target_configs[name][str(seed)])]:
                metrics, detail = b.evaluate(score, ytest, config, .3, detailed=True)
                rows.append(dict(model=name, seed=seed, policy=policy, **metrics))
                details[name, seed, policy] = pd.DataFrame(detail)[["tp", "fp", "fn"]].to_numpy()
    table = pd.DataFrame(rows)
    table.to_csv(OUT / "metrics.csv", index=False)
    pd.DataFrame(rule_candidates).to_csv(OUT / "all_rule_candidates.csv", index=False)
    summaries = []
    for (model, policy), group in table.groupby(["model", "policy"]):
        summaries.append(dict(model=model, policy=policy, f1=group.f1.mean(), f1_sd=group.f1.std(),
                              precision=group.precision.mean(), recall=group.recall.mean(), seeds=len(group)))
    pd.DataFrame(summaries).to_csv(OUT / "summary.csv", index=False)
    draws = np.random.default_rng(2026091705).integers(0, len(test), size=(2000, len(test)))
    bootstrap = {}
    for model in ["mean_rule", *prior["selection"]]:
        seeds = [0] if model == "mean_rule" else [41, 42, 43]
        for policy in ["source_frozen", "target_validation"]:
            bootstrap[model, policy] = np.mean([f1(details[model, seed, policy][draws].sum(axis=1)) for seed in seeds], axis=0)
    gains = []
    for model in prior["selection"]:
        for policy in ["source_frozen", "target_validation"]:
            difference = bootstrap[model, policy] - bootstrap["mean_rule", policy]
            point = table[(table.model == model) & (table.policy == policy)].f1.mean() - table[(table.model == "mean_rule") & (table.policy == policy)].f1.iloc[0]
            gains.append({"model": model, "policy": policy, "f1_gain_vs_mean_rule": point,
                          "ci95_low": np.quantile(difference, .025), "ci95_high": np.quantile(difference, .975)})
    pd.DataFrame(gains).to_csv(OUT / "paired_intervals.csv", index=False)
    print("selected mean window", best_rule["window"])
    print(pd.DataFrame(summaries).to_string(index=False))
    print(pd.DataFrame(gains).to_string(index=False))


if __name__ == "__main__":
    main()
