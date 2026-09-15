"""Prepare blind real-SCADA annotation windows, keeping machine suggestions separate.

Rules are operational definitions, not borrowed physical truth. Sampling is a
stratified review sample, NOT a prevalence estimate or a test set with labels.
"""
from pathlib import Path
import argparse
import json
import re
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs/annotation_v9'
SEED = 20260915
STRATA = ['downward', 'upward', 'low_output', 'screen_disagreement', 'random_control']


def bool_values(s):
    return s.astype(str).str.lower().isin(['true', '1'])


def continuous_low_runs(times, power, scale, nominal_min, minimum_min=60):
    """Return half-open low-power intervals; break at missing values or time gaps."""
    low = np.isfinite(power) & (np.abs(power) <= .01 * scale)
    dt = times.to_series().diff().dt.total_seconds().to_numpy() / 60
    runs = []
    start = None
    for i in range(len(low) + 1):
        discontinuity = i < len(low) and i > 0 and dt[i] > nominal_min * 1.5
        if start is not None and (i == len(low) or not low[i] or discontinuity):
            duration = (times[i-1] - times[start]).total_seconds()/60 + nominal_min
            if duration >= minimum_min:
                runs.append((start, i, duration))
            start = None
        if i < len(low) and low[i] and start is None:
            start = i
    return runs


def load_sources():
    """Only load a declared subset for annotation, not a new performance benchmark."""
    for site in ['pizhou', 'yandun']:
        paths = sorted((ROOT/'data/event_clean_v2'/site).glob('*.csv.gz'))
        paths = [p for p in paths if 'conflict' not in p.name and 'unmatched' not in p.name][:6]
        for p in paths:
            raw = pd.read_csv(p)
            raw['timestamp'] = pd.to_datetime(raw['timestamp_start_utc'], utc=True)
            raw.loc[~bool_values(raw['usable_power']), 'power_kw'] = np.nan
            d = raw.rename(columns={'power_kw':'power','wind_speed_ms':'wind'})
            cols = ['timestamp','power','wind']
            yield site, str(raw['turbine_id'].iloc[0]), p, d[cols], 'UTC (cleaned source)', 'kW'
    base = ROOT/'data/external_samples/greece_smd10towfgr/clean_native'
    mapping = {'Timestamp':'timestamp','Grid Production Power Avg. [W]':'power',
               'Ambient WindSpeed Avg. [m/s]':'wind','Rotor RPM Avg. [RPM]':'rpm',
               'Blades PitchAngle Avg. [°]':'pitch','Active power limit [W]':'active_limit'}
    for p in sorted(base.glob('WT*_data.csv.gz'))[:6]:
        d = pd.read_csv(p, usecols=lambda c: c in mapping or c == 'missing_data').rename(columns=mapping)
        d['timestamp'] = pd.to_datetime(d['timestamp'])  # source clock, not assumed UTC
        if 'missing_data' in d:
            d.loc[bool_values(d.missing_data), 'power'] = np.nan
        yield 'greece', p.name.split('_')[0], p, d, 'source clock (timezone unresolved)', 'source power units (W label unverified)'
    p = ROOT/'data/external_public/sdwpf/sdwpf_2001_2112_full.parquet'
    for tid in [1, 23, 46, 68, 91, 114]:
        d = pd.read_parquet(p, columns=['TurbID','Tmstamp','Patv','Wspd','Pab1','Pab2','Pab3'], filters=[('TurbID','=',tid)])
        d = d.rename(columns={'Tmstamp':'timestamp','Patv':'power','Wspd':'wind'})
        d['timestamp'] = pd.to_datetime(d.timestamp)  # retain source time, no UTC assertion
        d['pitch'] = d[['Pab1','Pab2','Pab3']].mean(axis=1)
        yield 'sdwpf', str(tid), p, d, 'source clock (timezone not reverified)', 'kW (source definition)'


def prepare_series(d):
    d = d.dropna(subset=['timestamp']).sort_values('timestamp')
    if d.timestamp.duplicated().any():
        raise ValueError('duplicate source timestamp: adjudicate before review sampling')
    d = d.set_index('timestamp')
    for c in ['power','wind','pitch','rpm','active_limit']:
        if c in d:
            d[c] = pd.to_numeric(d[c], errors='coerce')
    return d


def candidate_pool(site, tid, path, d, tz_status, units, rng):
    split_time = d.index[0] + .6 * (d.index[-1] - d.index[0])
    scale = d.loc[d.index < split_time, 'power'].quantile(.995)
    if not np.isfinite(scale) or scale <= 0:
        return []
    q = d[['power','wind']].resample('30min', label='left', closed='left').mean()
    p = q.power / scale
    change = p - p.shift(2)
    local_mean = p.rolling(4).mean() - p.shift(4).rolling(4).mean()
    hist_change = change[q.index < split_time].abs().dropna()
    if len(hist_change) < 10:
        return []
    tail = hist_change.quantile(.99)
    votes = pd.concat([change.abs() >= .20, change.abs() >= tail, local_mean.abs() >= .15], axis=1).sum(axis=1)
    # Require fully observed adjacent selection bins for transitions, not across gaps.
    valid3 = p.notna().rolling(3).sum().eq(3)
    eligible = (q.index >= split_time + pd.Timedelta('12h')) & (q.index < q.index[-1] - pd.Timedelta('6h'))
    masks = {'downward': (change <= -.20)&valid3,
             'upward': (change >= .20)&valid3,
             'low_output': pd.Series(np.abs(p) <= .01).rolling(3).sum().eq(3),
             'screen_disagreement': votes.isin([1,2])&valid3,
             'random_control': p.notna()}
    result=[]
    for stratum, mask in masks.items():
        ids=np.flatnonzero(mask.to_numpy() & eligible)
        for j in rng.permutation(ids)[:80]:
            t=q.index[j]
            result.append(dict(site=site,turbine=tid,source=str(path.relative_to(ROOT)),
                               source_clock=tz_status,source_units=units,scale=float(scale),
                               scale_end=str(split_time),stratum=stratum,anchor=t,
                               selection_change=float(change.iloc[j]) if np.isfinite(change.iloc[j]) else None,
                               selection_votes=int(votes.iloc[j]),series=d))
    return result


def machine_review(w, scale):
    times = pd.DatetimeIndex(w.index)
    nominal = float(times.to_series().diff().dt.total_seconds().div(60).median())
    p = w.power.to_numpy(float)
    runs = continuous_low_runs(times, p, scale, nominal)
    valid = np.flatnonzero(np.isfinite(p))
    if len(valid)<2:
        return {'suggestion':'insufficient_data','reason':'too few finite power samples'}
    delta = pd.Series(p/scale).diff().to_numpy()
    max_up=float(np.nanmax(delta)); max_down=float(np.nanmin(delta))
    if runs:
        suggestion='sustained_low_output'
    elif max_up>.15 and max_down<-.15:
        suggestion='mixed_transition'
    elif max_up>.15:
        suggestion='upward_transition'
    elif max_down<-.15:
        suggestion='downward_transition'
    else:
        suggestion='unresolved_or_no_prominent_transition'
    return {'suggestion':suggestion,'review_status':'MACHINE_SCREEN_NOT_HUMAN_VERIFIED',
            'event_truth':None,'cause':'unknown','largest_step_up_pu':max_up,'largest_step_down_pu':max_down,
            'low_runs_minutes':[round(r[2],1) for r in runs],
            'low_output_wind_median':float(w.loc[w.power.abs()<=.01*scale,'wind'].median()) if runs else None,
            'rpm_median':float(w.rpm.median()) if 'rpm' in w else None,
            'pitch_median':float(w.pitch.median()) if 'pitch' in w else None,
            'note':'Only observed trajectory semantics; neither wind coherence nor low power identifies dispatch or fault causes.'}


def plot_window(w, item, target):
    channels=[('power','Power / training-period q99.5'),('wind','Wind speed (m/s)')]
    for c,label in [('rpm','Rotor speed (RPM)'),('pitch','Pitch angle (deg)')]:
        if c in w and w[c].notna().any(): channels.append((c,label))
    fig,axes=plt.subplots(len(channels),1,figsize=(11,2.0*len(channels)+.8),sharex=True)
    hour=(w.index-item['anchor']).total_seconds()/3600
    gaps=w.index.to_series().diff().dt.total_seconds()/60
    for ax,(c,label) in zip(np.atleast_1d(axes),channels):
        vals=w[c].to_numpy(float).copy()
        if c=='power': vals/=item['scale']
        vals[gaps.to_numpy()>1.5*gaps.median()]=np.nan
        ax.plot(hour,vals,'o-',lw=1.1,ms=2.3,color='#17638b')
        ax.axvspan(-1,1,color='#efb85e',alpha=.15)
        ax.axvline(0,color='#444444',lw=.7,ls=':')
        ax.set_ylabel(label); ax.grid(alpha=.18)
    axes[-1].set_xlabel('Hours relative to review anchor (shaded: -1 to +1 h)')
    fig.suptitle(f"{item['window_id']} | {item['site']} | turbine {item['turbine']}\n{item['anchor']} | {item['source_clock']}",fontsize=11)
    fig.tight_layout(rect=(0,0,1,.94))
    fig.savefig(str(target)+'.png',dpi=140); fig.savefig(str(target)+'.svg'); plt.close(fig)


def logs_for(item, start, end):
    if item['site']!='greece': return []
    p=ROOT/'data/external_samples/greece_smd10towfgr/clean_native'/f"{item['turbine']}_logs.csv.gz"
    d=pd.read_csv(p); t=pd.to_datetime(d.Detected,errors='coerce')
    d=d.loc[(t>=start)&(t<=end),['Detected','Code','Description','Event type','Severity']]
    return d.fillna('').to_dict('records')


def run():
    for sub in ['windows','figures']: (OUT/sub).mkdir(parents=True,exist_ok=True)
    if (OUT/'human_annotations.csv').exists():
        raise FileExistsError('Refusing to overwrite the user annotation sheet')
    rng=np.random.default_rng(SEED); pool=[]; source_stats=[]
    for site,tid,path,raw,clock,units in load_sources():
        d=prepare_series(raw)
        pool+=candidate_pool(site,tid,path,d,clock,units,rng)
        source_stats.append({'site':site,'turbine':tid,'rows':len(d),'start':str(d.index.min()),'end':str(d.index.max()),'source':str(path.relative_to(ROOT))})
    picks=[]; used={}
    for site in ['pizhou','yandun','greece','sdwpf']:
        for stratum in STRATA:
            candidates=[x for x in pool if x['site']==site and x['stratum']==stratum]
            n=0
            for ix in rng.permutation(len(candidates)):
                x=candidates[ix]; key=(site,x['turbine'])
                if any(abs((x['anchor']-a).total_seconds())<12*3600 for a in used.get(key,[])): continue
                w=x['series'].loc[x['anchor']-pd.Timedelta('6h'):x['anchor']+pd.Timedelta('6h')]
                if len(w)<12 or w.power.notna().mean()<.75: continue
                used.setdefault(key,[]).append(x['anchor']); picks.append(x); n+=1
                if n==6: break
    rng.shuffle(picks); records=[]; manifest_rows=[]; sheets=[]
    for i,x in enumerate(picks,1):
        x['window_id']=f'W{i:03d}'; start=x['anchor']-pd.Timedelta('6h'); end=x['anchor']+pd.Timedelta('6h')
        w=x['series'].loc[start:end].copy(); w['relative_minutes']=(w.index-x['anchor']).total_seconds()/60
        w.to_csv(OUT/'windows'/f"{x['window_id']}.csv",index_label='source_timestamp')
        plot_window(w,x,OUT/'figures'/x['window_id'])
        machine=machine_review(w,x['scale']); logs=logs_for(x,start,end)
        rec={k:v for k,v in x.items() if k!='series'}; rec['anchor']=str(rec['anchor']); rec.update(start=str(start),end=str(end),machine=machine,logs=logs)
        rec['image']=f"figures/{x['window_id']}.png"; records.append(rec)
        manifest_rows.append({k:v for k,v in rec.items() if k not in ['machine','logs']})
        sheets.append({'window_id':x['window_id'],'annotator':'','event_presence':'','morphology':'','onset_relative_min':'','end_relative_min':'','confidence':'','cause':'unknown','notes':''})
        print(x['window_id'],x['site'],x['stratum'],flush=True)
    pd.DataFrame(manifest_rows).to_csv(OUT/'window_manifest.csv',index=False)
    pd.DataFrame(sheets).to_csv(OUT/'human_annotations.csv',index=False)
    (OUT/'machine_prereview.json').write_text(json.dumps(records,ensure_ascii=False,indent=2,allow_nan=True),encoding='utf8')
    # JSON inserted as a literal; sanitize NaNs to null for browser JSON semantics.
    payload=json.dumps(records,ensure_ascii=False).replace('NaN','null').replace('Infinity','null').replace('</','<\\/')
    template=(ROOT/'script/templates/annotation_v9.html').read_text(encoding='utf8')
    (OUT/'index.html').write_text(template.replace('__DATA__',payload),encoding='utf8')
    (OUT/'manifest.json').write_text(json.dumps({'status':'ANNOTATION_PACKET_READY_NOT_ADJUDICATED','seed':SEED,'windows':len(records),'source_series':source_stats,'sample_counts':pd.DataFrame(manifest_rows).groupby(['site','stratum']).size().astype(int).to_dict().__repr__(),'human_labels_complete':False,'selection':'stratified later-period windows, not a prevalence sample','privacy':'Private Pizhou/Yandun row-level data included. Do not publish packet.'},ensure_ascii=False,indent=2),encoding='utf8')
    assert records, 'No usable review windows'
    verify_packet()


def verify_packet():
    d=pd.read_csv(OUT/'window_manifest.csv',dtype={'turbine':str})
    assert d.window_id.is_unique
    for _,g in d.groupby(['site','turbine']):
        t=pd.to_datetime(g.anchor).sort_values()
        assert (t.diff().dropna()>=pd.Timedelta('12h')).all()
    for wid in d.window_id:
        for folder,suffix in [('windows','csv'),('figures','svg'),('figures','png')]:
            assert (OUT/folder/f'{wid}.{suffix}').stat().st_size>0
    counts=[{'site':s,'stratum':k,'actual':int(((d.site==s)&(d.stratum==k)).sum()),'target':6}
            for s in ['pizhou','yandun','greece','sdwpf'] for k in STRATA]
    pd.DataFrame(counts).to_csv(OUT/'sampling_support.csv',index=False)
    report={'status':'PASS_PACKET_INTEGRITY','windows':len(d),'requested_windows':120,
            'shortfalls':[x for x in counts if x['actual']<6],
            'reason':'Any shortfall is reported, not manufactured. W115-W120 use separately documented signed-observed power rule.',
            'human_labels_verified':False,'same_turbine_window_overlap':False}
    (OUT/'verification.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print(json.dumps(report,indent=2))


def self_test():
    t=pd.date_range('2020-01-01',periods=9,freq='10min')
    assert continuous_low_runs(t,np.zeros(9),1,10)==[(0,9,90)]
    assert continuous_low_runs(t,np.array([0,0,0,np.nan,0,0,0,0,0]),1,10)==[]
    t2=t[:3].append(t[3:]+pd.Timedelta('2h'))
    assert continuous_low_runs(t2,np.zeros(9),1,10)==[(3,9,60)]
    assert not bool_values(pd.Series(['False','false','0'])).any()
    print('PASS: duration, gaps, NaNs and boolean parsing')


if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--test',action='store_true'); ap.add_argument('--verify',action='store_true'); args=ap.parse_args()
    self_test() if args.test else verify_packet() if args.verify else run()
