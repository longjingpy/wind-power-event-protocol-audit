"""Rebuild the audited catalogue; preserve low-power transitions, not fault labels."""
import json
import hashlib
from itertools import combinations
import numpy as np
import pandas as pd
from event_contract_v5 import ROOT, OUT, digest, save_manifest, segment_corridor, pair_intervals
from multiscale_event_catalog import source_files, valid_runs, configurations, describe_interval
from common_event_experiment import series
from pizhou_component_matching import shutdown_mask
from literature_detectors_v5 import original_sda, opsda_2015


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    legacy = ROOT/'outputs/dynamic_events_v4'
    old_files = [p for p in legacy.iterdir() if p.is_file() and p.suffix in {'.csv','.gz','.npy','.json'}]
    old_hashes = {str(p.relative_to(ROOT)):digest(p) for p in old_files}
    (OUT/'legacy_evidence_status.json').write_text(json.dumps({
        'status':'WITHDRAWN_PENDING_RECOMPUTATION',
        'affected':['adaptive corridor comparison','cross-scale morphology','CV pairing','unseen-turbine NMI/ARI'],
        'reasons':['cross-turbine pairing','all-data scaling','negative encoding lookup','no per-segment adaptive history'],
        'preserved_outputs_sha256':old_hashes},indent=2),encoding='utf8')
    source_hashes={str(p.relative_to(ROOT)):digest(p) for p in source_files()}
    rows=[]; shapes=[]; audits=[]; overlaps=[]; run_audits=[]
    for site,tid,time,power,quality,capacity in series(audit_dir=OUT,exclude_hill_shutdown=False):
        time=pd.DatetimeIndex(time); raw=np.asarray(power,float)
        assert time.is_unique and np.all(np.diff(time.asi8)==1800_000_000_000)
        valid=np.asarray(quality,bool)&np.isfinite(raw)
        b1=time[0]+.6*(time[-1]-time[0]); b2=time[0]+.8*(time[-1]-time[0])
        calibration=raw[valid&(time<b1)]
        scale=float(capacity) if capacity is not None else float(np.quantile(calibration,.995))
        assert np.isfinite(scale) and scale>0
        x=raw/scale; splits=np.where(time<b1,'train',np.where(time<b2,'validation','test'))
        start_count=len(rows)
        for part in ['train','validation','test']:
            masks={}; common=np.zeros(len(x)-1,bool)
            for lo,hi in valid_runs(valid&(splits==part)):
                if hi-lo<2:continue
                values=x[lo:hi]; drop=shutdown_mask(values,np.ones(len(values),bool))
                common[lo+56:hi-1]=True
                all_configs=configurations(values)
                all_configs['sda_florita2013_0.025']=[(a,b,int(np.sign(values[b]-values[a])))
                    for a,b in original_sda(values,.025) if abs(values[b]-values[a])>=.2]
                for horizon in [2,4,8]:
                    all_configs[f'opsda_cui2015_{horizon//2}h_0.025']=[(a,b,int(np.sign(values[b]-values[a])))
                        for a,b in opsda_2015(values,.025,horizon)]
                adaptive=segment_corridor(values)
                adapt_lookup={(a,b):(eps,n,mode) for a,b,eps,n,mode in adaptive}
                all_configs['adaptive_corridor']=[(a,b,int(np.sign(values[b]-values[a])))
                    for a,b,eps,n,mode in adaptive if abs(values[b]-values[a])>=.2]
                run_audits.append({'site':site,'turbine':str(tid),'split':part,'run_start':lo,'run_end_exclusive':hi,
                    'adaptive_segments':len(adaptive),'segments_above_floor':sum(e>.025+1e-12 for a,b,e,n,m in adaptive),
                    'segments_full_history':sum(n==48 for a,b,e,n,m in adaptive)})
                for config,intervals in all_configs.items():
                    occupancy=masks.setdefault(config,np.zeros(len(x)-1,bool))
                    for a,b,sign in intervals:
                        # User-confirmed no faults: zero/drop-power patterns are not fault exclusions.
                        # Retain the legacy heuristic separately for a later sensitivity analysis.
                        desc,shape=describe_interval(values,a,b,np.zeros(len(values),bool))
                        support=slice(max(0,a-4),min(len(values),b+5))
                        desc['legacy_low_power_transition_support']=bool(drop[support].any())
                        desc['legacy_low_power_transition_event']=bool(drop[a:b+1].any())
                        desc.pop('suspected_shutdown_event'); desc.pop('suspected_shutdown_available_support')
                        aa,bb=int(lo+a),int(lo+b)
                        key=f'{site}|{tid}|{part}|{config}|{time[aa]}|{time[bb]}'
                        eps,n,mode=adapt_lookup[(a,b)] if config=='adaptive_corridor' else (None,None,'not_adaptive')
                        desc.update(event_id=hashlib.sha256(key.encode()).hexdigest()[:24],site=site,turbine=str(tid),
                            split=part,config=config,start_index=aa,end_index=bb,time_start=time[aa],time_end=time[bb],
                            time_min=time[aa+desc.pop('min_offset')],time_max=time[aa+desc.pop('max_offset')],
                            detector_direction=sign,scale=scale,scale_basis='nameplate' if capacity is not None else 'early_60pct_q995',
                            shape_row=len(shapes) if shape is not None else -1,epsilon=eps,history_n=n,history_mode=mode)
                        rows.append(desc)
                        if shape is not None:shapes.append(shape)
                        occupancy[aa:bb]=True
            for ca,cb in combinations(sorted(masks),2):
                inter=int((masks[ca]&masks[cb]&common).sum()); union=int(((masks[ca]|masks[cb])&common).sum())
                overlaps.append({'site':site,'turbine':str(tid),'split':part,'config_a':ca,'config_b':cb,
                    'intersection_edges':inter,'union_edges':union,'common_edges':int(common.sum()),
                    'iou':inter/union if union else None})
        audits.append({'site':site,'turbine':str(tid),'start':time[0],'end':time[-1],'b1':b1,'b2':b2,
            'scale':scale,'valid_rows':int(valid.sum()),'rows':len(time),'candidates':len(rows)-start_count})
        print(site,tid,len(rows)-start_count,flush=True)
    table=pd.DataFrame(rows); del rows
    array=np.stack(shapes); del shapes
    assert table.event_id.is_unique and array.shape==(table.representation_eligible.sum(),25)
    assert np.isfinite(array).all()
    table.to_csv(OUT/'candidate_intervals.csv.gz',index=False)
    np.save(OUT/'context_shapes.npy',array)
    pd.DataFrame(audits).to_csv(OUT/'source_series.csv',index=False)
    pd.DataFrame(overlaps).to_csv(OUT/'detector_overlap.csv',index=False)
    pd.DataFrame(run_audits).to_csv(OUT/'adaptive_run_audit.csv',index=False)
    table.groupby(['site','split','config']).agg(candidates=('event_id','size'),eligible=('representation_eligible','sum'),
        duration_median_h=('duration_hours','median')).to_csv(OUT/'catalog_summary.csv')
    assert all(digest(ROOT/p)==h for p,h in source_hashes.items())
    assert all(digest(ROOT/p)==h for p,h in old_hashes.items())
    outputs=[OUT/n for n in ['candidate_intervals.csv.gz','context_shapes.npy','source_series.csv',
                            'detector_overlap.csv','adaptive_run_audit.csv','catalog_summary.csv']]
    save_manifest(OUT/'catalog_manifest.json',{'status':'CATALOG_BUILT_AWAITING_INDEPENDENT_VERIFICATION',
        'source_hashes':source_hashes,'candidate_rows':len(table),'shape_rows':len(array),
        'configurations':sorted(table.config.unique()),'no_faults_basis':'user assertion; not independently adjudicated',
        'published_sda_opsda':'FLORITA2013_AND_CUI2015_SOURCE_TRACED_WITH_DECLARED_STUDY_SETTINGS_NOT_2016_REPRODUCTION',
        'legacy_low_power_exclusion':'removed in primary; retained as annotation'},
        inputs=[Path for Path in [ROOT/'script/prepare_events_v5.py',ROOT/'script/event_contract_v5.py',
                ROOT/'script/multiscale_event_catalog.py',ROOT/'script/common_event_experiment.py',ROOT/'script/pizhou_component_matching.py',
                ROOT/'script/literature_detectors_v5.py',ROOT/'reference-paper/cui2015_opsda_osti1215164.pdf',
                ROOT/'reference-paper/florita2013_sda_osti1062443.pdf']],outputs=outputs)
    print('catalog complete',len(table),len(array),flush=True)
    test=table[table.representation_eligible&table.split.eq('test')]
    pairs,coverage=pair_intervals(test)
    pairs.to_csv(OUT/'test_pairs.csv.gz',index=False); coverage.to_csv(OUT/'pair_coverage.csv',index=False)
    save_manifest(OUT/'pair_manifest.json',{'status':'PAIRED_AWAITING_INDEPENDENT_VERIFICATION','pairs':len(pairs)},
        inputs=[OUT/'candidate_intervals.csv.gz',ROOT/'script/event_contract_v5.py'],
        outputs=[OUT/'test_pairs.csv.gz',OUT/'pair_coverage.csv'])
    print('pairs complete',len(pairs),flush=True)


if __name__=='__main__':main()
