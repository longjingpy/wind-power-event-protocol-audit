# Wind-power event protocol audit

Open study-data release v0.2.0 for **Measuring transferable wind-power dynamics with explicit event protocols**.

## Study data

All wind-event study data are authorized for release by the data provider (15 September 2026). The release assets contain native Chinese SCADA, seven-farm analysis inputs, weather data, the event catalogue and human labels. Original public source terms remain applicable.

Download the ZIP assets from [v0.2.0](https://github.com/longjingpy/wind-power-event-protocol-audit/releases/tag/v0.2.0) and extract them at the repository root. Relative input paths are retained. `data_manifest.json` lists members, sizes and SHA-256 checksums.

The raw Chinese archive includes Pizhou, Suining and Yandun. Public originals and metadata are attributed through SDWPF (10.6084/m9.figshare.24798654), Greece (10.5281/zenodo.14546480), La Haute Borne and Hill of Towie source records. Unrelated GNSS projects, private attachments and corrupt download copies are excluded.

## Verified entry points

With Python 3.12 and `requirements.txt`:

```bash
python script/reproduce_aggregate_figures.py
python -m pytest -q tests
```

Research scripts additionally require `requirements-research.txt`. Current corrections are in `event_matching_v14.py`, `yandun_sampling_v14.py`, `weather_adjusted_v14.py` and `external_transfer_v14.py`. These scripts retain the full research workspace paths.

The v16 controlled HPO record is under `results/detection_hpo_v16/`. It covers three validation-selected candidates for each neural model, three training seeds, and four window candidates for the mean rule. Twelve selected checkpoints for TimesNet, KAN-AD, TCN-AE and Transformer-AE are under `models/detection_hpo_v16/`. Fresh post-selection results, paired intervals and CPU timing are in `results/detection_confirmation_v16/`. See `REPRODUCIBILITY_V16.md` for the tested checkpoint-inference command and for the distinction between an observed environment snapshot and a clean-install guarantee.

The storage-policy tables include the historical 10%-power/2-hour engineering benchmark, declared price scenarios and the complete conditional-advantage grid. These values are scenario costs per installed MW, with no claim of site-specific settlement revenue.

The full raw-data-to-manuscript command is under integration. Aggregate reproduction and targeted experiment checks are reported separately from that outstanding end-to-end test.

## Version status

V13 sensitivity outputs remain as historical records. V14 replaces the sampling lag, matching objective/aggregation, weather timing/outcome coding and same-encoder transfer comparison; use the v14 summaries for current claims.

Project-authored code is MIT licensed. Original data and upstream software keep their provider terms.
