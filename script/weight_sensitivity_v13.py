"""Sensitivity of event-weighted forecasting to the training weight."""
from pathlib import Path
import sys
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'script')); import real_forecast_economics_v9 as m
OUT=ROOT/'outputs/weight_sensitivity_v13'; m.OUT=OUT
def main():
    OUT.mkdir(parents=True,exist_ok=True); rows=[]; device='cuda' if __import__('torch').cuda.is_available() else 'cpu'
    for site in ['pizhou','yandun']:
        series,_=m.load_farm(site,'signed_observed'); n=len(series); a=int(.6*n); b=int(.8*n); scale=float(series.iloc[:a].quantile(.995)); y=series.to_numpy(float)/scale
        tr=m.dataset(y,0,a); va=m.dataset(y,a,b); te=m.dataset(y,b,n); ramp=float(np.quantile(np.abs(tr[1]-tr[0][:,-1]),.95))
        for factor in [0,1,2,4,8]:
            for seed in [41,42,43]:
                model,steps=m.fit('tcn',seed,factor>0,tr,va,ramp,20,device,site,weight_factor=factor)
                vp=m.predict(model,va[0],device); tp=m.predict(model,te[0],device); vp=np.maximum(vp,0);tp=np.maximum(tp,0)
                for split,ds,pred in [('validation',va,vp),('test',te,tp)]:
                    err=np.abs(ds[1]-pred); tail=np.abs(ds[1]-ds[0][:,-1])>=ramp
                    rows.append({'site':site,'factor':factor,'seed':seed,'split':split,'all_nmae_pct':100*err.mean(),'ramp_nmae_pct':100*err[tail].mean(),'ramp_n':int(tail.sum()),'optimizer_steps':steps})
                rv=np.full(b-a,np.nan);rv[va[2]-a]=va[1]-vp;rt=np.full(n-b,np.nan);rt[te[2]-b]=te[1]-tp
                for scenario,rates in m.SCENARIOS.items():
                    candidates=[(0,0)]+[(p,p*h) for p in [.01,.02,.04,.08,.16] for h in [.5,1,2,4,8]]
                    costs=[m.storage(rv,p,e,rates)['cost_cny_per_normalized_mw'] for p,e in candidates]; j=int(np.argmin(costs)); p,e=candidates[j]; test=m.storage(rt,p,e,rates); no=m.storage(rt,0,0,rates)
                    rows.append({'site':site,'factor':factor,'seed':seed,'split':'economics_'+scenario,'all_nmae_pct':np.nan,'ramp_nmae_pct':np.nan,'ramp_n':0,'optimizer_steps':steps,'selected_power':p,'selected_energy':e,'test_cost':test['cost_cny_per_normalized_mw'],'test_no_battery_cost':no['cost_cny_per_normalized_mw'],'test_saving':no['cost_cny_per_normalized_mw']-test['cost_cny_per_normalized_mw']})
                print(site,factor,seed,steps,flush=True)
    out=pd.DataFrame(rows);out.to_csv(OUT/'weight_sensitivity.csv',index=False);print(out[out.split.eq('test')].groupby(['site','factor'])[['all_nmae_pct','ramp_nmae_pct']].mean())
if __name__=='__main__':main()
