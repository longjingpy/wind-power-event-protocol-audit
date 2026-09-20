"""Native-grid conditional-distribution decisions for the Jiangsu 2022 rule.

Gneiting (2011), Making and Evaluating Point Forecasts,
doi:10.1198/jasa.2011.r10138, optimal point forecasts: the action depends on
the scoring loss. For an exceedance fee, maximize predictive probability
inside the allowed band, rather than minimize mean absolute/squared error.

Article 44(II): 15-min/4-h accuracy levels 97%/87%; 4 CNY per 10 MW per failed
point. This is the accuracy-charge component under the 2022 document, not an
invoice or a claim that later amendments/exemptions have been reconstructed.
"""
from pathlib import Path
import argparse,json,sys
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from wind_events.representation import Representation
OUT=ROOT/'outputs/protocol_benchmark_v24/economics/jiangsu_native'
DATA_BASE=OUT
WEATHER='none'
CAP=87.45;REPS=['scalar','raw25','raw_pca6','gaf_pca6','gaf_bit6']
CENTERS=np.arange(121)/100


def tolerance_action(probability,tolerance):
    actions=np.arange(201)/200
    lo=np.maximum(0,CENTERS-.005);hi=CENTERS+.005
    overlap=np.maximum(0,np.minimum(hi[None,:],actions[:,None]+tolerance)-
                       np.maximum(lo[None,:],actions[:,None]-tolerance))/(hi-lo)[None,:]
    mass=probability@overlap.T
    mean=probability@CENTERS
    # Numerically tied band probabilities prefer the conditional mean.
    quality=mass-1e-10*np.abs(actions[None,:]-mean[:,None])
    return actions[quality.argmax(axis=1)]


def model_inputs(f,history):
    x=f.available_power/CAP
    values=np.column_stack([x.shift(i) for i in range(history,-1,-1)])
    finite=np.isfinite(values).all(axis=1)
    delta=values-values[:,0,None];scale=np.max(np.abs(delta),axis=1)
    normalized=np.divide(delta,scale[:,None],out=np.zeros_like(delta),where=scale[:,None]>1e-8)
    shapes=np.stack([np.interp(np.linspace(0,history,25),np.arange(history+1),v) for v in np.nan_to_num(normalized)])
    hour=f.index.tz_convert('Asia/Shanghai').hour+f.index.minute/60
    common=np.c_[x,f.past15_power/CAP,f.wind/20,scale,np.abs(np.diff(values,axis=1)).sum(axis=1),
        np.sin(hour*2*np.pi/24),np.cos(hour*2*np.pi/24),
        np.sin(f.index.dayofyear*2*np.pi/365.25),np.cos(f.index.dayofyear*2*np.pi/365.25)]
    return shapes,common,finite&np.isfinite(common).all(axis=1)


def forecast_covariates(clock,horizon):
    data=pd.read_parquet(ROOT/'data/weather_v24/pizhou_fixed_lead/fixed_lead_hourly.parquet')
    columns=[c for c in data if c.startswith('jma_gsm') or WEATHER=='jma_gfs']
    data=data[columns]
    def at(times):
        lower=pd.DatetimeIndex(times).floor('h');upper=pd.DatetimeIndex(times).ceil('h')
        w=np.asarray((pd.DatetimeIndex(times)-lower)/pd.Timedelta(hours=1))[:,None]
        return data.reindex(lower).to_numpy()*(1-w)+data.reindex(upper).to_numpy()*w
    current=at(clock);future=at(clock+pd.Timedelta(minutes=15*horizon))
    if not ((clock+pd.Timedelta(minutes=15*horizon)-pd.Timedelta(hours=24))<clock).all():
        raise AssertionError('Forecast vintage does not precede issue')
    return np.c_[current,future,future-current]


def point_fee(actual,predicted,tolerance,capacity=CAP):
    actual,predicted=np.broadcast_arrays(actual,predicted)
    if capacity<=0 or tolerance<=0 or not np.isfinite([*actual.ravel(),*predicted.ravel()]).all():
        raise ValueError('Finite per-unit observations and positive capacity/tolerance required')
    return (np.abs(actual-predicted)>tolerance+1e-12).astype(float)*.4*capacity


def measures(y,q,tolerance):
    errors=np.abs(y-q);fees=point_fee(y,q,tolerance)
    return {'n':len(y),'nmae':errors.mean(),'failure_fraction':np.mean(fees>0),
            'failed_points':int((fees>0).sum()),'accuracy_charge_cny':fees.sum()}


def frame_and_splits():
    f=pd.read_parquet(DATA_BASE/'farm_15min.parquet');span=f.index[-1]-f.index[0]+pd.Timedelta(minutes=15)
    return f,f.index[0]+.6*span,f.index[0]+.8*span


def validate():
    f,b1,b2=frame_and_splits()
    protocol={'status':'FROZEN_BEFORE_NEW_POLICY_TEST_SCORES','mode':'EXPLORATORY_EXISTING_ARCHIVE_NEW_NATIVE_GRID_AND_TARGET',
        'capacity_mw':CAP,'capacity_basis':'provider-supplied 87.45-MW metadata note',
        'rule':'Jiangsu 2022 No.53 Article 44(II), printed pages 19-20, accuracy charge only',
        'source_url':'https://jsb.nea.gov.cn/eWebEditor/webpic/2022815133219753.pdf',
        'horizons_steps':{'1':.03,'16':.13},'point_charge_cny_per_mw':.4,
        'no_day_ahead_allowance':'The 2% monthly allowance belongs to subsection I, not this ultra-short-term accuracy component.',
        'training_end':str(b1),'validation_end':str(b2),'representations':REPS,
        'classifier':'ExtraTrees probability forest, 150 trees; leaves 8/32; depth16; seed41',
        'actions':['mean','median','tolerance'],'persistence_blends':[0,.25,.5,.75,1],
        'selection':'minimum validation failed points, ties by nMAE and smaller forecast blend',
        'future_inputs':'none; native inputs precede issue by at least one minute',
        'reporting':'observed eligible points and monthly coverage; no extrapolated actual invoice or exemptions'}
    if WEATHER!='none':
        protocol.update(weather=WEATHER,weather_source='Open-Meteo fixed-24h-lead operational forecasts; not reanalysis',
            coordinates='archived administrative proxy 34.3403N,118.0068E',
            weather_features='current-valid and target-valid u/v, temperature, pressure; their differences; no interpolation across gaps',
            comparison_population='all representations and persistence share complete forecast coverage')
    (OUT/'experiment_protocol.json').write_text(json.dumps(protocol,indent=2))
    candidates=[];chosen=[]
    for horizon,tolerance,history in [(1,.03,8),(16,.13,16)]:
        shapes,common,valid=model_inputs(f,history);y=(f.target_power.shift(-horizon)/CAP).to_numpy()
        if WEATHER!='none':
            extra=forecast_covariates(f.index,horizon);common=np.c_[common,extra];valid&=np.isfinite(extra).all(axis=1)
        target_time=f.index+pd.Timedelta(minutes=15*horizon)
        valid&=np.isfinite(y)&(y>=-.05)&(y<=1.2)
        tr=valid&(target_time<=b1);va=valid&(f.index>=b1)&(target_time<=b2)
        labels=np.clip(np.rint(y[tr]*100),0,120).astype(int)
        persistence=np.clip(f.available_power.to_numpy()/CAP,0,1)
        for rep in REPS:
            transform=None
            if rep!='scalar':
                rows=np.flatnonzero(tr);rows=np.random.default_rng(41).choice(rows,min(10000,len(rows)),replace=False)
                transform=Representation(rep).fit(shapes[rows])
                latent=transform.transform(shapes);xx=np.c_[common,latent]
            else:xx=common
            pool=[]
            for leaf in [8,32]:
                model=ExtraTreesClassifier(n_estimators=150,max_depth=16,min_samples_leaf=leaf,
                    max_features=1.,random_state=41,n_jobs=4).fit(xx[tr],labels)
                p=np.zeros((int(va.sum()),len(CENTERS)));p[:,model.classes_]=model.predict_proba(xx[va])
                forecasts={'mean':p@CENTERS,'median':CENTERS[(np.cumsum(p,axis=1)>=.5).argmax(axis=1)],
                           'tolerance':tolerance_action(p,tolerance)}
                for name,forecast in forecasts.items():
                    for blend in [0,.25,.5,.75,1]:
                        q=np.clip((1-blend)*persistence[va]+blend*forecast,0,1);s=measures(y[va],q,tolerance)
                        row={'horizon_steps':horizon,'representation':rep,'leaf':leaf,'action':name,'blend':blend,**s}
                        candidates.append(row);pool.append((s['failed_points'],s['nmae'],blend,leaf,name,model))
            winner=min(pool,key=lambda r:r[:5]);bad,mae,blend,leaf,name,model=winner
            record={'horizon_steps':horizon,'tolerance':tolerance,'history':history,'representation':rep,
                    'leaf':leaf,'action':name,'blend':blend,'validation_failed_points':bad,'validation_nmae':mae}
            joblib.dump({'config':record,'transform':transform,'model':model},OUT/f'model_{rep}_{horizon}.joblib',compress=3)
            chosen.append(record);pd.DataFrame(candidates).to_csv(OUT/'validation_candidates.csv',index=False)
            print('penalty validation',horizon,rep,bad,round(mae,4),name,blend,flush=True)
        print('persistence validation',horizon,measures(y[va],persistence[va],tolerance),flush=True)
    pd.DataFrame(chosen).to_csv(OUT/'selection.csv',index=False)
    (OUT/'test_gate.json').write_text(json.dumps({'status':'FROZEN','selected':chosen},indent=2))


def test():
    if (OUT/'test_summary.csv').exists():raise RuntimeError('Policy test already read')
    f,b1,b2=frame_and_splits();gate=json.loads((OUT/'test_gate.json').read_text());assert gate['status']=='FROZEN'
    summaries=[];panels=[]
    for horizon,tolerance,history in [(1,.03,8),(16,.13,16)]:
        shapes,common,valid=model_inputs(f,history);y=(f.target_power.shift(-horizon)/CAP).to_numpy()
        if WEATHER!='none':
            extra=forecast_covariates(f.index,horizon);common=np.c_[common,extra];valid&=np.isfinite(extra).all(axis=1)
        valid&=np.isfinite(y)&(y>=-.05)&(y<=1.2)&(f.index>=b2)
        base=np.clip(f.available_power.to_numpy()[valid]/CAP,0,1)
        predictions={'persistence':base}
        for rep in REPS:
            artifact=joblib.load(OUT/f'model_{rep}_{horizon}.joblib');c=artifact['config']
            xx=common[valid]
            if artifact['transform'] is not None:xx=np.c_[xx,artifact['transform'].transform(shapes[valid])]
            model=artifact['model'];p=np.zeros((len(xx),len(CENTERS)));p[:,model.classes_]=model.predict_proba(xx)
            forecasts={'mean':p@CENTERS,'median':CENTERS[(np.cumsum(p,axis=1)>=.5).argmax(axis=1)],
                       'tolerance':tolerance_action(p,tolerance)}
            predictions[rep]=np.clip((1-c['blend'])*base+c['blend']*forecasts[c['action']],0,1)
            # Same probability forest, different decision functional: actual objective ablation.
            predictions[rep+'_mean_action']=np.clip((1-c['blend'])*base+c['blend']*forecasts['mean'],0,1)
        for name,q in predictions.items():
            s=measures(y[valid],q,tolerance);b=measures(y[valid],base,tolerance)
            s.update(horizon_minutes=15*horizon,model=name,saved_cny=b['accuracy_charge_cny']-s['accuracy_charge_cny'],
                fee_reduction_pct=100*(b['failed_points']-s['failed_points'])/b['failed_points'])
            summaries.append(s)
            panels.append(pd.DataFrame({'target_time':f.index[valid]+pd.Timedelta(minutes=15*horizon),'horizon_minutes':15*horizon,
                'model':name,'actual_pu':y[valid],'forecast_pu':q,'fee_cny':point_fee(y[valid],q,tolerance),
                'persistence_fee_cny':point_fee(y[valid],base,tolerance)}))
            print('penalty test',horizon,name,s['failed_points'],round(s['saved_cny']),flush=True)
    s=pd.DataFrame(summaries);s.to_csv(OUT/'test_summary.csv',index=False)
    panel=pd.concat(panels,ignore_index=True);panel.to_parquet(OUT/'test_predictions.parquet',index=False)
    panel['local_month']=pd.to_datetime(panel.target_time,utc=True).dt.tz_convert('Asia/Shanghai').dt.strftime('%Y-%m')
    panel.groupby(['horizon_minutes','model','local_month']).agg(points=('fee_cny','size'),fee_cny=('fee_cny','sum'),
        baseline_cny=('persistence_fee_cny','sum')).reset_index().to_csv(OUT/'monthly_fees.csv',index=False)
    rows=[]
    for (h,name),g in panel.groupby(['horizon_minutes','model']):
        stamp=pd.DatetimeIndex(pd.to_datetime(g.target_time,utc=True)).as_unit('ns').asi8
        for length in [3,7,14]:
            a=g.assign(block=stamp//pd.Timedelta(days=length).value).groupby('block')[['fee_cny','persistence_fee_cny']].sum()
            w=np.random.default_rng(41).multinomial(len(a),np.full(len(a),1/len(a)),size=2000)
            draws=100*(1-(w@a.fee_cny)/(w@a.persistence_fee_cny));lo,hi=np.quantile(draws,[.025,.975])
            rows.append({'horizon_minutes':h,'model':name,'block_days':length,'blocks':len(a),
                'reduction_pct':100*(1-g.fee_cny.sum()/g.persistence_fee_cny.sum()),'low':lo,'high':hi})
    pd.DataFrame(rows).to_csv(OUT/'test_intervals.csv',index=False)
    print(s.to_string(index=False))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--phase',choices=['validate','test'],required=True)
    parser.add_argument('--weather',choices=['none','jma','jma_gfs'],default='none');args=parser.parse_args()
    WEATHER=args.weather
    if WEATHER!='none':OUT=OUT/WEATHER;OUT.mkdir(parents=True,exist_ok=True)
    with threadpool_limits(limits=4):validate() if args.phase=='validate' else test()
