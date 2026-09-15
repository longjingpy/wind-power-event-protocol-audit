# Reproducibility record v16

The release separates three reproducibility levels:

1. **Aggregate reproduction.** CSV summaries, figures and targeted tests use the scripts and inputs in this repository. The matching, sampling and benchmark unit tests pass in the recorded Python 3.12 environment.
2. **Controlled HPO and confirmation reproduction.** `results/detection_hpo_v16/` records validation selection across three candidates per neural model and four mean-rule windows. TimesNet varies channels, KAN-AD varies Fourier order, and sequence autoencoders vary width and latent size. Four selected models, each with three training seeds, are frozen before fresh confirmation draws. Selected-checkpoint inference has been run directly from this public repository using the vendored upstream subset; all confirmation metrics and paired intervals match the research-workspace outputs.
3. **Full raw-data rebuild.** The release contains the study inputs and analysis scripts. A complete raw-data-to-paper rebuild remains a separate integration task; the release does not represent it as a one-command guarantee.

The direct package versions observed during v16 checks are in `requirements-lock-py312.txt`. Despite the historical filename, this is an environment snapshot rather than a validated clean-install lock; the vendor ROCm torch build requires its own wheel source. The public scripts use fixed random seeds. Selected model checkpoints and training logs are under `models/detection_hpo_v16/`.

The following command was executed in the repository with the recorded research environment:

```bash
python script/confirm_detection_v16.py --model-root models/detection_hpo_v16 --selection-file results/detection_hpo_v16/selected_summary.csv --simple-rule-file results/detection_hpo_v16/simple_rule_selected.json --output-dir reproduced/confirmation_v16
```

It generates two fixed fresh-sample sets, restores all twelve selected checkpoints, scores all five methods, and computes 2,000 paired sequence-resampling intervals. It uses the four-file TSLib dependency subset and original MIT notice in `third_party/tslib/`. New CPU timing measurements can vary by run; statistical outputs are checked separately.

Economic results use declared price scenarios and a policy-grounded 10%-power/2-hour design. They are scenario costs per installed MW over the stated test calendar, not site settlement revenue. The storage conditional-advantage table lists every tested grid cell with a lower event-weighted three-seed mean.
