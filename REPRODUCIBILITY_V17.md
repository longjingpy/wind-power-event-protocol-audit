# v17 reproducibility and evidence map

The public repository now contains the processed-data v0.3.0 release and the evidence produced for the latest review cycle.

| Evidence | Public path | Verification |
|---|---|---|
| Processed SCADA | v0.3.0 asset `processed_scada_v17.zip` | 333 pseudonymous turbines, 7,548,467 rows, 338 archive members, whole-archive CRC and anonymous-download byte match |
| Model-size HPO | `results/detection_hpo_v16/` and selected checkpoints | Four neural models, three candidate sizes, three training seeds; validation selection precedes fresh test draws |
| Noise-calibrated confirmation | `results/noise_calibration_v17/` | Common 400-sequence high-noise validation population, new 1,600-sequence test population, paired intervals |
| Conditional correspondence | `results/conditional_agreement_v17/` | Five primary farms, per-pair strata and separate catalogue denominators |
| Native Yandun resolution | `results/yandun_resolution_v17/` | 15/30/60-min raw25 prototypes and one-to-one test matching |
| Storage and LP audit | `results/storage_audit_v17/` | Validation-selected policies, full cost decomposition, physical SOC equations and real fixed-capacity traces |
| Weather diagnostics | `results/weather_diagnostics_v17/` | 22 IRLS iterations, 31 calendar blocks, clustered covariance and block-t/BH values |

The v17 scripts preserve separate populations: measurement agreement, synthetic localization, forecasting and storage decision costs. The public processed data exclude original provider files, direct turbine identifiers, coordinates, absolute dates and private identity/clock maps. Original public-source terms remain applicable.

The full raw-data-to-paper rebuild remains a separate integration task. The public confirmation command restores selected checkpoints and reproduces the fresh synthetic evidence without accessing original provider files.
