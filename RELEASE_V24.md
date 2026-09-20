# v0.6.0: economic research snapshot

This snapshot adds completed economic experiments and replication inputs. It
does not replace the v23 manuscript or certify that every novelty/utility
question is closed. All successful and unsuccessful comparisons are retained.

## Verified findings

- A native 15-minute Pizhou replay uses the accuracy-charge component of the
  Jiangsu 2022 No.53 Article 44(II), rather than duplicating half-hour data.
  Validation-selected pipelines reduce simulated 15-minute/4-hour assessment
  charges by 3.755%/18.218%. The 4-hour reduction is CNY 27,109.50 over 9,345
  eligible test points (7-day block interval 15.432–21.382%). This is a specified
  policy-rule simulation, not a realized bill or a reconstruction of every
  later amendment, exemption or reporting charge.
- GFS/JMA fixed-24-hour-lead forecasts and historical Elexon WINDFOR vintages
  enter only when available before the experimental issue time.
- The 2021H1 GB storage replay produces positive operating gains after the
  specified throughput wear charge, but event features do not outperform the
  strongest market-information baseline.
- The frozen 2021H2 complete-revenue trade test does not outperform passive
  persistence. These results remain in `full_revenue/`.
- Strong scalar and nMAE-selected references can match or improve on the
  morphology pipeline. Independent morphology profit is not established.

## Reproduction and provenance

`results/protocol_benchmark_v24/economics/` contains validation candidates,
selections, primary results, full comparisons, calendar-block intervals and
classifier-seed checks. `docs/ECONOMIC_RESULTS_V24.md` explains the progression
in Chinese. Identical fee totals are audited in `equal_fee_explanations.csv`:
equal exceedance counts need not imply duplicate predictions.

The release asset `economic_replication_v24.zip` includes six selected model
checkpoints, de-identified training/validation/test model-input matrices and
`script/reproduce_policy_v24.py`. Original timestamps and turbine IDs are
excluded; calendar features remain, so this is not a non-reidentification
guarantee. Inputs are already transformed: the tested command reproduces
predictions and fees, not the entire private raw-minute preprocessing chain.
Use only trusted joblib checkpoints.

Code is project-authored and MIT licensed. Data-provider and upstream
forecast terms remain applicable, including Open-Meteo attribution. The
Chinese SCADA-derived material follows the provider authorization recorded
in this repository. This release does not relicense third-party data as MIT.

The current submission manuscript remains the separately versioned v0.5.0
packet. Integration of the new economic evidence is a subsequent author step.
