"""Publish authored code, aggregate outcomes and de-identified replication inputs.

The research snapshot includes unsuccessful comparisons. It does not replace
the v23 manuscript or claim that the economic novelty gate has been passed.
Native source clocks and turbine identifiers are excluded from the input pack.
"""
from pathlib import Path
import json,shutil,zipfile
import numpy as np
import pandas as pd
import joblib
import forecast_penalty_v24 as fp
ROOT=fp.ROOT;BASE=ROOT/'outputs/protocol_benchmark_v24/economics';PUB=ROOT/'public_release'
BUNDLE=ROOT/'temp/economic_replication_v24'


def copy(a,b):
    b.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(a,b)


def main():
    BUNDLE.mkdir(parents=True,exist_ok=True)
    copy(PUB/'LICENSE',BUNDLE/'LICENSE')
    for source in (ROOT/'src/wind_events').glob('*.py'):
        copy(source,PUB/'src/wind_events'/source.name);copy(source,BUNDLE/'src/wind_events'/source.name)
    for source in (ROOT/'script').glob('*v24.py'):
        copy(source,PUB/'script'/source.name);copy(source,BUNDLE/'script'/source.name)
    copy(ROOT/'script/prepare_weather_v18.py',PUB/'script/prepare_weather_v18.py')
    for source in (ROOT/'tests').glob('*v24.py'):copy(source,PUB/'tests'/source.name)
    for source in BASE.rglob('*'):
        if not source.is_file() or source.suffix not in ['.csv','.json']:continue
        if source.name=='data_protocol.json':continue  # Includes original turbine names.
        target=PUB/'results/protocol_benchmark_v24/economics'/source.relative_to(BASE)
        copy(source,target)
    for name in ['ECONOMIC_REDESIGN_V24.md','ECONOMIC_RESULTS_V24.md']:
        copy(ROOT/'docs'/name,PUB/'docs'/name);copy(ROOT/'docs'/name,BUNDLE/name)
    cases=json.loads((BASE/'jiangsu_native/pipeline_selection_before_weather_test.json').read_text())['selected']
    pools=[]
    for weather in ['none','jma','jma_gfs']:
        folder=fp.DATA_BASE if weather=='none' else fp.DATA_BASE/weather
        d=pd.read_csv(folder/'validation_candidates.csv');d['weather']=weather;pools.append(d)
    for r in pd.concat(pools).sort_values(['nmae','failed_points']).groupby('horizon_steps').head(1).to_dict('records'):
        cases.append(r|{'role':'nmae_selected_reference'})
    records=[]
    checked=pd.read_csv(BASE/'policy_classifier_seed_checks.csv')
    for number,c in enumerate(cases):
        fp.WEATHER=c['weather'];folder=fp.DATA_BASE if fp.WEATHER=='none' else fp.DATA_BASE/fp.WEATHER
        f,b1,b2=fp.frame_and_splits();h=int(c['horizon_steps']);history=8 if h==1 else 16
        shapes,common,valid=fp.model_inputs(f,history);y=(f.target_power.shift(-h)/fp.CAP).to_numpy()
        if fp.WEATHER!='none':
            extra=fp.forecast_covariates(f.index,h);common=np.c_[common,extra];valid&=np.isfinite(extra).all(axis=1)
        valid&=np.isfinite(y)&(y>=-.05)&(y<=1.2)
        target=f.index+pd.Timedelta(minutes=15*h)
        split=np.full(len(f),-1,int);split[valid&(target<=b1)]=0
        split[valid&(f.index>=b1)&(target<=b2)]=1;split[valid&(f.index>=b2)]=2
        keep=split>=0
        a=joblib.load(folder/f'model_{c["representation"]}_{h}.joblib')
        if int(c['leaf'])!=a['config']['leaf']:raise ValueError('Selected reference requires another checkpoint')
        a['config']=dict(c);xx=common if a['transform'] is None else np.c_[common,a['transform'].transform(shapes)]
        ident=f'case{number+1}_{h*15}min_{c["role"]}'
        model=BUNDLE/'models'/f'{ident}.joblib';model.parent.mkdir(exist_ok=True)
        joblib.dump(a,model,compress=3)
        inputs=BUNDLE/'inputs'/f'{ident}.npz';inputs.parent.mkdir(exist_ok=True)
        stamp=pd.DatetimeIndex(target).as_unit('ns').asi8
        blocks={}
        for days in [3,7,14]:
            block=stamp//pd.Timedelta(days=days).value;blocks[f'block_{days}d']=block[keep]-block[keep].min()
        np.savez_compressed(inputs,features=xx[keep].astype(np.float32),actual_pu=y[keep],
            persistence_pu=np.clip(f.available_power.to_numpy()[keep]/fp.CAP,0,1),split=split[keep],
            row_number=np.flatnonzero(keep),**blocks)
        reference=checked[(checked.seed==41)&checked.role.eq(c['role'])&checked.horizon_minutes.eq(h*15)]
        if len(reference)!=1:raise ValueError('Missing independent workspace check row')
        records.append({'case':ident,'role':c['role'],'weather':c['weather'],'representation':c['representation'],
            'horizon_minutes':h*15,'capacity_mw':fp.CAP,'tolerance':.03 if h==1 else .13,
            'rows':int(keep.sum()),'test_rows':int((split==2).sum()),'input_stage':'post-training-transform model-input matrix',
            'expected_fee_cny':float(reference.accuracy_charge_cny.iloc[0]),'expected_nmae':float(reference.nmae.iloc[0])})
        print('replication input',ident,flush=True)
    (BUNDLE/'cases.json').write_text(json.dumps(records,indent=2))
    readme='''# v24 economic replication inputs

These are de-identified model-input matrices for the validation-selected
policy pipeline, a scalar baseline and an nMAE-selected reference. Inputs are
already transformed using training-only representations. Row numbers and
relative block numbers replace original timestamps; no turbine IDs are stored.
Calendar features remain in the matrices, so this is not a non-reidentification
guarantee. Source/data-provider rights remain applicable.

Run: python script/reproduce_policy_v24.py
Use trusted joblib checkpoints only. Python 3.12, NumPy, pandas, SciPy, joblib
and scikit-learn are needed; exact observed versions accompany the research
verification record. This reproduces predictions and fee totals, not the full
raw-minute preprocessing from original provider files.

The policy replay implements the accuracy-charge component of Jiangsu's 2022
Article 44(II), not a realized invoice or all current amendments/exemptions.
Chinese SCADA-derived material follows the provider authorization recorded in
the repository. Weather-derived fields originate from Open-Meteo/JMA/GFS;
their source terms and attribution remain in force, not a blanket MIT relicence.
https://open-meteo.com/en/docs/previous-runs-api
https://open-meteo.com/en/licence

Current study conclusion: useful rule-specific operating/forecast pipelines
are demonstrated, while independent morphology profit beyond strong baselines
is not established. All GB failures are retained in the public results.
'''
    (BUNDLE/'README.md').write_text(readme,encoding='utf-8')
    copy(BASE/'verification.json',BUNDLE/'verification.json')
    zip_path=BASE/'economic_replication_v24.zip'
    with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(BUNDLE.rglob('*')):
            if p.is_file() and '__pycache__' not in p.parts:z.write(p,p.relative_to(BUNDLE))
    print(zip_path,zip_path.stat().st_size)


if __name__=='__main__':main()
