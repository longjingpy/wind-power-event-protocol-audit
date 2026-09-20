"""Reproduce all point alphas from anonymous window-level class counts."""
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'outputs/protocol_benchmark_v25/ai_reference'
if not BASE.exists():BASE=ROOT/'results/protocol_benchmark_v25/ai_reference'


def alpha_counts(counts):
    n_i=counts.sum(axis=1);keep=n_i>=2
    counts,n_i=counts[keep],n_i[keep];total=n_i.sum()
    observed=((n_i*n_i-(counts*counts).sum(axis=1))/(n_i-1)).sum()/total
    marginal=counts.sum(axis=0)
    expected=(total*total-(marginal*marginal).sum())/(total*(total-1))
    return 1-observed/expected


def main():
    data=pd.read_csv(BASE/'alpha_reproduction_counts.csv')
    expected=pd.read_csv(BASE/'agreement_intervals.csv')
    for panel,sources in [('human3',['human']),('AI7',['AI']),('mixed10',['human','AI'])]:
        for field in ['event_presence','morphology']:
            d=data[data.source_type.isin(sources)&data.field.eq(field)]
            counts=d.pivot_table(index='window_id',columns='category',values='count',aggfunc='sum',fill_value=0).to_numpy(float)
            actual=alpha_counts(counts)
            ref=expected[expected.population.eq(panel)&expected.field.eq(field)&expected.block_days.eq(7)].alpha.iloc[0]
            np.testing.assert_allclose(actual,ref,atol=1e-12)
            print(panel,field,f'{actual:.12f}')


if __name__=='__main__':main()
