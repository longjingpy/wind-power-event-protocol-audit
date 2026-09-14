# Wind-power event protocol audit

This repository contains the open analysis code and aggregate result tables for:

**Measuring transferable wind-power dynamics with explicit event protocols**

The release contains the detector contract, matching and representation interfaces, figure builders, tests, and aggregate summaries. Proprietary Pizhou, Suining and Yandun SCADA rows remain outside the release. Public archives are downloaded from their original sources by the documented scripts.

## Reproduction

The primary environment is Ubuntu 24.04 with Python 3.12. Install the pinned dependencies from the project lock file, then run:

```bash
python script/plot_manuscript_extensions_v11.py
python script/redraw_figures_v12.py
python -m pytest -q tests/test_user_label_clock_v9.py
```

The aggregate CSV files identify the evaluation population, sampling unit and metric used in each table and figure. The manuscript separates measurement results, observational associations and causal identification questions.

## Data

SDWPF is openly available from Figshare (doi:10.6084/m9.figshare.24798654; CC BY 4.0). The Greek monitoring archive is available from Zenodo (doi:10.5281/zenodo.14546480). La Haute Borne and Hill of Towie are public-source archives. Private SCADA records are represented by aggregate tables only.

## License

Code is released under the MIT License. Dataset rights remain with their original providers.
