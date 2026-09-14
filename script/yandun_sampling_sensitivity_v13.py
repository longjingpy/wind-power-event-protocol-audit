"""Yandun native/30/60-minute sampling sensitivity using the frozen threshold rule."""
from pathlib import Path
import warnings
import pandas as pd
import numpy as np
warnings.filterwarnings("ignore", category=FutureWarning)
ROOT=Path(__file__).resolve().parents[1]; BASE=ROOT/'data/whole-SCADA-data/wind_power/xinjiang/yandun'; OUT=ROOT/'outputs/yandun_sampling_v13'; OUT.mkdir(parents=True,exist_ok=True)
def main():
    meta=pd.read_csv(BASE/'machine_meta.csv').set_index('machine_num')
    d=pd.read_csv(BASE/'scadas_20240216-20240824_single.csv'); d['pow_fan_id']=pd.to_numeric(d['pow_fan_id'],errors='coerce'); d=d[d['pow_fan_id'].isin(meta.index)].copy(); d['time']=pd.to_datetime(d['timestamp']).dt.tz_localize('Asia/Shanghai').dt.tz_convert('UTC')
    rows=[]
    for tid,g in d.groupby('pow_fan_id'):
        cap=float(meta.loc[tid,'rated_power']); g=g.sort_values('time').set_index('time'); g['valid']=g['real_power'].between(0,1.2*cap)
        for freq in ['15min','30min','60min']:
            p=g.real_power.where(g.valid).resample(freq).mean(); n=g.valid.resample(freq).sum(); expected={'15min':1,'30min':2,'60min':4}[freq]; usable=p.notna() & n.eq(expected)
            x=p/cap; delta=x-x.shift(4 if freq=='15min' else 2 if freq=='30min' else 1); eligible=usable & usable.shift(1).fillna(False)
            hits=(delta.abs()>=.2)&eligible; gap=(g.index.to_series().diff().dt.total_seconds()>900).sum()
            rows.append({'turbine':int(tid),'frequency':freq,'grid_rows':len(p),'usable_rows':int(usable.sum()),'threshold_4h_candidates':int(hits.sum()),'median_abs_change':float(delta[usable].abs().median()),'native_gaps_gt15min':int(gap)})
    out=pd.DataFrame(rows); out.to_csv(OUT/'yandun_sampling_summary.csv',index=False); print(out.groupby('frequency')[['grid_rows','usable_rows','threshold_4h_candidates']].sum().to_string())
if __name__=='__main__':main()
