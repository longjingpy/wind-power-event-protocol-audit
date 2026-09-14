"""Render the later experiment results from existing tables, without model fits."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "manuscript/applied_energy/figures"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9,
                     "axes.titlesize": 10, "axes.titleweight": "bold",
                     "pdf.fonttype": 42, "svg.fonttype": "none",
                     "axes.spines.top": False, "axes.spines.right": False})
COLORS = ["#24778A", "#DC8C36", "#5367A4"]


def save(fig, number):
    for extension in ["pdf", "svg", "png"]:
        fig.savefig(OUT / f"fig{number}.{extension}", dpi=180, bbox_inches="tight")
    plt.close(fig)


def draw_metrics(ax, data, keys, labels, point_unit, title):
    x = np.arange(len(keys))
    for j, metric in enumerate(["nmi", "ari"]):
        position = x + (j - 0.5) * 0.34
        values = [data.loc[data.representation == key, metric].mean() for key in keys]
        ax.bar(position, values, width=0.31, color=COLORS[j], label=metric.upper(), alpha=0.85)
        for p, key, value in zip(position, keys, values):
            units = data[data.representation == key].groupby(point_unit)[metric].mean()
            ax.scatter(p + np.linspace(-0.07, 0.07, len(units)), units,
                       s=12, facecolors="white", edgecolors="#263D4A", linewidths=0.6, zorder=4)
            ax.text(p, max(value, units.max()) + 0.035, f"{value:.3f}",
                    ha="center", va="bottom", fontsize=8)
    ax.set(xticks=x, xticklabels=labels, ylim=(0, 1.04), ylabel="Matched-label agreement")
    ax.set_title(title, loc="left", pad=27)
    ax.grid(axis="y", alpha=0.16)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, ncol=2, loc="lower left", bbox_to_anchor=(0, 1.005))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cv = pd.read_csv(ROOT / "outputs/cv_benchmark_v7/cv_benchmark_metrics.csv")
    groups = ["pairs:" + farm for farm in ["pizhou", "suining", "yandun", "lahaute", "hill"]]
    cv = cv[(cv.k == 4) & cv.group.isin(groups)].copy()
    assert len(cv) == 60 and cv.nmi.notna().all()
    cv.to_csv(OUT / "fig7a_data.csv", index=False)
    external = pd.read_csv(ROOT / "outputs/sdwpf_v7/learned_forward_metrics.csv")
    external = external[external.k == 4].copy()
    assert len(external) == 42 and external.batch.nunique() == 7
    external.to_csv(OUT / "fig7b_data.csv", index=False)
    fig, axes = plt.subplots(2, 1, figsize=(7.09, 7.0), layout="constrained")
    draw_metrics(axes[0], cv, ["cnn_gaf", "cnn_signed_gaf", "tcn", "transformer"],
                 ["CNN-GAF", "Signed-GAF", "TCN", "Transformer"], "group",
                 "a  Learned representations across five primary farms")
    draw_metrics(axes[1], external, ["tcn", "transformer"], ["TCN", "Transformer"], "batch",
                 "b  External transfer to the 134-turbine SDWPF archive")
    save(fig, 7)

    results = pd.read_csv(ROOT / "outputs/detection_benchmark_v9/protocol_ablation_metrics.csv")
    keys = ["timesnet", "kanad", "tcn_ae", "transformer_ae"]
    results = results[(results.split == "test") & results.model.isin(keys)].copy()
    assert len(results) == 36
    results.to_csv(OUT / "fig8_data.csv", index=False)
    fig, ax = plt.subplots(figsize=(7.09, 4.1), layout="constrained")
    for j, (policy, label) in enumerate(zip(["default", "threshold_only", "full_protocol"],
                                           ["Training q99", "Threshold calibration", "Threshold + grouping"])):
        pos = np.arange(len(keys)) + (j - 1) * 0.24
        part = results[results.policy == policy]
        vals = [part[part.model == key].f1.mean() for key in keys]
        ax.bar(pos, vals, width=0.22, color=COLORS[j], label=label, alpha=0.9)
        for p, key, value in zip(pos, keys, vals):
            seeds = part[part.model == key].sort_values("seed").f1
            ax.scatter(p + np.linspace(-0.04, 0.04, len(seeds)), seeds,
                       s=14, facecolors="white", edgecolors="#263D4A", linewidths=0.6, zorder=4)
            ax.text(p, max(value, seeds.max()) + 0.025, f"{value:.3f}", ha="center", fontsize=8)
    ax.set(xticks=np.arange(len(keys)), xticklabels=["TimesNet", "KAN-AD", "TCN-AE", "Transformer-AE"],
           ylim=(0, 0.86), ylabel="Episode F1 (IoU >= 0.3)")
    ax.grid(axis="y", alpha=0.16)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, ncol=1, loc="upper left", fontsize=8)
    save(fig, 8)
    print("Figures 7 and 8: archived values, vector outputs and numerical tables complete")


if __name__ == "__main__":
    main()
