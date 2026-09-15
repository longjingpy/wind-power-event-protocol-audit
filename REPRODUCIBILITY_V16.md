# Reproducibility record v16

The release separates three reproducibility levels:

1. **Aggregate reproduction.** CSV summaries, figures and targeted tests use the scripts and inputs in this repository. The matching, sampling and benchmark unit tests pass in the recorded Python 3.12 environment.
2. **Controlled HPO reproduction.** `results/detection_hpo_v16/` records three hidden/latent/learning-rate configurations, three seeds, validation-selected configurations and held-out metrics. The test set is read only after validation selection.
3. **Full raw-data rebuild.** The release contains the study inputs and analysis scripts. A complete raw-data-to-paper rebuild remains a separate integration task; the release does not represent it as a one-command guarantee.

The exact package versions observed during v16 checks are in `requirements-lock-py312.txt`. The public scripts use fixed random seeds where a stochastic operation is present. Model checkpoints used by the HPO summary are stored under `models/detection_hpo_v16/`; their metadata and training logs remain beside the corresponding results.

Economic results use declared price scenarios and a policy-grounded 10%-power/2-hour design. They are scenario costs per installed MW over the stated test calendar, not site settlement revenue. The storage conditional-advantage table lists every tested grid cell with a lower event-weighted three-seed mean.
