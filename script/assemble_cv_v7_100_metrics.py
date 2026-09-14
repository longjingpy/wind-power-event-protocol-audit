"""Assemble metrics from completed 100-epoch label artifacts."""
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score
ROOT=Path(__file__).resolve().parents[1]; IN=ROOT/'outputs/dynamic_events_v6'; RUN=ROOT/'outputs/cv_benchmark_v7_100'; OUT=ROOT/'outputs/cv_benchmark_v7_100_complete'; OUT.mkdir(parents=True,exist_ok=True)
def main():
    d=pd.read_csv(IN/'candidate_intervals.csv.gz',dtype={'turbine':str}); d=d[d.representation_eligible.fillna(False)&d.split.eq('test')].reset_index(drop=True)
    pairs=pd.read_csv(IN/'test_pairs.csv.gz'); pos={e:i for i,e in enumerate(d.event_id)}; left=pairs.event_a.map(pos).to_numpy(); right=pairs.event_b.map(pos).to_numpy()
    groups={site:np.flatnonzero(d.site.eq(site).to_numpy()) for site in sorted(d.site.unique())}; seen=sorted(d.loc[d.site.eq('pizhou'),'turbine'].unique())[:26]; groups['pizhou_seen']=np.flatnonzero(d.site.eq('pizhou').to_numpy()&d.turbine.isin(seen).to_numpy()); groups['pizhou_unseen']=np.flatnonzero(d.site.eq('pizhou').to_numpy()&~d.turbine.isin(seen).to_numpy())
    pg={site:np.flatnonzero(pairs.site.eq(site).to_numpy()) for site in sorted(pairs.site.unique())}; pg['pizhou_seen']=np.flatnonzero(pairs.site.eq('pizhou').to_numpy()&pairs.turbine.isin(seen).to_numpy()); pg['pizhou_unseen']=np.flatnonzero(pairs.site.eq('pizhou').to_numpy()&~pairs.turbine.isin(seen).to_numpy())
    rows=[]
    for model in ['cnn_gaf','cnn_signed_gaf','tcn','transformer']:
        for seed in [41,42,43]:
            for k in [2,4,6]:
                f=RUN/f'labels_{model}_seed{seed}_k{k}.npz'
                if not f.exists(): raise FileNotFoundError(f)
                labels=np.load(f)['labels']
                for group,ix in groups.items(): rows.append({'representation':model,'seed':seed,'k':k,'group':group,'events':len(ix),'turbines':d.iloc[ix].turbine.nunique()})
                for group,ix in pg.items():
                    la,lb=labels[left[ix]],labels[right[ix]]
                    rows.append({'representation':model,'seed':seed,'k':k,'group':'pairs:'+group,'events':len(ix),'turbines':pairs.iloc[ix].turbine.nunique(),'nmi':normalized_mutual_info_score(la,lb),'ari':adjusted_rand_score(la,lb),'agreement':float(np.mean(la==lb))})
    out=pd.DataFrame(rows); out.to_csv(OUT/'cv_benchmark_metrics.csv',index=False)
    out[out.group.str.startswith('pairs:')].groupby(['representation','k','group'])[['nmi','ari','agreement']].agg(['mean','std','count']).to_csv(OUT/'cv_benchmark_summary.csv')
    (OUT/'manifest.json').write_text('{"status":"PASS_ASSEMBLED_100_EPOCH_LABELS","seeds":[41,42,43],"epochs":100,"source":"completed label artifacts"}')
    print(out[out.group=='pairs:pizhou'].query('k==4').groupby('representation')[['nmi','ari']].mean())
if __name__=='__main__': main()

