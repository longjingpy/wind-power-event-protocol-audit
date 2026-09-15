"""Recompute conditional NMI/ARI within configuration pairs.

This is an exploratory audit of the v6 held-out labels. Quantile cut points
are fitted from ``train_primary.csv`` only. A pair is conditional-matched when
the two events have the same stratum for the requested covariate. Metrics are
computed separately for every site/configuration pair, so aggregation cannot
hide low-support or single-label strata.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get("WPF_CONDITIONAL_SOURCE", ROOT / "outputs/dynamic_events_v6"))
OUT = Path(os.environ.get("WPF_CONDITIONAL_OUT", ROOT / "outputs/conditional_agreement_v17"))
REPRESENTATIONS = [
    "raw25", "statistics9", "raw_pca6", "gaf_pca6", "gaf_signed_pca6",
    "event_row_permutation", "within_event_time_permutation",
]
NUMERIC_VARS = ["amplitude_abs", "duration_hours", "power_start"]
ALL_VARS = ["direction", *NUMERIC_VARS]
QUANTILES = [0.25, 0.50, 0.75]


def sha256(path: Path) -> str:
    return hashlib.file_digest(path.open("rb"), "sha256").hexdigest()


def make_bins(train_values: pd.Series) -> list[float]:
    values = pd.to_numeric(train_values, errors="coerce").dropna().to_numpy(float)
    if not len(values):
        raise ValueError("No finite training values available for threshold fitting")
    # Duplicated quantiles are removed; searchsorted still produces stable bins.
    return sorted(set(float(x) for x in np.quantile(values, QUANTILES)))


def labels_for(values: pd.Series, variable: str, bins: list[float] | None) -> pd.Series:
    if variable == "direction":
        return values.astype("Int64").astype(str)
    x = pd.to_numeric(values, errors="coerce").to_numpy(float)
    code = np.full(len(x), -1, dtype=int)
    finite = np.isfinite(x)
    code[finite] = np.searchsorted(np.asarray(bins), x[finite], side="right")
    return pd.Series(code, index=values.index, dtype="int64").astype(str)


def pair_metric(left: np.ndarray, right: np.ndarray) -> tuple[float, float, str]:
    n = len(left)
    left_unique, right_unique = np.unique(left).size, np.unique(right).size
    if n < 2:
        return np.nan, np.nan, "INSUFFICIENT_SUPPORT"
    if left_unique < 2 and right_unique < 2:
        return np.nan, np.nan, "DEGENERATE_BOTH_CONSTANT"
    # sklearn is the independent implementation used to verify the old table.
    return (
        float(normalized_mutual_info_score(left, right, average_method="arithmetic")),
        float(adjusted_rand_score(left, right)),
        "VALID_ONE_SIDE_CONSTANT" if left_unique < 2 or right_unique < 2 else "VALID",
    )


def load_data() -> tuple[pd.DataFrame, pd.DataFrame, dict[str, np.ndarray], pd.DataFrame, pd.DataFrame]:
    fields = [
        "event_id", "site", "turbine", "split", "config", "direction",
        "amplitude", "duration_hours", "power_start", "pre_mean",
    ]
    catalog = pd.read_csv(SOURCE / "candidate_intervals.csv.gz", usecols=fields)
    pairs = pd.read_csv(SOURCE / "test_pairs.csv.gz")
    train = pd.read_csv(SOURCE / "train_primary.csv")
    base = np.load(SOURCE / "labels_primary_raw25_k4.npz")
    test = catalog.iloc[base["rows"]].reset_index(drop=True)
    lookup = pd.Index(test.event_id)
    left = lookup.get_indexer(pairs.event_a)
    right = lookup.get_indexer(pairs.event_b)
    if (left < 0).any() or (right < 0).any():
        raise ValueError("test_pairs contains an event absent from the primary label rows")
    labels: dict[str, np.ndarray] = {}
    for name in REPRESENTATIONS:
        path = SOURCE / f"labels_primary_{name}_k4.npz"
        loaded = np.load(path)
        np.testing.assert_array_equal(loaded["rows"], base["rows"])
        labels[name] = loaded["labels"]
    return test, pairs, labels, train, catalog


def build_strata(test: pd.DataFrame, train: pd.DataFrame, catalog: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    train_ids = set(train.event_id)
    train_rows = catalog[catalog.event_id.isin(train_ids)]
    if train_rows.empty:
        raise ValueError("train_primary event IDs do not resolve in candidate_intervals")
    assert len(train_rows) == len(train_ids)
    assert train_rows.split.eq("train").all() and train_rows.site.eq("pizhou").all()
    seen = set(json.loads((SOURCE / "representation_manifest_primary.json").read_text())["splits"][0]["seen"])
    assert train_rows.turbine.astype(str).isin(seen).all()
    test = test.copy()
    test["amplitude_abs"] = test["amplitude"].abs()
    train_rows = train_rows.copy()
    train_rows["amplitude_abs"] = train_rows["amplitude"].abs()
    bins: dict[str, list[float] | None] = {"direction": None}
    for variable in NUMERIC_VARS:
        bins[variable] = make_bins(train_rows[variable])
    for variable in ALL_VARS:
        test[f"stratum_{variable}"] = labels_for(test[variable], variable, bins[variable])
    return test, bins


def compute_table(
    test: pd.DataFrame,
    pairs: pd.DataFrame,
    labels: dict[str, np.ndarray],
    bins: dict,
    left: np.ndarray,
    right: np.ndarray,
    variables: list[str],
) -> pd.DataFrame:
    rows: list[dict] = []
    pair_groups = pairs.groupby(["site", "config_a", "config_b"], sort=True).groups
    for variable in variables:
        key = f"stratum_{variable}"
        for (site, config_a, config_b), group_idx in pair_groups.items():
            group_idx = np.asarray(list(group_idx), dtype=int)
            same = test.iloc[left[group_idx]][key].to_numpy() == test.iloc[right[group_idx]][key].to_numpy()
            for stratum in sorted(set(test.iloc[left[group_idx]][key].astype(str)) | set(test.iloc[right[group_idx]][key].astype(str))):
                selected = group_idx[same & (test.iloc[left[group_idx]][key].to_numpy() == stratum)]
                total_in_left = int(np.sum(test.iloc[left[group_idx]][key].astype(str).to_numpy() == stratum))
                total_in_right = int(np.sum(test.iloc[right[group_idx]][key].astype(str).to_numpy() == stratum))
                matched = len(selected)
                coverage = matched / max(total_in_left, total_in_right, 1)
                for representation, lab in labels.items():
                    nmi, ari, status = pair_metric(lab[left[selected]], lab[right[selected]])
                    rows.append({
                        "conditioning": variable, "stratum": stratum, "site": site,
                        "config_a": config_a, "config_b": config_b,
                        "threshold_source": "train_primary.csv only",
                        "thresholds": json.dumps(bins[variable], separators=(",", ":")),
                        "all_pairs_config_site": len(group_idx),
                        "left_stratum_pairs": total_in_left, "right_stratum_pairs": total_in_right,
                        "matched_pairs": matched, "matched_coverage": coverage,
                        "representation": representation,
                        "left_label_cardinality": int(np.unique(lab[left[selected]]).size) if matched else 0,
                        "right_label_cardinality": int(np.unique(lab[right[selected]]).size) if matched else 0,
                        "nmi": nmi, "ari": ari, "metric_status": status,
                    })
    return pd.DataFrame(rows)


def legacy_audit(test, pairs, labels, train, catalog, left, right) -> pd.DataFrame:
    """Reproduce v5's all-four-variable matching and compare its stored rows."""
    train_rows = catalog.set_index("event_id").loc[train.event_id]
    strata = test.direction.astype(str)
    for name in ["amplitude", "duration_hours", "pre_mean"]:
        train_values = train_rows[name].abs() if name == "amplitude" else train_rows[name]
        values = test[name].abs() if name == "amplitude" else test[name]
        bins = np.unique(np.quantile(train_values, QUANTILES))
        strata = strata + "|" + pd.Series(np.searchsorted(bins, values, side="right"), index=test.index).astype(str)
    left_key, right_key = strata.to_numpy()[left], strata.to_numpy()[right]
    old = pd.read_csv(SOURCE / "covariate_conditioned_stability.csv")
    seen = set(json.loads((SOURCE / "representation_manifest_primary.json").read_text())["splits"][0]["seen"])
    group_masks = {site: pairs.site.eq(site) for site in sorted(pairs.site.unique())}
    group_masks["pizhou_seen"] = pairs.site.eq("pizhou") & pairs.turbine.isin(seen)
    group_masks["pizhou_unseen"] = pairs.site.eq("pizhou") & ~pairs.turbine.isin(seen)
    out = []
    for group, mask in group_masks.items():
      selected_pairs = pairs.loc[mask]
      for (site, ca, cb), idx in selected_pairs.groupby(["site", "config_a", "config_b"], sort=True).groups.items():
        idx = np.asarray(list(idx), int)
        keep = left_key[idx] == right_key[idx]
        for rep, lab in labels.items():
            nmi, ari, status = pair_metric(lab[left[idx[keep]]], lab[right[idx[keep]]])
            old_row = old[(old.group == group) & (old.representation == rep) & (old.config_a == ca) & (old.config_b == cb)]
            out.append({"group": group, "site": site, "config_a": ca, "config_b": cb, "representation": rep,
                        "legacy_matched_pairs": int(keep.sum()), "legacy_nmi_sklearn": nmi,
                        "legacy_ari_sklearn": ari, "metric_status": status,
                        "stored_pairs": int(old_row.pairs.iloc[0]) if len(old_row) else -1,
                        "stored_nmi": float(old_row.nmi.iloc[0]) if len(old_row) else np.nan,
                        "stored_ari": float(old_row.ari.iloc[0]) if len(old_row) else np.nan,
                        "nmi_abs_diff": abs(nmi - float(old_row.nmi.iloc[0])) if len(old_row) and np.isfinite(nmi) else np.nan,
                        "ari_abs_diff": abs(ari - float(old_row.ari.iloc[0])) if len(old_row) and np.isfinite(ari) else np.nan})
    return pd.DataFrame(out)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    test, pairs, labels, train, catalog = load_data()
    test, bins = build_strata(test, train, catalog)
    lookup = pd.Index(test.event_id)
    left, right = lookup.get_indexer(pairs.event_a), lookup.get_indexer(pairs.event_b)
    # Joint key is formed after independent keys, with the same bins above.
    joint = test[[f"stratum_{v}" for v in ALL_VARS]].agg("|".join, axis=1)
    test["stratum_joint_all_four"] = joint
    table = compute_table(test, pairs, labels, bins | {"joint_all_four": None}, left, right, ["joint_all_four"])
    # compute_table is called separately to avoid accidental mixed-key selection.
    first = compute_table(test, pairs, labels, bins, left, right, ALL_VARS)
    table = pd.concat([first, table], ignore_index=True)
    table.to_csv(OUT / "conditional_agreement.csv", index=False)
    legacy = legacy_audit(test, pairs, labels, train, catalog, left, right)
    legacy.to_csv(OUT / "legacy_recalculation.csv", index=False)
    with (OUT / "thresholds.json").open("w", encoding="utf8") as handle:
        json.dump({"source": "outputs/dynamic_events_v6/train_primary.csv event IDs resolved in candidate_intervals.csv.gz",
                   "quantiles": QUANTILES, "bins": bins,
                   "power_start_definition": "catalog power_start: first event value; no pre_mean substitution"}, handle, indent=2)
    manifest = {"status": "EXPLORATORY_CONDITIONAL_AGREEMENT_AUDIT",
                "source": str(SOURCE.relative_to(ROOT)), "output": str(OUT.relative_to(ROOT)),
                "n_test_events": len(test), "n_test_pairs": len(pairs), "k": 4,
                "metric_implementation": "sklearn normalized_mutual_info_score(average_method=arithmetic) and adjusted_rand_score",
                "inputs_sha256": {str(p.relative_to(ROOT)): sha256(p) for p in [
                    SOURCE / "candidate_intervals.csv.gz", SOURCE / "test_pairs.csv.gz", SOURCE / "train_primary.csv",
                    SOURCE / "covariate_conditioned_stability.csv", Path(__file__)]},
                "notes": ["Thresholds fit on training IDs only", "Metrics are per site/configuration pair and stratum",
                          "NaN metrics mark insufficient or both-constant label support; one-side-constant comparisons retain zero scores", "Descriptive agreement, not causal adjustment"]}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf8")
    print(json.dumps({"output": str(OUT), "rows": len(table), "legacy_rows": len(legacy),
                      "legacy_max_nmi_abs_diff": float(legacy.nmi_abs_diff.max()),
                      "legacy_max_ari_abs_diff": float(legacy.ari_abs_diff.max())}, indent=2))


if __name__ == "__main__":
    main()
