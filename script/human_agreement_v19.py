"""Calendar-block uncertainty for all received human window assessments."""

import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/protocol_benchmark_v19/human_reference"


def nominal_alpha(a, b, weights):
    """Krippendorff (2004), Content Analysis, ch. 11: nominal disagreement.

    For two complete ratings per unit, weight whole windows rather than
    individual votes. This preserves rater pairing during block resampling.
    """
    weights = np.asarray(weights, float)
    n = weights.sum()
    if n == 0:
        return np.nan
    categories = np.unique(np.concatenate([a, b]))
    counts = np.array([weights[(a == c)].sum() + weights[(b == c)].sum()
                       for c in categories])
    expected = 1 - (counts * (counts - 1)).sum() / (2*n*(2*n-1))
    observed = (weights * (a != b)).sum() / n
    return 1 - observed / expected if expected > 0 else np.nan


def multirater_scores(values, weights):
    """Nominal coincidence alpha; missing votes are excluded, not imputed.

    Krippendorff (2004), Content Analysis, reliability chapter: within-unit
    coincidences are divided by the available rating count minus one.
    Resampling duplicates whole windows with all observed raters together.
    """
    values = np.asarray(values, dtype=object)
    weights = np.asarray(weights, float)
    categories = sorted({v for row in values for v in row if pd.notna(v)})
    counts = np.stack([(values == c).sum(axis=1) for c in categories], axis=1)
    sizes = counts.sum(axis=1)
    keep = sizes >= 2
    counts, sizes, weights = counts[keep], sizes[keep], weights[keep]
    n = float(weights @ sizes)
    if n < 2:
        return np.nan, np.nan
    observed = float(weights @ ((sizes**2 - (counts**2).sum(axis=1)) / (sizes-1))) / n
    margins = weights @ counts
    expected = (n*n - (margins**2).sum()) / (n*(n-1))
    return 1-observed/expected if expected > 0 else np.nan, 1-observed


def main():
    ratings = pd.read_csv(OUT / "ratings_long.csv")
    raters = sorted(ratings.annotator_id.unique())
    if len(raters) < 2:
        raise ValueError("Agreement requires at least two received raters")
    meta = ratings.drop_duplicates("window_id").set_index("window_id")
    records = []
    disagreements = []
    for field in ("event_presence", "morphology"):
        admissible = ratings[ratings.event_presence.isin(["yes", "no"])]
        paired = admissible.pivot(index="window_id", columns="annotator_id", values=field)
        paired = paired[paired.notna().sum(axis=1) >= 2]
        values = paired.to_numpy(object)
        aligned = meta.loc[paired.index]
        time = pd.to_datetime(aligned.target_start, utc=True).astype("int64")
        for ix in np.flatnonzero(paired.nunique(axis=1).to_numpy() > 1):
            disagreements.append({"field": field, "window_id": paired.index[ix],
                                  **{r: paired.iloc[ix].get(r) for r in raters},
                                  "site": aligned.site.iloc[ix]})
        for days in (3, 7, 14):
            labels = pd.DataFrame({"site": aligned.site.to_numpy(),
                                   "block": time.to_numpy() // pd.Timedelta(days=days).value})
            blocks = labels.drop_duplicates().sort_values(["site", "block"]).reset_index(drop=True)
            lookup = {(r.site, r.block): i for i, r in blocks.iterrows()}
            indices = np.array([lookup[p] for p in zip(labels.site, labels.block)])
            rng = np.random.default_rng(41)
            weights = np.zeros((2000, len(blocks)), int)
            for _, group in blocks.groupby("site"):
                idx = group.index.to_numpy()
                weights[:, idx] = rng.multinomial(len(idx), np.full(len(idx), 1/len(idx)), size=2000)
            samples = weights[:, indices]
            scores = np.array([multirater_scores(values, w) for w in samples])
            alpha, agreement = scores[:, 0], scores[:, 1]
            alpha_point, agreement_point = multirater_scores(values, np.ones(len(paired)))
            records.append({
                "field": field, "block_days": days, "windows": len(paired),
                "observers": len(raters),
                "farm_blocks": len(blocks), "repetitions": 2000,
                "observed_agreement": float(agreement_point),
                "agreement_low": float(np.quantile(agreement, .025)),
                "agreement_high": float(np.quantile(agreement, .975)),
                "alpha": float(alpha_point),
                "alpha_low": float(np.nanquantile(alpha, .025)),
                "alpha_high": float(np.nanquantile(alpha, .975)),
                "scope": "selected-window coincidence agreement; all received observers fixed",
            })
    pd.DataFrame(records).to_csv(OUT / "agreement_intervals.csv", index=False)
    pd.DataFrame(disagreements).to_csv(OUT / "disagreement_windows.csv", index=False)
    cohort_record = {
        "received_cohorts_and_observers": len(raters) + 1,
        "current_packet": {"packet_id": "wind-v19-20260918", "raters": raters,
                           "unique_windows": len(meta), "ratings": len(ratings)},
        "legacy_reference": {
            "regions": 120, "focus_revisions": 52,
            "source": "outputs/annotation_v9/submissions/",
            "role": "separate earlier regional reference; excluded from v19 inter-rater agreement",
        },
        "ongoing_additional_reviews": max(0, 4-len(raters)),
        "ongoing_status": "remaining from two reviews reported ongoing before third v19 return",
    }
    (OUT / "cohort_register.json").write_text(
        json.dumps(cohort_record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    expected = json.loads((OUT / "agreement.json").read_text())
    for r in records:
        assert abs(r["alpha"]-expected["alpha"][r["field"]]["alpha"]) < 1e-12
    print(pd.DataFrame(records).to_string(index=False))


if __name__ == "__main__":
    main()
