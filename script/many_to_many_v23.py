"""Split/merge sensitivity on frozen test events, including composite episodes.

Each overlap component receives one vote. Its similarity is the overlap of
the two four-class empirical label distributions (one minus total variation).
This evaluates episode composition, not ARI on duplicated edge endpoints.
"""
from pathlib import Path
from itertools import combinations
from collections import defaultdict
import sys,json,gzip,csv
import numpy as np
import pandas as pd
import joblib
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from wind_events.matching import overlap_graph,match_intervals
BASE=ROOT/'outputs/protocol_benchmark_v18'
OUT=ROOT/'outputs/protocol_benchmark_v23/many_to_many'
SITES=['pizhou','suining','yandun','lahaute','hill','greece','sdwpf','hill_2021']
ARMS=[('primitive_iou50','primitive','iou',.5),('hierarchy_iou30','all','iou',.3),
      ('hierarchy_iou50','all','iou',.5),('hierarchy_iou70','all','iou',.7),
      ('hierarchy_containment50','all','containment',.5)]

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    model=joblib.load(BASE/'structure/r30_a0.2_q0.05_training_q995/pizhou_raw25_kmeans_k4_s41.joblib')
    accum=defaultdict(lambda:defaultdict(float));blocks=defaultdict(lambda:np.zeros(2))
    columns=['site','turbine','arm','config_a','config_b','start','end','left_events','right_events','edges','type','mixed_levels','composition_overlap']
    with gzip.open(OUT/'components.csv.gz','wt',newline='',encoding='utf-8') as stream:
        writer=csv.DictWriter(stream,fieldnames=columns);writer.writeheader()
        for site in SITES:
            for fp in sorted((BASE/'catalogs/r30_a0.2_q0.05_training_q995'/site).glob('*/events.parquet')):
                table=pd.read_parquet(fp)
                table=table[table.split.eq('test')&table.representation_eligible].copy()
                if table.empty:continue
                shapes=np.load(fp.parent/'shapes.npy',mmap_mode='r');ids=table.shape_row.to_numpy(int)
                assert ids.min()>=0
                table['label']=model['cluster'].predict(model['transform'].transform(shapes[ids]))
                table['start']=pd.DatetimeIndex(pd.to_datetime(table.time_start,utc=True)).as_unit('ns').asi8
                table['end']=pd.DatetimeIndex(pd.to_datetime(table.time_end,utc=True)).as_unit('ns').asi8
                labels=dict(zip(table.event_id,table.label));levels=dict(zip(table.event_id,table.event_level))
                turb=str(table.turbine.iloc[0]);configs=sorted(table.config.unique())
                for arm,level,measure,cutoff in ARMS:
                    d=table[table.event_level.eq('primitive')] if level=='primitive' else table
                    parts={c:list(g[['event_id','start','end']].itertuples(index=False,name=None)) for c,g in d.groupby('config')}
                    for ca,cb in combinations(configs,2):
                        left,right=parts.get(ca,[]),parts.get(cb,[]);key=(site,arm,ca,cb);rec=accum[key]
                        rec['left_n']+=len(left);rec['right_n']+=len(right)
                        edges,comps=overlap_graph(left,right,cutoff,measure)
                        rec['edges']+=len(edges)
                        rec['covered_left']+=len({e['event_a'] for e in edges});rec['covered_right']+=len({e['event_b'] for e in edges})
                        if arm=='primitive_iou50':rec['one_to_one_pairs']+=len(match_intervals(left,right))
                        for c in comps:
                            aa=c['left_ids'];bb=c['right_ids']
                            pa=np.bincount([labels[v] for v in aa],minlength=4)/len(aa);pb=np.bincount([labels[v] for v in bb],minlength=4)/len(bb)
                            similarity=float(np.minimum(pa,pb).sum())
                            kind=('one_to_one' if len(aa)==len(bb)==1 else 'one_to_many' if len(aa)==1 else 'many_to_one' if len(bb)==1 else 'many_to_many')
                            mixed=len({levels[v] for v in aa}|{levels[v] for v in bb})>1
                            rec['components']+=1;rec[kind]+=1;rec['mixed_level_components']+=int(mixed);rec['similarity_sum']+=similarity
                            rec['longer_than_4h']+=int(c['end']-c['start']>pd.Timedelta(hours=4).value)
                            block=c['start']//pd.Timedelta(days=7).value;blocks[(site,arm,block)]+=np.array([similarity,1])
                            writer.writerow(dict(site=site,turbine=turb,arm=arm,config_a=ca,config_b=cb,start=pd.Timestamp(c['start'],tz='UTC'),
                                end=pd.Timestamp(c['end'],tz='UTC'),left_events=len(aa),right_events=len(bb),edges=len(c['edge_indices']),
                                type=kind,mixed_levels=mixed,composition_overlap=similarity))
                print(site,turb,'complete',flush=True)
            print(site,'complete',flush=True)
    records=[]
    for key,v in accum.items():
        rec=dict(zip(['site','arm','config_a','config_b'],key))|dict(v)
        for side in ['left','right']:rec[side+'_coverage']=v['covered_'+side]/v[side+'_n'] if v[side+'_n'] else np.nan
        rec['component_mean_overlap']=v['similarity_sum']/v['components'] if v['components'] else np.nan
        rec['supported_component_pair']=v['components']>=100
        records.append(rec)
    pairs=pd.DataFrame(records).fillna({c:0 for c in ['one_to_one','one_to_many','many_to_one','many_to_many','mixed_level_components']})
    pairs.to_csv(OUT/'configuration_pairs.csv',index=False)
    summaries=[]
    for (site,arm),d in pairs.groupby(['site','arm']):
        totals=d.select_dtypes(include=np.number).sum();nn=totals.components
        a=np.vstack([v for (s,k,b),v in sorted(blocks.items()) if s==site and k==arm]);n=len(a)
        w=np.random.default_rng(41).multinomial(n,np.full(n,1/n),size=2000);b=w@a;draws=b[:,0]/b[:,1]
        lo,hi=np.quantile(draws,[.025,.975])
        row=dict(site=site,arm=arm,configuration_pairs=len(d),supported_component_pairs=int(d.supported_component_pair.sum()),
            components=int(nn),edges=int(totals.edges),one_to_one_components=int(totals.one_to_one),
            one_to_many_components=int(totals.one_to_many),many_to_one_components=int(totals.many_to_one),
            many_to_many_components=int(totals.many_to_many),mixed_level_components=int(totals.mixed_level_components),
            non_one_to_one_fraction=1-totals.one_to_one/nn,longer_than_4h_fraction=totals.longer_than_4h/nn,
            left_coverage=totals.covered_left/totals.left_n,right_coverage=totals.covered_right/totals.right_n,
            component_mean_overlap=totals.similarity_sum/nn,low=lo,high=hi,occupied_7day_blocks=n)
        if arm=='primitive_iou50':
            row['one_to_one_left_coverage']=totals.one_to_one_pairs/totals.left_n
            row['one_to_one_right_coverage']=totals.one_to_one_pairs/totals.right_n
        summaries.append(row)
    pd.DataFrame(summaries).to_csv(OUT/'site_summary.csv',index=False)
    (OUT/'protocol.json').write_text(json.dumps(dict(status='COMPLETE',source_model='Pizhou raw25 k4 seed41 frozen',
        evaluation='test only; same site/turbine; no matching across split',arms=ARMS,
        estimand='Equal-weight overlap component label-composition similarity, not duplicate-edge ARI',
        coverage='Unique connected nodes per eligible side within each configuration pair; site summary pools counts across all 136 pairs.',
        support='At least 100 connected components; reported descriptively, not used to filter the all-pair site summary.',
        weighting='Each component one vote; main one-to-one coverage table instead averages configuration-specific fractions.',
        bootstrap='2000 shared within-site 7-calendar-day weights; each component anchored at its earliest start',
        zero_denominator='Invalid e<=s intervals rejected before score; empty side coverage undefined',
        cautions='Components can chain beyond 4h; report fraction and retain full duration. Connected components are measurement supports, not physical cause labels.'),indent=2))

if __name__=='__main__':
    with threadpool_limits(limits=2):main()
