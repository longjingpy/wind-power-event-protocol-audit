"""Prepare independent measured wind-process targets without scoring models.

Power-event construction reuses Protocol v18. Native wind completeness and
chronological context restrictions are fixed before prediction comparison.
Primitive and composite episodes are included, with duplicate intervals merged.
"""
from pathlib import Path
import argparse,json,sys,zipfile
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from wind_events import Protocol,regularize,build_catalog
from wind_events.matching import pair_catalog

BASE=ROOT/'outputs/protocol_benchmark_v18'
OUT=ROOT/'outputs/protocol_benchmark_v26'
TAG='r30_a0.2_q0.05_training_q995'
S5=['direction','amplitude','duration_hours','power_start','pre_mean']
S19=S5+['power_range','total_variation','max_abs_rate_per_hour','max_abs_chord_residual',
    'curvature_l1','post_mean','shape_normalizer','min_phase','max_phase','internal_mean',
    'internal_std','positive_chord','negative_chord','chord_extreme_phase']


def wind_curves(table,wind):
    """Interpolate only inside fully observed consecutive native wind supports."""
    wind=wind.sort_index()
    step=pd.Timedelta(minutes=10)
    wind=wind.reindex(pd.date_range(wind.index.min(),wind.index.max(),freq=step))
    time=wind.index.as_unit('ns').asi8;values=wind.to_numpy(float)
    si=wind.index.get_indexer(pd.to_datetime(table.time_start,utc=True))
    ei=wind.index.get_indexer(pd.to_datetime(table.time_end,utc=True))
    keep=(si>=0)&(ei>=0)&((ei-si)>=6)&((ei-si)<=24)
    missing=np.r_[0,np.cumsum(~np.isfinite(values))]
    safe_s=np.maximum(si,0);safe_e=np.maximum(ei,0)
    keep &= (missing[safe_e+1]-missing[safe_s])==0
    indices=np.flatnonzero(keep);curves=[]
    for row in indices:
        a,b=si[row],ei[row]
        curve=np.interp(np.linspace(time[a],time[b],17),time[a:b+1],values[a:b+1])
        curves.append(curve-curve[0])
    return indices,np.asarray(curves,float)


def scalar_features(d,x):
    inner=x[:,4:21]*d.shape_normalizer.to_numpy()[:,None]+d.power_start.to_numpy()[:,None]
    chord=inner[:,0,None]+(inner[:,-1]-inner[:,0])[:,None]*np.linspace(0,1,17)
    residual=inner-chord
    d=d.copy()
    d['min_phase']=inner.argmin(axis=1)/16;d['max_phase']=inner.argmax(axis=1)/16
    d['internal_mean']=inner.mean(axis=1);d['internal_std']=inner.std(axis=1)
    d['positive_chord']=residual.max(axis=1);d['negative_chord']=residual.min(axis=1)
    d['chord_extreme_phase']=np.abs(residual).argmax(axis=1)/16
    return d[S19].to_numpy(float)


def process_class(curves):
    up=(curves-np.minimum.accumulate(curves,axis=1)).max(axis=1)>=1.5
    down=(np.maximum.accumulate(curves,axis=1)-curves).max(axis=1)>=1.5
    return up.astype(int)+2*down.astype(int)


def matched_unique(table,shapes):
    eligible=table[table.representation_eligible & table.duration_hours.between(1,4)].copy()
    pairs,_=pair_catalog(eligible,configurations=sorted(eligible.config.unique()))
    ids=set(pairs.event_a)|set(pairs.event_b)
    selected=eligible[eligible.event_id.isin(ids)].copy()
    key=['turbine','time_start','time_end']
    flags=selected.assign(has_composite=selected.event_level.eq('composite')).groupby(key).has_composite.max()
    selected=selected.sort_values('event_id').drop_duplicates(key).set_index(key).join(flags).reset_index()
    return selected,shapes[selected.shape_row.to_numpy(int)],len(eligible),len(ids)


def lidar_data(turbine):
    parts=[]
    with zipfile.ZipFile(ROOT/'data/external_samples/hill_of_towie_v21/2026.zip') as archive:
        for month in range(1,5):
            with archive.open(f'tblSCTurGrid_2026_{month:02d}.csv') as f:
                d=pd.read_csv(f,usecols=['TimeStamp','StationId','wtc_ActPower_mean'])
            parts.append(d[d.StationId.eq(2304509+int(turbine[1:]))])
    d=pd.concat(parts).drop_duplicates();power=d.wtc_ActPower_mean.to_numpy(float)
    t,p,ok,_=regularize(pd.to_datetime(d.TimeStamp,utc=True),power,np.isfinite(power)&(power>=0)&(power<=2760),10,30,'end')
    scale=json.loads((BASE/'catalogs'/TAG/'hill'/turbine/'audit.json').read_text())['scale']
    table,x,_=build_catalog('hill_2026',turbine,t,p,ok,Protocol(),external_test=True,
        scale_override=(scale,'frozen_hill2020_training_q995'),include_composites=True)
    unit='2428' if turbine=='T11' else '5060'
    wind=pd.read_parquet(BASE/'lidar_confirmation'/f'lidar_{unit}_quality.parquet')
    series=wind.wind_ms.where(wind.valid);series.index=pd.to_datetime(series.index,utc=True)
    return [(table,x)],series,pd.Timestamp('2026-03-14',tz='UTC'),pd.Timestamp('2026-04-07',tz='UTC')


def smarteole_data():
    base=ROOT/'outputs/protocol_benchmark_v19/smarteole';items=[];starts=[];ends=[]
    for path in sorted((base/'catalogs').glob('*_events.parquet')):
        turbine=path.stem.replace('_events','')
        items.append((pd.read_parquet(path),np.load(base/'catalogs'/f'{turbine}_shapes.npy')))
        source=pd.read_parquet(base/f'{turbine}_30min.parquet')
        starts.append(source.index.min());ends.append(source.index.max()+pd.Timedelta(minutes=30))
    start,end=min(starts),max(ends);span=end-start
    wind=pd.read_parquet(base/'windcube_1min.parquet')
    wind.time=pd.to_datetime(wind.time,utc=True)
    wind=wind.set_index('time').sort_index()
    if not wind.index.is_unique:raise ValueError('Duplicate WindCube time')
    values=wind.ws_avg_80.where(wind.avail_80.gt(0)&wind.ws_avg_80.between(0,60))
    bins=values.resample('10min').agg(['mean','count'])
    series=bins['mean'].where(bins['count']>=8)
    return items,series,start+.6*span,start+.8*span


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--dataset',required=True,choices=['lidar_T11','lidar_T07','smarteole'])
    args=parser.parse_args();folder=OUT/args.dataset;folder.mkdir(parents=True,exist_ok=True)
    if (folder/'selection.json').exists():raise RuntimeError('Model selection exists; keep prepared dataset fixed')
    items,wind,b1,b2=smarteole_data() if args.dataset=='smarteole' else lidar_data(args.dataset[6:])
    tables=[];xs=[];ys=[];coverage=[]
    for table,x in items:
        d,z,eligible,matched=matched_unique(table,x)
        indices,y=wind_curves(d,wind);d=d.iloc[indices].reset_index(drop=True);z=z[indices]
        a=pd.to_datetime(d.time_start,utc=True)-pd.Timedelta(hours=2)
        b=pd.to_datetime(d.time_end,utc=True)+pd.Timedelta(minutes=150)
        d['split']=np.select([b<b1,(a>=b1)&(b<b2),a>=b2],['train','validation','test'],default='boundary')
        keep=d.split.ne('boundary').to_numpy()
        coverage.append({'turbine':str(table.turbine.iloc[0]),'eligible_before_match':eligible,'matched_ids':matched,
            'wind_complete_unique_intervals':len(d),'retained_after_split':int(keep.sum())})
        tables.append(d[keep]);xs.append(z[keep]);ys.append(y[keep])
    d=pd.concat(tables,ignore_index=True);x=np.vstack(xs);y=np.vstack(ys);s=scalar_features(d,x)
    assert d.event_id.is_unique and len(d)==len(x)==len(y) and np.isfinite(np.c_[x,y,s]).all()
    assert np.allclose(x[:,4],0) and np.allclose(y[:,0],0)
    assert all((d.split==split).sum()>=50 for split in ['train','validation','test'])
    d.to_parquet(folder/'events.parquet',index=False)
    np.savez_compressed(folder/'arrays.npz',shape=x,scalar=s,wind_change=y,process_class=process_class(y))
    pd.DataFrame(coverage).to_csv(folder/'coverage.csv',index=False)
    protocol={'status':'PREPARED_NO_MODEL_RESULTS','dataset':args.dataset,'rows':len(d),'split_counts':d.split.value_counts().to_dict(),
        'train_end':str(b1),'validation_end':str(b2),'scalar_columns':S19,'matched':True,
        'population':'unique turbine/start/end intervals; primitive and composite eligible',
        'duration_minutes':[60,240],'wind_native_minutes':10,'target_points':17,
        'weather_QC':'continuous valid support; WindCube ten-minute mean requires >=8 minute values',
        'context_purge':'start minus 120min and end plus150min fit one split',
        'task':'retrospective measured-wind trajectory reconstruction, not an issued weather forecast'}
    (folder/'data_protocol.json').write_text(json.dumps(protocol,indent=2))
    print(json.dumps(protocol,indent=2),flush=True)


if __name__=='__main__':main()
