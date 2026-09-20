"""Keep human and model sources separate when evaluating reference agreement.

Krippendorff (2004), Content Analysis, reliability chapter: nominal coincidence
alpha measures rater agreement, not annotation truth. Whole farm-calendar
blocks retain shared windows and all fixed raters. AI-only and mixed panels
cannot be reported as additional human respondents.
"""
from pathlib import Path
import json,sys
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'script'))
from human_agreement_v19 import multirater_scores

OUT=ROOT/'outputs/protocol_benchmark_v25/ai_reference'
VALID={'upward','downward','v_shape','inverted_v','oscillatory','quiet','low_state','uncertain','bad_data'}
DYNAMIC={'upward','downward','v_shape','inverted_v','oscillatory'}


def main():
    human=pd.read_csv(ROOT/'outputs/protocol_benchmark_v19/human_reference/ratings_long.csv')
    human['original_morphology']=human.morphology
    # UI and numeric-packet names are semantic aliases, not different classes.
    human['morphology']=human.morphology.replace({'valley':'v_shape','peak':'inverted_v','data_issue':'bad_data'})
    assert set(human.morphology.dropna())<=VALID
    ids=set(human.window_id);assert len(ids)==320 and human.annotator_id.nunique()==3
    meta=human.drop_duplicates('window_id')[['window_id','site','target_start','sampling_arm']]
    parts=[human[['window_id','annotator_id','event_presence','morphology','original_morphology']].assign(source_type='human')]
    register=[]
    for number in range(1,8):
        path=OUT/f'A{number:02d}'/'labels.csv';a=pd.read_csv(path)
        assert len(a)==320 and a.window_id.is_unique and set(a.window_id)==ids
        assert set(a.morphology)<=VALID and set(a.confidence)<={'H','M','L'}
        a['event_presence']=a.morphology.map(lambda x:'yes' if x in DYNAMIC else 'no' if x in {'quiet','low_state'} else 'uncertain')
        a['original_morphology']=a.morphology
        a['annotator_id']=f'AI_A{number:02d}';a['source_type']='AI'
        a['review_context']=f'/root/ai_review_a{number:02d}'
        register.append({'rater_id':f'AI_A{number:02d}','source_type':'AI','windows':len(a),
            'runtime':'independent Codex collaboration subagent; inherited configuration',
            'model_version':'not exposed by collaboration tool; not inferred',
            'task_name':f'/root/ai_review_a{number:02d}','input':str(path.with_name('input.txt').relative_to(ROOT)),
            'answers':str(path.relative_to(ROOT))})
        parts.append(a)
    all_rows=pd.concat(parts,ignore_index=True).merge(meta,on='window_id',validate='many_to_one')
    all_rows.to_csv(OUT/'ratings_with_source.csv',index=False)
    # Sufficient class-count records reproduce alpha without publishing a
    # human respondent's individual answers or the internal absolute clock.
    exported=[]
    metadata=meta.set_index('window_id').loc[sorted(ids)].copy()
    clock=pd.DatetimeIndex(pd.to_datetime(metadata.target_start,utc=True)).as_unit('ns').asi8
    for days in [3,7,14]:
        original=pd.Series(clock//pd.Timedelta(days=days).value,index=metadata.index)
        metadata[f'block_{days}d']=[dict(zip(sorted(original[metadata.site.eq(site)].unique()),range(original[metadata.site.eq(site)].nunique())))[value] for site,value in zip(metadata.site,original)]
    for (window,source),group in all_rows.groupby(['window_id','source_type']):
        for field in ['event_presence','morphology']:
            counts=group[group.event_presence.isin(['yes','no'])][field].value_counts()
            for category,count in counts.items():
                m=metadata.loc[window]
                exported.append({'window_id':window,'source_type':source,'field':field,'category':category,'count':int(count),
                    'site':m.site,**{f'block_{d}d':int(m[f'block_{d}d']) for d in [3,7,14]}})
    pd.DataFrame(exported).to_csv(OUT/'alpha_reproduction_counts.csv',index=False)
    records=[];pair_rows=[]
    for population,select in [('human3',all_rows.source_type.eq('human')),('AI7',all_rows.source_type.eq('AI')),('mixed10',np.ones(len(all_rows),bool))]:
        rows=all_rows[select].copy()
        for field in ['event_presence','morphology']:
            eligible=rows.event_presence.isin(['yes','no'])
            wide=rows[eligible].pivot(index='window_id',columns='annotator_id',values=field).reindex(sorted(ids))
            wide=wide[wide.notna().sum(axis=1)>=2]
            values=wide.to_numpy(object);m=meta.set_index('window_id').loc[wide.index]
            times=pd.DatetimeIndex(pd.to_datetime(m.target_start,utc=True)).as_unit('ns').asi8
            for days in [3,7,14]:
                key=pd.DataFrame({'site':m.site.to_numpy(),'block':times//pd.Timedelta(days=days).value})
                blocks=key.drop_duplicates().sort_values(['site','block']).reset_index(drop=True)
                lookup={(r.site,r.block):i for i,r in blocks.iterrows()}
                index=np.array([lookup[k] for k in zip(key.site,key.block)])
                weights=np.zeros((2000,len(blocks)),int);rng=np.random.default_rng(41)
                for _,group in blocks.groupby('site'):
                    ix=group.index.to_numpy()
                    weights[:,ix]=rng.multinomial(len(ix),np.full(len(ix),1/len(ix)),size=2000)
                draws=np.array([multirater_scores(values,w[index]) for w in weights])
                alpha,agreement=multirater_scores(values,np.ones(len(values)))
                lo,hi=np.nanquantile(draws[:,0],[.025,.975])
                records.append({'population':population,'field':field,'raters':wide.shape[1],'windows':len(wide),
                    'valid_votes':int(wide.notna().sum().sum()),'block_days':days,'farm_blocks':len(blocks),
                    'alpha':alpha,'alpha_low':lo,'alpha_high':hi,'observed_agreement':agreement})
            if population=='mixed10':
                for i,left in enumerate(wide.columns):
                    for right in wide.columns[i+1:]:
                        keep=wide[left].notna()&wide[right].notna()
                        pair_rows.append({'field':field,'left':left,'right':right,'source_pair':
                            'AI-AI' if left.startswith('AI_') and right.startswith('AI_') else
                            'human-human' if not left.startswith('AI_') and not right.startswith('AI_') else 'human-AI',
                            'windows':int(keep.sum()),'agreement':float((wide.loc[keep,left]==wide.loc[keep,right]).mean())})
    table=pd.DataFrame(records);table.to_csv(OUT/'agreement_intervals.csv',index=False)
    pd.DataFrame(pair_rows).to_csv(OUT/'pairwise_agreement.csv',index=False)
    all_rows.groupby(['source_type','annotator_id','morphology']).size().rename('windows').reset_index().to_csv(OUT/'category_counts.csv',index=False)
    protocol={'status':'COMPLETE_7_ACTUAL_AI_REVIEWS_PLUS_3_HUMANS','planned_ai_sessions':7,'completed_ai_sessions':7,
        'human_observers':3,'AI_votes':2240,'human_votes':960,'unique_windows':320,
        'roster_change':'user reduced 17 to 7 before computing any new panel alpha',
        'unused_prepared_inputs':'A08-A17; no reviews executed',
        'sampling':'existing stratified/random selected-window cohort; random presentation is not random human sampling',
        'category_aliases':{'valley':'v_shape','peak':'inverted_v','data_issue':'bad_data'},
        'interpretation':'alpha measures agreement within the named fixed panel; mixed10 is not 10 human raters',
        'AI_provenance':register}
    (OUT/'protocol.json').write_text(json.dumps(protocol,ensure_ascii=False,indent=2),encoding='utf-8')
    print(table[table.block_days.eq(7)].to_string(index=False))


if __name__=='__main__':main()
