"""Greek local-training baseline under the same event correspondence table."""
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import normalized_mutual_info_score, adjusted_rand_score
ROOT=Path(__file__).resolve().parents[1]; BASE=ROOT/'outputs/dynamic_events_v6/external_greece'; OUT=ROOT/'outputs/external_local_v13'; OUT.mkdir(parents=True,exist_ok=True)
def main():
    d=pd.read_csv(BASE/'candidate_intervals.csv.gz',dtype={'turbine':str}); z=np.load(BASE/'context_shapes.npy',mmap_mode='r'); d=d[d.representation_eligible.fillna(False)].copy()
    tr=d[d.split.eq('train')]; te=d[d.split.eq('test')]; train=np.asarray(z[tr.shape_row],float); test=np.asarray(z[te.shape_row],float); mu=train.mean(0); sd=train.std(0);sd[sd<1e-6]=1;train=(train-mu)/sd;test=(test-mu)/sd
    km=KMeans(n_clusters=4,n_init=20,random_state=41).fit(train); labels=km.predict(test); pos={e:i for i,e in enumerate(te.event_id)}; pairs=pd.read_csv(BASE/'test_pairs.csv.gz'); pairs=pairs[pairs.event_a.isin(pos)&pairs.event_b.isin(pos)]
    rows=[]
    for (ca,cb),p in pairs.groupby(['config_a','config_b']):
        la=labels[[pos[e] for e in p.event_a]];lb=labels[[pos[e] for e in p.event_b]];rows.append({'config_a':ca,'config_b':cb,'pairs':len(p),'nmi':normalized_mutual_info_score(la,lb),'ari':adjusted_rand_score(la,lb),'agreement':float(np.mean(la==lb))})
    out=pd.DataFrame(rows);out.to_csv(OUT/'greece_local_raw25_pairs.csv',index=False);summary={'site':'greece','train_events':len(tr),'test_events':len(te),'configuration_pairs':len(out),'mean_nmi':float(out.nmi.mean()),'mean_ari':float(out.ari.mean()),'mean_agreement':float(out.agreement.mean()),'model':'locally standardized raw25 + KMeans k4','frozen_training_rows':0};(OUT/'manifest.json').write_text(__import__('json').dumps(summary,indent=2));print(summary)
if __name__=='__main__':main()
