"""Fixed-protocol classifier seed checks and genuine nMAE-selection reference."""
from pathlib import Path
import json,sys,platform
import numpy as np
import pandas as pd
import sklearn,scipy,joblib
from sklearn.ensemble import ExtraTreesClassifier
from threadpoolctl import threadpool_limits
import forecast_penalty_v24 as fp
from summarize_economics_v24 import paired
ROOT=fp.ROOT;BASE=fp.DATA_BASE;OUT=ROOT/'outputs/protocol_benchmark_v24/economics'


def evaluate(config,seed):
    fp.WEATHER=config['weather'];folder=BASE if fp.WEATHER=='none' else BASE/fp.WEATHER
    f,b1,b2=fp.frame_and_splits();h=int(config['horizon_steps']);history=8 if h==1 else 16;tolerance=.03 if h==1 else .13
    shapes,common,valid=fp.model_inputs(f,history);y=(f.target_power.shift(-h)/fp.CAP).to_numpy()
    if fp.WEATHER!='none':
        extra=fp.forecast_covariates(f.index,h);common=np.c_[common,extra];valid&=np.isfinite(extra).all(axis=1)
    valid&=np.isfinite(y)&(y>=-.05)&(y<=1.2)
    tr=valid&(f.index+pd.Timedelta(minutes=15*h)<=b1);te=valid&(f.index>=b2)
    artifact=joblib.load(folder/f'model_{config["representation"]}_{h}.joblib')
    transform=artifact['transform'];xx=common if transform is None else np.c_[common,transform.transform(shapes)]
    leaf=int(config['leaf'])
    if seed==41 and leaf==artifact['config']['leaf']:model=artifact['model']
    else:
        labels=np.clip(np.rint(y[tr]*100),0,120).astype(int)
        model=ExtraTreesClassifier(n_estimators=150,max_depth=16,min_samples_leaf=leaf,max_features=1.,random_state=seed,n_jobs=4).fit(xx[tr],labels)
    p=np.zeros((int(te.sum()),len(fp.CENTERS)));p[:,model.classes_]=model.predict_proba(xx[te])
    if config['action']=='mean':q=p@fp.CENTERS
    elif config['action']=='median':q=fp.CENTERS[(np.cumsum(p,axis=1)>=.5).argmax(axis=1)]
    else:q=fp.tolerance_action(p,tolerance)
    baseline=np.clip(f.available_power.to_numpy()[te]/fp.CAP,0,1);q=np.clip((1-config['blend'])*baseline+config['blend']*q,0,1)
    result={'horizon_minutes':h*15,'role':config['role'],'seed':seed,'weather':fp.WEATHER,
        'representation':config['representation'],'action':config['action'],'blend':config['blend'],**fp.measures(y[te],q,tolerance)}
    result['baseline_fee_cny']=fp.point_fee(y[te],baseline,tolerance).sum()
    result['saved_cny']=result['baseline_fee_cny']-result['accuracy_charge_cny']
    result['fee_reduction_pct']=100*result['saved_cny']/result['baseline_fee_cny']
    panel=pd.DataFrame({'target_time':f.index[te]+pd.Timedelta(minutes=h*15),
                        'fee_cny':fp.point_fee(y[te],q,tolerance)})
    return result,panel


def main():
    choice=json.loads((BASE/'pipeline_selection_before_weather_test.json').read_text())['selected']
    candidates=[]
    for weather in ['none','jma','jma_gfs']:
        folder=BASE if weather=='none' else BASE/weather
        d=pd.read_csv(folder/'validation_candidates.csv');d['weather']=weather;candidates.append(d)
    candidates=pd.concat(candidates,ignore_index=True)
    mae_best=candidates.sort_values(['nmae','failed_points','blend']).groupby('horizon_steps').head(1)
    for r in mae_best.to_dict('records'):choice.append(r|{'role':'nmae_selected_reference'})
    rows=[];panels={};contrasts=[]
    for config in choice:
        seeds=[41,42,43] if config['role']!='nmae_selected_reference' else [41]
        for seed in seeds:
            result,panel=evaluate(config,seed);rows.append(result)
            panels[(result['horizon_minutes'],config['role'],seed)]=panel
            print('seed check',result['horizon_minutes'],config['role'],seed,round(result['saved_cny']),flush=True)
    for h in [15,240]:
        a=panels[(h,'morphology_pipeline',41)];b=panels[(h,'nmae_selected_reference',41)]
        contrasts+=paired(a,b,f'{h}min_cost_selected_vs_nmae_selected')
    pd.DataFrame(rows).to_csv(OUT/'policy_classifier_seed_checks.csv',index=False)
    pd.DataFrame(contrasts).to_csv(OUT/'policy_objective_selection_intervals.csv',index=False)
    verify={'status':'CHECKS_COMPLETED','seed_scope':'Classifier seeds 41/42/43; upstream transforms and validation-selected hyperparameters fixed',
        'source_versions':{'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__,
                           'sklearn':sklearn.__version__,'scipy':scipy.__version__},
        'economic_goal':'Policy-fee savings and GB operating gain verified; independent morphology increment is not established.',
        'claimed_success':'Positive pipeline utility under specified rules, not universal economic dominance or realized bills'}
    (OUT/'verification.json').write_text(json.dumps(verify,indent=2))
    print(pd.DataFrame(rows).to_string(index=False))


if __name__=='__main__':
    with threadpool_limits(limits=4):main()
