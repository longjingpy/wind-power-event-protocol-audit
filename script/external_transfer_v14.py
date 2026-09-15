"""Frozen and target-adapted TCN on identical Greek event pairs and aggregation units."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import torch
from sklearn.cluster import KMeans
from sklearn.metrics import normalized_mutual_info_score, adjusted_rand_score
from cv_benchmark_v7 import EncoderAE, sample_rows
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"outputs/dynamic_events_v6"; G=SRC/"external_greece"; OUT=ROOT/"outputs/external_transfer_v14"
def encode(model, x, device):
    model.eval(); parts=[]
    with torch.no_grad():
        for start in range(0,len(x),2048):
            parts.append(model.encode(torch.as_tensor(x[start:start+2048],device=device)).cpu().numpy())
    return np.concatenate(parts)
def main():
    torch.set_num_threads(2); torch.manual_seed(41)
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    d=pd.read_csv(SRC/"candidate_intervals.csv.gz",dtype={"turbine":str})
    x=np.load(SRC/"context_shapes.npy",mmap_mode="r")
    seen=sorted(d.loc[d.site.eq("pizhou"),"turbine"].unique())[:26]
    mask=d.representation_eligible.fillna(False)&d.site.eq("pizhou")&d.split.eq("train")&d.turbine.isin(seen)
    rows=sample_rows(d,mask,2500,41)
    greek=pd.read_csv(G/"candidate_intervals.csv.gz",dtype={"turbine":str})
    gx=np.load(G/"context_shapes.npy",mmap_mode="r")
    train=greek[greek.representation_eligible.fillna(False)&greek.split.eq("train")]
    test=greek[greek.representation_eligible.fillna(False)&greek.split.eq("test")].copy()
    checkpoint=torch.load(ROOT/"outputs/cv_benchmark_v7_100/model_tcn_seed41.pt",map_location="cpu",weights_only=False)
    mu,sd=checkpoint["input_mean"],checkpoint["input_std"]
    source_x=(np.asarray(x[d.loc[rows,"shape_row"]],np.float32)-mu)/sd
    train_x=(np.asarray(gx[train.shape_row],np.float32)-mu)/sd
    test_x=(np.asarray(gx[test.shape_row],np.float32)-mu)/sd
    pairs=pd.read_csv(G/"test_pairs.csv.gz")
    index=pd.Index(test.event_id)
    left,right=index.get_indexer(pairs.event_a),index.get_indexer(pairs.event_b)
    assert (left>=0).all() and (right>=0).all()
    results=[]; summaries=[]
    for mode in ["frozen","target_finetuned"]:
        torch.manual_seed(41)
        model=EncoderAE("tcn").to(device);model.load_state_dict(checkpoint["state_dict"])
        if mode=="target_finetuned":
            opt=torch.optim.Adam(model.parameters(),lr=1e-4);rng=np.random.default_rng(20260914)
            for epoch in range(5):
                model.train()
                order=rng.permutation(len(train_x))
                for start in range(0,len(order),256):
                    xb=torch.as_tensor(train_x[order[start:start+256]],device=device)
                    opt.zero_grad(set_to_none=True);loss=((model(xb)-xb)**2).mean();loss.backward();opt.step()
        source_z,test_z=encode(model,source_x,device),encode(model,test_x,device)
        mean,std=source_z.mean(0),source_z.std(0);std[std<1e-6]=1
        km=KMeans(n_clusters=4,n_init=20,random_state=41).fit((source_z-mean)/std)
        labels=km.predict((test_z-mean)/std)
        local=[]
        for (ca,cb),sub in pairs.groupby(["config_a","config_b"],sort=True):
            ix=sub.index.to_numpy();a,b=labels[left[ix]],labels[right[ix]]
            row=dict(mode=mode,config_a=ca,config_b=cb,pairs=len(ix),
                     nmi=normalized_mutual_info_score(a,b),ari=adjusted_rand_score(a,b))
            local.append(row);results.append(row)
        t=pd.DataFrame(local);a,b=labels[left],labels[right]
        summaries.append(dict(mode=mode,seed=41,adapt_epochs=5 if mode=="target_finetuned" else 0,
                    event_pairs=len(pairs),configuration_pairs=len(t),
                    pooled_nmi=normalized_mutual_info_score(a,b),pooled_ari=adjusted_rand_score(a,b),
                    equal_pair_nmi=t.nmi.mean(),equal_pair_ari=t.ari.mean(),
                    weighted_nmi=np.average(t.nmi,weights=t.pairs),weighted_ari=np.average(t.ari,weights=t.pairs)))
    OUT.mkdir(parents=True,exist_ok=True)
    pd.DataFrame(results).to_csv(OUT/"configuration_metrics.csv",index=False)
    pd.DataFrame(summaries).to_csv(OUT/"summary.csv",index=False)
    (OUT/"protocol.json").write_text(json.dumps({"source_turbines":seen,"source_rows":len(rows),
      "target_train_rows":len(train),"target_test_rows":len(test),"pair_count":len(pairs),
      "target_test_used_for_fit":False,"seed":41,"adaptation_epochs":5},indent=2))
    print(pd.DataFrame(summaries).to_string(index=False))
if __name__=="__main__":main()
