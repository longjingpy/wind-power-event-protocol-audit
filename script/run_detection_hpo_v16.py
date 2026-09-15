"""Portable launcher for the archived four-model, three-candidate search."""
from pathlib import Path
import argparse
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--seeds", type=int, nargs="+", default=[41, 42, 43])
    parser.add_argument("--output-root", type=Path, default=ROOT / "outputs/detection_hpo_v16")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    candidates = [("h08_z08", 8, 8, .0005), ("h16_z16", 16, 16, .001), ("h32_z16", 32, 16, .001)]
    commands = []
    for prefix, models in [("", ["timesnet", "kanad"]), ("sequence_", ["tcn_ae", "transformer_ae"])]:
        for name, width, latent, rate in candidates:
            commands.append([sys.executable, str(ROOT / "script/benchmark_detection_v9.py"),
                             "--epochs", str(args.epochs), "--seeds", *map(str, args.seeds),
                             "--models", *models, "--hidden", str(width), "--latent-dim", str(latent),
                             "--learning-rate", str(rate), "--output-dir", str(args.output_root / (prefix + name))])
    if args.dry_run:
        print(json.dumps(commands, indent=2))
        return
    args.output_root.mkdir(parents=True, exist_ok=True)
    (args.output_root / "launcher_protocol.json").write_text(json.dumps({
        "commands": commands, "candidate_count_per_model": 3, "model_count": 4,
        "size_semantics": "TimesNet channels; KAN-AD Fourier order; sequence encoder width",
        "latent_semantics": "used by TCN-AE/Transformer-AE only"}, indent=2))
    for command in commands:
        subprocess.run(command, cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
