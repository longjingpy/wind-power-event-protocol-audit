"""Native minute-to-quarter-hour point track for a policy-rule simulation.

The Jiangsu 2022 Article 44 refers to power at forecast time nodes. Preserve
actual minute samples at quarter hours; use only samples before issue as
inputs. A 15-minute mean track is retained separately, never silently equated
with these points. Capacity comes from the provider-supplied filename note.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/protocol_benchmark_v24/economics/jiangsu_native'
CAPACITY=87.45


def read(path):
    d=pd.read_csv(path,encoding='gb18030',usecols=['时间','风速','发电机有功功率'])
    d=d.rename(columns={'时间':'timestamp','风速':'wind','发电机有功功率':'power'})
    return d.set_index('timestamp')


def main():
    OUT.mkdir(parents=True,exist_ok=True);panels=[];audit=[]
    sources=sorted((ROOT/'data/whole-SCADA-data/wind_power/jiangsu/xuzhou/pizhou').rglob('*.csv'))
    assert len(sources)==33
    for source in sources:
        key=source.name.split('_')[0];later=list((ROOT/'data/real').glob(key+'_*.csv'));assert len(later)==1
        a,b=read(source),read(later[0]);same=a.index.intersection(b.index)
        np.testing.assert_allclose(a.loc[same,['power','wind']],b.loc[same,['power','wind']],equal_nan=True)
        d=pd.concat([a,b.loc[~b.index.isin(a.index)]]).sort_index()
        d.index=pd.to_datetime(d.index).tz_localize('Asia/Shanghai').tz_convert('UTC')
        if not d.index.is_unique:raise ValueError('Repeated timestamp')
        native=pd.date_range(d.index.min(),d.index.max(),freq='1min')
        d=d.reindex(native);d.power=d.power.where(np.isfinite(d.power)&d.power.ge(-150))
        d.wind=d.wind.where(d.wind.between(0,75))
        clock=pd.date_range(d.index.min().ceil('15min'),d.index.max().floor('15min'),freq='15min')
        past=clock-pd.Timedelta(minutes=1)
        frame=pd.DataFrame(index=clock)
        frame['target_power']=d.power.reindex(clock).to_numpy()/1000
        frame['available_power']=d.power.reindex(past).to_numpy()/1000
        frame['past15_power']=d.power.rolling(15,min_periods=15).mean().reindex(past).to_numpy()/1000
        frame['wind']=d.wind.rolling(15,min_periods=15).mean().reindex(past).to_numpy()
        panels.append(frame)
        audit.append({'turbine':key,'minute_rows':len(d),'overlap_rows_verified':len(same),
                      'valid_quarter_power':int(frame.target_power.notna().sum()),'maximum_kw':float(d.power.max())})
        print('native quarters',key,flush=True)
    result=pd.DataFrame(index=panels[0].index)
    for col in ['target_power','available_power','past15_power']:
        block=pd.concat([p[col] for p in panels],axis=1)
        result[col]=block.sum(axis=1,min_count=33)
        result[col]=result[col].where(result[col].between(-.05*CAPACITY,1.2*CAPACITY))
    w=pd.concat([p.wind for p in panels],axis=1)
    result['wind']=w.mean(axis=1).where(w.notna().sum(axis=1).eq(33))
    result.index.name='issue_time';result.to_parquet(OUT/'farm_15min.parquet')
    report={'status':'COMPLETE','capacity_mw':CAPACITY,
        'capacity_source':'data/real/时间：2024.7-2025.2，分分钟，33台风机，装机容量87.45mw',
        'capacity_evidence':'provider-supplied metadata note, not manufacturer verification',
        'time':'source Asia/Shanghai; computation UTC; input samples at least 1 minute before issue',
        'actual':'native point at the target quarter-hour; no replication from 30-minute means',
        'rows':len(result),'complete_target_points':int(result.target_power.notna().sum()),'turbines':audit}
    (OUT/'data_protocol.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print(result.notna().sum().to_string())


if __name__=='__main__':main()
