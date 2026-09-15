"""Validated one-to-one matching with the original greedy tie rule and maximum-IoU assignment."""
from pathlib import Path
from itertools import combinations
from collections import defaultdict
import json
import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment
from sklearn.metrics import normalized_mutual_info_score, adjusted_rand_score

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"outputs/dynamic_events_v6"
OUT=ROOT/"outputs/event_matching_v14"

def candidate_edges(left,right,cutoff):
    edges=[]
    starts=np.array([r[1] for r in right])
    longest=max((r[2]-r[1] for r in right),default=0)
    for i,(aid,a0,a1) in enumerate(left):
        lo=np.searchsorted(starts,a0-longest,side="right")
        hi=np.searchsorted(starts,a1,side="left")
        for j in range(lo,hi):
            bid,b0,b1=right[j]
            score=(min(a1,b1)-max(a0,b0))/(max(a1,b1)-min(a0,b0))
            if score>=cutoff:
                edges.append((i,j,score,aid,bid,abs(a0-b0)))
    return edges

def greedy(edges):
    taken_left,taken_right=set(),set()
    result=[]
    for e in sorted(edges,key=lambda x:(-x[2],x[5],x[3],x[4])):
        if e[0] not in taken_left and e[1] not in taken_right:
            result.append(e)
            taken_left.add(e[0]);taken_right.add(e[1])
    return result

def optimal(edges):
    if not edges:
        return []
    left=sorted({(e[3],e[0]) for e in edges})
    right=sorted({(e[4],e[1]) for e in edges})
    li={i:j for j,(_,i) in enumerate(left)}
    ri={i:j for j,(_,i) in enumerate(right)}
    # Zero-reward dummies allow every left event to remain unmatched.
    reward=np.full((len(left),len(right)+len(left)),-1e6)
    reward[:,len(right):]=0
    lookup={}
    for e in edges:
        a,b=li[e[0]],ri[e[1]]
        reward[a,b]=e[2];lookup[a,b]=e
    rr,cc=linear_sum_assignment(reward,maximize=True)
    return [lookup[r,c] for r,c in zip(rr,cc) if (r,c) in lookup]

def metrics(counts):
    counts=np.asarray(counts,int).reshape(4,4)
    if not counts.sum():return np.nan,np.nan
    a=np.repeat(np.arange(4),counts.sum(axis=1))
    b=np.concatenate([np.repeat(np.arange(4),row) for row in counts])
    return normalized_mutual_info_score(a,b),adjusted_rand_score(a,b)

def main():
    fields=["event_id","site","turbine","split","config","time_start","time_end","representation_eligible"]
    d=pd.read_csv(SRC/"candidate_intervals.csv.gz",usecols=fields,dtype={"turbine":str})
    d=d[d.representation_eligible.fillna(False)&d.split.eq("test")].copy()
    label_file=np.load(SRC/"labels_primary_raw25_k4.npz")
    assert np.array_equal(d.index.to_numpy(),label_file["rows"])
    d["label"]=label_file["labels"]
    event_labels=dict(zip(d.event_id,d.label))
    assert d.event_id.is_unique
    for column in ["time_start","time_end"]:
        d[column]=pd.to_datetime(d[column],utc=True).astype("int64")
    assert d.time_end.gt(d.time_start).all()
    archive=pd.read_csv(SRC/"test_pairs.csv.gz",dtype={"turbine":str})
    baseline={key:set(zip(g.event_a,g.event_b)) for key,g in archive.groupby(["site","turbine","config_a","config_b"])}
    accumulator={}
    verified=0
    for (site,turbine),g in d.groupby(["site","turbine"],sort=True):
        parts={name:list(q.sort_values(["time_start","time_end","event_id"])[["event_id","time_start","time_end"]].itertuples(index=False,name=None))
               for name,q in g.groupby("config",sort=True)}
        for ca,cb in combinations(sorted(parts),2):
            left,right=parts[ca],parts[cb]
            all_edges=candidate_edges(left,right,.3)
            for cutoff in [.3,.5,.7]:
                es=[e for e in all_edges if e[2]>=cutoff]
                for method,algorithm in [("greedy",greedy),("maximum_iou",optimal)]:
                    selected=algorithm(es)
                    assert len({e[0] for e in selected})==len(selected)==len({e[1] for e in selected})
                    if method=="greedy" and cutoff==.5:
                        expected=baseline.get((site,turbine,ca,cb),set())
                        assert {(e[3],e[4]) for e in selected}==expected,(site,turbine,ca,cb)
                        verified+=len(selected)
                    key=(site,cutoff,method,ca,cb)
                    if key not in accumulator:accumulator[key]=[np.zeros(16,dtype=np.int64),0.,0,0]
                    item=accumulator[key]
                    if selected:
                        encoded=[event_labels[e[3]]*4+event_labels[e[4]] for e in selected]
                        item[0]+=np.bincount(encoded,minlength=16)
                    item[1]+=sum(e[2] for e in selected);item[2]+=len(left);item[3]+=len(right)
        print(site,turbine,"complete",flush=True)
    assert verified==len(archive)
    rows=[]
    for (site,cutoff,method,ca,cb),(counts,total_iou,left_n,right_n) in accumulator.items():
        nmi,ari=metrics(counts); n=int(counts.sum())
        rows.append(dict(site=site,cutoff=cutoff,method=method,config_a=ca,config_b=cb,pairs=n,nmi=nmi,ari=ari,
                         mean_iou=total_iou/n if n else np.nan,left_n=left_n,right_n=right_n,
                         left_coverage=n/left_n,right_coverage=n/right_n))
    result=pd.DataFrame(rows)
    summary=[]
    for (site,cutoff,method),g in result.groupby(["site","cutoff","method"]):
        positive=g[g.pairs.gt(0)]
        summary.append(dict(site=site,cutoff=cutoff,method=method,pairs=int(g.pairs.sum()),nmi=positive.nmi.mean(),
                            ari=positive.ari.mean(),weighted_nmi=np.average(positive.nmi,weights=positive.pairs),
                            weighted_ari=np.average(positive.ari,weights=positive.pairs),
                            left_coverage=g.left_coverage.mean(),right_coverage=g.right_coverage.mean(),
                            mean_iou=np.average(positive.mean_iou,weights=positive.pairs)))
    OUT.mkdir(parents=True,exist_ok=True)
    result.to_csv(OUT/"configuration_pair_metrics.csv",index=False)
    pd.DataFrame(summary).to_csv(OUT/"event_matching_summary.csv",index=False)
    (OUT/"verification.json").write_text(json.dumps({"baseline_exact_event_pairs":verified,"baseline_matches":True,
        "aggregation":"pool labels across turbines within configuration pairs; average nonempty configuration pairs",
        "optimal_objective":"maximize total feasible IoU, unmatched reward zero","tie_rule":"greedy original v6 rule; optimal fixed ID-ordered matrix"},indent=2))
if __name__=="__main__":
    main()
