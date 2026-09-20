"""Train/validate net-value control, then unlock the later economic period.

Geurts et al. (2006), Extremely randomized trees, doi:10.1007/s10994-006-6226-1:
matched multi-output forest budgets predict wind delivery and settlement-price
trajectories from completed SCADA. No recent revised-price field is a feature.
The study-defined LP/controller is in wind_events.revenue_control.
"""
from pathlib import Path
import argparse,json,sys,zipfile
import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from wind_events.economics import Battery
from wind_events.revenue_control import plan_storage,deliver_storage

OUT=ROOT/'outputs/protocol_benchmark_v24/economics'
CAT=ROOT/'outputs/protocol_benchmark_v18/catalogs/r30_a0.2_q0.05_training_q995'
B1=pd.Timestamp('2020-08-07T14:24Z');B2=pd.Timestamp('2020-10-19T19:12Z')
CAP=48.3;H=48;WEAR=10.;REPLAN=8
ARMS=['calendar_persistence','weather','weather_events']
PRICE_HISTORY=False
ISSUED_WIND=False
PRICE_FILE=ROOT/'data/policy_v18/elexon/system_prices_2020_2021H1.parquet'
WIND_FILE=ROOT/'data/policy_v24/issued_wind/vintages_2020_2021H1.parquet'


def future_array(series,n=H,offset=0):
    return np.column_stack([series.shift(-(offset+h)).to_numpy() for h in range(n)])


def observations(period):
    if period=='2020':
        return pd.read_parquet(ROOT/'outputs/protocol_benchmark_v19/economics/forecast_replay/farm_observations.parquet')
    full=period=='2021_full'
    cache=ROOT/('outputs/protocol_benchmark_v24/economics/farm_observations_2021.parquet' if full else 'outputs/protocol_benchmark_v24/economics/farm_observations_2021H1.parquet')
    if cache.exists():return pd.read_parquet(cache)
    parts=[]
    with zipfile.ZipFile(ROOT/'data/external_samples/hill_of_towie_v21/2021.zip') as z:
        for month in range(1,13 if full else 7):
            with z.open(f'tblSCTurGrid_2021_{month:02d}.csv') as f:
                power=pd.read_csv(f,usecols=['TimeStamp','StationId','wtc_ActPower_mean'])
            with z.open(f'tblSCTurbine_2021_{month:02d}.csv') as f:
                wind=pd.read_csv(f,usecols=['TimeStamp','StationId','wtc_AcWindSp_mean'])
            parts.append(power.merge(wind,on=['TimeStamp','StationId'],validate='1:1'))
    d=pd.concat(parts,ignore_index=True).drop_duplicates()
    d['time']=pd.to_datetime(d.TimeStamp,utc=True)-pd.Timedelta(minutes=10)
    if d.duplicated(['time','StationId']).any():raise ValueError('Conflicting source rows')
    power=d.pivot(index='time',columns='StationId',values='wtc_ActPower_mean')/1000
    wind=d.pivot(index='time',columns='StationId',values='wtc_AcWindSp_mean')
    power=power.where(power.ge(-.115)&power.le(2.76));wind=wind.where(wind.ge(0)&wind.le(60))
    power=power.resample('30min').mean().where(power.resample('30min').count().eq(3))
    wind=wind.resample('30min').mean().where(wind.resample('30min').count().eq(3))
    frame=pd.DataFrame({'power_mw':power.sum(axis=1,min_count=21),
        'wind_ms':wind.mean(axis=1).where(wind.notna().sum(axis=1).eq(21)),
        'available_turbines':power.notna().sum(axis=1)})
    frame.index+=pd.Timedelta(minutes=30);frame.index.name='issue_time'
    ix=pd.date_range('2021-01-01','2022-01-01' if full else '2021-07-01',freq='30min',tz='UTC')
    frame=frame.reindex(ix)
    history=observations('2020').tail(192)
    frame=frame.combine_first(history).sort_index();frame.to_parquet(cache)
    return frame


def event_features(clock,site,fit=False):
    chunks=[];shapes=[]
    sources=['hill','hill_2021'] if site=='hill_2021' else [site]
    paths=sorted(path for source in sources for path in (CAT/source).glob('*/events.parquet'))
    for path in paths:
        t=pd.read_parquet(path);t=t[t.representation_eligible&t.event_level.eq('primitive')&t.config.eq('threshold_120min')].copy()
        t['available']=pd.to_datetime(t.time_end,utc=True)+pd.Timedelta(minutes=150)
        if not fit:t=t[t.available.ge(clock.min()-pd.Timedelta(hours=4))&t.available.le(clock.max())]
        if t.empty:continue
        xx=np.load(path.parent/'shapes.npy',mmap_mode='r')[t.shape_row.to_numpy(int)]
        chunks.append(t[['available']]);shapes.append(xx)
    t=pd.concat(chunks,ignore_index=True);xx=np.vstack(shapes)
    path=OUT/'operational_raw25.joblib'
    if fit:
        rows=np.flatnonzero(t.available.lt(B1));rows=np.random.default_rng(41).choice(rows,min(10000,len(rows)),replace=False)
        scaler=StandardScaler().fit(xx[rows]);cluster=KMeans(n_clusters=4,n_init=20,random_state=41).fit(scaler.transform(xx[rows]))
        joblib.dump({'scaler':scaler,'cluster':cluster,'training_end':str(B1),'events':len(rows)},path)
    model=joblib.load(path);t['cluster']=model['cluster'].predict(model['scaler'].transform(xx))
    result=pd.DataFrame(index=clock);total=np.zeros(len(clock))
    for k in range(4):
        counts=t[t.cluster.eq(k)].groupby('available').size().reindex(clock,fill_value=0)
        result[f'event_count_{k}']=counts.rolling(8,min_periods=1).sum();total+=result[f'event_count_{k}']
    for k in range(4):result[f'event_fraction_{k}']=result[f'event_count_{k}']/np.maximum(total,1)
    result['event_total']=total
    return result


def features(frame,events):
    x=pd.DataFrame(index=frame.index)
    hour=frame.index.hour+frame.index.minute/60
    for name,value,period in [('hour',hour,24),('year',frame.index.dayofyear,365.25),('week',frame.index.dayofweek,7)]:
        for harmonic in (1,2):
            x[f'cal_{name}_s{harmonic}']=np.sin(2*np.pi*harmonic*value/period)
            x[f'cal_{name}_c{harmonic}']=np.cos(2*np.pi*harmonic*value/period)
    for lag in list(range(9))+[16,24,48]:
        x[f'power_{lag}']=frame.power_mw.shift(lag)/CAP;x[f'wind_{lag}']=frame.wind_ms.shift(lag)
    for length in [2,4,8,16,48]:
        x[f'power_change_{length}']=frame.power_mw.diff(length)/CAP
        x[f'power_sd_{length}']=frame.power_mw.rolling(length,min_periods=2).std()/CAP
        x[f'wind_mean_{length}']=frame.wind_ms.rolling(length,min_periods=1).mean()
    x['observed_turbines']=frame.available_turbines/21
    if not ISSUED_WIND:x=x.join(events)
    if PRICE_HISTORY:
        x=x.join(published_price_features(frame.index))
    if ISSUED_WIND:
        x=x.join(issued_wind_features(frame.index))
        x=x.join(ongoing_geometry(frame,fit=frame.index.min().year==2020 and frame.index.max()<=pd.Timestamp('2021-01-01',tz='UTC')))
    return x


def published_price_features(clock,reports=None):
    """Use only reports whose recorded creation and interval end precede issue.

    A five-minute delivery allowance is added. Late reports for older delivery
    intervals cannot replace the latest known delivery-period observation.
    The archived API version remains explicit; no future-price lag shortcuts.
    """
    d=reports.copy() if reports is not None else pd.read_parquet(PRICE_FILE)
    d['start']=pd.to_datetime(d.startTime,utc=True).astype('datetime64[ns, UTC]')
    created=pd.to_datetime(d.createdDateTime,utc=True,format='mixed').astype('datetime64[ns, UTC]')
    d['available']=pd.concat([created,d.start+pd.Timedelta(minutes=30)],axis=1).max(axis=1)+pd.Timedelta(minutes=5)
    d=d.sort_values(['available','start']);d=d[d.start.eq(d.start.cummax())]
    cols=['available','start','systemBuyPrice','netImbalanceVolume']
    result=pd.DataFrame(index=clock)
    for lag in [0,1,2,4,24,168]:
        q=pd.DataFrame({'cutoff':pd.DatetimeIndex(clock).as_unit('ns')-pd.Timedelta(hours=lag)})
        m=pd.merge_asof(q,d[cols].sort_values('available'),left_on='cutoff',right_on='available',direction='backward')
        if (m.available>m.cutoff).any():raise AssertionError('Unpublished-price leakage')
        result[f'market_price_lag{lag}']=m.systemBuyPrice.to_numpy()
        result[f'market_niv_lag{lag}']=m.netImbalanceVolume.to_numpy()
    result['market_base24']=result.market_price_lag0.rolling(48,min_periods=1).mean()
    result['market_sd24']=result.market_price_lag0.rolling(48,min_periods=2).std()
    return result


def issued_wind_features(clock,reports=None):
    d=reports.copy() if reports is not None else pd.read_parquet(WIND_FILE)
    d['available']=pd.to_datetime(d.publishTime,utc=True).astype('datetime64[ns, UTC]')+pd.Timedelta(minutes=5)
    d['target']=pd.to_datetime(d.startTime,utc=True).astype('datetime64[ns, UTC]')
    d=d.sort_values('available');result=pd.DataFrame(index=clock)
    for hour in [0,1,2,4,8,12,18,24]:
        q=pd.DataFrame({'cutoff':pd.DatetimeIndex(clock).as_unit('ns'),
                        'target':pd.DatetimeIndex(clock).as_unit('ns').floor('h')+pd.Timedelta(hours=hour)})
        m=pd.merge_asof(q,d[['available','target','generation']],left_on='cutoff',right_on='available',by='target',direction='backward')
        if (m.available>m.cutoff).any():raise AssertionError('Forecast-vintage leakage')
        result[f'market_issued_wind_h{hour}']=m.generation.to_numpy()/1000
    return result


def ongoing_geometry(frame,fit=False):
    """Causal shape distances from exactly the farm history given to the baseline.

    Two/four-hour prefixes have 5/9 measured half-hour means interpolated to 25
    coordinates, not 25 independent observations. No post-event context is used.
    Current-window scale and turning information are also common scalar controls.
    """
    result=pd.DataFrame(index=frame.index)
    for steps in [4,8]:
        values=np.column_stack([frame.power_mw.shift(i) for i in range(steps,-1,-1)])
        finite=np.isfinite(values).all(axis=1);delta=values-values[:,0,None]
        scale=np.max(np.abs(delta),axis=1);delta=np.divide(delta,scale[:,None],out=np.zeros_like(delta),where=scale[:,None]>1e-8)
        xx=np.stack([np.interp(np.linspace(0,steps,25),np.arange(steps+1),v) for v in np.nan_to_num(delta)])
        file=OUT/f'causal_shape_{steps}.joblib'
        if fit:
            keep=finite&(frame.index<B1);scaler=StandardScaler().fit(xx[keep])
            cluster=KMeans(n_clusters=4,n_init=20,random_state=41).fit(scaler.transform(xx[keep]))
            joblib.dump({'scaler':scaler,'cluster':cluster},file)
        model=joblib.load(file);distance=model['cluster'].transform(model['scaler'].transform(xx));distance[~finite]=np.nan
        for k in range(4):result[f'event_prefix_{steps}_distance{k}']=distance[:,k]
        # Same scalar shape descriptors in the no-event control arm.
        result[f'prefix_scale_{steps}']=scale/CAP
        result[f'prefix_variation_{steps}']=np.abs(np.diff(values,axis=1)).sum(axis=1)/CAP
        result[f'prefix_turns_{steps}']=(np.diff(np.sign(np.diff(values,axis=1)),axis=1)!=0).sum(axis=1).astype(float)
        result.loc[~finite,f'prefix_turns_{steps}']=np.nan
    return result


def context(frame):
    prices=pd.read_parquet(PRICE_FILE)
    prices=prices.set_index(pd.to_datetime(prices.startTime,utc=True))
    if not np.allclose(prices.systemBuyPrice,prices.systemSellPrice):raise ValueError('Single-price condition changed')
    data=pd.DataFrame(index=frame.index)
    data['actual']=frame.power_mw.shift(-1);data['last_power']=frame.power_mw.ffill()
    data['price']=prices.systemBuyPrice.reindex(frame.index)
    data['day']=frame.index.floor('D')
    return data


def fit_forecasts(frame,x,data):
    yp=future_array(data.price);yw=future_array(frame.power_mw,offset=1)
    eligible=(x.index+pd.Timedelta(hours=24)<=B1)&(x.index>=pd.Timestamp('2020-01-03',tz='UTC'))
    reports=[]
    for arm in ARMS:
        cols=[c for c in x if c.startswith(('cal_','market_'))] if arm.endswith('persistence') else [c for c in x if arm=='weather_events' or not c.startswith('event_')]
        imp=SimpleImputer(add_indicator=True).fit(x.loc[eligible,cols]);xx=imp.transform(x[cols])
        for leaf in [24,96]:
            mp=np.asarray(eligible)&np.isfinite(yp).all(axis=1);mw=np.asarray(eligible)&np.isfinite(yw).all(axis=1)
            target_price=yp-x.market_base24.fillna(0).to_numpy()[:,None] if PRICE_HISTORY else yp
            horizon_weight=np.exp(-np.arange(H)/16) if ISSUED_WIND else np.ones(H)
            price=ExtraTreesRegressor(n_estimators=120,max_depth=12,min_samples_leaf=leaf,random_state=41,n_jobs=4).fit(xx[mp],target_price[mp]*horizon_weight)
            power=None
            if not arm.endswith('persistence'):
                power=ExtraTreesRegressor(n_estimators=120,max_depth=12,min_samples_leaf=leaf,random_state=41,n_jobs=4).fit(xx[mw],yw[mw])
            artifact={'arm':arm,'leaf':leaf,'imputer':imp,'cols':cols,'price':price,'power':power,
                      'price_history':PRICE_HISTORY,'horizon_weight':horizon_weight,'train_price_rows':int(mp.sum()),'train_wind_rows':int(mw.sum()),'latest_training_target':str(B1)}
            joblib.dump(artifact,OUT/f'{arm}_l{leaf}.joblib',compress=3)
            reports.append({k:artifact[k] for k in ['arm','leaf','train_price_rows','train_wind_rows','latest_training_target']})
            print('fit',arm,leaf,flush=True)
    pd.DataFrame(reports).to_csv(OUT/'training_support.csv',index=False)


def predictions(artifact,x,data):
    xx=artifact['imputer'].transform(x[artifact['cols']]);price=artifact['price'].predict(xx)/artifact.get('horizon_weight',np.ones(H))
    if artifact.get('price_history'):price+=x.market_base24.fillna(0).to_numpy()[:,None]
    if artifact['power'] is None:wind=np.repeat(data.last_power.to_numpy()[:,None],H,axis=1)
    else:wind=artifact['power'].predict(xx)
    return np.maximum(np.nan_to_num(wind,nan=0),0),price


def simulate(data,wind_forecast,price_forecast,fraction,shrink,wear=WEAR):
    b=Battery(CAP*fraction,2*CAP*fraction);low=b.minimum_fraction*b.energy_mwh
    records=[]
    for day,indices in data.groupby('day').indices.items():
        idx=np.asarray(indices);d=data.iloc[idx]
        if len(idx)!=48:continue
        state=low;gain=throughput=spill_sum=price_value=0.;overrides=0
        valid=np.isfinite(d.actual).all() and np.isfinite(d.price).all()
        plan=None
        for i,row in enumerate(d.itertuples()):
            if i%REPLAN==0:
                w=wind_forecast[idx[i],:48-i];p=price_forecast[idx[i],:48-i]
                p=p.mean()+shrink*(p-p.mean())
                plan=plan_storage(w,p,state,b,wear);first=i
            a=i-first;observed=float(row.actual) if np.isfinite(row.actual) else 0.
            step=deliver_storage(observed,plan['charge'][a],plan['discharge'][a],plan['curtail'][a],state,b,47-i)
            state=step['inventory'];throughput+=step['throughput'];spill_sum+=step['curtail']*.5
            delta=(step['delivered']-observed)*.5*(row.price if np.isfinite(row.price) else 0.)
            price_value+=delta;gain+=delta-wear*step['throughput'];overrides+=step['terminal_safety_override']
        assert abs(state-low)<1e-6
        records.append({'day':day,'score_eligible':bool(valid),'intervals':48,'fraction':fraction,'shrink':shrink,
            'net_gain_gbp':gain,'settlement_gain_gbp':price_value,'degradation_gbp':wear*throughput,
            'throughput_mwh':throughput,'curtailed_mwh':spill_sum,'terminal_error_mwh':state-low,
            'safety_overrides':overrides})
    return pd.DataFrame(records)


def score(frame):
    d=frame[frame.score_eligible];v=d.net_gain_gbp.to_numpy()
    tail=np.sort(v)[:max(1,int(np.ceil(.05*len(v))))]
    return {'days':len(v),'net_gain_gbp':float(v.sum()),'mean_gain_gbp':float(v.mean()),
            'worst_5pct_mean_day_gbp':float(tail.mean()),'selection_score':float(v.mean() if PRICE_HISTORY else v.mean()+.25*min(tail.mean(),0)),
            'throughput_mwh':float(d.throughput_mwh.sum()),'curtailed_mwh':float(d.curtailed_mwh.sum())}


def paired_intervals(d,a,b,label):
    pivot=d[d.score_eligible].pivot(index='day',columns='candidate',values='net_gain_gbp')
    z=pivot[a]-(0 if b is None else pivot[b]);z=z.dropna();out=[]
    stamp=pd.DatetimeIndex(z.index).as_unit('ns').asi8
    for days in [3,7,14]:
        g=pd.DataFrame({'gain':z.to_numpy(),'n':1,'block':stamp//pd.Timedelta(days=days).value}).groupby('block')[['gain','n']].sum()
        weights=np.random.default_rng(41).multinomial(len(g),np.full(len(g),1/len(g)),size=2000)
        draws=(weights@g.gain)/(weights@g.n);lo,hi=np.quantile(draws,[.025,.975])
        out.append({'comparison':label,'days':len(z),'blocks':len(g),'block_days':days,
            'gain_gbp':float(z.sum()),'gain_gbp_per_day':float(z.mean()),'low_daily':lo,'high_daily':hi})
    return out


def main():
    global OUT,PRICE_HISTORY,ARMS,REPLAN,ISSUED_WIND
    parser=argparse.ArgumentParser();parser.add_argument('--phase',choices=['validate','test'],required=True)
    parser.add_argument('--variant',choices=['base','price_history','issued_wind'],default='base');args=parser.parse_args()
    if args.variant in ('price_history','issued_wind'):
        OUT=OUT/args.variant;PRICE_HISTORY=True;ARMS=['market_persistence','weather','weather_events'];REPLAN=2
        ISSUED_WIND=args.variant=='issued_wind'
    OUT.mkdir(parents=True,exist_ok=True)
    if args.phase=='validate':
        protocol={'status':'FROZEN_BEFORE_V24_VALIDATION','training_end':str(B1),'validation_end':str(B2),
            'test':'Hill 2021H1: previously used structurally, not for this economic selection',
            'arms':ARMS,'leaves':[24,96],'price_profile_shrink':[.5,1.], 'battery_fractions':[0,.05,.1,.2],
            'wear_gbp_per_ac_mwh':WEAR,'roundtrip_efficiency':.92**2,'replan_half_hours':REPLAN,
            'objective':'maximise forecast-price net operating gain; validation mean plus .25 times negative worst-5%-day mean',
            'forecast_inputs':('calendar, completed SCADA and publication-aware past market price/NIV; price trajectories predict deviations from known 24h level' if PRICE_HISTORY else 'calendar and completed SCADA; events available after full context; no settlement-price history'),
            'controller':'wind-only charging; export cap=48.3MW engineering assumption; daily minimum SOC restored',
            'dispatch_resolution':'30-minute planning and passive average-interval clipping; no sub-interval guarantee',
            'primary':'installed 10%-power 2h battery; incremental event value vs strongest validation-selected non-event arm',
            'secondary':'validation-selected capacity; operational gain before capital; all arms retained'}
        if PRICE_HISTORY:
            protocol.update(objective='Maximise validation mean net operating gain after wear; tail risk reported separately',
                price_availability='max(createdDateTime,startTime+30min)+5min; discard late older-period replacements',
                version_scope='Pre-test validation redesign after weak no-price-history results; prior candidate matrix retained')
        if ISSUED_WIND:
            protocol.update(event_interface='Causal 2h/4h farm-shape distances on training-fitted prototypes; no delayed turbine-count features',
                matched_inputs='Both SCADA arms get all nine half-hour powers, scalar scale/variation/turn count, market reports and issued national wind forecasts',
                external_forecast='WINDFOR publishTime+5min gate; national generation MW, not local weather truth',
                price_loss='Exponentially horizon-weighted forest splitting; predictions returned in original GBP/MWh')
        (OUT/'control_protocol.json').write_text(json.dumps(protocol,indent=2))
        f=observations('2020');e=event_features(f.index,'hill',fit=True);x=features(f,e);d=context(f)
        fit_forecasts(f,x,d);mask=(d.index>=B1.ceil('D'))&(d.index<B2.floor('D'))
        d=d[mask];x=x.loc[d.index];allrows=[];summary=[]
        for arm in ARMS:
            for leaf in [24,96]:
                w,p=predictions(joblib.load(OUT/f'{arm}_l{leaf}.joblib'),x,d)
                for shrink in [.5,1.]:
                    for fraction in [0,.05,.1,.2]:
                        ident=f'{arm}_l{leaf}_s{shrink}_b{fraction}'
                        result=simulate(d,w,p,fraction,shrink);result['candidate']=ident
                        allrows.append(result);summary.append({'candidate':ident,'arm':arm,'leaf':leaf,'shrink':shrink,'fraction':fraction,**score(result)})
                        print('validated',ident,round(summary[-1]['net_gain_gbp']),flush=True)
                        pd.DataFrame(summary).to_csv(OUT/'validation_candidates.csv',index=False)
        pd.concat(allrows).to_csv(OUT/'validation_daily.csv',index=False)
        s=pd.DataFrame(summary);selected=[]
        for arm in ARMS:
            for fraction in [0,.05,.1,.2]:
                r=s[s.arm.eq(arm)&s.fraction.eq(fraction)].sort_values(['selection_score','leaf'],ascending=[False,False]).iloc[0]
                selected.append(r.to_dict())
        pd.DataFrame(selected).to_csv(OUT/'frozen_selection.csv',index=False)
        (OUT/'test_gate.json').write_text(json.dumps({'status':'FROZEN_BEFORE_2021_ECONOMIC_SCORES',
            'chosen':selected,'candidate_count':len(summary)},indent=2))
        print(pd.DataFrame(selected).to_string(index=False))
    else:
        gate=json.loads((OUT/'test_gate.json').read_text());assert gate['status']=='FROZEN_BEFORE_2021_ECONOMIC_SCORES'
        if (OUT/'test_summary.csv').exists():raise RuntimeError('2021 test has already been evaluated; preserve its identity')
        f=observations('2021');e=event_features(f.index,'hill_2021');x=features(f,e);d=context(f)
        d=d[(d.index>=pd.Timestamp('2021-01-01',tz='UTC'))&(d.index<pd.Timestamp('2021-07-01',tz='UTC'))]
        x=x.loc[d.index]
        rows=[];summaries=[];cache={}
        for r in gate['chosen']:
            key=(r['arm'],r['leaf'])
            if key not in cache:cache[key]=predictions(joblib.load(OUT/f'{key[0]}_l{key[1]}.joblib'),x,d)
            w,p=cache[key];result=simulate(d,w,p,r['fraction'],r['shrink']);result['candidate']=r['candidate']
            rows.append(result);summaries.append({k:r[k] for k in ['candidate','arm','leaf','shrink','fraction']}|score(result))
            print('test',r['candidate'],round(summaries[-1]['net_gain_gbp']),flush=True)
        daily=pd.concat(rows);daily.to_csv(OUT/'test_daily.csv',index=False);s=pd.DataFrame(summaries);s.to_csv(OUT/'test_summary.csv',index=False)
        val=pd.DataFrame(gate['chosen']);comparisons=[]
        for r in gate['chosen']:
            comparisons+=paired_intervals(daily,r['candidate'],None,r['candidate']+'_vs_passive')
            zero=val[val.arm.eq(r['arm'])&val.fraction.eq(0)].iloc[0].candidate
            if r['fraction']>0:comparisons+=paired_intervals(daily,r['candidate'],zero,r['candidate']+'_vs_same_arm_no_storage')
        for fraction in [.05,.1,.2]:
            event=val[val.arm.eq('weather_events')&val.fraction.eq(fraction)].iloc[0].candidate
            other=val[val.arm.ne('weather_events')&val.fraction.eq(fraction)].sort_values('selection_score',ascending=False).iloc[0].candidate
            comparisons+=paired_intervals(daily,event,other,f'event_increment_at_{fraction}')
        pd.DataFrame(comparisons).to_csv(OUT/'test_intervals.csv',index=False)
        print(s.to_string(index=False))


if __name__=='__main__':
    with threadpool_limits(limits=4):main()
