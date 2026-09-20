"""Summarise current k=2/4/6 files with identical six-representation support."""
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'outputs/protocol_benchmark_v18/structure/r30_a0.2_q0.05_training_q995'
OUT=ROOT/'outputs/protocol_benchmark_v23';OUT.mkdir(parents=True,exist_ok=True)
REPS=['raw25','raw_pca6','statistics9','gaf_pca6','gaf_signed_pca6','gaf_bit6']
rows=[]
for site in ['pizhou','suining','yandun','lahaute','hill','greece','sdwpf','hill_2021']:
    for k in [2,4,6]:
        frames=[]
        available=[rep for rep in REPS if all((BASE/f'pizhou_{rep}_kmeans_k{k}_s{seed}_to_{site}_pairs.csv').exists() for seed in [41,42,43])]
        for rep in available:
            for seed in [41,42,43]:
                f=BASE/f'pizhou_{rep}_kmeans_k{k}_s{seed}_to_{site}_pairs.csv'
                if not f.exists():raise FileNotFoundError(f)
                d=pd.read_csv(f);d=d[d.split.eq('test')&d.block_days.eq(7)];frames.append(d)
        d=pd.concat(frames);good=d[d.pairs.ge(100)&d.informative_partition]
        sets=[set(zip(g.config_a,g.config_b)) for _,g in good.groupby(['representation','seed'])]
        assert len(sets)==3*len(available)
        shared=set.intersection(*sets);d=d[[tuple(a) in shared for a in d[['config_a','config_b']].to_numpy()]]
        by=d.groupby(['representation','config_a','config_b'],as_index=False)[['ari','nmi']].median()
        for rep,g in by.groupby('representation'):
            rows.append(dict(site=site,k=k,representation=rep,seeds=3,comparison_representations=len(available),supported_configuration_pairs=len(shared),
                median_ari=g.ari.median(),median_nmi=g.nmi.median(),ari_q25=g.ari.quantile(.25),ari_q75=g.ari.quantile(.75)))
d=pd.DataFrame(rows);d.to_csv(OUT/'cluster_count_common_support.csv',index=False)
print(d[d.representation.isin(['raw25','gaf_pca6','statistics9'])].to_string(index=False))
