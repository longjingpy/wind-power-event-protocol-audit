"""Validation-stage physical scale restoration and additive residual decoding.

Restoring p_start+a*x recombines separately stored shape and amplitude.
Cube-root power is only a physics-motivated input basis; it is not declared
to be an observed wind speed or a universally valid turbine power curve.
All targets remain independent LiDAR/WindCube observations.
"""
from pathlib import Path
import argparse,json,sys
import joblib
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits
from physical_process_v26 import ROOT,OUT,CONFIGS,estimator,datasets,features,measures,paired


def calibrated_features(folder,d,x,s,fit=False):
    level=d.power_start.to_numpy()[:,None]+d.shape_normalizer.to_numpy()[:,None]*x
    root=np.cbrt(np.maximum(level,0));delta=root-root[:,4,None];inner=root[:,4:21]
    extra=np.c_[root[:,4],root[:,20],inner.mean(axis=1),inner.std(axis=1),np.ptp(inner,axis=1),
        root[:,:4].mean(axis=1),root[:,21:].mean(axis=1),np.abs(np.diff(inner,axis=1)).mean(axis=1)]
    strong=np.c_[s,extra]
    path=folder/'physical_calibration/transform.joblib'
    if fit:
        train=d.split.eq('train').to_numpy();scale=StandardScaler().fit(delta[train])
        pca=PCA(6,svd_solver='full').fit(scale.transform(delta[train]))
        joblib.dump((scale,pca),path)
    else:scale,pca=joblib.load(path)
    existing=features(folder,d,x,s)
    a=d.shape_normalizer.to_numpy()[:,None]
    return {'scalar19':s,'scalar27':strong,
        'normalized_raw25':np.c_[strong,x],
        'level_delta17':np.c_[strong,level[:,4:21]-level[:,4,None]],
        'cube_delta17':np.c_[strong,delta[:,4:21]],
        'cube_delta25':np.c_[strong,delta],
        'cube_pca6':np.c_[strong,pca.transform(scale.transform(delta))],
        'scale_gadf6':np.c_[strong,a*existing['gadf6'][:,19:]],
        'scale_phase12':np.c_[strong,a*existing['phase_protected12'][:,19:]]}


def validate(name):
    folder,d,x,s,y=datasets(name);branch=folder/'physical_calibration';branch.mkdir(exist_ok=True)
    if (branch/'test_summary.csv').exists():raise RuntimeError('Cannot retune after opening this test')
    z=calibrated_features(folder,d,x,s,fit=True)
    train=d.split.eq('train').to_numpy();val=d.split.eq('validation').to_numpy()
    rows=[];selected=[]
    for arm,values in z.items():
        best=None
        for i,config in enumerate(CONFIGS):
            model=estimator(config).fit(values[train],y[train]);p=model.predict(values[val]);mse=float(np.mean((p-y[val])**2))
            rows.append({'arm':arm,'candidate':i,'validation_mse':mse,'features':values.shape[1],**config})
            if best is None or (mse,i)<best[:2]:best=(mse,i,model,p,config)
        loss,i,model,p,config=best
        joblib.dump(model,branch/f'{arm}.joblib',compress=3);np.save(branch/f'validation_{arm}.npy',p)
        selected.append({'arm':arm,'validation_mse':loss,'candidate':i,'config':config})
        print('PHYSICAL_VALIDATED',name,arm,round(np.sqrt(loss),4),config,flush=True)
        pd.DataFrame(rows).to_csv(branch/'validation_candidates.csv',index=False)
    baseline=min([r for r in selected if r['arm'] in ['scalar19','scalar27']],key=lambda r:r['validation_mse'])
    proposed=min([r for r in selected if r['arm'] not in ['scalar19','scalar27','normalized_raw25']],key=lambda r:r['validation_mse'])
    (branch/'selection.json').write_text(json.dumps({'status':'FROZEN_VALIDATION_ONLY','selected':selected,
        'baseline':baseline['arm'],'primary_representation':proposed['arm'],
        'revision':'Added after first encoding-only validation, before any v26 test was opened',
        'all_targets':'independent measured wind trajectories; no inferred-wind ground truth'},indent=2))


def residual_validate(name):
    folder,d,x,s,y=datasets(name);branch=folder/'physical_calibration'
    if (branch/'test_summary.csv').exists():raise RuntimeError('Residual design must precede test evaluation')
    record=json.loads((branch/'selection.json').read_text());z=calibrated_features(folder,d,x,s)
    base=record['baseline'];configuration=next(r['config'] for r in record['selected'] if r['arm']==base)
    tr=np.flatnonzero(d.split.eq('train'));va=np.flatnonzero(d.split.eq('validation'))
    time=pd.DatetimeIndex(pd.to_datetime(d.time_start,utc=True)).as_unit('ns').asi8
    end=pd.DatetimeIndex(pd.to_datetime(d.time_end,utc=True)).as_unit('ns').asi8
    blocks=time[tr]//pd.Timedelta(days=7).value;folds=np.array_split(np.unique(blocks),min(5,len(np.unique(blocks))))
    oof=np.full((len(tr),y.shape[1]),np.nan);fold_record=[]
    for fold,labels in enumerate(folds):
        held=np.flatnonzero(np.isin(blocks,labels));idx=tr[held]
        left=time[idx].min()-pd.Timedelta(hours=2).value;right=end[idx].max()+pd.Timedelta(minutes=150).value
        fit=tr[((end[tr]+pd.Timedelta(minutes=150).value)<left)|((time[tr]-pd.Timedelta(hours=2).value)>right)]
        if len(fit)<100:raise ValueError('Insufficient purged OOF training support')
        m=estimator(configuration).fit(z[base][fit],y[fit]);oof[held]=m.predict(z[base][idx])
        fold_record.append({'fold':fold,'held_events':len(idx),'fit_events':len(fit),'purge':'full observed power context'})
    assert np.isfinite(oof).all()
    np.save(branch/'baseline_oof.npy',oof)
    base_model=joblib.load(branch/f'{base}.joblib');base_val=base_model.predict(z[base][va])
    residual=y[tr]-oof;rows=[];selected=[]
    for arm in ['scalar27','level_delta17','cube_delta17','cube_pca6','scale_phase12']:
        best=None
        for i,config in enumerate(CONFIGS):
            m=estimator(config).fit(z[arm][tr],residual);correction=m.predict(z[arm][va])
            for weight in [0.,.25,.5,1.]:
                p=base_val+weight*correction;loss=float(np.mean((p-y[va])**2))
                rows.append({'arm':arm,'candidate':i,'weight':weight,'validation_mse':loss,**config})
                if best is None or (loss,weight,i)<best[:3]:best=(loss,weight,i,m,p,config)
        loss,weight,i,m,p,config=best
        joblib.dump(m,branch/f'residual_{arm}.joblib',compress=3);np.save(branch/f'validation_residual_{arm}.npy',p)
        selected.append({'arm':arm,'weight':weight,'candidate':i,'validation_mse':loss,'config':config})
        print('RESIDUAL_VALIDATED',name,arm,round(np.sqrt(loss),4),'weight',weight,flush=True)
    pd.DataFrame(rows).to_csv(branch/'residual_candidates.csv',index=False)
    (branch/'residual_selection.json').write_text(json.dumps({'status':'FROZEN_VALIDATION_ONLY','base':base,
        'folds':fold_record,'selected':selected,'control':'scalar-only correction receives the same learner and shrinkage budget'},indent=2))


def test(name):
    folder,d,x,s,y=datasets(name);branch=folder/'physical_calibration'
    if (branch/'test_summary.csv').exists():raise RuntimeError('Test already evaluated in this branch')
    record=json.loads((branch/'selection.json').read_text())
    residual=json.loads((branch/'residual_selection.json').read_text())
    z=calibrated_features(folder,d,x,s);take=d.split.eq('test').to_numpy();meta=d[take].reset_index(drop=True);target=y[take]
    predictions={};validation={}
    for r in record['selected']:
        name_=r['arm'];predictions[name_]=joblib.load(branch/f'{name_}.joblib').predict(z[name_][take]);validation[name_]=r['validation_mse']
    base_prediction=predictions[residual['base']]
    for r in residual['selected']:
        key='residual_'+r['arm']
        predictions[key]=base_prediction+r['weight']*joblib.load(branch/f'{key}.joblib').predict(z[r['arm']][take])
        validation[key]=r['validation_mse']
    baseline=min(['scalar19','scalar27','residual_scalar27'],key=validation.get)
    candidates=[n for n in predictions if n not in ['scalar19','scalar27','residual_scalar27','normalized_raw25']]
    primary=min(candidates,key=validation.get)
    # Freeze identities before deriving any test metric.
    (branch/'test_entry_selection.json').write_text(json.dumps({'baseline':baseline,'primary':primary,
        'selection_basis':'validation MSE only, including matched scalar residual control'},indent=2))
    all_metrics={n:measures(target,p) for n,p in predictions.items()};rows=[];intervals=[]
    for arm,m in all_metrics.items():
        rows.append({'dataset':name,'arm':arm,'events':len(meta),'validation_mse':validation[arm],
            'wind_change_rmse_ms':np.sqrt(m['mse'].mean()),'geometry_rmse_ms':np.sqrt(m['geometry_mse'].mean()),
            'endpoint_mae_ms':m['endpoint_abs_error'].mean(),'excursion_mae_ms':m['excursion_abs_error'].mean(),
            'selected_baseline':arm==baseline,'selected_primary':arm==primary})
        for base in sorted(set([baseline,'scalar19','scalar27','normalized_raw25','residual_scalar27'])):
            if arm==base:continue
            for task in ['mse','geometry_mse']:
                for days in [3,7,14]:
                    intervals.append({'dataset':name,'arm':arm,'baseline':base,'task':task,
                        **paired(meta.time_start,m[task],all_metrics[base][task],days)})
    pd.DataFrame(rows).to_csv(branch/'test_summary.csv',index=False);pd.DataFrame(intervals).to_csv(branch/'test_intervals.csv',index=False)
    np.savez_compressed(branch/'test_predictions.npz',actual=target,**predictions)
    meta.to_parquet(branch/'test_events.parquet',index=False)
    print(pd.DataFrame(rows).to_string(index=False),flush=True)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--dataset',required=True)
    parser.add_argument('--phase',required=True,choices=['validate','residual','test']);a=parser.parse_args()
    {'validate':validate,'residual':residual_validate,'test':test}[a.phase](a.dataset)


if __name__=='__main__':
    with threadpool_limits(limits=2):main()
