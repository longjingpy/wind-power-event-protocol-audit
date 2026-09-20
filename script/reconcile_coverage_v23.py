"""Verify identical primitive populations and separate macro/pooled coverage.

Macro coverage weights each detector-configuration pair equally. Pooled
coverage weights by that side's eligible event count. Keeping both prevents
a change in aggregation from being interpreted as a matching effect.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs/protocol_benchmark_v23/many_to_many'
BASE = ROOT / 'outputs/protocol_benchmark_v18/structure/r30_a0.2_q0.05_training_q995'


def main():
    current = pd.read_csv(OUT / 'configuration_pairs.csv')
    current = current[current.arm.eq('primitive_iou50')]
    rows = []
    for site, now in current.groupby('site'):
        old = pd.read_csv(BASE / f'pizhou_raw25_kmeans_k4_s41_to_{site}_pairs.csv')
        old = old[old.split.eq('test') & old.block_days.eq(7)]
        joined = now.merge(old, on=['config_a', 'config_b'], suffixes=('_v23', '_v18'), validate='1:1')
        assert len(joined) == 136
        for a, b in [('left_n_v23', 'left_n_v18'), ('right_n_v23', 'right_n_v18'), ('one_to_one_pairs', 'pairs')]:
            np.testing.assert_array_equal(joined[a], joined[b])
        row = {'site': site, 'configuration_pairs': len(joined), 'counts_identical': True}
        for side in ['left', 'right']:
            row[f'macro_{side}_coverage'] = (joined.one_to_one_pairs / joined[f'{side}_n_v23']).mean()
            row[f'pooled_{side}_coverage'] = joined.one_to_one_pairs.sum() / joined[f'{side}_n_v23'].sum()
            np.testing.assert_allclose(row[f'macro_{side}_coverage'], joined[f'{side}_coverage_v18'].mean())
        rows.append(row)
    pd.DataFrame(rows).to_csv(OUT / 'coverage_aggregation_reconciliation.csv', index=False)
    report = {'status': 'PASS', 'populations': len(rows), 'configuration_pairs_checked': len(rows)*136,
              'same_eligible_counts_and_one_to_one_matches': True,
              'difference_source': 'Main table averages configuration-specific fractions; v23 site rows divide summed connected nodes by summed eligible nodes.',
              'left_right_order': 'Lexicographic configuration name; identical in both experiments.'}
    (OUT / 'coverage_reconciliation.json').write_text(json.dumps(report, indent=2))
    print(pd.DataFrame(rows).to_string(index=False))


if __name__ == '__main__':
    main()
