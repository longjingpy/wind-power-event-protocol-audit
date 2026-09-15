"""Policy-capacity storage audit with validation-selected online controls and an oracle bound."""
from pathlib import Path
from itertools import product
import json
import numpy as np
import pandas as pd
from scipy.optimize import linprog
from scipy.sparse import coo_matrix

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"outputs/real_decision_v9_signed"
OUT=ROOT/"outputs/storage_policy_v15"
DT=.5
ETA=np.sqrt(.92)
LIFE=10
DISCOUNT=.08
CRF=DISCOUNT*(1+DISCOUNT)**LIFE/((1+DISCOUNT)**LIFE-1)
SCENARIOS=[(name,short,surplus,tail) for name,short,surplus in
           [("low",150.,40.),("base",300.,80.),("high",600.,160.)]
           for tail in [0.,1000.,5000.]]

def capital(power,energy,hours):
    # Assumed upfront investment, converted to annual equivalent plus fixed O&M.
    upfront=350*1000*power+1100*1000*energy
    return upfront*(CRF+.02)*hours/8760

def online(residual,power,energy,reserve=0.,critical=.2):
    soc=.5*energy; start=soc; lower=.1*energy;upper=.9*energy
    short=surplus=throughput=tail=0.; min_soc=soc;max_soc=soc
    for value in residual:
        if not np.isfinite(value):continue
        charge=discharge=0.
        if value>=0:
            charge=min(value,power,max(upper-soc,0)/(ETA*DT))
            soc+=ETA*DT*charge
        else:
            floor=lower+reserve*(upper-lower) if -value<critical else lower
            discharge=min(-value,power,max(soc-floor,0)*ETA/DT)
            soc-=DT*discharge/ETA
        remaining=value-charge+discharge
        short+=max(-remaining,0)*DT;surplus+=max(remaining,0)*DT
        tail+=max(abs(remaining)-critical,0)*DT
        throughput+=(charge+discharge)*DT
        min_soc=min(min_soc,soc);max_soc=max(max_soc,soc)
    assert min_soc>=lower-1e-8 and max_soc<=upper+1e-8
    return {"shortfall_mwh":short,"surplus_mwh":surplus,"throughput_mwh":throughput,
            "tail_mwh":tail,"inventory_draw_mwh":start-soc,"initial_soc_mwh":start,
            "terminal_soc_mwh":soc}

def price(state,short,surplus,tail,inventory=300.):
    return state["shortfall_mwh"]*short+state["surplus_mwh"]*surplus+state["throughput_mwh"]*25+state["tail_mwh"]*tail+state["inventory_draw_mwh"]*inventory

def oracle(residual,power,energy,short,surplus,tail,critical=.2):
    # Perfect-information lower bound, not a deployable controller.
    r=np.nan_to_num(residual,nan=0.); n=len(r); u=np.maximum(-r,0);v=np.maximum(r,0)
    width=5*n+1; c=np.zeros(width); c[:n]=DT*(25-surplus);c[n:2*n]=DT*(25-short)
    c[3*n]= -300.;c[3*n+1:]=DT*tail
    rr=[];cc=[];vv=[]
    for i in range(n):
        rr.extend([i]*4);cc.extend([i,n+i,2*n+i,2*n+i+1]);vv.extend([-ETA*DT,DT/ETA,-1,1])
    rr.append(n);cc.append(2*n);vv.append(1)
    aeq=coo_matrix((vv,(rr,cc)),shape=(n+1,width)).tocsr()
    beq=np.zeros(n+1);beq[-1]=.5*energy
    ir=[];jc=[];vals=[];bub=np.r_[critical-u,critical-v]
    for i in range(n):
        ir.extend([i,i,n+i,n+i]);jc.extend([n+i,3*n+1+i,i,4*n+1+i]);vals.extend([-1,-1,-1,-1])
    aub=coo_matrix((vals,(ir,jc)),shape=(2*n,width)).tocsr()
    bounds=[(0,min(power,x)) for x in v]+[(0,min(power,x)) for x in u]+[(.1*energy,.9*energy)]*(n+1)+[(0,None)]*(2*n)
    fit=linprog(c,A_ub=aub,b_ub=bub,A_eq=aeq,b_eq=beq,bounds=bounds,method="highs")
    if not fit.success:raise RuntimeError(fit.message)
    constant=DT*(u.sum()*short+v.sum()*surplus)+.5*energy*300
    return {"operating_cost":float(fit.fun+constant),"success":True,"variables":width}

def load_pair(site,model,training,seed,metadata):
    spec=metadata["sites"][site]; total=spec["total_grid_rows"]; a=int(.6*total);b=int(.8*total)
    clock=pd.date_range(pd.Timestamp(spec["start"]),periods=total,freq="30min")
    capacity=87.45 if site=="pizhou" else 200.5
    scale=spec["scale_kw_training_q995"]/1000
    output={}
    for split,lo,hi in [("validation",a,b),("test",b,total)]:
        table=pd.read_csv(SRC/f"forecast_{site}_{model}_{training}_{seed}_{split}.csv")
        stamp=pd.to_datetime(table.target_interval_start_utc,utc=True)
        assert not stamp.duplicated().any()
        series=pd.Series((table.actual_pu-table.forecast_pu).to_numpy()*scale,index=stamp)
        output[split]=series.reindex(clock[lo:hi]).to_numpy()
    return capacity,output

def main():
    meta=json.loads((SRC/"manifest.json").read_text())
    rows=[];selected=[];bounds=[]
    capacities=[(0.,0.)]+[(p,h) for p in [.05,.10,.20] for h in [1.,2.,4.]]
    for site,model,training,seed in product(["pizhou","yandun"],["tcn","timesnet"],["mse","event_weighted"],[41,42,43]):
        nameplate,period=load_pair(site,model,training,seed,meta)
        states={}
        for fraction,duration in capacities:
            power=fraction*nameplate;energy=power*duration
            for reserve in [0.,.25,.5]:
                for split,r in period.items():
                    state=online(r,power,energy,reserve,critical=.2*nameplate)
                    states[fraction,duration,reserve,split]=state
        for rate_name,short,surplus,tail in SCENARIOS:
            for fraction,duration in capacities:
                valid=[(price(states[fraction,duration,reserve,"validation"],short,surplus,tail),reserve) for reserve in [0.,.25,.5]]
                _,reserve=min(valid)
                state=states[fraction,duration,reserve,"test"]
                op=price(state,short,surplus,tail)
                cap=capital(fraction*nameplate,fraction*nameplate*duration,len(period["test"])*DT)
                row=dict(site=site,model=model,training=training,seed=seed,price_case=rate_name,
                         shortfall_price=short,surplus_price=surplus,tail_premium=tail,
                         storage_fraction=fraction,duration_h=duration,reserve=reserve,
                         nameplate_mw=nameplate,power_mw=fraction*nameplate,energy_mwh=fraction*nameplate*duration,
                         calendar_h=len(period["test"])*DT,observed_h=np.isfinite(period["test"]).sum()*DT,
                         operating_cny_per_installed_mw=op/nameplate,capital_cny_per_installed_mw=cap/nameplate,
                         total_cny_per_installed_mw=(op+cap)/nameplate,
                         **{k:v/nameplate for k,v in state.items()})
                rows.append(row)
            for regime in ["unconstrained","at_least_10pct_2h"]:
                valid=[]
                for fraction,duration in capacities:
                    if regime=="at_least_10pct_2h" and (fraction<.10 or duration<2):continue
                    for reserve in [0.,.25,.5]:
                        op=price(states[fraction,duration,reserve,"validation"],short,surplus,tail)
                        cost=op+capital(fraction*nameplate,fraction*nameplate*duration,len(period["validation"])*DT)
                        valid.append((cost,fraction,duration,reserve))
                _,fraction,duration,reserve=min(valid)
                state=states[fraction,duration,reserve,"test"]
                cost=price(state,short,surplus,tail)+capital(fraction*nameplate,fraction*nameplate*duration,len(period["test"])*DT)
                selected.append(dict(site=site,model=model,training=training,seed=seed,price_case=rate_name,
                          tail_premium=tail,regime=regime,fraction=fraction,duration_h=duration,reserve=reserve,
                          test_cny_per_installed_mw=cost/nameplate))
        for case,short,surplus,tail in [("base",300.,80.,0.),("high",600.,160.,0.)]:
            result=oracle(period["test"],.10*nameplate,.20*nameplate,short,surplus,tail,.2*nameplate)
            feasible=price(states[.10,2.,0.,"test"],short,surplus,tail)
            assert result["operating_cost"]<=feasible+1e-4*nameplate
            bounds.append(dict(site=site,model=model,training=training,seed=seed,case=case,
                               oracle_operating_cny_per_installed_mw=result["operating_cost"]/nameplate,
                               online_operating_cny_per_installed_mw=feasible/nameplate))
        print(site,model,training,seed,"complete",flush=True)
    OUT.mkdir(parents=True,exist_ok=True)
    pd.DataFrame(rows).to_csv(OUT/"capacity_price_surface.csv",index=False)
    pd.DataFrame(selected).to_csv(OUT/"validation_selected_designs.csv",index=False)
    pd.DataFrame(bounds).to_csv(OUT/"oracle_bounds.csv",index=False)
    protocol={"policy_benchmark":{"power_fraction":.1,"duration_h":2,"meaning":"historical Jiangsu policy scenario, not a universal current obligation"},
       "efficiency":.92,"soc_fraction_bounds":[.1,.9],"initial_soc_fraction":.5,"terminal_energy_value_cny_mwh":300,
       "capital_assumptions":{"power_cny_kw_upfront":350,"energy_cny_kwh_upfront":1100,"life_years":LIFE,"discount":DISCOUNT,"crf":CRF,"fixed_om_fraction":.02},
       "price_scope":"Declared shortfall/surplus scenarios; severe-deviation premiums are sensitivity parameters, not observed site tariffs",
       "critical_deviation_fraction":.2,"controller":"delivery-time deviation following with validation-selected energy reserve",
       "oracle":"perfect-information lower bound only","units":"CNY per installed MW over the complete test calendar",
       "pizhou_capacity_basis":"provided data/real filename records 87.45MW","yandun_capacity_basis":"sum machine_meta rated_power = 200500kW"}
    (OUT/"protocol.json").write_text(json.dumps(protocol,indent=2))
    print(pd.DataFrame(rows).query("storage_fraction==.1 and duration_h==2 and tail_premium==0 and price_case=='base'").groupby(["site","model","training"]).total_cny_per_installed_mw.mean())
if __name__=="__main__":main()
