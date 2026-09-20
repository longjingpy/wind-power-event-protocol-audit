"""Matched-budget physical information increments beyond scalar controls.

Uses the pre-existing Pizhou representation and per-site train/validation/test
event identities. The reviewer-triggered extension is exploratory. Source tree
probes follow Friedman (2001), doi:10.1214/aos/1013203451; validation-only score
calibration follows the held-out calibration principle in Guo et al. (2017),
arXiv:1706.04599. No external target test labels select the model or calibration.
"""
from pathlib import Path
import argparse,json,sys,zipfile
import joblib
import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar
from scipy.special import softmax
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss
from threadpoolctl import threadpool_limits

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from run_structure_v18 import load_site
from physical_tracking_v18 import weather_targets,CAT,MODELS
from wind_events.representation import polarity_bit
from wind_events.paired_probability import paired_rows

BASE=ROOT/'outputs/protocol_benchmark_v18'
OUT=ROOT/'outputs/protocol_benchmark_v25/polarity'
CONTROLS=['direction','amplitude','duration_hours','power_start','pre_mean']
ARMS=['scalar','scalar_g5','scalar_bit','scalar_g5_bit','scalar_g6','scalar_signed6',
      'scalar_raw25','scalar_g5_random','scalar_g5_reversed','scalar_g5_endpoint',
      'scalar_g5_pre','scalar_g5_post','scalar_g5_internal']
CONTRASTS=[('scalar_g5','scalar'),('scalar_bit','scalar'),('scalar_g5_bit','scalar'),
    ('scalar_g5_bit','scalar_g5'),('scalar_g5_bit','scalar_bit'),('scalar_g5','scalar_bit'),
    ('scalar_g5_bit','scalar_g6'),('scalar_g5_bit','scalar_signed6'),
    ('scalar_g5_bit','scalar_g5_random'),('scalar_g5_reversed','scalar_g5_bit'),
    ('scalar_g5_endpoint','scalar_g5_bit'),('scalar_g5_pre','scalar_g5_bit'),
    ('scalar_g5_post','scalar_g5_bit'),('scalar_g5_internal','scalar_g5_bit')]


def archive_site(site):
    table,shapes,pairs,_=load_site(CAT,site)
    table=table.join(weather_targets(table,site,'legacy'))
    train_ids=set(pd.read_parquet(BASE/'physical_tracking'/f'{site}_training_events.parquet').event_id)
    paired=set(pairs.event_a)|set(pairs.event_b)
    keep=table.event_id.isin(train_ids)|(table.weather_valid & table.split.isin(['validation','test']) & table.event_id.isin(paired))
    d=table[keep].copy().reset_index(drop=True)
    x=shapes[d.array_row.to_numpy(int)]
    d['outcome']=np.where(d.wind_change_ms<=-1.5,0,np.where(d.wind_change_ms>=1.5,2,1))
    assert np.isfinite(x).all() and np.isfinite(d[CONTROLS].to_numpy()).all()
    assert d.event_id.is_unique
    return d,x


def encode(d,x):
    ordinary=joblib.load(MODELS/'pizhou_gaf_pca6_kmeans_k4_s41.joblib')['transform']
    signed=joblib.load(MODELS/'pizhou_gaf_signed_pca6_kmeans_k4_s41.joblib')['transform']
    def apply(transform):return np.vstack([transform.transform(x[i:i+2048]) for i in range(0,len(x),2048)])
    g6=apply(ordinary);g5=g6[:,:5];channel=apply(signed)
    bit=polarity_bit(x);s=d[CONTROLS].to_numpy(float)
    random=np.random.default_rng(250041).choice([-1.,1.],len(d))[:,None]
    inner=x[:,4:21];internal=np.sign(inner[np.arange(len(x)),np.abs(inner).argmax(axis=1)])[:,None]
    result={'scalar':s,'scalar_g5':np.c_[s,g5],'scalar_bit':np.c_[s,bit],
        'scalar_g5_bit':np.c_[s,g5,bit],'scalar_g6':np.c_[s,g6],
        'scalar_signed6':np.c_[s,channel],'scalar_raw25':np.c_[s,x],
        'scalar_g5_random':np.c_[s,g5,random],'scalar_g5_reversed':np.c_[s,g5,-bit],
        'scalar_g5_endpoint':np.c_[s,g5,np.sign(x[:,20])],
        'scalar_g5_pre':np.c_[s,g5,np.sign(x[:,0])],
        'scalar_g5_post':np.c_[s,g5,np.sign(x[:,24])],
        'scalar_g5_internal':np.c_[s,g5,internal]}
    return result


def probability(artifact,x):
    raw=np.clip(artifact['model'].predict_proba(x),1e-8,1)
    return softmax(np.log(raw)/artifact['temperature'],axis=1)


def train_heads(site,d,features):
    train=d.split.eq('train').to_numpy();val=d.split.eq('validation').to_numpy()
    y=d.outcome.to_numpy(int);fitted={}
    folder=OUT/'models';folder.mkdir(exist_ok=True)
    for name,x in features.items():
        path=folder/f'{site}_{name}.joblib'
        if path.exists():
            fitted[name]=joblib.load(path);continue
        candidates=[]
        for leaf in (7,15):
            model=HistGradientBoostingClassifier(max_leaf_nodes=leaf,max_iter=200,learning_rate=.05,
                l2_regularization=1.,early_stopping=False,random_state=41).fit(x[train],y[train])
            pv=np.clip(model.predict_proba(x[val]),1e-8,1)
            candidates.append((log_loss(y[val],pv,labels=[0,1,2]),leaf,model,pv))
        _,leaf,model,pv=min(candidates,key=lambda r:(r[0],r[1]))
        temp=float(minimize_scalar(lambda t:log_loss(y[val],softmax(np.log(pv)/t,axis=1),labels=[0,1,2]),bounds=(.5,5),method='bounded').x)
        artifact={'model':model,'temperature':temp,'leaf':leaf,'site':site,'arm':name,
                  'train_events':int(train.sum()),'validation_events':int(val.sum()),'features':x.shape[1]}
        joblib.dump(artifact,path);fitted[name]=artifact
        print('FIT',site,name,int(train.sum()),leaf,flush=True)
    return fitted


def report(dataset,d,predictions,source,comparisons=CONTRASTS):
    folder=OUT/dataset;folder.mkdir(exist_ok=True)
    record=d[['event_id','time_start','outcome']].copy()
    for name,p in predictions.items():
        for k in range(3):record[f'p_{name}_{k}']=p[:,k]
    record.to_parquet(folder/'predictions.parquet',index=False)
    scores=[];effects=[]
    for days in [3,7,14]:
        a,b=paired_rows(d,predictions,comparisons,days)
        scores += [{'dataset':dataset,'source':source,**r} for r in a]
        effects += [{'dataset':dataset,'source':source,**r} for r in b]
    pd.DataFrame(scores).to_csv(folder/'scores.csv',index=False)
    pd.DataFrame(effects).to_csv(folder/'paired.csv',index=False)
    print('SCORED',dataset,len(d),flush=True)


def lidar_dataset(turbine):
    from wind_events import Protocol,regularize,build_catalog
    data_path=ROOT/'data/external_samples/hill_of_towie_v21/2026.zip'
    parts=[]
    with zipfile.ZipFile(data_path) as archive:
        for month in range(1,5):
            with archive.open(f'tblSCTurGrid_2026_{month:02d}.csv') as stream:
                z=pd.read_csv(stream,usecols=['TimeStamp','StationId','wtc_ActPower_mean'])
            parts.append(z[z.StationId.eq(2304509+int(turbine[1:]))])
    z=pd.concat(parts).drop_duplicates();power=z.wtc_ActPower_mean.to_numpy(float)
    t,x,ok,_=regularize(pd.to_datetime(z.TimeStamp,utc=True),power,np.isfinite(power)&(power>=0)&(power<=2760),10,30,'end')
    scale=json.loads((CAT/'hill'/turbine/'audit.json').read_text())['scale']
    events,shapes,_=build_catalog('hill_2026',turbine,t,x,ok,Protocol(),external_test=True,
        scale_override=(scale,'frozen_hill2020_training_q995'),include_composites=False)
    target=pd.read_parquet(BASE/'lidar_confirmation'/f'{turbine}_signed_shift0.parquet')[['event_id','outcome']]
    d=target.merge(events,on='event_id',validate='one_to_one')
    assert len(d)==len(target)
    return d,shapes[d.shape_row.to_numpy(int)]


def field_calibration(d,source_predictions):
    start=pd.to_datetime(d.time_start,utc=True)-pd.Timedelta(hours=2)
    end=pd.to_datetime(d.time_end,utc=True)+pd.Timedelta(minutes=150)
    b1=pd.Timestamp('2026-03-14',tz='UTC');b2=pd.Timestamp('2026-04-07',tz='UTC')
    train=(end<b1).to_numpy();val=((start>=b1)&(end<b2)).to_numpy();test=(start>=b2).to_numpy()
    models={};out={};y=d.outcome.to_numpy(int)
    for name,p in source_predictions.items():
        x=np.log(np.clip(p,1e-8,1));candidates=[]
        for c in [.1,1,10]:
            m=LogisticRegression(C=c,max_iter=1000).fit(x[train],y[train])
            candidates.append((log_loss(y[val],m.predict_proba(x[val]),labels=[0,1,2]),c,m))
        _,c,m=min(candidates,key=lambda r:(r[0],r[1]));out[name]=m.predict_proba(x[test]);models[name]=m
    return test,out,models


def noise_tests(dataset,d,x,features,heads,calibrators=None):
    """Perturb the representation channel while freezing scalar controls.

Noise is relative to the pre-normalization shape scale. Recentring at the
event-start coordinate and renormalizing keeps the unit-domain constraint.
Scalar covariates remain fixed: this is an encoding-channel stress test,
not a new detector or a full noisy-SCADA experiment.
"""
    ordinary=joblib.load(MODELS/'pizhou_gaf_pca6_kmeans_k4_s41.joblib')['transform']
    s=d[CONTROLS].to_numpy(float);clean_bit=polarity_bit(x).ravel()
    def predict(name,z):
        p=probability(heads[name],z)
        return p if calibrators is None else calibrators[name].predict_proba(np.log(np.clip(p,1e-8,1)))
    clean={n:predict(n,features[n]) for n in ['scalar','scalar_g5','scalar_g5_bit']}
    metrics=[];effects=[];robust=[]
    for seed in [101,202,303]:
        rng=np.random.default_rng(seed);noise=rng.normal(size=x.shape)
        for sigma in [0.,.01,.05,.10,.20,.40]:
            v=x+sigma*(noise-noise[:,4,None]);scale=np.abs(v).max(axis=1)
            v=np.divide(v,scale[:,None],out=np.zeros_like(v),where=scale[:,None]>0)
            g5=np.vstack([ordinary.transform(v[i:i+2048])[:,:5] for i in range(0,len(v),2048)])
            bit=polarity_bit(v)
            p={'clean_protected':clean['scalar_g5_bit'],
               'noisy_protected':predict('scalar_g5_bit',np.c_[s,g5,bit]),
               'noisy_angular':predict('scalar_g5',np.c_[s,g5])}
            a,b=paired_rows(d,p,[('noisy_protected','noisy_angular'),('noisy_protected','clean_protected')],7,2000)
            metrics += [{'seed':seed,'noise_ratio':sigma,**r} for r in a]
            effects += [{'seed':seed,'noise_ratio':sigma,**r} for r in b]
            robust.append({'seed':seed,'noise_ratio':sigma,'events':len(d),'bit_flip_fraction':float((bit.ravel()!=clean_bit).mean())})
    for rate in [.25,.5,1.]:
        v=features['scalar_g5_bit'].copy();rng=np.random.default_rng(404)
        flip=rng.random(len(v))<rate;v[flip,-1]*=-1
        p={'clean':clean['scalar_g5_bit'],'wrong_test_bit':predict('scalar_g5_bit',v)}
        a,b=paired_rows(d,p,[('wrong_test_bit','clean')],7)
        metrics += [{'seed':404,'test_flip_probability':rate,**r} for r in a]
        effects += [{'seed':404,'test_flip_probability':rate,**r} for r in b]
    folder=OUT/dataset
    pd.DataFrame(metrics).to_csv(folder/'noise_scores.csv',index=False)
    pd.DataFrame(effects).to_csv(folder/'noise_paired.csv',index=False)
    pd.DataFrame(robust).to_csv(folder/'anchor_flip.csv',index=False)
    # Both extrema close to equal magnitude can switch the global anchor sign.
    margin=np.abs(x.max(axis=1)+x.min(axis=1))
    pd.DataFrame({'event_id':d.event_id,'positive_negative_extreme_margin':margin,
        'normalized_max_abs':np.abs(x).max(axis=1),'amplitude':d.amplitude,'power_range':d.power_range,
        'anchor_sign':clean_bit,'endpoint_sign':np.sign(x[:,20])}).to_parquet(folder/'anchor_support.parquet',index=False)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--site',required=True,choices=['pizhou','suining','yandun','lahaute','hill','lidar','smarteole'])
    parser.add_argument('--noise',action='store_true');args=parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    if args.site in ['pizhou','suining','yandun','lahaute','hill']:
        d,x=archive_site(args.site);features=encode(d,x);heads=train_heads(args.site,d,features)
        test=d.split.eq('test').to_numpy();target=d[test].reset_index(drop=True)
        p={n:probability(heads[n],v[test]) for n,v in features.items()}
        report('era5_'+args.site,target,p,args.site+'_training')
        if args.noise:noise_tests('era5_'+args.site,target,x[test],{n:v[test] for n,v in features.items()},heads)
    elif args.site=='lidar':
        heads={n:joblib.load(OUT/'models'/f'hill_{n}.joblib') for n in ARMS}
        for turbine in ['T11','T07']:
            d,x=lidar_dataset(turbine);features=encode(d,x);p={n:probability(heads[n],v) for n,v in features.items()}
            test,calibrated,calibrators=field_calibration(d,p);target=d[test].reset_index(drop=True)
            expected=pd.read_parquet(BASE/'lidar_confirmation/chronological_calibration'/f'{turbine}_predictions.parquet')
            assert set(expected.event_id)==set(target.event_id)
            report('lidar_'+turbine,target,calibrated,'Hill2020_head_then_chronological_LiDAR_calibration')
            joblib.dump(calibrators,OUT/'models'/f'{turbine}_calibrators.joblib')
            if args.noise:noise_tests('lidar_'+turbine,target,x[test],{n:v[test] for n,v in features.items()},heads,calibrators)
    else:
        folder=ROOT/'outputs/protocol_benchmark_v19/smarteole';tables=[];xs=[]
        for path in sorted((folder/'catalogs').glob('*_events.parquet')):
            turbine=path.stem.replace('_events','');events=pd.read_parquet(path)
            targets=pd.read_parquet(folder/'scores'/f'{turbine}_targets.parquet').rename(columns={'outcome_class':'outcome'})
            d=targets.merge(events,on='event_id',validate='one_to_one');assert len(d)==len(targets)
            x=np.load(folder/'catalogs'/f'{turbine}_shapes.npy')[d.shape_row.to_numpy(int)]
            tables.append(d);xs.append(x)
        d=pd.concat(tables,ignore_index=True);x=np.vstack(xs);features=encode(d,x)
        heads={n:joblib.load(OUT/'models'/f'pizhou_{n}.joblib') for n in ARMS}
        report('smarteole',d,{n:probability(heads[n],v) for n,v in features.items()},'Pizhou_training_no_target_fit')
        if args.noise:noise_tests('smarteole',d,x,features,heads)


if __name__=='__main__':
    with threadpool_limits(limits=2):main()
