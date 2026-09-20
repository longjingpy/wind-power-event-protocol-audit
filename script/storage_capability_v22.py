"""Settlement-period correction capability with closed daily inventories.

This is an ex-post capability benchmark: the controller receives the realised
half-hour average, which is not available at issue time. It does not establish
deployable real-time forecast gains. Daily terminal SOC equals initial SOC,
and every restoration action is settled. Gross debits are max(signed cost,0),
not the absolute total of purchase and sale legs. These quantities implement
the accounting identity in src/wind_events/economics.py.
"""
from pathlib import Path
import sys,json
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from wind_events.economics import Battery,planned_inventory_step,imbalance_cashflow
OUT=ROOT/'outputs/protocol_benchmark_v22/economics'
MODELS=['persistence','selected_weather','selected_weather_events','predicted_ramp_historical_events']

def legs(actual,schedule,buy,sell):
    signed=imbalance_cashflow(actual,schedule,buy,sell,.5)['net_imbalance_cost_gbp']
    return signed,np.maximum(signed,0),np.maximum(-signed,0)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    signed,debit,credit=legs(np.array([0,2,0,2]),np.ones(4),np.array([100,100,-100,-100]),np.array([100,100,-100,-100]))
    np.testing.assert_allclose(signed,[50,-50,-50,50]);np.testing.assert_allclose(debit,[50,0,0,50])
    days=[]
    max_terminal=max_soc_violation=0.
    for horizon in [1,2,4]:
        f=pd.read_parquet(ROOT/f'outputs/protocol_benchmark_v20/economics/calendar_{horizon}h.parquet')
        for split in ['validation','test']:
            frame=f[f.split.eq(split)].copy();frame['day']=pd.to_datetime(frame.target_start,utc=True).dt.floor('D')
            for day,d in frame.groupby('day'):
                d=d.sort_values('target_start')
                if len(d)!=48 or d.actual_mw.isna().any() or d.persistence.isna().any():continue
                actual=d.actual_mw.to_numpy();buy=d.systemBuyPrice.to_numpy();sell=d.systemSellPrice.to_numpy()
                if not np.isfinite(sell).all(): raise ValueError('Missing sell-side settlement price')
                if not np.allclose(buy,sell,atol=1e-12): raise ValueError('This public Elexon calendar is not the declared single-price experiment')
                for model in MODELS:
                    forecast=d[model].to_numpy();ready=d.feature_ready.to_numpy(bool)&np.isfinite(forecast)
                    schedule=np.where(ready,forecast,d.persistence.to_numpy())
                    pre_signed,pre_gross,pre_credit=legs(actual,schedule,buy,sell)
                    for fraction in [0,.05,.1,.2]:
                        battery=Battery(48.3*fraction,96.6*fraction);state=initial=.5*battery.energy_mwh
                        delivered=[];throughput=0.
                        for i in range(48):
                            step=planned_inventory_step(actual[i],schedule[i],state,battery,47-i,initial)
                            state=step['stored_mwh'];throughput+=step['throughput_mwh']
                            delivered.append(actual[i]+step['battery_export_mw'])
                            max_soc_violation=max(max_soc_violation,battery.minimum_fraction*battery.energy_mwh-state,state-battery.maximum_fraction*battery.energy_mwh)
                        max_terminal=max(max_terminal,abs(state-initial));assert abs(state-initial)<1e-7
                        post_signed,post_gross,post_credit=legs(np.array(delivered),schedule,buy,sell)
                        np.testing.assert_allclose(post_gross-post_credit,post_signed,atol=1e-8)
                        days.append(dict(split=split,day=day,horizon_hours=horizon,model=model,power_fraction=fraction,
                            power_mw=battery.power_mw,energy_mwh=battery.energy_mwh,intervals=48,
                            forecast_available_intervals=int(ready.sum()),gross_before_gbp=pre_gross.sum(),gross_after_gbp=post_gross.sum(),
                            credits_before_gbp=pre_credit.sum(),credits_after_gbp=post_credit.sum(),
                            signed_before_gbp=pre_signed.sum(),signed_after_gbp=post_signed.sum(),
                            schedule_deviation_before=np.abs(actual-schedule).mean()/48.3,
                            delivery_deviation_after=np.abs(np.array(delivered)-schedule).mean()/48.3,
                            throughput_mwh=throughput,terminal_inventory_error_mwh=state-initial))
            print(horizon,split,'complete',flush=True)
    daily=pd.DataFrame(days);daily.to_csv(OUT/'capability_daily.csv',index=False)
    summary=daily.groupby(['split','horizon_hours','model','power_fraction'],as_index=False).agg(
        days=('day','size'),intervals=('intervals','sum'),gross_before_gbp=('gross_before_gbp','sum'),gross_after_gbp=('gross_after_gbp','sum'),
        signed_before_gbp=('signed_before_gbp','sum'),signed_after_gbp=('signed_after_gbp','sum'),throughput_mwh=('throughput_mwh','sum'),
        schedule_deviation_before=('schedule_deviation_before','mean'),delivery_deviation_after=('delivery_deviation_after','mean'))
    summary['gross_reduction_pct']=100*(1-summary.gross_after_gbp/summary.gross_before_gbp)
    summary.to_csv(OUT/'capability_frontier.csv',index=False)
    intervals=[]
    for (h,model,fraction),d in daily[daily.split.eq('test')].groupby(['horizon_hours','model','power_fraction']):
        stamp=pd.DatetimeIndex(pd.to_datetime(d.day,utc=True)).as_unit('ns').asi8
        for length in [3,7,14]:
            a=d.assign(block=stamp//pd.Timedelta(days=length).value).groupby('block')[['gross_before_gbp','gross_after_gbp']].sum()
            weights=np.random.default_rng(41).multinomial(len(a),np.full(len(a),1/len(a)),size=2000)
            draws=100*(1-(weights@a.gross_after_gbp)/(weights@a.gross_before_gbp));lo,hi=np.quantile(draws,[.025,.975])
            intervals.append(dict(horizon_hours=h,model=model,power_fraction=fraction,block_days=length,blocks=len(a),
                point=100*(1-d.gross_after_gbp.sum()/d.gross_before_gbp.sum()),low=lo,high=hi))
    pd.DataFrame(intervals).to_csv(OUT/'capability_intervals.csv',index=False)
    test_daily=daily[daily.split.eq('test')]
    calendar=test_daily.drop_duplicates(['horizon_hours','day'])
    test_days=int(calendar.day.nunique())
    test_intervals_by_horizon={str(int(h)):int(q.intervals.sum()) for h,q in calendar.groupby('horizon_hours')}
    (OUT/'verification.json').write_text(json.dumps(dict(status='PASS',gross_negative_price_hand_examples=True,
        debit_credit_identity=True,max_terminal_inventory_error_mwh=max_terminal,max_soc_violation_mwh=max_soc_violation,
        price_leg_fidelity='systemBuyPrice and systemSellPrice are aligned, finite and equal in the archived single-price calendar',
        test_complete_days=test_days,test_intervals_by_horizon=test_intervals_by_horizon,
        scope='Ex-post correction capability using realised half-hour averages; complete-day cohort; terminal restoration settled',
        price_fidelity='systemBuyPrice and systemSellPrice columns both present and identical; this is an observed single-price Elexon replay',
        supersedes='v21 online_metered_correction: gross included credits and daily SOC was reset without accounting'),indent=2))
    print(summary[(summary.split=='test')&(summary.horizon_hours==2)&(summary.model=='selected_weather_events')].to_string(index=False))

if __name__=='__main__':main()
