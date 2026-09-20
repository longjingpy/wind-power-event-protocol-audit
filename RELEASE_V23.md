# v0.5.0: correspondence, definitions and current manuscript

This release adds the completed split/merge overlap experiment across seven
primary archives and the reserved Hill 2021 period, with five correspondence
arms and 5,440 configuration rows. Primitive intervals yield 6.6–9.5% non-one-
to-one components; including compound V/inverted-V intervals yields
19.8–36.7%. These are measurement-support components, distinct from independent
weather processes. Full configuration and site summaries are included.

The release also provides the actual k=2/4/6 common-support sensitivity scope,
current manuscript and supplement, native draw.io Figure 1, and corrected
figure exports. Definitions distinguish supported event/configuration/component
pairs, full-field GASF reconstruction from compressed empirical encodings, and
the three economic scheduled positions. The S57/S58 tables and supplementary
overlap figure are integrated into the existing supplement.

## Entry points

- `manuscript/applied_energy/main.pdf` and `supplementary.pdf`.
- `manuscript/figures_v22/fig01_workflow.drawio` and native PDF/SVG/PNG exports.
- `results/protocol_benchmark_v23/cluster_count_common_support.csv`.
- `results/protocol_benchmark_v23/many_to_many/`: configuration/site summaries,
  protocol, verification and exact reconciliation with original one-to-one counts.
- `results/protocol_benchmark_v22/economics/`: complete-day settlement capability
  and the corrected unique calendar count; monetary results are unchanged.
- `docs/V23_REVIEW_RESPONSE.md`: independent reviews and author responses.

The attached source packet is self-contained for manuscript typesetting.
Research-stage scripts retain the workspace `outputs/` layout. Re-running
catalogue-scale experiments additionally requires the corresponding processed
catalogues and frozen models; this release does not assert an untested one-command
raw-to-paper reproduction. Unit tests can be run from this checkout:

```bash
python -m pytest -q tests/test_overlap_graph_v23.py tests/test_protocol_v18.py tests/test_representation_v18.py tests/test_economics_v18.py tests/test_conditional_v18.py
```

The detailed local overlap-component ledger retains internal clocks. Public
tables aggregate those records; processed SCADA access remains through v0.3.0
under its identifier/clock policy. Authored code is MIT licensed. Original
provider data and third-party materials retain their own terms.
