"""Common-duration support check for observed hierarchy effect modification.

Each duration stratum receives the same target mass in both groups, equal to
the smaller group count. No wind outcome selects support or stratum weights.
This is a descriptive standardization, not a causal intervention estimate.
"""
import json
import numpy as np
import pandas as pd
from physical_process_v26 import OUT,measures
from summarize_process_v26 import load_prediction
from wind_events.paired_probability import block_design


def main():
    locked=json.loads((OUT/'final_validation_lock.json').read_text());rows=[];support=[]
    for item in locked['choices']:
        if item['scope']!='native10':continue
        d,y,p=load_prediction(item['pipeline']);_,_,b=load_prediction(item['baseline'])
        pm,bm=measures(y,p),measures(y,b);comp=d.has_composite.to_numpy(bool)
        weights=np.zeros(len(d));durations=d.duration_hours.to_numpy(float)
        for duration in sorted(set(durations)):
            a=(durations==duration)&comp;c=(durations==duration)&~comp
            n1,n0=int(a.sum()),int(c.sum());mass=min(n1,n0)
            if mass:
                weights[a]=mass/n1;weights[c]=mass/n0
            support.append({'source':item['source'],'duration_hours':duration,'composite':n1,'primitive':n0,'common_mass':mass})
        for days in [3,7,14]:
            index,draw=block_design(d.time_start,days,2000);draw=np.vstack([np.ones((1,draw.shape[1])),draw])
            for task in ['mse','geometry_mse']:
                gains={}
                for label,mask in [('composite',comp),('primitive',~comp)]:
                    w=weights*mask
                    a=draw@np.bincount(index,weights=w*pm[task],minlength=draw.shape[1])
                    b_=draw@np.bincount(index,weights=w*bm[task],minlength=draw.shape[1])
                    gains[label]=100*(1-np.sqrt(np.divide(a,b_,out=np.full(len(draw),np.nan),where=b_>0)))
                gains['composite_minus_primitive']=gains['composite']-gains['primitive']
                for label,v in gains.items():
                    lo,hi=np.nanquantile(v[1:],[.025,.975])
                    rows.append({'source':item['source'],'task':task,'population':label,'block_days':days,
                        'gain_pct_or_pp':v[0],'low':lo,'high':hi,'valid_draws':int(np.isfinite(v[1:]).sum()),
                        'supported_events':int((weights>0).sum()),'support_rule':'identical physical duration only; outcome-blind weights'})
    pd.DataFrame(rows).to_csv(OUT/'duration_standardized_intervals.csv',index=False)
    pd.DataFrame(support).to_csv(OUT/'duration_standardized_support.csv',index=False)
    print(pd.DataFrame(rows).query('block_days==7').to_string(index=False))


if __name__=='__main__':main()
