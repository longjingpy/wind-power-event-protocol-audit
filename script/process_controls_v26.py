"""Frozen-model controls for temporal order and event-to-curve correspondence.

Scalars and endpoint changes remain fixed. The two perturbations test different
relationships and are labelled separately; no perturbation selects a model.
"""
import json
import joblib
import numpy as np
import pandas as pd
from physical_process_v26 import OUT,datasets,measures,paired
from physical_calibration_v26 import calibrated_features


def main():
    locked=json.loads((OUT/'final_validation_lock.json').read_text());rows=[];scores=[]
    for choice in locked['choices']:
        if choice['scope']!='native10':continue
        record=choice['pipeline'];assert record['track']=='physical' and record['arm']=='level_delta17'
        name=record['dataset'];folder,d,x,s,y=datasets(name);branch=folder/'physical_calibration'
        train=d.split.eq('train').to_numpy();test=d.split.eq('test').to_numpy();meta=d[test].reset_index(drop=True)
        z=calibrated_features(folder,d,x,s)['level_delta17'][test]
        model=joblib.load(branch/'level_delta17.joblib');truth=y[test];clean=model.predict(z)
        clean_error=measures(truth,clean)
        amplitude_edges=np.quantile(np.abs(d.loc[train,'amplitude']),[1/3,2/3])
        amplitude_bins=np.digitize(np.abs(d.loc[test,'amplitude']),amplitude_edges)
        duration_bins=np.digitize(d.loc[test,'duration_hours'],[1.5,2.5,3.5])
        groups=pd.DataFrame({'direction':d.loc[test,'direction'].to_numpy(),'amplitude':amplitude_bins,'duration':duration_bins})
        for seed in [101,202,303]:
            rng=np.random.default_rng(seed);order=z.copy()
            for i in range(len(order)):
                order[i,28:43]=z[i,27+np.r_[rng.permutation(np.arange(1,16))]]
            # Last 17 columns are level differences, start/end unchanged.
            assert np.array_equal(order[:,:28],z[:,:28]) and np.array_equal(order[:,-1],z[:,-1])
            assignment=np.arange(len(z))
            for _,g in groups.groupby(['direction','amplitude','duration']):
                ix=g.index.to_numpy()
                if len(ix)>1:assignment[ix]=np.roll(ix,int(rng.integers(1,len(ix))))
            reassigned=z.copy();phase=np.linspace(0,1,17)
            original_chord=z[:,-1,None]*phase
            residual=z[:,27:]-original_chord
            reassigned[:,27:]=original_chord+residual[assignment]
            for control,values in [('within_event_order',order),('between_event_residual_reassignment',reassigned)]:
                pred=model.predict(values);m=measures(truth,pred)
                scores.append({'dataset':name,'control':control,'seed':seed,'events':len(z),
                    'wind_change_rmse_ms':np.sqrt(m['mse'].mean()),'geometry_rmse_ms':np.sqrt(m['geometry_mse'].mean()),
                    'reassigned_fraction':float((assignment!=np.arange(len(z))).mean()) if 'reassignment' in control else 1.})
                for task in ['mse','geometry_mse']:
                    rows.append({'dataset':name,'control':control,'seed':seed,'task':task,
                        **paired(meta.time_start,m[task],clean_error[task],7)})
    pd.DataFrame(scores).to_csv(OUT/'negative_control_scores.csv',index=False)
    pd.DataFrame(rows).to_csv(OUT/'negative_control_intervals.csv',index=False)
    print(pd.DataFrame(scores).groupby(['dataset','control'])[['wind_change_rmse_ms','geometry_rmse_ms']].mean().to_string())


if __name__=='__main__':main()
