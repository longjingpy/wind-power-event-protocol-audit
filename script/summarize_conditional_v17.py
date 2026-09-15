"""Summarize within-stratum scores and keep every coverage denominator visible."""
from itertools import combinations
from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "outputs/conditional_agreement_v17"


def main():
    metrics = pd.read_csv(BASE / "conditional_agreement.csv")
    counts = pd.read_csv(ROOT / "outputs/dynamic_events_v6/catalog_summary.csv")
    counts = counts[counts.split.eq("test")]
    eligible = {(row.site, row.config): int(row.eligible) for row in counts.itertuples()}
    denominators = {}
    for site, group in counts.groupby("site"):
        pairs = list(combinations(sorted(group.config), 2))
        denominators[site] = (sum(eligible[site, ca] for ca, cb in pairs), sum(eligible[site, cb] for ca, cb in pairs))
    rows = []
    for (site, conditioning, representation), group in metrics.groupby(["site", "conditioning", "representation"]):
        original_pairs = int(group.groupby(["config_a", "config_b"]).all_pairs_config_site.first().sum())
        retained = int(group.matched_pairs.sum())
        defined = group[group.nmi.notna() & group.ari.notna()]
        supported = defined[defined.matched_pairs.ge(30)]
        n = int(supported.matched_pairs.sum())
        weighted = lambda field: float(np.average(supported[field], weights=supported.matched_pairs)) if n else np.nan
        left_n, right_n = denominators[site]
        rows.append({"site": site, "conditioning": conditioning, "representation": representation,
                     "strata": len(group), "defined_strata": len(defined), "strata_n_ge_30": len(supported),
                     "both_constant_strata": int(group.metric_status.eq("DEGENERATE_BOTH_CONSTANT").sum()),
                     "one_side_constant_strata": int(group.metric_status.eq("VALID_ONE_SIDE_CONSTANT").sum()),
                     "original_matched_pairs": original_pairs, "retained_pairs": retained,
                     "retained_pair_fraction": retained / original_pairs if original_pairs else np.nan,
                     "catalogue_left_views": left_n, "catalogue_right_views": right_n,
                     "conditional_left_coverage": retained / left_n, "conditional_right_coverage": retained / right_n,
                     "scored_pairs_n_ge_30": n, "scored_fraction_of_retained": n / retained if retained else np.nan,
                     "equal_stratum_nmi_n_ge_30": supported.nmi.mean(), "equal_stratum_ari_n_ge_30": supported.ari.mean(),
                     "median_nmi_n_ge_30": supported.nmi.median(), "median_ari_n_ge_30": supported.ari.median(),
                     "pair_weighted_nmi_n_ge_30": weighted("nmi"), "pair_weighted_ari_n_ge_30": weighted("ari")})
    output = pd.DataFrame(rows)
    output.to_csv(BASE / "paper_summary.csv", index=False)
    (BASE / "summary_protocol.json").write_text(json.dumps({
        "score_support_threshold": 30, "status": "DESCRIPTIVE_WITHIN_STRATUM_SUMMARY",
        "denominator_rule": "all 17-configuration pair-side catalogue views at each primary site, including zero-match pairings",
        "retention": "conditional matches / original temporal matches; distinct from full-catalogue coverage",
        "scoring": "one-side constant comparisons contribute zero; both-constant comparisons have no informative conditional partition",
        "uncertainty": "point summaries only; no new block intervals or significance claim for the conditional decrease"}, indent=2))
    print(output[output.representation.eq("raw25")][["site", "conditioning", "retained_pair_fraction", "conditional_left_coverage", "scored_fraction_of_retained", "pair_weighted_nmi_n_ge_30", "pair_weighted_ari_n_ge_30"]].to_string(index=False))


if __name__ == "__main__":
    main()
