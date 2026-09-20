# Wind-power event protocol audit

Code and analysis resources for **Preserving physical information in transferable wind-power event measurements**.

Current manuscript, supplementary material, editable figures and v23 overlap
results are in the [v0.5.0 release](https://github.com/longjingpy/wind-power-event-protocol-audit/releases/tag/v0.5.0).
See `RELEASE_V23.md` for current paths, tested commands and the source packet.

The [v0.6.0 economic research snapshot](https://github.com/longjingpy/wind-power-event-protocol-audit/releases/tag/v0.6.0)
adds native policy-fee experiments, forecast-price storage control, complete
trade-revenue tests and de-identified model-input replication data. See
`RELEASE_V24.md` for successes, unsuccessful comparisons and remaining evidence
gates. It is a research snapshot, not a replacement submission manuscript.

## Study data

The provider authorizes release, and the current distribution uses de-identified processed datasets. Download the verified [processed SCADA v0.3.0 release](https://github.com/longjingpy/wind-power-event-protocol-audit/releases/tag/v0.3.0), containing seven archives and 333 turbines. The former original-input v0.2.0 release remains a non-public draft. See `DATA_POLICY_V17.md` for identifier and clock handling. Original provider terms remain applicable.

The processed-data schema and verified file index are under `datasets/processed_v17/`. The former raw-file manifest has been removed from the current distribution tree; its historical copies remain outside the new dataset bundle.

Public original sources are attributed through SDWPF (10.6084/m9.figshare.24798654), Greece (10.5281/zenodo.14546480), La Haute Borne and Hill of Towie source records. Unrelated GNSS projects, private attachments and corrupt download copies are excluded.

## Verified entry points

With Python 3.12 and `requirements.txt`:

```bash
python script/reproduce_aggregate_figures.py
python -m pytest -q tests
```

Research scripts additionally require `requirements-research.txt`. Current corrections are in `event_matching_v14.py`, `yandun_sampling_v14.py`, `weather_adjusted_v14.py` and `external_transfer_v14.py`. These scripts retain the full research workspace paths.

The v16 controlled HPO record is under `results/detection_hpo_v16/`. It covers three validation-selected candidates for each neural model, three training seeds, and four window candidates for the mean rule. Twelve selected checkpoints for TimesNet, KAN-AD, TCN-AE and Transformer-AE are under `models/detection_hpo_v16/`. Fresh post-selection results, paired intervals and CPU timing are in `results/detection_confirmation_v16/`. See `REPRODUCIBILITY_V16.md` for the tested checkpoint-inference command and for the distinction between an observed environment snapshot and a clean-install guarantee.

The storage-policy tables include the historical 10%-power/2-hour engineering benchmark, declared price scenarios and the complete conditional-advantage grid. These values are scenario costs per installed MW, with no claim of site-specific settlement revenue.

The v17 historical evidence map is `REPRODUCIBILITY_V17.md`; its itemized review register is `REVIEW_ACTION_REGISTER_V17.md`. Current additions and two independent review responses are indexed in `RELEASE_V23.md` and `docs/V23_REVIEW_RESPONSE.md`. The public repository separates measurement, synthetic confirmation, storage, weather and processed-data populations so that a passing check in one population does not silently become a claim about another.

The earlier v19/v22 evidence is retained in the [v0.4.6 release](https://github.com/longjingpy/wind-power-event-protocol-audit/releases/tag/v0.4.6). The v0.5.0 release adds current manuscript sources, v23 result tables and the native draw.io exports; provider attribution and upstream data terms remain applicable.

The full raw-data-to-manuscript command is under integration. Aggregate reproduction and targeted experiment checks are reported separately from that outstanding end-to-end test.

## Version status

V13 sensitivity outputs remain as historical records. V14 replaces the sampling lag, matching objective/aggregation, weather timing/outcome coding and same-encoder transfer comparison; use the v14 summaries for current claims.

Project-authored code is MIT licensed. Original data and upstream software keep their provider terms.
