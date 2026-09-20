"""Freeze all primary choices using validation records before test evaluation."""
from pathlib import Path
import json
import pandas as pd

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/protocol_benchmark_v26'
SOURCES=['lidar_T11','lidar_T07','smarteole']


def main():
    target=OUT/'final_validation_lock.json'
    if target.exists():raise RuntimeError('Final validation lock already exists; inspect instead of replacing')
    if list(OUT.rglob('test_summary.csv')):raise RuntimeError('Test opened before global lock')
    choices=[];candidates=[]
    for source in SOURCES:
        for suffix in ['', '_native10']:
            dataset=source+suffix;folder=OUT/dataset
            data=json.loads((folder/'data_protocol.json').read_text())
            for track,file in [('encoding',folder/'selection.json'),('physical',folder/'physical_calibration/selection.json'),
                               ('residual',folder/'physical_calibration/residual_selection.json')]:
                selected=json.loads(file.read_text())
                assert selected['status']=='FROZEN_VALIDATION_ONLY'
                for row in selected['selected']:
                    arm=row['arm'] if track!='residual' else 'residual_'+row['arm']
                    candidates.append({'source':source,'dataset':dataset,'power_minutes':10 if suffix else 30,
                        'track':track,'arm':arm,'validation_mse':row['validation_mse'],
                        'scalar_only':arm in ['scalar5','scalar19','scalar27','residual_scalar27']})
            if suffix:
                base=pd.read_parquet(OUT/source/'events.parquet').event_id
                new=pd.read_parquet(folder/'events.parquet').event_id
                assert list(base)==list(new),'Cross-resolution primary comparison requires identical event IDs/order'
    rows=pd.DataFrame(candidates)
    for source,group in rows.groupby('source'):
        for scope in ['native10','across_resolution']:
            g=group[group.power_minutes.eq(10)] if scope=='native10' else group
            baseline=g[g.scalar_only].sort_values(['validation_mse','track','arm']).iloc[0].to_dict()
            pipeline=g[~g.scalar_only].sort_values(['validation_mse','track','arm']).iloc[0].to_dict()
            choices.append({'source':source,'scope':scope,'baseline':baseline,'pipeline':pipeline,
                'validation_rmse_reduction_pct':100*(1-(pipeline['validation_mse']/baseline['validation_mse'])**.5)})
    rows.to_csv(OUT/'final_validation_candidates.csv',index=False)
    target.write_text(json.dumps({'status':'LOCKED_BEFORE_V26_TEST','choices':choices,
        'selection':'minimum validation wind-trajectory MSE only; all feature families retained',
        'endpoint_history':'previous endpoint tasks had used these calendars; this new task is exploratory',
        'primary_comparison':'same-resolution native10, with all scalar/correction controls eligible',
        'secondary_comparison':'validation selection across 10/30min using identical targets',
        'practical_gate_pct':10,'all_test_results_required':True},indent=2))
    for row in choices:print(row['source'],row['scope'],row['baseline']['arm'],row['pipeline']['arm'],round(row['validation_rmse_reduction_pct'],2),flush=True)


if __name__=='__main__':main()
