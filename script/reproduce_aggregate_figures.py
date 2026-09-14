"""Reproduce two numerical comparisons using only files in this release."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FARMS = ["hill", "lahaute", "pizhou", "suining", "yandun"]


def main():
    out = ROOT / "reproduced"
    out.mkdir(exist_ok=True)
    primary = pd.read_csv(ROOT / "results/representation_summary_primary.csv")
    primary = primary[primary.group.isin(FARMS) & primary.k.eq(4)]
    learned = pd.read_csv(ROOT / "results/cv_benchmark_metrics_100.csv")
    learned = learned[learned.group.isin(["pairs:" + site for site in FARMS]) & learned.k.eq(4)]
    assert len(learned) == 60 and learned.nmi.notna().all()
    for name, frame in [("fixed_representations", primary), ("learned_100_epoch", learned)]:
        values = frame.groupby("representation")[["nmi", "ari"]].mean()
        values.to_csv(out / f"{name}.csv")
        ax = values.plot.bar(figsize=(9, 5), color=["#216E8C", "#D99348"])
        ax.set_ylabel("Five-farm mean agreement")
        ax.set_ylim(0, 1)
        ax.figure.tight_layout()
        ax.figure.savefig(out / f"{name}.pdf")
        plt.close(ax.figure)
    print("PASS: release-local aggregate figures and tables reproduced")


if __name__ == "__main__":
    main()
