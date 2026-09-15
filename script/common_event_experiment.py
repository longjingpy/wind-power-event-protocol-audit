"""Common retrospective detection contract; no event ground-truth claims."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
R=Path(__file__).resolve().parents[1]; OUT=R/'outputs/dynamic_events_v3'

def series(audit_dir=OUT, exclude_hill_shutdown=True):
    for p in sorted((R/'data/event_clean_v2/pizhou').glob('*.csv.gz')):
        d=pd.read_csv(p); yield 'pizhou',p.name.split('.')[0],pd.to_datetime(d.timestamp_start_utc,utc=True),d.power_kw,d.usable_power,None
    for p in sorted((R/'data/external_samples/hill_of_towie/clean_native').glob('T[0-9][0-9].csv.gz')):
        d=pd.read_csv(p); d.index=pd.to_datetime(d.timestamp_start_utc,utc=True)
        s=d.power_kw.resample('30min').mean(); native_ok=d.power_valid & (~d.suspected_shutdown if exclude_hill_shutdown else True); ok=native_ok.resample('30min').sum().eq(3)
        yield 'hill',p.name.split('.')[0],s.index,s,ok,2300.
    base=R/'data/whole-SCADA-data/wind_power/jiangsu/xuzhou/suining'
    for p in sorted(base.rglob('*.csv')):
        d=pd.read_csv(p,encoding='gb18030'); d.index=pd.to_datetime(d['时间']).dt.tz_localize('Asia/Shanghai').dt.tz_convert('UTC')
        s=d['发电机有功功率'].resample('30min').mean(); ok=d['发电机有功功率'].ge(0).resample('30min').sum().eq(3)
        yield 'suining',str(d['名称'].iloc[0]),s.index,s,ok,None
    d=pd.read_csv(R/'data/external_samples/la_haute_borne/la-haute-borne-data-2014-2015.csv')
    for tid,g in d.groupby('Wind_turbine_name'):
        g=g.copy(); g.index=pd.to_datetime(g.Date_time,utc=True)
        duplicate=g.index.duplicated(keep=False)
        if duplicate.any():
            g.loc[duplicate].to_csv(audit_dir/(str(tid)+"_conflict_times.csv.gz"),index=False)
            g=g.loc[~duplicate]
        s=g.P_avg.resample('30min').mean(); ok=g.P_avg.between(0,2460).resample('30min').sum().eq(3)
        yield 'lahaute',tid,s.index,s,ok,2050.
    for p in sorted((R/'data/event_clean_v2/yandun').glob('*.csv.gz')):
        if p.name=='unmatched_ids.csv.gz': continue
        g=pd.read_csv(p)
        yield 'yandun',str(g.turbine_id.iloc[0]),pd.to_datetime(g.timestamp_start_utc,utc=True),g.power_kw,g.usable_power,float(g.rated_power_kw.iloc[0])

def main():
    OUT.mkdir(parents=True,exist_ok=True); rows=[]; shapes=[]; diagnostics=[]
    rng=np.random.default_rng(42)
    for site,tid,t,p,ok,cap in series():
        t=pd.DatetimeIndex(t); x=np.asarray(p,float); valid=np.asarray(ok,bool)&np.isfinite(x)
        b1=t[0]+.6*(t[-1]-t[0]); b2=t[0]+.8*(t[-1]-t[0])
        scale=cap if cap else np.quantile(x[valid & (t<b1)],.995) if (valid & (t<b1)).any() else np.nan
        if not np.isfinite(scale) or scale<=0: continue
        x=x/scale; v=pd.Series(x); ret=v.diff(2)
        lo=ret.shift(1).rolling(48,min_periods=48).quantile(.05); hi=ret.shift(1).rolling(48,min_periods=48).quantile(.95)
        window_ok=pd.Series(valid).rolling(9,center=True).sum().eq(9).to_numpy()
        contiguous=pd.Series(t).diff().dt.total_seconds().eq(1800).rolling(8).sum().eq(8).shift(-4).fillna(False).to_numpy()
        window_ok &= contiguous
        warm=pd.Series(valid).rolling(51).sum().eq(51).to_numpy()
        hits={'threshold_020':ret.abs().ge(.2).to_numpy(),'financial_tail':((ret.lt(lo)|ret.gt(hi)) & ret.abs().ge(.1)).to_numpy(),'mean_shift':(v.rolling(2).mean()-v.shift(2).rolling(2).mean()).abs().ge(.2).to_numpy()}
        sets={}; pool={}
        for method,hit in hits.items():
            ids=np.flatnonzero(hit & window_ok & warm); keep=[]; last=-100
            for i in ids:
                if i-last<9: continue
                if t[i-4]<b1<=t[i+4] or t[i-4]<b2<=t[i+4]: continue
                keep.append(i); last=i
            sets[method]=set(keep)
            for i in keep: pool.setdefault(i,[]).append(method)
        count=len(pool)
        candidates=np.flatnonzero(window_ok & warm)
        candidates=np.array([i for i in candidates if not any(abs(i-j)<=8 for j in pool)],dtype=int)
        for i in rng.choice(candidates,min(count,len(candidates)),replace=False): pool[int(i)]=['random_control']
        for i,methods in sorted(pool.items()):
            if t[i-4]<b1<=t[i+4] or t[i-4]<b2<=t[i+4]: continue
            w=x[i-4:i+5]; centered=w-w[0]; norm=np.max(np.abs(centered))
            if norm<1e-8: continue
            shape=centered/norm
            rows.append({'site':site,'turbine':tid,'time':str(t[i]),'split':'train' if t[i+4]<b1 else 'validation' if t[i+4]<b2 else 'test','methods':';'.join(methods),'scale':scale,'scale_basis':'nameplate' if cap else 'early_60pct_q995','amplitude':float(w[-1]-w[0]),'mean_power':float(w.mean()),'variation':float(np.abs(np.diff(shape)).sum()),'month':t[i].month})
            shapes.append(shape)
        diagnostics.append({'site':site,'turbine':tid,'start':str(t.min()),'end':str(t.max()),'eligible_windows':int((window_ok & warm).sum()),'detections':{k:len(v) for k,v in sets.items()},'exact_anchor_intersection':len(sets['threshold_020']&sets['financial_tail'])})
        print(site,tid,count,flush=True)
    pd.DataFrame(rows).to_csv(OUT/'windows.csv.gz',index=False)
    np.save(OUT/'shapes.npy',np.asarray(shapes,dtype=np.float32))
    (OUT/'detection_report.json').write_text(json.dumps({'contract':'30min; nine points; common 51-point valid history; 60/20/20 time split with purged boundary windows; financial trailing 5/95% tails with absolute change >=0.1; threshold >=0.2; mean shift >=0.2; random excludes +-4h around event anchor; retrospectively aligned, not physical truth','provisional':'Yandun uses previous 15min cleaning; external unnamed capacity uses local early-period calibration; random controls are not month-matched','turbines':diagnostics},indent=2))
if __name__=='__main__': main()
