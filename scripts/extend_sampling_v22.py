"""Extend the fixed-physical-time sampling test to two European archives.

Question: does retained structure survive 30-to-60 minute averaging outside
the original Greece/Yandun sensitivity? Keep training scale, source prototype,
test clocks and 120-minute context fixed; vary only observation resolution.
"""
from pathlib import Path
import sys,json
import numpy as np
import pandas as pd
import joblib
from threadpoolctl import threadpool_limits
from run_catalog_v18 import sources,ROOT
sys.path.insert(0,str(ROOT/'src'))
from wind_events import Protocol,build_catalog
from wind_events.matching import match_intervals
from wind_events.metrics import contingency,scores_from_counts,block_intervals
BASE=ROOT/'outputs/protocol_benchmark_v18'
OUT=ROOT/'outputs/protocol_benchmark_v22/sampling'

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    model=joblib.load(BASE/'structure/r30_a0.2_q0.05_training_q995/pizhou_raw25_kmeans_k4_s41.joblib')
    collected={s:{30:[],60:[]} for s in ['lahaute','hill']}
    audits=[]
    for site,tid,t,x,ok,cap,clock,source_audit in sources(set(collected),60):
        ref=BASE/'catalogs/r30_a0.2_q0.05_training_q995'/site/str(tid)
        a=json.loads((ref/'audit.json').read_text())
        out=OUT/site/str(tid);out.mkdir(parents=True,exist_ok=True)
        if (out/'events.parquet').exists():
            table=pd.read_parquet(out/'events.parquet'); shapes=np.load(out/'shapes.npy')
            audit=json.loads((out/'audit.json').read_text())
        else:
            table,shapes,audit=build_catalog(site,tid,t,x,ok,Protocol(resolution_minutes=60),cap,'training_q995',clock,
                split_boundaries=(pd.Timestamp(a['b1']),pd.Timestamp(a['b2'])),scale_override=(a['scale'],'frozen_30min_training_reference'))
            table.to_parquet(out/'events.parquet',index=False);np.save(out/'shapes.npy',shapes)
            (out/'audit.json').write_text(json.dumps(audit,indent=2))
        for minutes,frame,arr in [(60,table,shapes),(30,pd.read_parquet(ref/'events.parquet'),np.load(ref/'shapes.npy'))]:
            keep=frame.split.eq('test')&frame.event_level.eq('primitive')&frame.representation_eligible
            d=frame[keep].copy(); indices=d.shape_row.to_numpy(int)
            if (indices<0).any():raise ValueError('invalid shape index')
            d['label']=model['cluster'].predict(model['transform'].transform(arr[indices]))
            collected[site][minutes].append(d)
        audits.append(dict(site=site,turbine=tid,scale=a['scale'],b1=a['b1'],b2=a['b2'],minutes=60))
        print(site,tid,'prepared',flush=True)
    rows=[]
    for site,data in collected.items():
        left,right=[pd.concat(data[m],ignore_index=True) for m in [30,60]]
        for config in sorted(set(left.config)|set(right.config)):
            a,b=left[left.config.eq(config)],right[right.config.eq(config)]
            matches=[]
            for tid in sorted(set(a.turbine)|set(b.turbine)):
                def intervals(frame):
                    start=pd.DatetimeIndex(pd.to_datetime(frame.time_start,utc=True)).as_unit('ns').asi8
                    end=pd.DatetimeIndex(pd.to_datetime(frame.time_end,utc=True)).as_unit('ns').asi8
                    return list(zip(frame.event_id,start,end))
                matches.extend(match_intervals(intervals(a[a.turbine.eq(tid)]),intervals(b[b.turbine.eq(tid)])))
            ai,bi=a.set_index('event_id'),b.set_index('event_id')
            la=np.array([ai.at[r[0],'label'] for r in matches],int);lb=np.array([bi.at[r[1],'label'] for r in matches],int)
            nmi,ari,exact,inf=scores_from_counts(contingency(la,lb,4))
            times=pd.to_datetime([r[3] for r in matches],utc=True)
            record=dict(site=site,left_minutes=30,right_minutes=60,config=config,left_events=len(a),right_events=len(b),
                matched_pairs=len(matches),left_coverage=len(matches)/len(a) if len(a) else np.nan,
                right_coverage=len(matches)/len(b) if len(b) else np.nan,nmi=float(nmi[0]),ari=float(ari[0]),
                agreement=float(exact[0]),informative=bool(inf[0]),prototype='pizhou_raw25_kmeans_k4_s41_frozen',
                normalization='fixed_30min_training_reference')
            for days in [3,7,14]:rows.append(record|dict(block_days=days)|block_intervals(la,lb,times,4,days))
            pd.DataFrame(rows).to_csv(OUT/'cross_resolution_metrics.csv',index=False)
            print(site,config,'matched',len(matches),flush=True)
    pd.DataFrame(audits).to_csv(OUT/'reference_audit.csv',index=False)
    (OUT/'verification.json').write_text(json.dumps(dict(status='COMPLETE',sites=list(collected),turbines=len(audits),rows=len(rows),
        scope='30/60-minute sampling; original native grid not newly reconstructed',physical_context_minutes=120),indent=2))

if __name__=='__main__':
    with threadpool_limits(limits=2):main()
