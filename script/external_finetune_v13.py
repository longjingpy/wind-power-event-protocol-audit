"""Unlabelled Greek fine-tuning baseline with Pizhou prototype refitting."""
from pathlib import Path
import copy, json, sys
import numpy as np
import pandas as pd
import torch
from sklearn.cluster import KMeans
from sklearn.metrics import normalized_mutual_info_score, adjusted_rand_score
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'script')); from cv_benchmark_v7 import EncoderAE
IN=ROOT/'outputs/dynamic_events_v6'; G=IN/'external_greece'; OUT=ROOT/'outputs/external_finetune_v13'; OUT.mkdir(parents=True,exist_ok=True)
def embed(model,x,device):
    model.eval(); out=[]
    with torch.no_grad():
        for i in range(0,len(x),4096): out.append(model.encode(torch.as_tensor(x[i:i+4096],device=device)).cpu().numpy())
    return np.concatenate(out)
def main():
    device=torch.device('cuda' if torch.cuda.is_available() else 'cpu'); d=pd.read_csv(IN/'candidate_intervals.csv.gz',dtype={'turbine':str}); z=np.load(IN/'context_shapes.npy',mmap_mode='r'); p=d[(d.representation_eligible.fillna(False))&(d.site.eq('pizhou'))&(d.split.eq('train'))]; gp=pd.read_csv(G/'candidate_intervals.csv.gz',dtype={'turbine':str}); gz=np.load(G/'context_shapes.npy',mmap_mode='r'); gt=gp[gp.representation_eligible.fillna(False)&gp.split.eq('train')]; ge=gp[gp.representation_eligible.fillna(False)&gp.split.eq('test')].reset_index(drop=True)
    # Same Pizhou sample used by the 100-epoch run.
    rng=np.random.default_rng(41); rows=[]
    for _,q in p.groupby('config',sort=True): rows.extend(rng.choice(q.index,min(2500,len(q)),replace=False).tolist())
    px=np.asarray(z[p.loc[sorted(rows),'shape_row']],np.float32); gx=np.asarray(gz[gt.shape_row],np.float32); ex=np.asarray(gz[ge.shape_row],np.float32)
    model=EncoderAE('tcn').to(device); state=torch.load(ROOT/'outputs/cv_benchmark_v7_100/model_tcn_seed41.pt',map_location=device,weights_only=False); model.load_state_dict(state['state_dict']); mu=np.asarray(state['input_mean']);sd=np.asarray(state['input_std']); gx=(gx-mu)/sd;ex=(ex-mu)/sd; opt=torch.optim.Adam(model.parameters(),lr=1e-4); rng2=np.random.default_rng(20260914)
    for _ in range(5):
        model.train(); order=rng2.permutation(len(gx))
        for i in range(0,len(order),256):
            xb=torch.as_tensor(gx[order[i:i+256]],device=device);opt.zero_grad(set_to_none=True);loss=((model(xb)-xb)**2).mean();loss.backward();opt.step()
    pz=(px-mu)/sd; ztrain=embed(model,pz,device); ztest=embed(model,ex,device); km=KMeans(n_clusters=4,n_init=20,random_state=41).fit(ztrain); labels=km.predict(ztest); pos={e:i for i,e in enumerate(ge.event_id)}; pairs=pd.read_csv(G/'test_pairs.csv.gz'); pairs=pairs[pairs.event_a.isin(pos)&pairs.event_b.isin(pos)]; la=labels[[pos[e] for e in pairs.event_a]];lb=labels[[pos[e] for e in pairs.event_b]]; result={'training':'Pizhou encoder fine-tuned on unlabeled Greek train shapes','epochs':5,'test_pairs':len(pairs),'nmi':float(normalized_mutual_info_score(la,lb)),'ari':float(adjusted_rand_score(la,lb)),'agreement':float(np.mean(la==lb)),'source_training_labels':0};(OUT/'manifest.json').write_text(json.dumps(result,indent=2));pd.DataFrame([result]).to_csv(OUT/'greece_finetune_summary.csv',index=False);print(result)
if __name__=='__main__':main()
