"""Hold event boundaries and wind targets fixed while restoring 10-min power.

This is an observation-support ablation: detectors remain on their frozen
30-min grid. Both scalar controls and trajectory encodings receive the same
native-resolution power data. It is not a comparison with a weaker-input
scalar baseline. Primary relative clocks are retained from the earlier track.
"""
from pathlib import Path
import argparse,json,zipfile
import numpy as np
import pandas as pd
from prepare_process_v26 import ROOT,OUT,scalar_features
from wind_events import Protocol,regularize
from wind_events.catalog import describe


def series_for(dataset,turbines):
    if dataset=='smarteole':
        path=ROOT/'data/external_samples/smarteole_wfc/clean_native/SMARTEOLE_WakeSteering_SCADA_1minData.csv'
        cols=['time']+[f'active_power_{int(t[3:])}_avg' for t in turbines]
        d=pd.read_csv(path,usecols=cols);d.time=pd.to_datetime(d.time,utc=True)
        d=d.set_index('time').sort_index();out={}
        for t in turbines:
            v=d[f'active_power_{int(t[3:])}_avg']
            group=v.resample('10min').agg(['mean','count'])
            out[t]=group['mean'].where(group['count'].eq(10))
        return out
    turbine=dataset[6:];parts=[]
    with zipfile.ZipFile(ROOT/'data/external_samples/hill_of_towie_v21/2026.zip') as archive:
        for month in range(1,5):
            with archive.open(f'tblSCTurGrid_2026_{month:02d}.csv') as f:
                d=pd.read_csv(f,usecols=['TimeStamp','StationId','wtc_ActPower_mean'])
            parts.append(d[d.StationId.eq(2304509+int(turbine[1:]))])
    d=pd.concat(parts).drop_duplicates();power=d.wtc_ActPower_mean.to_numpy(float)
    t,p,ok,_=regularize(pd.to_datetime(d.TimeStamp,utc=True),power,np.isfinite(power)&(power>=0)&(power<=2760),10,10,'end')
    return {turbine:pd.Series(p,index=pd.DatetimeIndex(t)).where(ok)}


def main():
    p=argparse.ArgumentParser();p.add_argument('--dataset',required=True,choices=['lidar_T11','lidar_T07','smarteole']);a=p.parse_args()
    original=OUT/a.dataset;folder=OUT/(a.dataset+'_native10');folder.mkdir(exist_ok=True)
    if (folder/'selection.json').exists():raise RuntimeError('Native representation inputs already locked')
    d=pd.read_parquet(original/'events.parquet');arrays=np.load(original/'arrays.npz')
    series=series_for(a.dataset,sorted(d.turbine.unique()));rows=[];shapes=[];indices=[];excluded=[]
    for i,row in d.iterrows():
        wind_series=series[row.turbine]
        values=wind_series.to_numpy(float)/float(row.scale)
        start=wind_series.index.get_indexer([pd.Timestamp(row.time_start)])[0]
        end=wind_series.index.get_indexer([pd.Timestamp(row.time_end)])[0]
        if start<12 or end<0 or end+12>=len(values) or not np.isfinite(values[start-12:end+13]).all():
            excluded.append(row.event_id);continue
        description,x=describe(values,start,end,Protocol(resolution_minutes=10))
        if x is None:excluded.append(row.event_id);continue
        new=row.to_dict();new.update(description);rows.append(new);shapes.append(x);indices.append(i)
    frame=pd.DataFrame(rows);x=np.vstack(shapes);s=scalar_features(frame,x)
    frame.to_parquet(folder/'events.parquet',index=False)
    np.savez_compressed(folder/'arrays.npz',shape=x,scalar=s,wind_change=arrays['wind_change'][indices],process_class=arrays['process_class'][indices])
    protocol=json.loads((original/'data_protocol.json').read_text())
    protocol.update(dataset=a.dataset+'_native10',status='PREPARED_NO_MODEL_RESULTS',rows=len(frame),
        parent_dataset=a.dataset,parent_rows=len(d),input_power_minutes=10,detector_boundary_minutes=30,
        split_counts=frame.split.value_counts().to_dict(),unchanged_event_ids=not excluded,
        excluded_missing_native_power=len(excluded),scalar_resolution='same native10 observations as the shape inputs',
        relative_clock='Hill SCADA interval-end shifted to start as in the parent track; Wind10 primary clock unchanged')
    (folder/'data_protocol.json').write_text(json.dumps(protocol,indent=2))
    (folder/'excluded_event_ids.json').write_text(json.dumps(excluded))
    print(json.dumps(protocol,indent=2),flush=True)


if __name__=='__main__':main()
