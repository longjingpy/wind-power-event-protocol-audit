"""Event-level IoU and matching-strategy sensitivity for the five-farm test set."""
from pathlib import Path
from itertools import combinations
import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment
from sklearn.metrics import normalized_mutual_info_score, adjusted_rand_score

ROOT=Path(__file__).resolve().parents[1]; SRC=ROOT/'outputs/dynamic_events_v6'; OUT=ROOT/'outputs/event_matching_v13'; OUT.mkdir(parents=True,exist_ok=True)
GROUP=['site','turbine','split']
def edges(a,b,cut):
    out=[]
    b0=np.array([x[1] for x in b]); b1=np.array([x[2] for x in b])
    for ai,(aid,a0,a1) in enumerate(a):
        lo=np.searchsorted(b0,a0-(b1-b0).max(),side='right'); hi=np.searchsorted(b0,a1,side='left')
        for bi in range(lo,hi):
            bid,bb0,bb1=b[bi]; inter=min(a1,bb1)-max(a0,bb0); union=max(a1,bb1)-min(a0,bb0); score=inter/union
            if score>=cut: out.append((ai,bi,score,aid,bid))
    return out
def greedy(es):
    useda=set(); usedb=set(); return [(a,b,s,aid,bid) for a,b,s,aid,bid in sorted(es,key=lambda x:(-x[2],x[0],x[1])) if not (a in useda or b in usedb) and not (useda.add(a) or usedb.add(b))]
def hungarian(es,na,nb):
    if not es:return []
    aa=sorted(set(x[0] for x in es)); bb=sorted(set(x[1] for x in es)); ai={x:i for i,x in enumerate(aa)}; bi={x:i for i,x in enumerate(bb)}
    mat=np.full((len(aa),len(bb)),1.1); lookup={}
    for a,b,s,aid,bid in es: mat[ai[a],bi[b]]=1-s; lookup[(ai[a],bi[b])]=(a,b,s,aid,bid)
    n=max(len(aa),len(bb)); pad=np.ones((n,n)); pad[:len(aa),:len(bb)]=mat
    rr,cc=linear_sum_assignment(pad); return [lookup[(r,c)] for r,c in zip(rr,cc) if (r,c) in lookup]
def main():
    use=['event_id','site','turbine','split','config','time_start','time_end','representation_eligible']
    d=pd.read_csv(SRC/'candidate_intervals.csv.gz',usecols=use,dtype={'turbine':str}); d=d[d.representation_eligible.fillna(False)&d.split.eq('test')&d.site.isin(['pizhou','suining','yandun','lahaute','hill'])].copy()
    for f in ['time_start','time_end']: d[f]=pd.to_datetime(d[f],utc=True).astype('int64')
    labels=np.load(SRC/'labels_primary_raw25_k4.npz'); lab={int(r):int(y) for r,y in zip(labels['rows'],labels['labels'])}
    # label rows are aligned with eligible test rows in the v6 catalogue
    full=pd.read_csv(SRC/'candidate_intervals.csv.gz',usecols=['event_id','site','split','representation_eligible']); full=full[full.representation_eligible.fillna(False)&full.split.eq('test')].copy(); event_label=dict(zip(full.event_id,[lab.get(int(i),-1) for i in full.index])); assert all(v>=0 for v in event_label.values())
    rows=[]
    for cut in [.3,.5,.7]:
      for (site,turbine,split),g in d.groupby(GROUP,sort=True):
       parts={c:list(t.sort_values(['time_start','time_end','event_id'])[['event_id','time_start','time_end']].itertuples(index=False,name=None)) for c,t in g.groupby('config',sort=True)}
       for ca,cb in combinations(sorted(parts),2):
        a,b=parts[ca],parts[cb]; es=edges(a,b,cut)
        for method in ['greedy','hungarian']:
         selected=greedy(es) if method=='greedy' else hungarian(es,len(a),len(b))
         if not selected: continue
         la=[event_label[x[3]] for x in selected]; lb=[event_label[x[4]] for x in selected]
         rows.append({'site':site,'turbine':turbine,'config_a':ca,'config_b':cb,'cutoff':cut,'method':method,'pairs':len(selected),'nmi':normalized_mutual_info_score(la,lb),'ari':adjusted_rand_score(la,lb),'mean_iou':np.mean([x[2] for x in selected])})
    out=pd.DataFrame(rows); out.to_csv(OUT/'event_matching_metrics.csv',index=False)
    summary=out.groupby(['site','cutoff','method']).agg(pairs=('pairs','sum'),pair_median=('pairs','median'),nmi=('nmi','mean'),ari=('ari','mean'),mean_iou=('mean_iou','mean')).reset_index(); summary.to_csv(OUT/'event_matching_summary.csv',index=False)
    print(summary.to_string(index=False))
if __name__=='__main__': main()
