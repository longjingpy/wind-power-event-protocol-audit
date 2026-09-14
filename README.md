# Wind-power event protocol audit

Initial public release v0.1.0 for **Measuring transferable wind-power dynamics with explicit event protocols**.

This initial package contains selected analysis interfaces, tests and aggregate tables. It supports local reproduction of the two aggregate representation comparisons. Full raw-data-to-manuscript reproduction remains under preparation.

## Reproduce the included comparisons

Use Python 3.12, install `requirements.txt`, then run from this repository:

```bash
python script/reproduce_aggregate_figures.py
python -m pytest -q tests
```

Outputs are written to `reproduced/`. Other scripts retain paths to the full research workspace and require additional input archives.

## Data access

SDWPF: doi:10.6084/m9.figshare.24798654 (CC BY 4.0).
Greek monitoring archive: doi:10.5281/zenodo.14546480.
La Haute Borne and Hill of Towie are public-source archives.
The current release contains aggregate results for Pizhou, Suining and Yandun. Raw-data redistribution scope is being confirmed with the data provider.

## License

Project-authored code is MIT licensed. Original dataset and third-party code rights remain with their providers.
