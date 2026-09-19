# v19 release candidate (local manifest only)

This file records the current v19 evidence bundle without claiming a public
GitHub release. It is a release-candidate checklist for the manuscript and for
the eventual repository archive.

## Verified remote state

The repository remote is
`https://github.com/longjingpy/wind-power-event-protocol-audit.git`.
The tags visible on the remote at the time of this record are `v0.1.0`,
`v0.2.0` and `v0.3.0`; the public processed-data entry point is
[v0.3.0](https://github.com/longjingpy/wind-power-event-protocol-audit/releases/tag/v0.3.0).
There is no remote `v19` or `v0.4.0` tag in this snapshot. This file therefore
does not present a local directory as an already published release.

## Local v19 evidence entry points

The machine-readable manifest is
`outputs/protocol_benchmark_v19/RELEASE_MANIFEST_V19.json`. The principal
protocol, validation and human-reference records are:

- `outputs/protocol_benchmark_v19/protocol.json`
- `outputs/protocol_benchmark_v19/v19_validation.json`
- `outputs/protocol_benchmark_v19/human_reference/agreement.json`
- `outputs/protocol_benchmark_v19/human_reference/detector_window_metrics.csv`
- `outputs/protocol_benchmark_v19/additional_partition_metrics/manifest.json`
- `outputs/protocol_benchmark_v19/economics/forecast_replay/protocol.json`
- `outputs/protocol_benchmark_v19/economics/online_battery/protocol.json`
- `docs/V19_CURRENT_EXECUTION.md`

The canonical manuscript and merged supplementary source are kept under
`manuscript/applied_energy/`. Their publication package must be rebuilt from
the current sources after the remaining text and figure review.

## Publication gates before a v19 GitHub release

1. Record the SMARTEOLE source licence or permission route; the Zenodo record
   used by the current analysis has an empty licence field.
2. Add the remaining independent annotation exports when they are received,
   without replacing the two byte-preserved exports already in the bundle.
3. Rebuild and visually review the manuscript and supplementary PDFs from the
   canonical sources.
4. Add the final figure data and source files, then create a release archive
   with a DOI or GitHub release URL. Until these gates are met, v19 remains a
   local candidate and v0.3.0 remains the only public processed-data release.

The candidate manifest is intentionally additive: it does not alter or revoke
the existing v0.3.0 release.
