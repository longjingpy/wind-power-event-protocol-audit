from pathlib import Path
import json, hashlib
import numpy as np, pandas as pd
from sklearn.metrics import normalized_mutual_info_score, adjusted_rand_score
from event_contract_v5 import ROOT, OUT, pair_intervals, checked_take
from multiscale_event_catalog import configurations, describe_interval, valid_runs

BASE=ROOT/'data/external_samples/greece_smd10towfgr/clean_native'; EOUT=OUT/'external_greece';

def load_series(p):
 d=pd.read_csv(p); t=pd.to_datetime(d.Timestamp,errors='coerce'); power=pd.to_numeric(d['Grid Production Power Avg. [W]'],errors='coerce').to_numpy(float); valid=t.notna().to_numpy()&np.isfinite(power); t=pd.DatetimeIndex(t); order=np.argsort(t.values); return t[order],power[order],valid[order]

def build():
 rows=[]; shapes=[]
 for p in sorted(BASE.glob('WT*_data.csv.gz')):
  tid=p.name.split('_')[0]; t,x,valid=load_series(p); valid &= np.isfinite(x)
  if valid.sum()<100: continue
  scale=float(np.quantile(x[valid],.995)); scale=abs(scale) if scale else 1.; xn=x/scale
  b1=t[0]+.6*(t[-1]-t[0]); b2=t[0]+.8*(t[-1]-t[0]); split_ids=np.where(t<b1,'train',np.where(t<b2,'validation','test'))
  for split in ['train','validation','test']:
   for lo,hi in valid_runs(valid&(split_ids==split)):
    if hi-lo<20: continue
    vals=xn[lo:hi]
    for cfg,ints in configurations(vals).items():
     for a,b,sgn in ints:
      if b-a<2 or a<4 or b+4>=len(vals): continue
      row,shape=describe_interval(vals,a,b,np.zeros(len(vals),bool))
      if shape is None: continue
      row.update(event_id=hashlib.sha256(f'greece|{tid}|{split}|{cfg}|{t[lo+a]}|{t[lo+b]}'.encode()).hexdigest()[:24],site='greece',turbine=tid,split=split,config=cfg,start_index=int(lo+a),end_index=int(lo+b),time_start=t[lo+a],time_end=t[lo+b],time_min=t[lo+a+int(row.pop('min_offset'))],time_max=t[lo+a+int(row.pop('max_offset'))],detector_direction=int(sgn),scale=scale,scale_basis='early_q995_unverified_units',shape_row=len(shapes),epsilon=None,history_n=48,history_mode='full_history',legacy_low_power_transition_support=False,legacy_low_power_transition_event=False)
      rows.append(row); shapes.append(shape)
 return pd.DataFrame(rows),np.asarray(shapes,np.float32)

def log_assoc(events):
 logs=pd.read_csv(EOUT/'greece_logs.csv'); logs['detected']=pd.to_datetime(logs.detected,errors='coerce'); strict=logs[logs.strict_label.astype(bool)].copy(); out=[]
 for _,e in events.iterrows():
  ts=pd.Timestamp(e.time_start); sub=strict[strict.turbine.eq(e.turbine)]
  if len(sub): delta=(sub.detected-ts).dt.total_seconds().abs()/60; out.append({'event_id':e.event_id,'turbine':e.turbine,'within_30min':bool((delta<=30).any()),'within_1h':bool((delta<=60).any()),'within_4h':bool((delta<=240).any())})
  else: out.append({'event_id':e.event_id,'turbine':e.turbine,'within_30min':False,'within_1h':False,'within_4h':False})
 return pd.DataFrame(out)

def main():
 d,z=build(); d.to_csv(EOUT/'candidate_intervals.csv.gz',index=False); np.save(EOUT/'context_shapes.npy',z)
 test=d[d.split.eq('test')].copy(); pairs,cov=pair_intervals(test); pairs.to_csv(EOUT/'test_pairs.csv.gz',index=False); cov.to_csv(EOUT/'pair_coverage.csv',index=False)
 # Frozen Pizhou raw25 model; no refit on Greece.
 m=np.load(OUT/'model_primary_raw25_k4.npz'); mean,std,centers=m['mean'],m['std'],m['centers']; x=(z-mean)/std; labels=((x[:,None,:]-centers[None,:,:])**2).sum(2).argmin(1)
 lookup=pd.Index(test.event_id); left=lookup.get_indexer(pairs.event_a); right=lookup.get_indexer(pairs.event_b); assert (left>=0).all() and (right>=0).all(); rows=[]
 for (ca,cb),g in pairs.groupby(['config_a','config_b'],sort=True):
  ix=g.index.to_numpy(); la=labels[test.index.to_numpy()[left[ix]]]; lb=labels[test.index.to_numpy()[right[ix]]]; rows.append({'config_a':ca,'config_b':cb,'pairs':len(ix),'nmi':normalized_mutual_info_score(la,lb),'ari':adjusted_rand_score(la,lb),'agreement':float((la==lb).mean())})
 summary=pd.DataFrame(rows); summary.to_csv(EOUT/'representation_summary.csv',index=False)
 assoc=log_assoc(test); assoc.to_csv(EOUT/'strict_log_association.csv',index=False)
 logs=pd.read_csv(EOUT/'greece_logs.csv'); logs['description']=logs['description'].fillna('').astype(str)
 mapping=[]
 for code,g in logs.groupby('code',dropna=False):
  desc=' | '.join(sorted(set(g.description))[:5]); mapping.append({'code':code,'n':len(g),'strict_n':int(g.strict_label.sum()),'description_examples':desc})
 pd.DataFrame(mapping).sort_values(['strict_n','n'],ascending=False).to_csv(EOUT/'log_code_mapping.csv',index=False)
 ss=summary.assign(sample_bin=pd.cut(summary.pairs,[0,4,9,29,99,10**9],labels=['2-4','5-9','10-29','30-99','>=100']))
 ss.groupby('sample_bin',observed=True).agg(configuration_pairs=('pairs','size'),median_nmi=('nmi','median'),min_nmi=('nmi','min'),max_nmi=('nmi','max')).reset_index().to_csv(EOUT/'summary_by_sample_size.csv',index=False)
 unit_audit={'power_column':'Grid Production Power Avg. [W]','source_label':'W','observed_max_W':float(d['power_end'].max()) if len(d) else None,'unit_status':'SOURCE_LABEL_UNVERIFIED','timezone_status':'NAIVE_TIMESTAMPS_UNVERIFIED','hub_height_m':140,'hub_height_status':'FALLBACK_ASSUMPTION'}
 (EOUT/'sampling_unit_audit.json').write_text(json.dumps(unit_audit,indent=2),encoding='utf8')
 result={'status':'EXTERNAL_CONFIRMATION_EXPLORATORY','turbines':int(d.turbine.nunique()),'candidate_rows':len(d),'complete_shapes':len(z),'test_pairs':len(pairs),'pair_coverage_mean':float(cov.pairs.div(cov[['left_n','right_n']].max(axis=1)).mean()) if len(cov) else None,'strict_log_events':int(pd.read_csv(EOUT/'greece_logs.csv').strict_label.sum()),'log_association_rates':{c:float(assoc[c].mean()) for c in ['within_30min','within_1h','within_4h']},'notes':['Pizhou raw25 model frozen; Greece not used for fitting','power units and timezone remain unverified','log association is descriptive, not causal']}
 (EOUT/'result.json').write_text(json.dumps(result,indent=2),encoding='utf8'); print(json.dumps(result,indent=2))
if __name__=='__main__': main()
