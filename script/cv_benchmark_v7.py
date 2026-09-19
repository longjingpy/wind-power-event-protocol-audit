"""Learning-based CV baselines under the frozen v5 event protocol.

The Pizhou training split alone defines the input standardisation and neural
autoencoder weights. Test and external site rows are used only for forward
prediction and paired agreement metrics. This is a representation audit,
not a supervised event-truth benchmark.
"""
from __future__ import annotations

import argparse
import copy
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score
from torch import nn

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "outputs" / "dynamic_events_v6"
DEFAULT_OUTPUT = ROOT / "outputs" / "cv_benchmark_v7"


class EncoderAE(nn.Module):
    def __init__(self, kind: str, latent_dim: int = 6):
        super().__init__()
        self.kind = kind
        if kind in {"cnn_gaf", "cnn_signed_gaf"}:
            channels = 2 if kind == "cnn_signed_gaf" else 1
            self.encoder = nn.Sequential(
                nn.Conv2d(channels, 16, 3, padding=1), nn.ReLU(),
                nn.Conv2d(16, 32, 3, padding=1), nn.ReLU(),
                nn.AdaptiveAvgPool2d((5, 5)), nn.Flatten(),
                nn.Linear(32 * 5 * 5, latent_dim),
            )
        elif kind == "tcn":
            self.encoder = nn.Sequential(
                nn.Conv1d(1, 24, 3, padding=1), nn.ReLU(),
                nn.Conv1d(24, 24, 3, padding=2, dilation=2), nn.ReLU(),
                nn.AdaptiveAvgPool1d(8), nn.Flatten(), nn.Linear(24 * 8, latent_dim),
            )
        elif kind == "transformer":
            layer = nn.TransformerEncoderLayer(
                d_model=24, nhead=4, dim_feedforward=48,
                dropout=0.0, batch_first=True, activation="gelu",
            )
            self.project = nn.Linear(1, 24)
            self.position = nn.Parameter(torch.zeros(1, 25, 24))
            self.encoder = nn.Sequential(nn.TransformerEncoder(layer, 2), nn.Flatten(), nn.Linear(25 * 24, latent_dim))
        else:
            raise ValueError(kind)
        self.decoder = nn.Sequential(nn.Linear(latent_dim, 48), nn.ReLU(), nn.Linear(48, 25))

    @staticmethod
    def _gaf(x: torch.Tensor) -> torch.Tensor:
        x = torch.clamp(x, -1.0, 1.0)
        comp = torch.sqrt(torch.clamp(1.0 - x * x, min=0.0))
        return x[:, :, None] * x[:, None, :] - comp[:, :, None] * comp[:, None, :]

    def embed_input(self, x: torch.Tensor) -> torch.Tensor:
        if self.kind in {"cnn_gaf", "cnn_signed_gaf"}:
            image = self._gaf(x)[:, None]
            if self.kind == "cnn_signed_gaf":
                image = torch.cat([image, x[:, None, :, None].expand(-1, 1, -1, 25)], dim=1)
            return image
        if self.kind == "tcn":
            return x[:, None]
        return self.project(x[:, :, None]) + self.position

    def encode(self, x: torch.Tensor) -> torch.Tensor:
        return self.encoder(self.embed_input(x))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.decoder(self.encode(x))


def latent_and_recon(model, x: np.ndarray, device: torch.device, batch: int = 4096):
    model.eval(); z_parts, rec_parts = [], []
    with torch.no_grad():
        for start in range(0, len(x), batch):
            xb = torch.as_tensor(x[start:start + batch], device=device)
            z_parts.append(model.encode(xb).cpu().numpy())
            rec_parts.append(model(xb).cpu().numpy())
    return np.concatenate(z_parts), np.concatenate(rec_parts)


def sample_rows(d: pd.DataFrame, mask: pd.Series, per_config: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed); rows = []
    for _, group in d.loc[mask].groupby("config", sort=True):
        ix = group.index.to_numpy()
        rows.extend(rng.choice(ix, min(per_config, len(ix)), replace=False).tolist())
    return np.asarray(sorted(rows), dtype=np.int64)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT)
    ap.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    ap.add_argument("--per-config", type=int, default=2500)
    ap.add_argument("--epochs", type=int, default=20)
    ap.add_argument("--seeds", type=int, nargs="+", default=[41, 42, 43])
    ap.add_argument("--k", type=int, nargs="+", default=[2, 4, 6])
    ap.add_argument("--models", nargs="+", default=["cnn_gaf", "cnn_signed_gaf", "tcn", "transformer"])
    args = ap.parse_args()
    started = time.monotonic(); args.output_dir.mkdir(parents=True, exist_ok=True)
    torch.set_num_threads(2); device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    d = pd.read_csv(args.input_dir / "candidate_intervals.csv.gz", dtype={"turbine": str})
    x = np.load(args.input_dir / "context_shapes.npy", mmap_mode="r")
    eligible = d.representation_eligible.fillna(False)
    turbines = sorted(d.loc[d.site.eq("pizhou"), "turbine"].unique()); seen = turbines[:26]
    train_mask = eligible & d.site.eq("pizhou") & d.turbine.isin(seen) & d.split.eq("train")
    val_mask = eligible & d.site.eq("pizhou") & d.turbine.isin(seen) & d.split.eq("validation")
    test = d.loc[eligible & d.split.eq("test")].copy(); test_rows = test.shape_row.to_numpy(dtype=np.int64)
    test_pos = {event_id: i for i, event_id in enumerate(test.event_id)}
    pairs = pd.read_csv(args.input_dir / "test_pairs.csv.gz")
    pair_left = pairs.event_a.map(test_pos).to_numpy(); pair_right = pairs.event_b.map(test_pos).to_numpy()
    if ((pair_left < 0) | (pair_right < 0)).any(): raise RuntimeError("pair points to non-eligible row")
    groups = {site: np.flatnonzero(test.site.eq(site).to_numpy()) for site in sorted(test.site.unique())}
    groups["pizhou_seen"] = np.flatnonzero(test.site.eq("pizhou").to_numpy() & test.turbine.isin(seen).to_numpy())
    groups["pizhou_unseen"] = np.flatnonzero(test.site.eq("pizhou").to_numpy() & ~test.turbine.isin(seen).to_numpy())
    pair_groups = {site: np.flatnonzero(pairs.site.eq(site).to_numpy()) for site in sorted(pairs.site.unique())}
    pair_groups["pizhou_seen"] = np.flatnonzero(pairs.site.eq("pizhou").to_numpy() & pairs.turbine.isin(seen).to_numpy())
    pair_groups["pizhou_unseen"] = np.flatnonzero(pairs.site.eq("pizhou").to_numpy() & ~pairs.turbine.isin(seen).to_numpy())

    rows = []; model_kinds = args.models
    for seed in args.seeds:
        train_rows = sample_rows(d, train_mask, args.per_config, seed); val_rows = sample_rows(d, val_mask, max(100, args.per_config // 4), seed + 1000)
        train_shape_rows = d.loc[train_rows, "shape_row"].to_numpy(dtype=np.int64); val_shape_rows = d.loc[val_rows, "shape_row"].to_numpy(dtype=np.int64)
        mu = np.asarray(x[train_shape_rows], dtype=np.float64).mean(axis=0).astype(np.float32)
        sd = np.asarray(x[train_shape_rows], dtype=np.float64).std(axis=0).astype(np.float32); sd[sd < 1e-6] = 1.0
        x_train = ((np.asarray(x[train_shape_rows], dtype=np.float32) - mu) / sd).astype(np.float32)
        x_val = ((np.asarray(x[val_shape_rows], dtype=np.float32) - mu) / sd).astype(np.float32)
        test_x = ((np.asarray(x[test_rows], dtype=np.float32) - mu) / sd).astype(np.float32)
        for kind in model_kinds:
            torch.manual_seed(seed); model = EncoderAE(kind).to(device); opt = torch.optim.Adam(model.parameters(), lr=1e-3)
            best, best_state, patience = float("inf"), None, 0; rng = np.random.default_rng(seed)
            for _ in range(args.epochs):
                model.train(); order = rng.permutation(len(x_train))
                for batch_ix in np.array_split(order, max(1, len(order) // 256)):
                    xb = torch.as_tensor(x_train[batch_ix], device=device); opt.zero_grad(set_to_none=True)
                    loss = ((model(xb) - xb) ** 2).mean(); loss.backward(); opt.step()
                model.eval(); xv = torch.as_tensor(x_val, device=device)
                with torch.no_grad(): val_loss = float(((model(xv) - xv) ** 2).mean().cpu())
                if val_loss < best - 1e-7: best, patience, best_state = val_loss, 0, copy.deepcopy(model.state_dict())
                else:
                    patience += 1
                    if patience >= 4: break
            if best_state is None: raise RuntimeError(f"no checkpoint for {kind}/{seed}")
            model.load_state_dict(best_state); z_train, _ = latent_and_recon(model, x_train, device); z_test, rec_test = latent_and_recon(model, test_x, device)
            zmu, zsd = z_train.mean(axis=0), z_train.std(axis=0); zsd[zsd < 1e-6] = 1.0
            z_train, z_test = (z_train - zmu) / zsd, (z_test - zmu) / zsd
            np.savez_compressed(args.output_dir / f"latent_{kind}_seed{seed}.npz", train=z_train, test=z_test, test_rows=test_rows)
            torch.save({"state_dict": best_state, "input_mean": mu, "input_std": sd, "latent_mean": zmu, "latent_std": zsd}, args.output_dir / f"model_{kind}_seed{seed}.pt")
            recon_mse = ((rec_test - test_x) ** 2).mean(axis=1)
            for k in args.k:
                km = KMeans(n_clusters=k, n_init=20, random_state=seed).fit(z_train); labels = km.predict(z_test)
                np.savez_compressed(args.output_dir / f"labels_{kind}_seed{seed}_k{k}.npz", labels=labels, rows=test_rows)
                for group, ix in groups.items():
                    if len(ix) == 0: continue
                    counts = np.bincount(labels[ix], minlength=k) / len(ix)
                    rows.append({"representation": kind, "seed": seed, "k": k, "group": group, "events": int(len(ix)), "turbines": int(test.iloc[ix].turbine.nunique()), "reconstruction_mse": float(recon_mse[ix].mean()), "cluster_proportions": json.dumps(counts.tolist())})
                for group, pix in pair_groups.items():
                    if len(pix) == 0: continue
                    la, lb = labels[pair_left[pix]], labels[pair_right[pix]]
                    rows.append({"representation": kind, "seed": seed, "k": k, "group": f"pairs:{group}", "events": int(len(pix)), "turbines": int(pairs.iloc[pix].turbine.nunique()), "nmi": float(normalized_mutual_info_score(la, lb)), "ari": float(adjusted_rand_score(la, lb)), "agreement": float(np.mean(la == lb)), "reconstruction_mse": float(recon_mse[np.unique(np.r_[pair_left[pix], pair_right[pix]])].mean())})
            print(f"{kind} seed={seed} best_val={best:.6g} device={device}", flush=True)
    result = pd.DataFrame(rows); result.to_csv(args.output_dir / "cv_benchmark_metrics.csv", index=False)
    pairs_result = result[result.group.str.startswith("pairs:")]
    pairs_result.groupby(["representation", "k", "group"])[["nmi", "ari", "agreement"]].agg(["mean", "std", "count"]).to_csv(args.output_dir / "cv_benchmark_summary.csv")
    manifest = {"status": "PASS_FROZEN_PIZHOU_TRAIN", "input_dir": str(args.input_dir), "device": str(device), "train_rows_per_seed": int(train_mask.sum()), "test_rows": int(len(test)), "train_turbines": seen, "heldout_turbines": sorted(set(turbines) - set(seen)), "representations": model_kinds, "seeds": args.seeds, "clusters": args.k, "epochs": args.epochs, "per_config": args.per_config, "notes": ["Pizhou train split alone fitted input/latent transforms and autoencoder weights.", "Greek and other sites are forward-only external/test evaluation.", "No labels or test rows enter training; pairs are checked before indexing.", "Autoencoder reconstruction is self-supervision, not event-truth supervision."], "runtime_seconds": time.monotonic() - started}
    (args.output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
