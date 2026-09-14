"""Continuous-time forecast and storage study; no event-subset time compression.

TimesNet upstream: Wu et al., ICLR 2023, arXiv:2210.02186, forecasting head.
Weighted training is a study-defined ablation, not a published new algorithm.
Only training ramp labels set weights. Test future power never becomes a feature.
Economic rates are inherited illustrative scenarios, not measured market tariffs.
"""
from pathlib import Path
from types import SimpleNamespace
import argparse
import copy
import json
import time
import sys
import numpy as np
import pandas as pd
import torch
from torch import nn

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/real_decision_v9';L=24;H=2;DT=.5
SCENARIOS={'low':(150.,40.),'base':(300.,80.),'high':(600.,160.)}


def load_farm(site, power_policy):
    paths=sorted((ROOT/'data/event_clean_v2'/site).glob('*.csv.gz'))
    paths=[p for p in paths if 'unmatched' not in p.name and 'conflict' not in p.name]
    cols=[]
    for p in paths:
        d=pd.read_csv(p,usecols=lambda c:c in ['timestamp_start_utc','power_kw','usable_power','observations','native_count','rated_power_kw'])
        t=pd.to_datetime(d.timestamp_start_utc,utc=True)
        if t.duplicated().any():raise ValueError(f'duplicate {p}')
        if power_policy=='legacy_nonnegative':
            valid=d.usable_power.astype(str).str.lower().isin(['true','1'])
        else:
            early=d.power_kw.iloc[:int(.6*len(d))].quantile(.995)
            scale=float(d.rated_power_kw.iloc[0]) if 'rated_power_kw' in d else float(early)
            obs=d.observations.eq(30) if 'observations' in d else d.native_count.eq(2)
            valid=obs & np.isfinite(d.power_kw) & d.power_kw.between(-.05*scale,1.2*scale)
        cols.append(pd.Series(d.power_kw.where(valid).to_numpy(),index=t,name=p.stem))
    d=pd.concat(cols,axis=1).sort_index();d=d.reindex(pd.date_range(d.index.min(),d.index.max(),freq='30min'))
    # A fixed fleet: all included turbine observations are needed for each total.
    farm=d.sum(axis=1,min_count=len(cols))
    return farm,{'turbines':len(cols),'total_grid_rows':len(farm),'complete_fleet_rows':int(farm.notna().sum()),'start':str(farm.index.min()),'end':str(farm.index.max())}


def dataset(y,lo,hi):
    xs=[];ys=[];ids=[]
    for j in range(lo+L-1,hi-H):
        seg=y[j-L+1:j+H+1]
        if not np.isfinite(seg).all():continue
        xs.append(y[j-L+1:j+1]);ys.append(y[j+H]);ids.append(j+H)
    return np.asarray(xs,np.float32),np.asarray(ys,np.float32),np.asarray(ids,int)


class Forecast(nn.Module):
    def __init__(self,name):
        super().__init__();self.name=name
        if name=='tcn':
            self.net=nn.Sequential(nn.Conv1d(1,24,3,padding=1),nn.GELU(),nn.Conv1d(24,24,3,padding=2,dilation=2),nn.GELU(),nn.Flatten(),nn.Linear(L*24,1))
        else:
            sys.path.insert(0,str(ROOT/'temp/tslib_official'))
            from models.TimesNet import Model
            cfg=SimpleNamespace(task_name='short_term_forecast',seq_len=L,label_len=0,pred_len=H,d_model=16,d_ff=32,e_layers=1,top_k=3,num_kernels=3,enc_in=1,c_out=1,embed='fixed',freq='h',dropout=.1)
            self.net=Model(cfg)

    def forward(self,x):
        if self.name=='tcn':return self.net(x[:,None,:]).squeeze(-1)
        return self.net(x[:,:,None],None,None,None)[:,-1,0]


def predict(m,x,device):
    m.eval();out=[]
    with torch.no_grad():
        for j in range(0,len(x),256):out.append(m(torch.tensor(x[j:j+256],device=device)).cpu().numpy())
    return np.concatenate(out)


def fit(name,seed,weighted,tr,va,ramp_q,epochs,device,site,weight_factor=3.0):
    torch.manual_seed(seed);rng=np.random.default_rng(seed);m=Forecast(name).to(device)
    opt=torch.optim.Adam(m.parameters(),lr=.001);best=float('inf');saved=None;bad=steps=0;logs=[]
    x,y,_=tr;vx,vy,_=va
    weights=1+float(weight_factor)*(np.abs(y-x[:,-1])>=ramp_q) if weighted else np.ones(len(x))
    for epoch in range(epochs):
        m.train();ix=rng.permutation(len(x));losses=[]
        for j in range(0,len(ix),256):
            idx=ix[j:j+256];xb=torch.tensor(x[idx],device=device);yb=torch.tensor(y[idx],device=device);w=torch.tensor(weights[idx],dtype=torch.float32,device=device)
            opt.zero_grad(set_to_none=True);loss=((m(xb)-yb).square()*w).sum()/w.sum()
            if not torch.isfinite(loss):raise ValueError('nonfinite loss')
            loss.backward();nn.utils.clip_grad_norm_(m.parameters(),1.);opt.step();steps+=1;losses.append(float(loss.detach()))
        val=float(np.mean((predict(m,vx,device)-vy)**2));logs.append({'epoch':epoch+1,'steps':steps,'train_objective':np.mean(losses),'validation_mse':val})
        if val<best-1e-7:best=val;saved=copy.deepcopy(m.state_dict());bad=0
        else:bad+=1
        if bad>=5 and epoch>=9:break
    m.load_state_dict(saved);mode='event_weighted' if weighted else 'mse'
    pd.DataFrame(logs).to_csv(OUT/f'train_{site}_{name}_{mode}_{seed}.csv',index=False)
    torch.save({'state_dict':saved,'ramp_q_train':ramp_q,'steps':steps},OUT/f'model_{site}_{name}_{mode}_{seed}.pt')
    return m,steps


def storage(residual_pu,p_mw,e_mwh,rates):
    """Causal-at-delivery ideal balancing; zero initial stock, no terminal credit."""
    eta=np.sqrt(.92);soc=0.;un=cur=th=0.
    for r in residual_pu:
        if not np.isfinite(r):continue  # retain stock through missing time; no fictitious flow
        if r>=0:
            c=min(r,p_mw,max(0.,(e_mwh-soc)/(eta*DT)));soc+=c*eta*DT;cur+=(r-c)*DT;th+=c*DT
        else:
            d=min(-r,p_mw,max(0.,soc*eta/DT));soc-=d/eta*DT;un+=(-r-d)*DT;th+=d*DT
        if not -1e-8<=soc<=e_mwh+1e-8:raise AssertionError('SOC violation')
    capital=(p_mw*1000*350+e_mwh*1000*1100)*len(residual_pu)*DT/8760
    variable=un*rates[0]+cur*rates[1]+th*25
    return {'cost_cny_per_normalized_mw':capital+variable,'capital_cny':capital,'variable_cny':variable,'shortfall_mwh_per_normalized_mw':un,'surplus_mwh_per_normalized_mw':cur,'throughput_mwh_per_normalized_mw':th,'terminal_soc_mwh':soc}


def main(args):
    OUT.mkdir(parents=True,exist_ok=True);torch.set_num_threads(2);device='cuda' if torch.cuda.is_available() else 'cpu';t0=time.monotonic()
    results=[];econ=[];meta={};candidates=[(0.,0.)]+[(p,p*h) for p in [.01,.02,.04,.08,.16] for h in [.5,1,2,4,8]]
    for site in ['pizhou','yandun']:
        series,site_meta=load_farm(site,args.power_policy);n=len(series);a=int(.6*n);b=int(.8*n)
        scale=float(series.iloc[:a].quantile(.995));y=series.to_numpy(float)/scale
        tr=dataset(y,0,a);va=dataset(y,a,b);te=dataset(y,b,n)
        meta[site]=site_meta|{'power_policy':args.power_policy,'scale_kw_training_q995':scale,'train':len(tr[1]),'validation':len(va[1]),'test':len(te[1]),'horizon_half_hours':H}
        if min(len(tr[1]),len(va[1]),len(te[1]))<100:
            meta[site]['status']='INSUFFICIENT_COMPLETE_FLEET_WINDOWS';continue
        ramp_q=float(np.quantile(np.abs(tr[1]-tr[0][:,-1]),.95));meta[site]['ramp_threshold_training_q95']=ramp_q
        specs=[('persistence','none',0)] + [(name,mode,seed) for name in args.models for mode in ['mse','event_weighted'] for seed in args.seeds]
        for name,mode,seed in specs:
            if name=='persistence':vpred=va[0][:,-1];tpred=te[0][:,-1];steps=0
            else:
                model,steps=fit(name,seed,mode=='event_weighted',tr,va,ramp_q,args.epochs,device,site)
                vpred=predict(model,va[0],device);tpred=predict(model,te[0],device)
            # Restrict to non-negative production without changing targets.
            vpred=np.maximum(vpred,0);tpred=np.maximum(tpred,0)
            for split,ds,pred in [('validation',va,vpred),('test',te,tpred)]:
                x,actual,ids=ds;err=np.abs(actual-pred);tail=np.abs(actual-x[:,-1])>=ramp_q
                for subset,mask in [('all',np.ones(len(err),bool)),('training_threshold_ramp',tail)]:
                    results.append({'site':site,'model':name,'training':mode,'seed':seed,'split':split,'subset':subset,'n':int(mask.sum()),'nmae_pct_train_scale':100*float(err[mask].mean()) if mask.any() else None,'optimizer_steps':steps})
                pd.DataFrame({'target_interval_start_utc':series.index[ids].astype(str),'forecast_issue_utc':(series.index[ids-H]+pd.Timedelta('30min')).astype(str),'actual_pu':actual,'forecast_pu':pred,'ramp_truth_for_evaluation_only':tail}).to_csv(OUT/f'forecast_{site}_{name}_{mode}_{seed}_{split}.csv',index=False)
            rv=np.full(b-a,np.nan);rv[va[2]-a]=va[1]-vpred
            rt=np.full(n-b,np.nan);rt[te[2]-b]=te[1]-tpred
            for scenario,rates in SCENARIOS.items():
                costs=[storage(rv,p,e,rates)['cost_cny_per_normalized_mw'] for p,e in candidates]
                j=min(range(len(costs)),key=lambda j:(costs[j],candidates[j][1],candidates[j][0]));p,e=candidates[j]
                result=storage(rt,p,e,rates);no=storage(rt,0,0,rates)
                econ.append({'site':site,'model':name,'training':mode,'seed':seed,'scenario':scenario,'p_mw_per_normalized_mw':p,'e_mwh_per_normalized_mw':e,'validation_selected_cost':costs[j],**result,'test_no_battery_cost':no['cost_cny_per_normalized_mw'],'test_saving_vs_own_no_battery':no['cost_cny_per_normalized_mw']-result['cost_cny_per_normalized_mw'],'calendar_test_intervals':len(rt),'observed_delivery_intervals':int(np.isfinite(rt).sum())})
            pd.DataFrame(results).to_csv(OUT/'forecast_metrics.csv',index=False);pd.DataFrame(econ).to_csv(OUT/'economic_results.csv',index=False)
            (OUT/'progress.json').write_text(json.dumps({'latest':f'{site}/{name}/{mode}/{seed}','runtime_seconds':time.monotonic()-t0,'metadata':meta},indent=2))
            print(site,name,mode,seed,'steps',steps,'sec',round(time.monotonic()-t0),flush=True)
    (OUT/'manifest.json').write_text(json.dumps({'status':'COMPLETE_SCENARIO_STUDY_NOT_MARKET_RETURN','sites':meta,'seeds':args.seeds,'models':args.models,'training_protocol':'weights 1 versus 1+3*training future ramp flag; identical features, no test oracle','time_contract':'30-minute interval means; issue after last input interval; target interval END H half-hours after issue','storage_selection':'validation only, 26 candidates including no-storage','storage_simulation':'zero initial energy, no terminal credit, actual residual balancing at delivery, missing timestamps retained','cost_scope':'illustrative CNY per 1-MW-normalized production scale, not observed site tariffs or installed nameplate','rate_parameters':{'annual_power_cny_kw':350,'annual_energy_cny_kwh':1100,'throughput_cny_mwh':25,'imbalance_surplus_cny_mwh':SCENARIOS},'runtime_seconds':time.monotonic()-t0},indent=2))


def tests():
    y=np.arange(100,dtype=float);x,t,ids=dataset(y,0,100);assert np.all(t==x[:,-1]+H)
    y[50]=np.nan;x,t,ids=dataset(y,0,100);assert not ((ids>=50)&(ids<=50+L+H-1)).any()
    r=np.array([1.,-1.]);z=storage(r,0,0,(300,80));assert abs(z['cost_cny_per_normalized_mw']-190)<1e-9
    z=storage(np.array([-1.,-1.]),1,2,(300,80));assert z['shortfall_mwh_per_normalized_mw']==1.
    print('PASS: true forecast horizon, no gap-crossing windows, zero battery, zero initial energy')


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--test',action='store_true');ap.add_argument('--models',nargs='+',default=['tcn','timesnet']);ap.add_argument('--seeds',type=int,nargs='+',default=[41,42,43]);ap.add_argument('--epochs',type=int,default=20);ap.add_argument('--power-policy',choices=['signed_observed','legacy_nonnegative'],default='signed_observed');ap.add_argument('--output-dir',type=Path,default=ROOT/'outputs/real_decision_v9_signed');args=ap.parse_args();OUT=args.output_dir;tests() if args.test else main(args)
