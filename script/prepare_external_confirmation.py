from pathlib import Path
import json, hashlib
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'data/external_samples/greece_smd10towfgr/clean_native'
OUT=ROOT/'outputs/dynamic_events_v5/external_greece'; OUT.mkdir(parents=True,exist_ok=True)

def main():
 rows=[]; logs=[]
 for p in sorted(BASE.glob('WT*_data.csv.gz')):
  d=pd.read_csv(p); tid=p.name.split('_')[0]
  ts=pd.to_datetime(d['Timestamp'],errors='coerce')
  power=pd.to_numeric(d['Grid Production Power Avg. [W]'],errors='coerce') if 'Grid Production Power Avg. [W]' in d else pd.Series(index=d.index,dtype=float)
  wind=pd.to_numeric(d['Ambient WindSpeed Avg. [m/s]'],errors='coerce') if 'Ambient WindSpeed Avg. [m/s]' in d else pd.Series(index=d.index,dtype=float)
  rows.append({'turbine':tid,'file':str(p.relative_to(ROOT)),'rows':len(d),'invalid_timestamp':int(ts.isna().sum()),'duplicate_timestamp':int(ts.duplicated(keep=False).sum()),'start':str(ts.min()),'end':str(ts.max()),'median_interval_s':float(ts.sort_values().diff().dt.total_seconds().median()),'p95_interval_s':float(ts.sort_values().diff().dt.total_seconds().quantile(.95)),'power_valid_fraction':float(power.notna().mean()),'wind_valid_fraction':float(wind.notna().mean()),'power_min':float(power.min()),'power_max':float(power.max())})
 for p in sorted(BASE.glob('WT*_logs.csv.gz')):
  d=pd.read_csv(p); tid=p.name.split('_')[0]
  ts=pd.to_datetime(d.get('Detected'),errors='coerce')
  desc=d.get('Description',pd.Series(dtype=object)).fillna('').astype(str)
  high=desc.str.contains('generator|bearing|yaw|shutdown|stop|reset|run',case=False,regex=True)
  for i,r in d.iterrows():
   if not pd.isna(ts.iloc[i]): logs.append({'turbine':tid,'detected':ts.iloc[i].isoformat(),'code':r.get('Code'),'description':r.get('Description'),'event_type':r.get('Event type'),'severity':r.get('Severity'),'strict_label':bool(high.iloc[i])})
 report={'status':'READY_FOR_EXTERNAL_CONFIRMATION','timezone':'UNVERIFIED_NAIVE_TIMESTAMPS','power_unit':'W_SOURCE_LABEL_UNVERIFIED','hub_height_m':140,'hub_height_basis':'fallback_until_verified','scada':rows,'log_rows':len(logs),'strict_log_rows':sum(x['strict_label'] for x in logs),'notes':['No labels used for fitting','Naive timestamps retained as provisional UTC only for sensitivity','Absolute power comparisons blocked until unit verification']}
 pd.DataFrame(logs).to_csv(OUT/'greece_logs.csv',index=False); pd.DataFrame(rows).to_csv(OUT/'greece_scada_quality.csv',index=False); (OUT/'quality_report.json').write_text(json.dumps(report,indent=2),encoding='utf8'); print(json.dumps(report,indent=2))
if __name__=='__main__': main()
