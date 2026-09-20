"""Matched-budget source/target structure matrix using v18 catalogue shards."""
from pathlib import Path
import argparse
import json
import sys
import time
import joblib
import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"src"))
from wind_events.representation import FEATURES, Representation, fit_cluster
from wind_events.metrics import contingency, scores_from_counts, block_intervals, support_components


def load_site(folder, site):
    frames, shapes, pairs, coverages = [], [], [], []
    offset = 0
    for audit_path in sorted((folder/site).glob("*/audit.json")):
        audit = json.loads(audit_path.read_text())
        if audit.get("status") != "COMPLETE" or audit.get("schema_version") != "18.1":
            continue
        base = audit_path.parent
        table = pd.read_parquet(base/"events.parquet")
        table = table[table.representation_eligible & table.event_level.eq("primitive")].copy()
        indices = table.shape_row.to_numpy(int)
        native = np.load(base/"shapes.npy", mmap_mode="r")
        if (indices < 0).any() or (indices >= len(native)).any():
            raise IndexError("Invalid shape row")
        shapes.append(np.asarray(native[indices], np.float32))
        table["array_row"] = np.arange(len(table))+offset
        offset += len(table)
        frames.append(table)
        p = pd.read_parquet(base/"pairs.parquet")
        pairs.append(p[p.event_level.eq("primitive")])
        c = pd.read_parquet(base/"coverage.parquet")
        coverages.append(c[c.event_level.eq("primitive")])
    if not frames:
        raise ValueError(f"No completed site shards for {site}")
    table = pd.concat(frames, ignore_index=True)
    if not table.event_id.is_unique:
        raise ValueError("Duplicate site event identity")
    return table, np.vstack(shapes), pd.concat(pairs, ignore_index=True), pd.concat(coverages, ignore_index=True)


def balanced_pick(frame, n, seed):
    rng = np.random.default_rng(seed)
    pools = [rng.permutation(group.index.to_numpy()) for _, group in frame.groupby("turbine", sort=True)]
    result, depth = [], 0
    while len(result) < n:
        added = 0
        for pool in pools:
            if depth < len(pool):
                result.append(int(pool[depth])); added += 1
                if len(result) == n:
                    break
        if not added:
            break
        depth += 1
    return result


def matched_training(datasets, sources, seed, budget):
    tables = {}
    for source in sources:
        table = datasets[source][0]
        keep = table.split.eq("train")
        if source == "pizhou":
            keep &= table.turbine.isin(sorted(table.turbine.unique())[:26])
        tables[source] = table[keep]
    common = sorted(set.intersection(*(set(table.config.unique()) for table in tables.values())))
    per_config = budget//len(common)
    picks = {source: [] for source in sources}
    for number, config in enumerate(common):
        n = min(per_config, *(int(table.config.eq(config).sum()) for table in tables.values()))
        for source, table in tables.items():
            picks[source].extend(balanced_pick(table[table.config.eq(config)], n, seed+number))
    if len({len(rows) for rows in picks.values()}) != 1:
        raise AssertionError("Source/target training budgets differ")
    return {source: np.array(sorted(rows), int) for source, rows in picks.items()}


def evaluate(dataset, labels, latent, cluster, metadata, bootstrap_days, repetitions):
    table, shapes, pairs, coverage = dataset
    lookup = pd.Index(table.event_id)
    left, right = lookup.get_indexer(pairs.event_a), lookup.get_indexer(pairs.event_b)
    if (left < 0).any() or (right < 0).any():
        raise IndexError("Pair endpoint absent from evaluation set")
    k = metadata["k"]
    rows = []
    for (split, ca, cb), cov in coverage.groupby(["split", "config_a", "config_b"], sort=True):
        select = np.flatnonzero((pairs.split == split) & (pairs.config_a == ca) & (pairs.config_b == cb))
        a, b = labels[left[select]], labels[right[select]]
        nmi, ari, exact, informative = scores_from_counts(contingency(a, b, k))
        count, left_n, right_n = len(select), int(cov.left_n.sum()), int(cov.right_n.sum())
        block_count = pd.to_datetime(pairs.iloc[select].pair_time, utc=True).dt.floor("7D").nunique()
        la, lb = table.iloc[left[select]], table.iloc[right[select]]
        starts = np.minimum(pd.to_datetime(la.time_start, utc=True).to_numpy(), pd.to_datetime(lb.time_start, utc=True).to_numpy())
        ends = np.maximum(pd.to_datetime(la.time_end, utc=True).to_numpy(), pd.to_datetime(lb.time_end, utc=True).to_numpy())
        record = metadata | {"target_site": table.site.iloc[0], "split": split, "config_a": ca, "config_b": cb,
                  "pairs": count, "left_n": left_n, "right_n": right_n,
                  "left_coverage": count/left_n if left_n else np.nan, "right_coverage": count/right_n if right_n else np.nan,
                  "nmi": float(nmi[0]), "ari": float(ari[0]), "exact_agreement": float(exact[0]),
                  "left_clusters": len(np.unique(a)), "right_clusters": len(np.unique(b)),
                  "informative_partition": bool(informative[0]), "low_support": count < 100,
                  "occupied_7day_blocks": block_count,
                  "support_components": support_components(starts, ends, pairs.iloc[select].turbine.to_numpy()) if count else 0}
        for days in bootstrap_days:
            interval = block_intervals(a, b, pairs.iloc[select].pair_time, k, days, repetitions, metadata["seed"])
            rows.append(record | {"block_days": days, **interval})
    composition = []
    centers = cluster.means_ if hasattr(cluster, "means_") else cluster.cluster_centers_
    for split in ("validation", "test"):
        indices = np.flatnonzero(table.split.eq(split))
        counts = np.bincount(labels[indices], minlength=k)
        distances = np.linalg.norm(latent[indices]-centers[labels[indices]], axis=1)
        for label in range(k):
            composition.append(metadata | {"target_site": table.site.iloc[0], "split": split, "cluster": label,
                "events": int(counts[label]), "fraction": float(counts[label]/len(indices)) if len(indices) else np.nan,
                "median_assigned_center_distance": float(np.median(distances[labels[indices] == label])) if counts[label] else np.nan})
    return rows, composition


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", type=Path, default=ROOT/"outputs/protocol_benchmark_v18/catalogs/r30_a0.2_q0.05_training_q995")
    parser.add_argument("--sources", nargs="+", default=["pizhou", "greece"])
    parser.add_argument("--targets", nargs="+", default=["pizhou", "greece"])
    parser.add_argument("--representations", nargs="+", default=["raw25", "statistics9", "raw_pca6", "gaf_pca6", "gaf_signed_pca6", "gaf_bit6"])
    parser.add_argument("--algorithms", nargs="+", default=["kmeans", "gmm", "medoids"])
    parser.add_argument("--clusters", nargs="+", type=int, default=[2, 4, 6])
    parser.add_argument("--seeds", nargs="+", type=int, default=[41, 42, 43])
    parser.add_argument("--training-budget", type=int, default=10000)
    parser.add_argument("--bootstrap-days", nargs="+", type=int, default=[3, 7, 14])
    parser.add_argument("--bootstrap-replicates", type=int, default=2000)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    out = ROOT/"outputs/protocol_benchmark_v18/structure"/args.catalog.name
    out.mkdir(parents=True, exist_ok=True)
    datasets = {site: load_site(args.catalog, site) for site in sorted(set(args.sources+args.targets))}
    for site, value in datasets.items():
        print("loaded", site, len(value[0]), len(value[2]), flush=True)
    for seed in args.seeds:
        selected = matched_training(datasets, args.sources, seed, args.training_budget)
        for source, ids in selected.items():
            table, shapes, _, _ = datasets[source]
            training = table.iloc[ids]
            training.to_parquet(out/f"training_{source}_s{seed}.parquet", index=False)
            for name in args.representations:
                x = training[FEATURES].to_numpy(float) if name == "statistics9" else shapes[training.array_row.to_numpy()]
                transform = Representation(name).fit(x)
                encoded = transform.transform(x)
                for k in args.clusters:
                    for algorithm in args.algorithms:
                        token = f"{source}_{name}_{algorithm}_k{k}_s{seed}"
                        model_path = out/(token+".joblib")
                        if args.resume and model_path.exists():
                            artifact = joblib.load(model_path)
                            if artifact["training_ids"] != training.event_id.tolist():
                                raise ValueError("Saved model training IDs do not match")
                            transform, cluster = artifact["transform"], artifact["cluster"]
                        else:
                            cluster = fit_cluster(encoded, algorithm, k, seed)
                            joblib.dump({"transform": transform, "cluster": cluster, "training_ids": training.event_id.tolist()}, model_path)
                        metadata = {"source_site": source, "representation": name, "algorithm": algorithm, "k": k,
                                    "seed": seed, "training_events": len(training), "budget_design": "matched_common_configurations"}
                        for target in args.targets:
                            result_path = out/(token+f"_to_{target}_pairs.csv")
                            if args.resume and result_path.exists():
                                continue
                            target_table, target_shapes, _, _ = datasets[target]
                            blocks, labels = [], []
                            for start in range(0, len(target_table), 4096):
                                frame = target_table.iloc[start:start+4096]
                                data = frame[FEATURES].to_numpy(float) if name == "statistics9" else target_shapes[frame.array_row.to_numpy()]
                                latent = transform.transform(data)
                                blocks.append(latent); labels.append(cluster.predict(latent))
                            latent, prediction = np.vstack(blocks), np.concatenate(labels)
                            results, composition = evaluate(datasets[target], prediction, latent, cluster, metadata,
                                                            args.bootstrap_days, args.bootstrap_replicates)
                            pd.DataFrame(results).to_csv(result_path, index=False)
                            pd.DataFrame(composition).to_csv(out/(token+f"_to_{target}_composition.csv"), index=False)
                            np.savez_compressed(out/(token+f"_to_{target}_labels.npz"), labels=prediction,
                                                event_ids=target_table.event_id.to_numpy(str))
                            print(token, "to", target, "complete", flush=True)
    print("structure schedule complete", flush=True)


if __name__ == "__main__":
    main()
