"""Merge user annotation rounds and evaluate detector presence in the labeled 2-h region."""
from pathlib import Path
import argparse, json
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]; A=ROOT/'outputs/annotation_v9'; OUT=ROOT/'outputs/user_labels_v9'; OUT.mkdir(parents=True,exist_ok=True)
ORIG=A/'submissions/human_annotations_20260914T091209_001557Z_dd447d.json'
def naive(v):
    t=pd.to_datetime(v,errors='coerce');
    return t.tz_localize(None) if getattr(t,'tzinfo',None) is not None else t
def load(path,n=None):
    d=json.loads(Path(path).read_text(encoding='utf8')); assert d.get('schema')=='annotation_v9'; rows=d['annotations'];ids=[r['window_id'] for r in rows];assert len(ids)==len(set(ids));
    if n is not None:assert len(rows)==n
    return {r['window_id']:r for r in rows}
def catalogs():
    files=[('primary_v6',ROOT/'outputs/dynamic_events_v6/candidate_intervals.csv.gz'),('greece',ROOT/'outputs/dynamic_events_v6/external_greece/candidate_intervals.csv.gz')]
    files += [('sdwpf',p/'candidate_intervals.csv.gz') for p in sorted((ROOT/'outputs/sdwpf_v7').glob('batch*/'))]
    out=[]
    for source,p in files:
        if not p.exists():continue
        d=pd.read_csv(p,compression='infer',low_memory=False);need={'site','turbine','config','time_start','time_end'}
        if not need<=set(d):continue
        d=d[['site','turbine','config','time_start','time_end']].copy();d['turbine']=d.turbine.astype(str);d['start']=pd.to_datetime(d.time_start,errors='coerce').dt.tz_localize(None);d['end']=pd.to_datetime(d.time_end,errors='coerce').dt.tz_localize(None);d['source_version']=source;out.append(d)
    return pd.concat(out,ignore_index=True) if out else pd.DataFrame()
def main(original,focus):
    first=load(original,120);second=load(focus,52);assert set(second)<=set(first)
    rows=[]
    for wid,r in first.items():
        q=dict(r);q['round1_label']=r.get('quick_label') or r.get('morphology','');q['round2_label']=second.get(wid,{}).get('quick_label','');q['final_label']=q['round2_label'] or q['round1_label'];q['final_presence']=(second.get(wid) or r).get('event_presence','');q['round2_applied']=wid in second;q['final_scope']='center_2h';rows.append(q)
    labels=pd.DataFrame(rows);m=pd.read_csv(A/'window_manifest.csv',dtype={'turbine':str})
    # Parse source-clock strings individually: this table mixes naive and UTC strings.
    # Applying one inferred format to all rows silently erased the UTC-site anchors.
    m['anchor']=m.anchor.map(naive)
    assert m.anchor.notna().all(), 'Every review window needs a finite source-clock anchor'
    labels=labels.drop(columns=['anchor'],errors='ignore').merge(m[['window_id','site','turbine','anchor','source']],on='window_id',how='left');assert labels.site.notna().all();labels['target_start']=labels.anchor-pd.Timedelta(minutes=60);labels['target_end']=labels.anchor+pd.Timedelta(minutes=60);labels.to_csv(OUT/'merged_window_labels.csv',index=False)
    c=catalogs();metrics=[]
    for (site,cfg),g in c.groupby(['site','config'],sort=True):
        e=labels[labels.site.eq(site)];tp=fp=fn=0;offset=[]
        if e.empty: continue
        for _,r in e.iterrows():
            z=g[g.turbine.eq(str(r.turbine))&(g.start<r.target_end)&(g.end>r.target_start)].sort_values('start');hit=not z.empty;pos=r.final_presence=='yes';tp+=int(hit and pos);fp+=int(hit and not pos);fn+=int(not hit and pos)
            if hit:offset.append((z.iloc[0].start-r.target_start).total_seconds()/60)
        p=tp/(tp+fp) if tp+fp else 0.;rec=tp/(tp+fn) if tp+fn else 0.;metrics.append({'site':site,'config':cfg,'n_windows':len(e),'positive_windows':int((e.final_presence=='yes').sum()),'tp':tp,'fp':fp,'fn':fn,'precision':p,'recall':rec,'f1':2*p*rec/(p+rec) if p+rec else 0.,'median_offset_from_region_start_min':float(np.median(offset)) if offset else None,'delay_status':'onset boundaries not supplied; offset is not delay'})
    out=pd.DataFrame(metrics);out.to_csv(OUT/'window_detector_metrics.csv',index=False);manifest={'status':'PASS_USER_LABEL_MERGE_WINDOW_LEVEL','round1_windows':len(first),'round2_windows':len(second),'merged_windows':len(labels),'round2_overrides':int(labels.round2_applied.sum()),'final_labels':labels.final_label.value_counts().to_dict(),'final_presence':labels.final_presence.value_counts().to_dict(),'scope':'user-confirmed center 2-h shading','delay_status':'NOT_IDENTIFIABLE_WITHOUT_ONSET_BOUNDARIES','catalog_rows':len(c),'catalog_sources':c.source_version.value_counts().to_dict() if len(c) else {}}
    (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(manifest,ensure_ascii=False,indent=2));print(out.groupby('config')[['precision','recall','f1']].mean().sort_values('f1',ascending=False).head(15).round(3).to_string())
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--original',type=Path,default=ORIG);ap.add_argument('--focus',type=Path,required=True);x=ap.parse_args();main(x.original,x.focus)
