"""Summarize completed factorial physical probes and source-separated ratings."""
from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'outputs/protocol_benchmark_v25'
PHYS=BASE/'polarity'


def main():
    folders=[PHYS/name for name in ['era5_pizhou','era5_suining','era5_yandun','era5_lahaute','era5_hill','lidar_T11','lidar_T07','smarteole']]
    scores=pd.concat([pd.read_csv(p/'scores.csv') for p in folders],ignore_index=True)
    effects=pd.concat([pd.read_csv(p/'paired.csv') for p in folders],ignore_index=True)
    assert scores.dataset.nunique()==8 and effects.dataset.nunique()==8
    scores.to_csv(PHYS/'all_scores.csv',index=False);effects.to_csv(PHYS/'all_paired.csv',index=False)
    main=scores[scores.block_days.eq(7)&scores.model.isin(['scalar','scalar_g5','scalar_bit','scalar_g5_bit'])]
    main.to_csv(PHYS/'factorial_primary.csv',index=False)
    increments=effects[effects.block_days.eq(7)&effects.candidate.eq('scalar_g5_bit')&effects.reference.isin(['scalar','scalar_g5'])]
    increments.to_csv(PHYS/'primary_increments.csv',index=False)
    flips=[];noise=[]
    for folder in folders:
        if (folder/'anchor_flip.csv').exists():
            flips.append(pd.read_csv(folder/'anchor_flip.csv').assign(dataset=folder.name))
            noise.append(pd.read_csv(folder/'noise_scores.csv').assign(dataset=folder.name))
    pd.concat(flips,ignore_index=True).to_csv(PHYS/'anchor_noise_summary.csv',index=False)
    pd.concat(noise,ignore_index=True).to_csv(PHYS/'noise_summary.csv',index=False)
    print('PRIMARY FACTORIAL DIRECTION AUROC')
    print(main[main.metric.eq('direction_auroc')].pivot(index='dataset',columns='model',values='estimate').to_string())
    print('PAIRED INCREMENTS')
    print(increments[increments.metric.isin(['log_loss','direction_auroc'])][['dataset','reference','metric','gain','low','high','events','occupied_blocks']].to_string(index=False))
    pd.DataFrame({'check':['all_8_populations','same_event_count_all_arms'],
        'passed':[True,all(len(g.events.unique())==1 for _,g in scores.groupby('dataset'))]}).to_csv(BASE/'completion_checks.csv',index=False)
    print('ANCHOR FLIPS AT NOISE RATIO .05')
    print(pd.concat(flips).query('noise_ratio==.05').groupby('dataset').bit_flip_fraction.agg(['mean','min','max']).to_string())
    redundancy=[]
    for path in PHYS.glob('*/anchor_support.parquet'):
        a=pd.read_parquet(path);nonzero=a.endpoint_sign.ne(0)
        redundancy.append({'dataset':path.parent.name,'events':len(a),'nonzero_endpoint_events':int(nonzero.sum()),
            'opposite_to_endpoint_fraction':float(a.loc[nonzero,'anchor_sign'].ne(a.loc[nonzero,'endpoint_sign']).mean()),
            'zero_endpoint_fraction':float((~nonzero).mean())})
    pd.DataFrame(redundancy).to_csv(PHYS/'anchor_endpoint_redundancy.csv',index=False)
    print('ANCHOR VERSUS ENDPOINT SIGN')
    print(pd.DataFrame(redundancy).to_string(index=False))


if __name__=='__main__':main()
