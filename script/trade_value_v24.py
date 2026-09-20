"""Risk-constrained schedule decisions with both market revenue legs.

Browell (2018), doi:10.3390/en11061345, Sections 2-3: price spreads and wind
forecast risk jointly determine bids in a single-price balancing market.
Study adaptation: bounded forecast/hedge candidates are selected only before
2021-07-01; H2 is opened after selection. Realised MID is an execution-price
reference, not proof that historical orders could clear at that exact price.
"""
from pathlib import Path
import argparse,json,sys
import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from threadpoolctl import threadpool_limits
import economic_value_v24 as ev
from wind_events.revenue_control import complete_revenue

ROOT=ev.ROOT;OUT=ROOT/'outputs/protocol_benchmark_v24/economics/full_revenue'
TRAIN_END=pd.Timestamp('2021-04-01',tz='UTC');TEST_START=pd.Timestamp('2021-07-01',tz='UTC')
TEST_END=pd.Timestamp('2022-01-01',tz='UTC');ARMS=['market_persistence','weather','weather_events']
FEE=.5


def setup():
    OUT.mkdir(parents=True,exist_ok=True)
    ev.OUT=OUT;ev.PRICE_HISTORY=True;ev.ISSUED_WIND=True;ev.ARMS=ARMS;ev.B1=TRAIN_END
    folder=ROOT/'data/policy_v24/holdout_2021H2'
    ev.PRICE_FILE=folder/'system_prices_2020_2021.parquet';ev.WIND_FILE=folder/'wind_vintages_2020_2021.parquet'


def build_inputs(test=False):
    if test:f=ev.observations('2021_full')
    else:
        a=ev.observations('2020');b=ev.observations('2021')
        f=b.combine_first(a).sort_index()
        f=f[f.index<=TEST_START]
        ev.ongoing_geometry(f,fit=True)
    x=ev.features(f,pd.DataFrame(index=f.index));d=ev.context(f)
    mid=pd.read_parquet(ROOT/'data/policy_v24/holdout_2021H2/market_index_2020_2021.parquet')
    d['forward']=mid.market_index_price.reindex(d.index)
    return f,x,d


def target_table(d,h):
    steps=2*h
    target=d[['actual','price','forward']].shift(-steps).copy()
    target['target_start']=d.index+pd.Timedelta(hours=h)
    target['target_end']=target.target_start+pd.Timedelta(minutes=30)
    target['persistence']=d.last_power.clip(0,ev.CAP)
    target['valid']=target[['actual','price','forward','persistence']].notna().all(axis=1)
    return target


def receipts(t,q,fee=FEE):
    return complete_revenue(t.actual.to_numpy(),q,t.forward.to_numpy(),t.price.to_numpy(),t.price.to_numpy())-fee*np.abs(q)*.5


def stats(t,q):
    baseline=t.persistence.to_numpy();r=receipts(t,q);base=receipts(t,baseline)
    absolute=np.abs(q-t.actual.to_numpy())/ev.CAP
    return {'intervals':len(t),'nmae':absolute.mean(),'revenue_gbp':r.sum(),
            'gain_vs_persistence_gbp':(r-base).sum(),'mean_gain_gbp':(r-base).mean(),
            'bias_mw':float(np.mean(q-t.actual.to_numpy()))}


def issue_schedule(t,mu,spread,blend,offset,hedge,scale):
    anchor=t.persistence.to_numpy()
    return np.clip(anchor+blend*(mu-anchor)+ev.CAP*offset-ev.CAP*hedge*np.clip(spread/scale,-1,1),0,ev.CAP)


def validation():
    protocol={'status':'FROZEN_BEFORE_H2_RESULTS','train_end_exclusive':str(TRAIN_END),
        'validation':'2021-04-01 through 2021-06-30; development period already seen in storage research',
        'holdout':'2021-07-01 through 2021-12-31; no prior economic score used for selection',
        'horizons_hours':[1,2,4],'arms':ARMS,'forecast_leaves':[24,96],'spread_leaves':[7,15],
        'blends':[0,.5,1],'capacity_offsets':[-.025,0,.025],'hedge_capacity_fractions':[0,.025,.05],
        'selection':'Maximum complete validation net revenue subject to scheduling nMAE <= persistence; passive fallback included',
        'trade_reference':'Realised Elexon volume-weighted MID, ex-post execution reference only',
        'fees_gbp_per_scheduled_mwh':FEE,'fee_sensitivity':[0,.5,1],
        'revenue':'S*MID*0.5+(P-S)*imbalance_price*0.5-fee*abs(S)*0.5',
        'role':'Risk-constrained research trade replay, not actual orders/invoices',
        'power_forecast':'Common past farm powers and scalars plus archived issued national wind forecasts',
        'event_increment':'Training-fitted causal 2h/4h shape distances, no extra raw measurements'}
    (OUT/'protocol.json').write_text(json.dumps(protocol,indent=2))
    f,x,d=build_inputs();ev.fit_forecasts(f,x,d)
    records=[];selected=[]
    for h in [1,2,4]:
        target=target_table(d,h)
        train=target.valid&(target.target_end<=TRAIN_END)&(x.index>=pd.Timestamp('2020-01-03',tz='UTC'))
        valid=target.valid&(x.index>=TRAIN_END)&(target.target_end<=TEST_START)
        tv=target[valid];baseline=stats(tv,tv.persistence.to_numpy());scale=max(5,float(np.std((target.price-target.forward)[train])))
        for arm in ARMS:
            candidates=[]
            for fl in [24,96]:
                artifact=joblib.load(OUT/f'{arm}_l{fl}.joblib')
                cols=artifact['cols'];imp=SimpleImputer(add_indicator=True).fit(x.loc[train,cols]);xx=imp.transform(x[cols])
                wind,_=ev.predictions(artifact,x.loc[valid],d.loc[valid]);mu=wind[:,2*h]
                for sl in [7,15]:
                    model=HistGradientBoostingRegressor(max_leaf_nodes=sl,max_iter=160,learning_rate=.05,
                        l2_regularization=10,early_stopping=False,random_state=41).fit(xx[train],(target.price-target.forward)[train])
                    spread=model.predict(xx[valid])
                    for blend in [0,.5,1]:
                        if arm.endswith('persistence') and blend!=0:continue
                        for offset in [-.025,0,.025]:
                            for hedge in [0,.025,.05]:
                                q=issue_schedule(tv,mu,spread,blend,offset,hedge,scale);metrics=stats(tv,q)
                                config={'horizon_hours':h,'arm':arm,'forecast_leaf':fl,'spread_leaf':sl,
                                    'blend':blend,'offset':offset,'hedge':hedge,'scale':scale}
                                feasible=metrics['nmae']<=baseline['nmae']+1e-12
                                records.append(config|metrics|{'risk_feasible':feasible,'persistence_nmae':baseline['nmae']})
                                if feasible:candidates.append((metrics['revenue_gbp'],-abs(offset)-hedge,-blend,-sl,config,imp,model,cols))
            best=max(candidates,key=lambda q:q[:4]);config=best[4]
            joblib.dump({'config':config,'imputer':best[5],'spread_model':best[6],'cols':best[7]},OUT/f'policy_{arm}_{h}h.joblib')
            selected.append(config|{'validation_revenue_gbp':best[0],'validation_gain_gbp':best[0]-baseline['revenue_gbp']})
            print('trade validation',h,arm,round(selected[-1]['validation_gain_gbp']),config,flush=True)
            pd.DataFrame(records).to_csv(OUT/'validation_candidates.csv',index=False)
    pd.DataFrame(selected).to_csv(OUT/'selection.csv',index=False)
    (OUT/'test_gate.json').write_text(json.dumps({'status':'FROZEN_BEFORE_H2_RESULTS','policies':selected},indent=2))


def test():
    gate=json.loads((OUT/'test_gate.json').read_text());assert gate['status']=='FROZEN_BEFORE_H2_RESULTS'
    if (OUT/'test_summary.csv').exists():raise RuntimeError('H2 economics already evaluated; preserve test identity')
    f,x,d=build_inputs(test=True);summaries=[];predictions=[]
    for h in [1,2,4]:
        target=target_table(d,h);valid=target.valid&(x.index>=TEST_START)&(target.target_end<=TEST_END)
        tv=target[valid];baseline=stats(tv,tv.persistence.to_numpy())
        summaries.append({'horizon_hours':h,'arm':'passive_persistence',**baseline})
        for arm in ARMS:
            policy=joblib.load(OUT/f'policy_{arm}_{h}h.joblib');c=policy['config']
            a=joblib.load(OUT/f'{arm}_l{c["forecast_leaf"]}.joblib');wind,_=ev.predictions(a,x.loc[valid],d.loc[valid])
            spread=policy['spread_model'].predict(policy['imputer'].transform(x.loc[valid,policy['cols']]))
            q=issue_schedule(tv,wind[:,2*h],spread,c['blend'],c['offset'],c['hedge'],c['scale'])
            summaries.append({'horizon_hours':h,'arm':arm,**stats(tv,q)})
            z=tv[['target_start','actual','price','forward','persistence']].copy();z['arm']=arm;z['horizon_hours']=h;z['schedule']=q
            z['net_revenue_gbp']=receipts(tv,q);z['baseline_revenue_gbp']=receipts(tv,tv.persistence.to_numpy());predictions.append(z)
            print('H2 trade',h,arm,round(summaries[-1]['gain_vs_persistence_gbp']),flush=True)
    pd.DataFrame(summaries).to_csv(OUT/'test_summary.csv',index=False)
    panel=pd.concat(predictions,ignore_index=True);panel.to_parquet(OUT/'test_predictions.parquet',index=False)
    rows=[]
    selection=pd.read_csv(OUT/'selection.csv')
    for h,p in panel.groupby('horizon_hours'):
        p['day']=pd.to_datetime(p.target_start,utc=True).dt.floor('D')
        daily=p.groupby(['day','arm'])[['net_revenue_gbp','baseline_revenue_gbp']].sum().reset_index()
        pivot=daily.pivot(index='day',columns='arm',values='net_revenue_gbp')
        base=daily.groupby('day').baseline_revenue_gbp.first()
        best=selection[(selection.horizon_hours==h)&selection.arm.ne('weather_events')].sort_values('validation_revenue_gbp',ascending=False).iloc[0].arm
        differences={arm+'_vs_persistence':pivot[arm]-base for arm in ARMS}
        differences['event_vs_validation_selected_non_event']=pivot.weather_events-pivot[best]
        differences['event_vs_weather']=pivot.weather_events-pivot.weather
        for name,gain in differences.items():
            stamp=pd.DatetimeIndex(gain.index).as_unit('ns').asi8
            for days in [3,7,14]:
                g=pd.DataFrame({'gain':gain.to_numpy(),'n':1,'block':stamp//pd.Timedelta(days=days).value}).groupby('block')[['gain','n']].sum()
                w=np.random.default_rng(41).multinomial(len(g),np.full(len(g),1/len(g)),size=2000)
                draws=(w@g.gain)/(w@g.n);lo,hi=np.quantile(draws,[.025,.975])
                rows.append({'horizon_hours':h,'comparison':name,'days':len(gain),'blocks':len(g),'block_days':days,
                    'gain_gbp':gain.sum(),'mean_gain_gbp_per_day':gain.mean(),'low_daily':lo,'high_daily':hi})
    pd.DataFrame(rows).to_csv(OUT/'test_intervals.csv',index=False)
    print(pd.DataFrame(summaries).to_string(index=False))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--phase',choices=['validate','test'],required=True);args=parser.parse_args()
    setup()
    with threadpool_limits(limits=4):
        validation() if args.phase=='validate' else test()
