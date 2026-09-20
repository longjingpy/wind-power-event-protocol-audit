"""Stress small pre-normalization amplitudes with fixed-scale input noise."""
from pathlib import Path
import argparse
import joblib
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits
from polarity_increment_v25 import ROOT,OUT,MODELS,BASE,CONTROLS,ARMS,archive_site,lidar_dataset,encode,probability
from wind_events.representation import polarity_bit
from wind_events.paired_probability import paired_rows


def load(dataset):
    if dataset.startswith('era5_'):
        site=dataset[5:];d,x=archive_site(site);test=d.split.eq('test').to_numpy()
        return d[test].reset_index(drop=True),x[test],site,None
    turbine=dataset[6:];d,x=lidar_dataset(turbine)
    ids=set(pd.read_parquet(BASE/'lidar_confirmation/chronological_calibration'/f'{turbine}_predictions.parquet').event_id)
    test=d.event_id.isin(ids).to_numpy()
    return d[test].reset_index(drop=True),x[test],'hill',joblib.load(OUT/'models'/f'{turbine}_calibrators.joblib')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--dataset',required=True);args=parser.parse_args()
    d,x,source,cal=load(args.dataset);features=encode(d,x)
    heads={n:joblib.load(OUT/'models'/f'{source}_{n}.joblib') for n in ['scalar_g5','scalar_g5_bit']}
    transform=joblib.load(MODELS/'pizhou_gaf_pca6_kmeans_k4_s41.joblib')['transform']
    scale=d.shape_normalizer.to_numpy(float);assert (scale>0).all()
    controls=d[CONTROLS].to_numpy(float);bit=polarity_bit(x).ravel()
    def predict(name,z):
        p=probability(heads[name],z)
        return p if cal is None else cal[name].predict_proba(np.log(np.clip(p,1e-8,1)))
    clean=predict('scalar_g5_bit',features['scalar_g5_bit'])
    rows=[];effects=[];flips=[]
    for seed in [101,202,303]:
        noise=np.random.default_rng(seed).normal(size=x.shape)
        for sigma in [.001,.005,.01]:
            v=x+(sigma/scale[:,None])*(noise-noise[:,4,None]);v/=np.abs(v).max(axis=1)[:,None]
            g=np.vstack([transform.transform(v[i:i+2048])[:,:5] for i in range(0,len(v),2048)])
            b=polarity_bit(v);pred={'clean':clean,'perturbed':predict('scalar_g5_bit',np.c_[controls,g,b]),
                                  'angular':predict('scalar_g5',np.c_[controls,g])}
            a,e=paired_rows(d,pred,[('perturbed','clean'),('perturbed','angular')],7)
            rows += [{'dataset':args.dataset,'noise_sigma_reference_scale':sigma,'seed':seed,**r} for r in a]
            effects += [{'dataset':args.dataset,'noise_sigma_reference_scale':sigma,'seed':seed,**r} for r in e]
            changed=b.ravel()!=bit;gap=np.abs(x.max(axis=1)+x.min(axis=1))
            strata={'all':np.ones(len(d),bool),'normalizer_lt_0.05':scale<.05,'normalizer_0.05_0.2':(scale>=.05)&(scale<.2),'normalizer_ge_0.2':scale>=.2,'extreme_gap_lt_0.1':gap<.1,'extreme_gap_ge_0.1':gap>=.1}
            for name,take in strata.items():
                flips.append({'dataset':args.dataset,'noise_sigma_reference_scale':sigma,'seed':seed,'stratum':name,'events':int(take.sum()),
                    'bit_flip_fraction':float(changed[take].mean()) if take.any() else np.nan})
    folder=OUT/args.dataset
    pd.DataFrame(rows).to_csv(folder/'absolute_noise_scores.csv',index=False)
    pd.DataFrame(effects).to_csv(folder/'absolute_noise_paired.csv',index=False)
    pd.DataFrame(flips).to_csv(folder/'absolute_noise_strata.csv',index=False)
    print('ABSOLUTE_NOISE_COMPLETE',args.dataset,len(d),flush=True)


if __name__=='__main__':
    with threadpool_limits(limits=2):main()
