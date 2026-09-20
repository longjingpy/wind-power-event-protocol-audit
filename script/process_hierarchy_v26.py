"""Paired effect modification by the pre-existing power-event hierarchy."""
import json
import numpy as np
import pandas as pd
from physical_process_v26 import OUT,measures
from summarize_process_v26 import load_prediction
from wind_events.paired_probability import block_design


def conditional_gains(index,weights,candidate,baseline,mask):
    numerator=weights@np.bincount(index[mask],weights=candidate[mask],minlength=weights.shape[1])
    denominator=weights@np.bincount(index[mask],weights=baseline[mask],minlength=weights.shape[1])
    ratio=np.divide(numerator,denominator,out=np.full(len(weights),np.nan),where=denominator>0)
    return 100*(1-np.sqrt(ratio))


def main():
    lock=json.loads((OUT/'final_validation_lock.json').read_text());rows=[]
    for item in lock['choices']:
        if item['scope']!='native10':continue
        events,y,p=load_prediction(item['pipeline']);_,_,b=load_prediction(item['baseline'])
        pm,bm=measures(y,p),measures(y,b);composite=events.has_composite.to_numpy(bool)
        for days in [3,7,14]:
            index,weights=block_design(events.time_start,days,2000)
            both=np.vstack([np.ones((1,weights.shape[1])),weights])
            for task in ['mse','geometry_mse']:
                comp=conditional_gains(index,both,pm[task],bm[task],composite)
                primitive=conditional_gains(index,both,pm[task],bm[task],~composite)
                for label,v,n in [('composite',comp,int(composite.sum())),('primitive_only',primitive,int((~composite).sum())),
                                  ('composite_minus_primitive',comp-primitive,len(events))]:
                    lo,hi=np.nanquantile(v[1:],[.025,.975])
                    rows.append({'source':item['source'],'population':label,'task':task,'events':n,'block_days':days,
                        'occupied_farm_blocks':weights.shape[1],'gain_pct_or_pp':v[0],'low':lo,'high':hi,
                        'valid_draws':int(np.isfinite(v[1:]).sum()),
                        'subset_rule':'power-catalog composite flag; no wind-outcome selection'})
    result=pd.DataFrame(rows);result.to_csv(OUT/'hierarchy_intervals.csv',index=False)
    print(result[result.block_days.eq(7)].to_string(index=False))


if __name__=='__main__':main()
