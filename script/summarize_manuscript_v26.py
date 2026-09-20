"""Deterministic manuscript summaries from completed v18-v26 outputs.

This script does not fit models, choose hyperparameters, or alter experiment
outputs. It only derives tables and editable/vector figures for manuscript use.
"""
from pathlib import Path
import json
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

ROOT = Path(__file__).resolve().parents[1]
V26 = ROOT / "outputs/protocol_benchmark_v26"
V19 = ROOT / "outputs/protocol_benchmark_v19/human_reference"
V18 = ROOT / "outputs/protocol_benchmark_v18"
FIG = ROOT / "manuscript/figures_v26"
FIG.mkdir(parents=True, exist_ok=True)

COLORS = {"baseline": "#536474", "pipeline": "#0B7A75",
          "composite": "#A33378", "primitive": "#9AA6B2", "geometry": "#28719D"}


def block_summary():
    rows = []
    matrix = []
    examples = []
    config = {
        "lidar_T11": ("T11", "residual_scalar27"),
        "lidar_T07": ("T07", "residual_scalar27"),
        "smarteole": ("SMARTEOLE", "scalar19"),
    }
    for source, (label, baseline_key) in config.items():
        folder = V26 / (source + "_native10")
        events = pd.read_parquet(folder / "test_events.parquet").reset_index(drop=True)
        pred = np.load(folder / "physical_calibration" / "test_predictions.npz")
        actual = pred["actual"]
        baseline = pred[baseline_key]
        pipeline = pred["level_delta17"]
        times = pd.to_datetime(events.time_start, utc=True)
        block = (times.astype("int64") // pd.Timedelta(days=7).value).to_numpy()
        block_labels = {value: index + 1 for index, value in enumerate(sorted(np.unique(block)))}
        unique_blocks = sorted(np.unique(block))
        for value in unique_blocks:
            mask = block == value
            compound = events.has_composite.to_numpy(bool)[mask]
            b = np.mean((baseline[mask] - actual[mask]) ** 2, axis=1)
            p = np.mean((pipeline[mask] - actual[mask]) ** 2, axis=1)
            gain = 100 * (1 - math.sqrt(p.mean() / b.mean()))
            rows.append({
                "source": source, "reference": label,
                "block_index": block_labels[value], "block_start": pd.Timestamp(value * pd.Timedelta(days=7).value, unit="ns", tz="UTC").isoformat(),
                "events": int(mask.sum()), "compound_events": int(compound.sum()),
                "primitive_events": int((~compound).sum()), "compound_fraction": float(compound.mean()),
                "baseline_rmse_ms": float(math.sqrt(b.mean())), "pipeline_rmse_ms": float(math.sqrt(p.mean())),
                "full_gain_pct": float(gain),
            })
        for value in unique_blocks:
            mask = block != value
            b = np.mean((baseline[mask] - actual[mask]) ** 2, axis=1)
            p = np.mean((pipeline[mask] - actual[mask]) ** 2, axis=1)
            rows.append({
                "source": source, "reference": label,
                "block_index": f"leave_out_{block_labels[value]}",
                "block_start": pd.Timestamp(value * pd.Timedelta(days=7).value, unit="ns", tz="UTC").isoformat(),
                "events": int(mask.sum()), "compound_events": int(events.has_composite.to_numpy(bool)[mask].sum()),
                "primitive_events": int((~events.has_composite.to_numpy(bool)[mask]).sum()),
                "compound_fraction": float(events.has_composite.to_numpy(bool)[mask].mean()),
                "baseline_rmse_ms": float(math.sqrt(b.mean())), "pipeline_rmse_ms": float(math.sqrt(p.mean())),
                "full_gain_pct": float(100 * (1 - math.sqrt(p.mean() / b.mean()))),
            })
        for subset, subset_mask in [
            ("all", np.ones(len(events), dtype=bool)),
            ("compound", events.has_composite.to_numpy(bool)),
            ("primitive_only", ~events.has_composite.to_numpy(bool)),
        ]:
            b = np.mean((baseline[subset_mask] - actual[subset_mask]) ** 2, axis=1)
            p = np.mean((pipeline[subset_mask] - actual[subset_mask]) ** 2, axis=1)
            geometry_actual = np.c_[np.zeros(subset_mask.sum()), actual[subset_mask]]
            geometry_baseline = np.c_[np.zeros(subset_mask.sum()), baseline[subset_mask]]
            geometry_pipeline = np.c_[np.zeros(subset_mask.sum()), pipeline[subset_mask]]
            phase = np.linspace(0, 1, 17)[None, :]
            geometry_actual = geometry_actual - geometry_actual[:, -1, None] * phase
            geometry_baseline = geometry_baseline - geometry_baseline[:, -1, None] * phase
            geometry_pipeline = geometry_pipeline - geometry_pipeline[:, -1, None] * phase
            gb = np.mean((geometry_baseline[:, 1:] - geometry_actual[:, 1:]) ** 2, axis=1)
            gp = np.mean((geometry_pipeline[:, 1:] - geometry_actual[:, 1:]) ** 2, axis=1)
            matrix.append({
                "source": source, "reference": label, "subset": subset,
                "events": int(subset_mask.sum()),
                "baseline_full_rmse_ms": float(math.sqrt(b.mean())),
                "pipeline_full_rmse_ms": float(math.sqrt(p.mean())),
                "full_gain_pct": float(100 * (1 - math.sqrt(p.mean() / b.mean()))),
                "baseline_geometry_rmse_ms": float(math.sqrt(gb.mean())),
                "pipeline_geometry_rmse_ms": float(math.sqrt(gp.mean())),
                "geometry_gain_pct": float(100 * (1 - math.sqrt(gp.mean() / gb.mean()))),
            })
        # Outcome-blind illustrative event: nearest to median power duration/amplitude.
        candidates = events[events.has_composite].copy()
        if len(candidates):
            target_duration = candidates.duration_hours.median()
            target_amplitude = candidates.amplitude.abs().median()
            distance = (candidates.duration_hours - target_duration).abs() + (candidates.amplitude.abs() - target_amplitude).abs()
            chosen = candidates.index[int(distance.to_numpy().argmin())]
            index = list(events.index).index(chosen)
            for j in range(17):
                measured = np.r_[0.0, actual[index]]
                scalar = np.r_[0.0, baseline[index]]
                ordered = np.r_[0.0, pipeline[index]]
                examples.append({"source": source, "reference": label, "event_id": events.loc[chosen, "event_id"],
                                 "subset": "compound", "phase": j / 16,
                                 "measured_wind_change_ms": float(measured[j]),
                                 "scalar_reconstruction_ms": float(scalar[j]),
                                 "ordered_reconstruction_ms": float(ordered[j])})
    pd.DataFrame(rows).to_csv(V26 / "block_diagnostics.csv", index=False)
    pd.DataFrame(matrix).to_csv(V26 / "reconstruction_matrix.csv", index=False)
    pd.DataFrame(examples).to_csv(V26 / "reconstruction_examples.csv", index=False)
    return pd.DataFrame(rows), pd.DataFrame(matrix), pd.DataFrame(examples)


def conditional_summary():
    src = V18 / "conditional/conditional_information_protocol_conditioned.csv"
    data = pd.read_csv(src)
    # The implemented nuisance variable is pre_mean; keep one primary joint row.
    out = data[(data.condition == "joint") & (data.block_days == 7)].copy()
    out["control_definition"] = "direction + abs amplitude + duration + pre-window mean; pair-side means"
    out.to_csv(V26 / "conditional_information_summary.csv", index=False)
    return out


def threshold_summary():
    data = pd.read_csv(V18 / "threshold_sensitivity/scores.csv")
    rows = data.groupby(["site", "factor"], as_index=False).agg(
        configurations=("config", "nunique"),
        median_nmi=("nmi", "median"), median_ari=("ari", "median"),
        median_left_coverage=("left_coverage", "median"),
        median_right_coverage=("right_coverage", "median"),
        median_low=("low_support", "mean"),
    )
    rows.to_csv(V26 / "threshold_sensitivity_summary.csv", index=False)
    return rows


def process_figure(blocks, matrix, examples):
    fig, axes = plt.subplots(2, 3, figsize=(7.1, 5.6), gridspec_kw={"height_ratios": [1.25, 1]})
    references = {"lidar_T11": "T11", "lidar_T07": "T07", "smarteole": "SMARTEOLE"}
    for col, source in enumerate(references):
        d = examples[examples.source == source]
        ax = axes[0, col]
        ax.plot(d.phase, d.measured_wind_change_ms, color="#202D3A", lw=2.0, label="Measured wind")
        ax.plot(d.phase, d.scalar_reconstruction_ms, color=COLORS["baseline"], lw=1.5, ls="--", label="Scalar control")
        ax.plot(d.phase, d.ordered_reconstruction_ms, color=COLORS["pipeline"], lw=1.7, label="Ordered trajectory")
        ax.axhline(0, color="#C8D0D7", lw=.7)
        ax.set_title(references[source], fontsize=10, fontweight="bold")
        ax.set_xlabel("Relative event phase")
        if col == 0:
            ax.set_ylabel("Wind change (m s$^{-1}$)")
        ax.grid(axis="y", color="#E6EAEE", lw=.7)
        ax.spines[["top", "right"]].set_visible(False)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    axes[0, 0].legend(handles, labels, loc="lower left", fontsize=7, frameon=False)
    for col, source in enumerate(references):
        d = matrix[(matrix.source == source) & (matrix.subset.isin(["compound", "primitive_only"]))]
        ax = axes[1, col]
        x = np.arange(2)
        for i, subset in enumerate(["compound", "primitive_only"]):
            q = d[d.subset == subset].iloc[0]
            ax.bar(i - .16, q.baseline_full_rmse_ms, width=.3, color=COLORS["baseline"])
            ax.bar(i + .16, q.pipeline_full_rmse_ms, width=.3, color=COLORS["pipeline"])
        ax.set_xticks(x, ["Compound", "Primitive"])
        ax.set_title(f"Full-curve RMSE · {references[source]}", fontsize=8.7)
        ax.grid(axis="y", color="#E6EAEE", lw=.7)
        ax.spines[["top", "right"]].set_visible(False)
        if col == 0:
            ax.set_ylabel("RMSE (m s$^{-1}$)")
    axes[1, 2].cla()
    axes[1, 2].axis("off")
    axes[1, 2].text(.02, .85, "Power-defined hierarchy", fontsize=10, fontweight="bold")
    axes[1, 2].text(.02, .66, "Bars use the same events and\nnative 10-min inputs.\n\nCompound events are defined\nfrom power records before\nwind evaluation.", fontsize=9, va="top")
    fig.suptitle("Ordered trajectories recover intermediate wind-process structure", fontsize=12, fontweight="bold", y=.99)
    fig.tight_layout(rect=[0, 0, 1, .96])
    fig.savefig(FIG / "fig13_physical_process.pdf", bbox_inches="tight")
    fig.savefig(FIG / "fig13_physical_process.svg", bbox_inches="tight")
    fig.savefig(FIG / "fig13_physical_process.png", dpi=300, bbox_inches="tight")
    pd.DataFrame({"panel": ["a", "b"], "description": ["Representative measured and reconstructed trajectories", "Absolute RMSE by power-defined hierarchy"]}).to_csv(FIG / "fig13_physical_process.csv", index=False)


def polarity_figure():
    path = pd.read_csv(ROOT / "manuscript/figures_v22/fig07_polarity_paths.csv")
    gasf = pd.read_csv(ROOT / "manuscript/figures_v22/fig08_shared_gasf.csv", header=None).to_numpy(float)
    fig, axes = plt.subplots(1, 2, figsize=(6.8, 2.75), gridspec_kw={"width_ratios": [1.12, 1]})
    ax = axes[0]
    ax.plot(path.coordinate, path.x, color="#253744", lw=1.8, marker="o", ms=3, label="Observed path, x")
    ax.plot(path.coordinate, path.negative_x, color="#A33378", lw=1.6, ls="--", label="Sign reversal, −x")
    ax.axhline(0, color="#C8D0D7", lw=.8)
    ax.set(xlabel="Shape coordinate", ylabel="Signed value", title="a  Opposite trajectories")
    ax.set_ylim(-1.1, 1.1); ax.grid(axis="y", color="#E6EAEE", lw=.7)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(loc="lower left", frameon=False, fontsize=7)
    im = axes[1].imshow(gasf, cmap="RdBu_r", vmin=-1, vmax=1, aspect="equal")
    axes[1].set(xlabel="Shape coordinate", ylabel="Shape coordinate", title="b  Same GASF: G(x) = G(−x)")
    axes[1].set_xticks([0, 6, 12, 18, 24]); axes[1].set_yticks([0, 6, 12, 18, 24])
    fig.colorbar(im, ax=axes[1], fraction=.046, pad=.04, label="Angular field")
    fig.suptitle("A protected polarity coordinate preserves a distinction erased by GASF", fontsize=11, fontweight="bold", y=1.02)
    fig.tight_layout()
    fig.savefig(FIG / "fig07_polarity_mechanism.pdf", bbox_inches="tight")
    fig.savefig(FIG / "fig07_polarity_mechanism.svg", bbox_inches="tight")
    fig.savefig(FIG / "fig07_polarity_mechanism.png", dpi=300, bbox_inches="tight")
    pd.DataFrame({"coordinate": path.coordinate, "x": path.x, "negative_x": path.negative_x}).to_csv(FIG / "fig07_polarity_mechanism.csv", index=False)


def main():
    blocks, matrix, examples = block_summary()
    conditional_summary()
    threshold_summary()
    process_figure(blocks, matrix, examples)
    polarity_figure()
    print(json.dumps({"status": "COMPLETE_DETERMINISTIC_SUMMARY", "block_rows": len(blocks),
                      "matrix_rows": len(matrix), "example_rows": len(examples),
                      "figure": str(FIG / "fig13_physical_process.pdf")}, indent=2))


if __name__ == "__main__":
    main()
