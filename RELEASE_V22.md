# v22 measurement and decision release

This release accompanies the protocol-aware wind-power event manuscript. It adds the reproducible v22 representation audit, four-site 30/60-minute sampling comparison, corrected settlement-capability frontier, and the figure data used in the revised manuscript.

Included result tables:

- `results/protocol_benchmark_v21/representation_audit/`: raw25 versus raw/PCA6 full-precision differences, training compression diagnostics and test partition comparisons.
- `results/protocol_benchmark_v22/sampling/`: La Haute Borne and Hill of Towie 30/60-minute sampling comparison, with Greece and Yandun tables retained in the manuscript evidence.
- `results/protocol_benchmark_v22/economics/`: complete-day capability replay, gross debit and signed settlement accounting, and 3/7/14-day block intervals.
- `results/protocol_benchmark_v22/figures/`: plotting tables for the revised vector figures.
- `scripts/*_v22.py`: the deterministic figure, sampling and accounting entry points.

The economic capability replay uses realised half-hour power as an ex-post correction input, prices daily terminal-inventory restoration, and reports gross exposure separately from signed settlement cost. It is a capability benchmark for an installed battery, not a claim that future power or future prices are available to a forecast-time controller.

Original public-data licences and attribution requirements remain in force. The release does not relicense upstream ERA5, NOAA, SDWPF, Greek, La Haute Borne, Hill of Towie or SMARTEOLE data.
