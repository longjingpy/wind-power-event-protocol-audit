"""Validation-locked decoding of independently measured wind trajectories.

Geurts et al. (2006), Extremely randomized trees, doi:10.1007/s10994-006-6226-1:
randomized tree ensembles provide a common nonlinear multi-output decoder.
Ridge regression supplies a regularized linear comparison. All feature arms
receive identical decoder search budgets; validation selects configurations.
"""
from pathlib import Path
import argparse,json,sys
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import f1_score
from threadpoolctl import threadpool_limits

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from wind_events.process_encoding import ProcessEncodings
from wind_events.paired_probability import block_design
from prepare_process_v26 import process_class
OUT=ROOT/'outputs/protocol_benchmark_v26'
NEW_ARMS=['gadf6','dual_gaf6','balanced_signed6','phase_protected6','phase_protected12']
CONFIGS=[{'family':'ridge','alpha':a} for a in [.1,1.,10.,100.]]+[
    {'family':'extra','leaf':leaf,'depth':depth,'trees':192} for leaf in [4,16] for depth in [12,None]]


def estimator(config,seed=41):
    if config['family']=='ridge':return make_pipeline(StandardScaler(),Ridge(alpha=config['alpha']))
    return ExtraTreesRegressor(n_estimators=config['trees'],min_samples_leaf=config['leaf'],
        max_depth=config['depth'],max_features=1.,random_state=seed,n_jobs=2)


def datasets(name):
    folder=OUT/name;d=pd.read_parquet(folder/'events.parquet')
    a=np.load(folder/'arrays.npz');x=a['shape'];s=a['scalar'];y=a['wind_change'][:,1:]
    return folder,d,x,s,y


def features(folder,d,x,s,fit=False):
    path=folder/'encodings.joblib'
    if fit:
        train=d.split.eq('train').to_numpy()
        encoder=ProcessEncodings().fit(x[train]);joblib.dump(encoder,path)
    else:encoder=joblib.load(path)
    chunks=[encoder.transform(x[i:i+512]) for i in range(0,len(x),512)]
    reps={n:np.vstack([v[n] for v in chunks]) for n in chunks[0]}
    return {'scalar5':s[:,:5],'scalar19':s,**{n:np.c_[s,v] for n,v in reps.items()}}


def validate(name):
    folder,d,x,s,y=datasets(name)
    if (folder/'test_summary.csv').exists():raise RuntimeError('Test has been opened; validation rerun forbidden in this version')
    train=d.split.eq('train').to_numpy();val=d.split.eq('validation').to_numpy()
    feat=features(folder,d,x,s,fit=True);records=[];selected=[]
    models=folder/'models';models.mkdir(exist_ok=True)
    for arm,z in feat.items():
        best=None
        for number,config in enumerate(CONFIGS):
            model=estimator(config).fit(z[train],y[train]);p=model.predict(z[val])
            mse=float(np.mean((p-y[val])**2))
            row={'arm':arm,'candidate':number,'validation_mse':mse,'validation_rmse_ms':np.sqrt(mse),
                'features':z.shape[1],'train_events':int(train.sum()),'validation_events':int(val.sum()),**config}
            records.append(row)
            if best is None or (mse,number)<best[:2]:best=(mse,number,model,p,config)
        loss,number,model,p,config=best
        joblib.dump(model,models/f'{arm}.joblib',compress=3)
        np.save(folder/f'validation_{arm}.npy',p)
        selected.append({'arm':arm,'candidate':number,'validation_mse':loss,'config':config,'features':z.shape[1]})
        print('VALIDATED',name,arm,round(np.sqrt(loss),4),config,flush=True)
        pd.DataFrame(records).to_csv(folder/'validation_candidates.csv',index=False)
    baseline=min([r for r in selected if r['arm'] in ['scalar5','scalar19']],key=lambda r:r['validation_mse'])
    primary=min([r for r in selected if r['arm'] in NEW_ARMS],key=lambda r:r['validation_mse'])
    record={'status':'FROZEN_VALIDATION_ONLY','dataset':name,'primary_task':'event-mean squared error of 16 wind-change samples',
        'baseline':baseline['arm'],'primary_representation':primary['arm'],'selected':selected,
        'candidate_count':len(records),'test_seen_in_prior_tasks':True,'new_task_identity':'EXPLORATORY_CHRONOLOGICAL_PROCESS_RECONSTRUCTION',
        'practical_target':'at least 10% RMSE improvement over strong scalar controls; not enforced by outcome selection'}
    (folder/'selection.json').write_text(json.dumps(record,indent=2))


def measures(y,p):
    actual=np.c_[np.zeros(len(y)),y];pred=np.c_[np.zeros(len(y)),p]
    chord=np.linspace(0,1,17)[None,:]
    residual_actual=actual-actual[:,-1,None]*chord
    residual_pred=pred-pred[:,-1,None]*chord
    up=lambda z:(z-np.minimum.accumulate(z,axis=1)).max(axis=1)
    down=lambda z:(np.maximum.accumulate(z,axis=1)-z).max(axis=1)
    return {'mse':np.mean((p-y)**2,axis=1),'geometry_mse':np.mean((residual_pred[:,1:]-residual_actual[:,1:])**2,axis=1),
        'endpoint_abs_error':np.abs(p[:,-1]-y[:,-1]),
        'excursion_abs_error':(np.abs(up(pred)-up(actual))+np.abs(down(pred)-down(actual)))/2,
        'predicted_class':process_class(pred),'actual_class':process_class(actual)}


def paired(times,a,b,days=7):
    index,weights=block_design(times,days,2000)
    n=np.bincount(index,minlength=weights.shape[1])
    av=np.bincount(index,weights=a,minlength=weights.shape[1])
    bv=np.bincount(index,weights=b,minlength=weights.shape[1])
    denominator=weights@n
    draw=100*(1-np.sqrt((weights@av)/(weights@bv)))
    lo,hi=np.nanquantile(draw,[.025,.975])
    return {'block_days':days,'occupied_blocks':weights.shape[1],'events':len(a),
        'relative_rmse_reduction_pct':100*(1-np.sqrt(np.mean(a)/np.mean(b))),'low':lo,'high':hi}


def test(name):
    folder,d,x,s,y=datasets(name)
    if (folder/'test_summary.csv').exists():raise RuntimeError('This version already contains test results')
    selection=json.loads((folder/'selection.json').read_text())
    assert selection['status']=='FROZEN_VALIDATION_ONLY'
    keep=d.split.eq('test').to_numpy();meta=d[keep].reset_index(drop=True);target=y[keep]
    feat=features(folder,d,x,s);metrics={};summary=[];predictions={}
    for row in selection['selected']:
        arm=row['arm'];model=joblib.load(folder/'models'/f'{arm}.joblib')
        pred=model.predict(feat[arm][keep]);predictions[arm]=pred;m=measures(target,pred);metrics[arm]=m
        summary.append({'dataset':name,'arm':arm,'events':len(meta),'wind_change_rmse_ms':np.sqrt(m['mse'].mean()),
            'geometry_rmse_ms':np.sqrt(m['geometry_mse'].mean()),'endpoint_mae_ms':m['endpoint_abs_error'].mean(),
            'excursion_mae_ms':m['excursion_abs_error'].mean(),'process_macro_f1':f1_score(m['actual_class'],m['predicted_class'],labels=[0,1,2,3],average='macro',zero_division=0),
            'validation_mse':row['validation_mse'],'selected_primary':arm==selection['primary_representation'],
            'selected_baseline':arm==selection['baseline']})
    intervals=[]
    for arm in predictions:
        for baseline in sorted(set([selection['baseline'],'scalar19','raw25','raw_pca6'])):
            if arm==baseline:continue
            for task in ['mse','geometry_mse']:
                for days in [3,7,14]:
                    intervals.append({'dataset':name,'arm':arm,'baseline':baseline,'task':task,
                        **paired(meta.time_start,metrics[arm][task],metrics[baseline][task],days)})
    pd.DataFrame(summary).to_csv(folder/'test_summary.csv',index=False)
    pd.DataFrame(intervals).to_csv(folder/'test_intervals.csv',index=False)
    np.savez_compressed(folder/'test_predictions.npz',actual=target,**predictions)
    meta.to_parquet(folder/'test_events.parquet',index=False)
    (folder/'test_status.json').write_text(json.dumps({'status':'COMPLETE_ALL_LOCKED_ARMS','events':len(meta),
        'primary':selection['primary_representation'],'baseline':selection['baseline'],
        'none_hidden':True,'scope':'new trajectory task on previously studied periods'},indent=2))
    print(pd.DataFrame(summary).to_string(index=False),flush=True)


def main():
    p=argparse.ArgumentParser();p.add_argument('--dataset',required=True,choices=['lidar_T11','lidar_T07','smarteole','lidar_T11_native10','lidar_T07_native10','smarteole_native10'])
    p.add_argument('--phase',required=True,choices=['validate','test']);a=p.parse_args()
    (validate if a.phase=='validate' else test)(a.dataset)


if __name__=='__main__':
    with threadpool_limits(limits=2):main()
