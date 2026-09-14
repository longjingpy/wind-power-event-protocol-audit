"""Quantify support, unmatched-event composition and IoU sensitivity from v6 archives."""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]; SRC=ROOT/'outputs/dynamic_events_v6'; OUT=ROOT/'outputs/matching_coverage_v12'; OUT.mkdir(parents=True,exist_ok=True)
def main():
    cand=pd.read_csv(SRC/'candidate_intervals.csv.gz',usecols=['event_id','site','turbine','split','config','duration_hours','amplitude','direction','power_start','power_range','representation_eligible'])
    cand=cand[(cand.split=='test') & cand.representation_eligible.fillna(False)].copy()
    pairs=pd.read_csv(SRC/'test_pairs.csv.gz',usecols=['event_a','event_b','site','config_a','config_b','iou'])
    matched={}
    for r in pairs.itertuples(index=False):
        matched.setdefault((r.site,r.config_a),set()).add(r.event_a); matched.setdefault((r.site,r.config_b),set()).add(r.event_b)
    rows=[]
    for (site,config),g in cand.groupby(['site','config']):
        ids=matched.get((site,config),set()); hit=g.event_id.isin(ids)
        row={'site':site,'config':config,'candidate_events':len(g),'matched_events':int(hit.sum()),'coverage':float(hit.mean()),'unmatched_events':int((~hit).sum())}
        for col in ['duration_hours','amplitude','power_range','power_start','direction']:
            row[f'matched_{col}_median']=float(g.loc[hit,col].median()) if hit.any() else np.nan
            row[f'unmatched_{col}_median']=float(g.loc[~hit,col].median()) if (~hit).any() else np.nan
        rows.append(row)
    pd.DataFrame(rows).to_csv(OUT/'matched_unmatched_composition.csv',index=False)
    pair_rows=[]
    for (site,ca,cb),p in pairs.groupby(['site','config_a','config_b'],sort=True):
        left=cand[(cand.site==site)&(cand.config==ca)]; right=cand[(cand.site==site)&(cand.config==cb)]
        pair_rows.append({'site':site,'config_a':ca,'config_b':cb,'pairs':len(p),
                          'left_candidates':len(left),'right_candidates':len(right),
                          'left_coverage':len(p)/max(len(left),1),'right_coverage':len(p)/max(len(right),1),
                          'mean_iou':p.iou.mean(),'iou_ge_030':(p.iou>=.3).mean(),
                          'iou_ge_050':(p.iou>=.5).mean(),'iou_ge_070':(p.iou>=.7).mean()})
    pd.DataFrame(pair_rows).to_csv(OUT/'pair_coverage_summary.csv',index=False)
    rp=pd.read_csv(SRC/'representation_pairs_primary.csv'); rp=rp[(rp.representation=='raw25') & rp.group.isin(['hill','lahaute','pizhou','suining','yandun'])]
    weighted=rp.groupby('group').apply(lambda g: pd.Series({'pair_weighted_nmi':np.average(g.nmi,weights=g.pairs),'pair_weighted_ari':np.average(g.ari,weights=g.pairs),'total_pairs':g.pairs.sum(),'configuration_pairs':len(g)}),include_groups=False).reset_index()
    weighted.to_csv(OUT/'coverage_weighted_agreement.csv',index=False)
    overlap=pd.read_csv(SRC/'detector_overlap.csv')
    sens=overlap.groupby('site').apply(lambda g: pd.Series({'overlap_edges':len(g),'iou_q10':g.iou.quantile(.1),'iou_median':g.iou.median(),'iou_q90':g.iou.quantile(.9),'fraction_iou_ge_030':(g.iou>=.3).mean(),'fraction_iou_ge_050':(g.iou>=.5).mean(),'fraction_iou_ge_070':(g.iou>=.7).mean()}),include_groups=False).reset_index()
    sens.to_csv(OUT/'iou_threshold_sensitivity.csv',index=False)
    (OUT/'README.md').write_text('Support audit for the v6 test catalogue. Coverage is matched complete-event count divided by eligible candidate count. Matched/unmatched medians describe composition. Weighted agreement uses pair counts as weights. IoU sensitivity summarizes all archived overlap edges at thresholds 0.3, 0.5 and 0.7.\n')
    print(f'coverage rows={len(rows)} weighted sites={len(weighted)} IoU sites={len(sens)}')
if __name__=='__main__': main()
