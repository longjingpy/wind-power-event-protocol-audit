"""Synchronize the canonical manuscript, supplement and current evidence map."""
from pathlib import Path
import json,re

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / 'manuscript/applied_energy'


def main():
    body = (DOC / 'manuscript_body.md').read_text(encoding='utf-8')
    body = body.replace('The processed data, v22 experiment tables, editable workflow source and reproducibility scripts are available in the [v0.4.6 study release](https://github.com/longjingpy/wind-power-event-protocol-audit/releases/tag/v0.4.6).',
        'Processed-data access, the current v18–v23 result tables, editable workflow source, manuscript sources and reproducibility scripts are available in the [v0.5.0 study release](https://github.com/longjingpy/wind-power-event-protocol-audit/releases/tag/v0.5.0).')
    def caption(match):
        relative = match.group(1)
        source = ROOT / 'manuscript' / relative
        text = source.with_name(source.stem+'_caption.md').read_text(encoding='utf-8').strip()
        return '!['+text+']('+relative+')'
    body = re.sub(r'!\[[^\]]*\]\((figures_v22/[^)]+)\)', caption, body)
    (DOC / 'manuscript_body.md').write_text(body, encoding='utf-8')
    methods = (DOC / 'supplementary_methods.md').read_text(encoding='utf-8')
    methods = methods.replace('## S18. v18 output and reproducibility map', '## S18. Output and reproducibility map')
    start = methods.index('The v19 manifest')
    stop = methods.index('\n\n## S19.', start)
    methods = methods[:start] + (
        'The v19 manifest records the multirater and SMARTEOLE stages. Current v21/v22 representation, sampling and economic tables remain under their versioned output folders. The v23 extension adds `outputs/protocol_benchmark_v23/cluster_count_common_support.csv` and the `many_to_many/` directory: `configuration_pairs.csv`, `site_summary.csv`, `verification.json` and `coverage_aggregation_reconciliation.csv`. The last table verifies the equal-configuration versus pooled-coverage distinction against the original one-to-one counts. Supplementary Tables S57–S58 and Fig. S1 summarize these additions. The public v0.5.0 release mirrors aggregate outputs under `results/`, contains the current manuscript and editable Fig. 1, and links the de-identified processed-data release. The detailed local component ledger retains internal event clocks; public tables use aggregate counts. The SMARTEOLE support diagnostic remains `outputs/protocol_benchmark_v19/smarteole/diagnostic/report.json`, with the supported-row median, all-row and pair-weighted summaries.'
    ) + methods[stop:]
    (DOC / 'supplementary_methods.md').write_text(methods, encoding='utf-8')
    full = (DOC / 'supplementary_complete.md').read_text(encoding='utf-8')
    tables = full[full.index('## Supplementary result tables'):]
    (DOC / 'supplementary_complete.md').write_text(methods.rstrip()+'\n\n'+tables, encoding='utf-8')
    protocol_path = ROOT / 'outputs/protocol_benchmark_v23/many_to_many/protocol.json'
    protocol = json.loads(protocol_path.read_text())
    protocol.update(support='At least 100 connected components; descriptive count, not a filter on site summaries.',
                    weighting='Each component one vote across all configuration pairs; site coverage pools node counts.',
                    coverage_reconciliation='coverage_aggregation_reconciliation.csv: all 1088 original primitive counts agree exactly.')
    protocol_path.write_text(json.dumps(protocol, indent=2))


if __name__ == '__main__':
    main()
