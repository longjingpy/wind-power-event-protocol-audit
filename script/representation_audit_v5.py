"""Unified train-only representation comparisons over one audited UTC pair table.

All representation comparisons use identical events and correspondences. This
is an exploratory stability measurement, not event truth or causal inference.
The signed GAF formula and PCA/K-means comparison are specified in the protocol;
no comparison of silhouette across unequal metric spaces is made.
"""
import argparse
import json
import time
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import normalized_mutual_info_score, adjusted_rand_score
from event_contract_v5 import ROOT,OUT,FEATURES,digest,checked_take,fit_standardizer,save_manifest


def encode(x, name):
    if name in ['raw25','raw_pca6','statistics9']:return x
    x=np.clip(x,-1,1)
    complement=np.sqrt(np.maximum(0,1-x*x))
    g=(x[:,:,None]*x[:,None,:]-complement[:,:,None]*complement[:,None,:]).reshape(len(x),-1)
    return np.concatenate([g,x],axis=1) if name=='gaf_signed_pca6' else g


def fit_model(x, name, k, seed):
    a=encode(x,name)
    mean,std=fit_standardizer(a,np.arange(len(a)))
    a=(a-mean)/std
    pca=PCA(6,svd_solver='full') if name.endswith('pca6') else None
    if pca is not None:a=pca.fit_transform(a)
    km=KMeans(n_clusters=k,n_init=20,random_state=seed).fit(a)
    return mean,std,pca,km


def predict_model(x,name,model):
    mean,std,pca,km=model
    labels=np.empty(len(x),np.int16); distances=np.empty(len(x))
    for start in range(0,len(x),2048):
        a=(encode(x[start:start+2048],name)-mean)/std
        if pca is not None:a=pca.transform(a)
        lab=km.predict(a); labels[start:start+len(lab)]=lab
        distances[start:start+len(lab)]=np.linalg.norm(a-km.cluster_centers_[lab],axis=1)
    return labels,distances


def training_rows(d,seen,seed):
    rng=np.random.default_rng(seed); indices=[]
    train=d[d.site.eq('pizhou')&d.split.eq('train')&d.turbine.isin(seen)&d.representation_eligible]
    for _,g in train.groupby('config',sort=True):
        ix=g.index.to_numpy(); indices.extend(rng.choice(ix,min(2500,len(ix)),replace=False))
    return np.asarray(sorted(indices),int)


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--mode',choices=['primary','sensitivity','repeated'],default='primary')
    args=parser.parse_args()
    verification=json.loads((OUT/'verification.json').read_text())
    assert verification['status']=='PASS_INTERNAL_CONTRACT'
    # Refuse stale verification after any catalogue or pairing mutation.
    for name,sha in verification['inputs_sha256'].items():assert digest(ROOT/name)==sha
    for mf in ['catalog_manifest.json','pair_manifest.json']:
        for name,sha in json.loads((OUT/mf).read_text())['outputs_sha256'].items():assert digest(ROOT/name)==sha
    d=pd.read_csv(OUT/'candidate_intervals.csv.gz',dtype={'turbine':str})
    z=np.load(OUT/'context_shapes.npy',mmap_mode='r')
    test=d[d.representation_eligible&d.split.eq('test')].copy()
    testrows=test.index.to_numpy(); test_index=pd.Index(test.event_id)
    xtest=checked_take(z,test.shape_row.to_numpy()).astype(float)
    ftest=test[FEATURES].to_numpy(float)
    pairs=pd.read_csv(OUT/'test_pairs.csv.gz',dtype={'turbine':str})
    left=test_index.get_indexer(pairs.event_a); right=test_index.get_indexer(pairs.event_b)
    checked_take(xtest,left); checked_take(xtest,right)
    turbines=sorted(d.loc[d.site.eq('pizhou'),'turbine'].unique())
    primary_seen=turbines[:26]
    if args.mode=='repeated':
        schedule=[(f'repeat_{seed}',seed,sorted(np.random.default_rng(seed).choice(turbines,26,replace=False)),4,['raw25'])
                  for seed in range(20260912,20260922)]
    else:
        reps=['raw25','statistics9','raw_pca6','gaf_pca6','gaf_signed_pca6']
        schedule=[('primary',41,primary_seen,k,reps) for k in ([4] if args.mode=='primary' else [2,6])]
    results=[]; distances=[]; all_outputs=[]; start_time=time.monotonic()
    for run,seed,seen,k,names in schedule:
        tr=training_rows(d,seen,seed)
        assert d.loc[tr,'split'].eq('train').all() and d.loc[tr,'turbine'].isin(seen).all()
        train_key=OUT/f'train_{run}.csv'
        d.loc[tr,['event_id','site','turbine','split','config','shape_row']].to_csv(train_key,index=False)
        all_outputs.append(train_key)
        xtrain=checked_take(z,d.loc[tr,'shape_row'].to_numpy()).astype(float)
        ftrain=d.loc[tr,FEATURES].to_numpy(float)
        groups={site:np.flatnonzero(test.site.eq(site)) for site in sorted(test.site.unique())}
        groups['pizhou_seen']=np.flatnonzero(test.site.eq('pizhou')&test.turbine.isin(seen))
        groups['pizhou_unseen']=np.flatnonzero(test.site.eq('pizhou')&~test.turbine.isin(seen))
        pair_groups={site:np.flatnonzero(pairs.site.eq(site)) for site in sorted(pairs.site.unique())}
        pair_groups['pizhou_seen']=np.flatnonzero(pairs.site.eq('pizhou')&pairs.turbine.isin(seen))
        pair_groups['pizhou_unseen']=np.flatnonzero(pairs.site.eq('pizhou')&~pairs.turbine.isin(seen))
        for name in names:
            model=fit_model(ftrain if name=='statistics9' else xtrain,name,k,seed)
            labels,dist=predict_model(ftest if name=='statistics9' else xtest,name,model)
            variants={name:(labels,dist)}
            if args.mode=='primary' and name=='raw25':
                rng=np.random.default_rng(20260912)
                # Perturb held-out measurements only; frozen train-only model is identical.
                shuffled=xtest.copy()
                for ix in test.groupby(['site','turbine'],sort=True).indices.values():shuffled[ix]=xtest[rng.permutation(ix)]
                variants['event_row_permutation']=predict_model(shuffled,name,model)
                order=np.argsort(rng.random(xtest.shape),axis=1)
                variants['within_event_time_permutation']=predict_model(np.take_along_axis(xtest,order,axis=1),name,model)
            mean,std,pca,km=model
            model_file=OUT/f'model_{run}_{name}_k{k}.npz'
            np.savez_compressed(model_file,mean=mean,std=std,centers=km.cluster_centers_,
                pca_components=pca.components_ if pca is not None else np.empty((0,0)),
                pca_mean=pca.mean_ if pca is not None else np.empty(0))
            all_outputs.append(model_file)
            for variant,(lab,dis) in variants.items():
                label_file=OUT/f'labels_{run}_{variant}_k{k}.npz'
                np.savez_compressed(label_file,rows=testrows,labels=lab,distances=dis)
                all_outputs.append(label_file)
                for group,ix in groups.items():
                    frequency=np.bincount(lab[ix],minlength=k)/len(ix)
                    entropy=float(-np.sum(frequency[frequency>0]*np.log(frequency[frequency>0])))
                    distances.append({'run':run,'seed':seed,'k':k,'representation':variant,'group':group,
                        'events':len(ix),'turbines':test.iloc[ix].turbine.nunique(),
                        'median_distance':np.median(dis[ix]),'q90_distance':np.quantile(dis[ix],.9),'entropy':entropy,
                        'cluster_proportions':json.dumps(frequency.tolist())})
                for group,ix in pair_groups.items():
                    for (ca,cb),sub in pairs.iloc[ix].groupby(['config_a','config_b'],sort=True):
                        loc=sub.index.to_numpy(); la,lb=lab[left[loc]],lab[right[loc]]
                        results.append({'run':run,'seed':seed,'k':k,'representation':variant,'group':group,
                            'config_a':ca,'config_b':cb,'pairs':len(loc),'nmi':normalized_mutual_info_score(la,lb),
                            'ari':adjusted_rand_score(la,lb),'agreement':float(np.mean(la==lb)),
                            'left_clusters':len(np.unique(la)),'right_clusters':len(np.unique(lb))})
            print(run,k,name,'complete',flush=True)
    summary=pd.DataFrame(results); target=OUT/f'representation_pairs_{args.mode}.csv'
    summary.to_csv(target,index=False); all_outputs.append(target)
    target2=OUT/f'representation_distances_{args.mode}.csv'; pd.DataFrame(distances).to_csv(target2,index=False); all_outputs.append(target2)
    summary.groupby(['run','k','representation','group'])[['nmi','ari','agreement']].mean().to_csv(OUT/f'representation_summary_{args.mode}.csv')
    all_outputs.append(OUT/f'representation_summary_{args.mode}.csv')
    save_manifest(OUT/f'representation_manifest_{args.mode}.json',{'status':'EXPLORATORY_AWAITING_INDEPENDENT_RESULT_CHECK',
        'mode':args.mode,'runtime_seconds':time.monotonic()-start_time,'test_rows':len(test),
        'splits':[{'run':run,'seed':seed,'k':k,'seen':seen,'unseen':sorted(set(turbines)-set(seen))} for run,seed,seen,k,names in schedule],
        'notes':['No causal or confirmatory interpretation','Row/time controls perturb held-out data under frozen raw25 model',
                 'PCA representations have equal dimension, not identical metrics','Training cap 2500 per config shared across representations']},
        inputs=[OUT/'verification.json',OUT/'catalog_manifest.json',OUT/'pair_manifest.json',
                ROOT/'script/representation_audit_v5.py',ROOT/'script/event_contract_v5.py'],outputs=list(set(all_outputs)))


if __name__=='__main__':main()
