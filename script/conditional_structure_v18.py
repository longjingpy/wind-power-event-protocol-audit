"""Conditional partition information with training-fitted nuisance strata.

Cover and Thomas, Elements of Information Theory (2006), Chapter 2:
conditional mutual information and entropy. Report residual entropy as well
as normalized conditional information, so a largely constant partition is
not mistaken for evidence of rich structure. Same-site calendar resampling
preserves turbine and cross-configuration dependence.
"""
from pathlib import Path
import argparse
import json
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits
from run_structure_v18 import load_site, ROOT

BASE = ROOT/"outputs/protocol_benchmark_v18"
CAT = BASE/"catalogs/r30_a0.2_q0.05_training_q995"
MODELS = BASE/"structure"/CAT.name
OUT = BASE/"conditional"


def conditional_scores(counts):
    c = np.asarray(counts, float)
    if c.ndim == 3:
        c = c[None]
    ns = c.sum(axis=(-2, -1))
    total = ns.sum(axis=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        p = c/ns[:, :, None, None]
        a, b = p.sum(axis=-1), p.sum(axis=-2)
        mi = np.where(p > 0, p*np.log(p/(a[:, :, :, None]*b[:, :, None, :])), 0).sum(axis=(-2, -1))
        ha = -np.where(a > 0, a*np.log(a), 0).sum(axis=-1)
        hb = -np.where(b > 0, b*np.log(b), 0).sum(axis=-1)
        weight = ns/total[:, None]
        cm = (weight*mi).sum(axis=1)
        ca, cb = (weight*ha).sum(axis=1), (weight*hb).sum(axis=1)
        normalized = 2*cm/(ca+cb)
        marginal = c.sum(axis=1)
        pa, pb = marginal.sum(axis=-1)/total[:, None], marginal.sum(axis=-2)/total[:, None]
        marginal_a = -np.where(pa > 0, pa*np.log(pa), 0).sum(axis=1)
        marginal_b = -np.where(pb > 0, pb*np.log(pb), 0).sum(axis=1)
        remaining = (ca+cb)/(marginal_a+marginal_b)
    normalized[(ca+cb) <= 1e-12] = np.nan
    return cm, normalized, remaining


def counts_for(a, b, strata, nstrata, k=4):
    return np.bincount(strata*k*k+a*k+b, minlength=nstrata*k*k).reshape(nstrata, k, k)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--targets", nargs="+", default=["pizhou", "suining", "yandun", "lahaute", "hill", "greece", "sdwpf", "hill_2021"])
    parser.add_argument("--representations", nargs="+", default=["raw25", "gaf_pca6", "gaf_bit6"])
    parser.add_argument("--protocol-conditioned", action="store_true")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    train = pd.read_parquet(MODELS/"training_pizhou_s41.parquet")
    cut = {name: {"terciles": np.quantile(values, [1/3, 2/3]), "median": np.median(values)} for name, values in
        {"amplitude": train.amplitude.abs(), "duration": train.duration_hours, "pre_power": train.pre_mean}.items()}
    results = []
    for site in args.targets:
        table, _, pairs, _ = load_site(CAT, site)
        pairs = pairs[pairs.split.eq("test")].reset_index(drop=True)
        index = pd.Index(table.event_id)
        left, right = index.get_indexer(pairs.event_a), index.get_indexer(pairs.event_b)
        if (left < 0).any() or (right < 0).any():
            raise IndexError("Missing conditional-analysis endpoint")
        a, b = table.iloc[left], table.iloc[right]
        orientation = (a.direction.to_numpy(int)+1)*3+(b.direction.to_numpy(int)+1)
        variables = {"amplitude": (a.amplitude.abs().to_numpy()+b.amplitude.abs().to_numpy())/2,
                     "duration": (a.duration_hours.to_numpy()+b.duration_hours.to_numpy())/2,
                     "pre_power": (a.pre_mean.to_numpy()+b.pre_mean.to_numpy())/2}
        strata = {"direction": orientation}
        for name, values in variables.items():
            strata[name] = np.searchsorted(cut[name]["terciles"], values, side="right")
        joint = orientation.copy()
        for name, values in variables.items():
            joint = joint*2+(values >= cut[name]["median"])
        strata["joint"] = joint
        timestamp = pd.DatetimeIndex(pd.to_datetime(pairs.pair_time, utc=True)).as_unit("ns").asi8
        protocol_code = pd.factorize(pd.MultiIndex.from_frame(pairs[["config_a", "config_b"]]), sort=True)[0]
        for rep in args.representations:
            saved = np.load(MODELS/f"pizhou_{rep}_kmeans_k4_s41_to_{site}_labels.npz")
            labels = saved["labels"]
            if len(labels) != len(table):
                raise AssertionError("Label/table row count differs")
            if "event_ids" in saved:
                assert np.array_equal(saved["event_ids"], table.event_id.to_numpy(str))
            else:
                ref = str(saved["event_index_file"].item()).replace("\\", "/")
                assert pd.read_parquet(ROOT/ref).event_id.tolist() == table.event_id.tolist()
            la, lb = labels[left].astype(int), labels[right].astype(int)
            for condition, raw_stratum in strata.items():
                if args.protocol_conditioned:
                    raw_stratum = protocol_code*(int(raw_stratum.max())+1)+raw_stratum
                values, inverse = np.unique(raw_stratum, return_inverse=True)
                sizes = np.bincount(inverse)
                keep = sizes[inverse] >= 30
                _, groups = np.unique(raw_stratum[keep], return_inverse=True)
                aa, bb, stamps = la[keep], lb[keep], timestamp[keep]
                nstrata = int(groups.max()+1) if len(groups) else 0
                if not nstrata:
                    continue
                count = counts_for(aa, bb, groups, nstrata)
                cm, cn, entropy = conditional_scores(count)
                rng = np.random.default_rng(41)
                membership = [np.flatnonzero(groups == j) for j in range(nstrata)]
                if args.protocol_conditioned:
                    nuisance = pd.DataFrame({"stratum": groups, "turbine": pairs.loc[keep, "turbine"].to_numpy()})
                    membership = [indices for indices in nuisance.groupby(["stratum", "turbine"], sort=True).indices.values() if len(indices) > 1]
                null = []
                for _ in range(100):
                    shuffled = bb.copy()
                    for rows in membership:
                        shuffled[rows] = bb[rng.permutation(rows)]
                    null.append(float(conditional_scores(counts_for(aa, shuffled, groups, nstrata))[0][0]))
                record = {"site": site, "representation": rep, "condition": condition, "pairs_before": len(pairs), "retained_pairs": int(keep.sum()),
                    "retained_fraction": float(keep.mean()), "strata": nstrata, "conditional_mi_nats": float(cm[0]),
                    "normalized_conditional_mi": float(cn[0]), "label_entropy_remaining_fraction": float(entropy[0]),
                    "within_stratum_permutation_mean_cmi": float(np.mean(null)), "conditional_mi_above_permutation": float(cm[0]-np.mean(null)),
                    "aggregation": "conditional on protocol pair and physical strata" if args.protocol_conditioned else "pooled matched-pair distribution",
                    "minimum_stratum_pairs": 30, "permutable_pair_fraction": sum(len(ix) for ix in membership)/len(aa)}
                for days in (3, 7, 14):
                    blocks, bi = np.unique(stamps//pd.Timedelta(days=days).value, return_inverse=True)
                    block_counts = np.zeros((len(blocks), nstrata*16), np.int64)
                    np.add.at(block_counts, (bi, groups*16+aa*4+bb), 1)
                    weights = np.random.default_rng(41).multinomial(len(blocks), np.full(len(blocks), 1/len(blocks)), size=2000)
                    bcm, bcn = np.empty(2000), np.empty(2000)
                    block_counts = block_counts.astype(float)
                    for first in range(0, 2000, 16):
                        boot = (weights[first:first+16]@block_counts).reshape(-1, nstrata, 4, 4)
                        cm_batch, cn_batch, _ = conditional_scores(boot)
                        bcm[first:first+len(cm_batch)], bcn[first:first+len(cn_batch)] = cm_batch, cn_batch
                    interval = {"block_days": days, "occupied_blocks": len(blocks)}
                    for name, values in (("cmi", bcm), ("normalized_cmi", bcn)):
                        finite = values[np.isfinite(values)]
                        interval[name+"_low"], interval[name+"_high"] = np.quantile(finite, [.025, .975]) if len(finite) else (np.nan, np.nan)
                    results.append(record | interval)
                filename = "conditional_information_protocol_conditioned.csv" if args.protocol_conditioned else "conditional_information.csv"
                pd.DataFrame(results).to_csv(OUT/filename, index=False)
                print(site, rep, condition, round(record["conditional_mi_above_permutation"], 4), round(record["retained_fraction"], 3), flush=True)
    protocol_name = "protocol_conditioned.json" if args.protocol_conditioned else "protocol.json"
    (OUT/protocol_name).write_text(json.dumps({"status": "COMPLETE", "protocol_conditioned": args.protocol_conditioned,
        "permutation": "within physical stratum and turbine" if args.protocol_conditioned else "within physical stratum",
        "training_source": "Pizhou seed41 training IDs",
        "minimum_stratum_size": 30, "permutation_repeats": 100, "bootstrap_repeats": 2000,
        "cutpoints": {name: {key: np.asarray(value).tolist() for key, value in values.items()} for name, values in cut.items()}}, indent=2))


if __name__ == "__main__":
    with threadpool_limits(limits=2):
        main()
