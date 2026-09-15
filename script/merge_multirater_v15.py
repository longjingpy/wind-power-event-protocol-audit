"""Merge blinded rating exports and compute agreement only on shared real responses."""
from pathlib import Path
from collections import Counter, defaultdict
from itertools import combinations
import argparse, csv, json, re

SCHEMA="wind_multirater_v15"
LABELS={"upward":"yes","downward":"yes","valley":"yes","peak":"yes","oscillatory":"yes",
        "low_state":"no","quiet":"no","uncertain":"uncertain","data_issue":"unassessable"}

def validate(payload,packet):
    if payload.get("schema")!=SCHEMA or payload.get("packet_id")!=packet["packet_id"]:
        raise ValueError("Schema or frozen packet does not match")
    rater=payload.get("annotator_id","")
    if not re.fullmatch(r"[A-Za-z0-9_-]{3,40}",rater):
        raise ValueError("Invalid anonymous annotator ID")
    if rater.startswith("QA_"):
        raise ValueError("UI-test responses cannot enter research agreement estimates")
    known={w["window_id"]:w for w in packet["windows"]}
    rows=payload.get("annotations")
    if not isinstance(rows,list) or len(rows)>len(known):raise ValueError("Invalid annotations")
    used=set()
    for row in rows:
        wid=row.get("window_id")
        if wid not in known or wid in used:raise ValueError("Unknown or duplicate window")
        used.add(wid)
        if row.get("morphology") not in LABELS or row.get("event_presence")!=LABELS[row["morphology"]]:
            raise ValueError("Presence and morphology must follow packet definitions")
        if any(row.get(k)!=known[wid][k] for k in ["target_start","target_end"]):
            raise ValueError("Target region was changed")
        if row.get("confidence") not in ["unrated","low","medium","high"]:raise ValueError("Invalid confidence")
        a,b=row.get("event_start_relative_min"),row.get("event_end_relative_min")
        if (a is None)!=(b is None):raise ValueError("Boundary endpoints must both be supplied")
        if a is not None:
            if not isinstance(a,(int,float)) or not isinstance(b,(int,float)) or not -60<=a<=b<=60:
                raise ValueError("Invalid within-region boundary")
        if not isinstance(row.get("updated_at"),str):raise ValueError("Missing response time")
    return rater,rows

def cohen(left,right):
    n=len(left)
    if n==0:return {"n":0,"observed_agreement":None,"kappa":None,"status":"NO_SHARED_RATINGS"}
    po=sum(a==b for a,b in zip(left,right))/n
    a,b=Counter(left),Counter(right)
    pe=sum(a[k]*b[k] for k in set(a)|set(b))/(n*n)
    return {"n":n,"observed_agreement":po,"kappa":(po-pe)/(1-pe) if pe<1 else None,
            "status":"DEFINED" if pe<1 else "DEGENERATE_MARGINALS"}

def nominal_alpha(units):
    eligible=[list(unit) for unit in units if len(unit)>=2]
    n=sum(len(u) for u in eligible)
    if n<2:return {"alpha":None,"rated_units":len(eligible),"ratings":n,"status":"INSUFFICIENT_OVERLAP"}
    margins=Counter(v for u in eligible for v in u)
    disagreement=sum((len(u)**2-sum(c*c for c in Counter(u).values()))/(len(u)-1) for u in eligible)/n
    expected=(n*n-sum(c*c for c in margins.values()))/(n*(n-1))
    return {"alpha":1-disagreement/expected if expected else None,"rated_units":len(eligible),
            "ratings":n,"observed_disagreement":disagreement,"expected_disagreement":expected,
            "status":"DEFINED" if expected else "DEGENERATE_MARGINALS"}

def merge_payloads(payloads,packet):
    merged={};versions=defaultdict(int)
    for payload in payloads:
        rater,rows=validate(payload,packet)
        for row in rows:
            row=dict(row,annotator_id=rater)
            key=(rater,row["window_id"]);versions[key]+=1
            if key in merged and row["updated_at"]==merged[key]["updated_at"] and row!=merged[key]:
                raise ValueError("Conflicting answers with the same annotator, window and timestamp")
            if key not in merged or row["updated_at"]>merged[key]["updated_at"]:
                merged[key]=row
    return list(merged.values()),sum(n-1 for n in versions.values())

def agreement(rows):
    raters=sorted({r["annotator_id"] for r in rows})
    output={"distinct_annotator_ids":len(raters),"responses":len(rows),
            "status":"AGREEMENT_AVAILABLE" if len(raters)>=2 else "AWAITING_INDEPENDENT_RATINGS",
            "pairwise":[],"alpha":{}}
    for field in ["event_presence","morphology"]:
        admissible=lambda r:r["event_presence"] in ["yes","no"]
        lookup={(r["annotator_id"],r["window_id"]):r[field] for r in rows if admissible(r)}
        units=defaultdict(list)
        for (_,wid),value in lookup.items():units[wid].append(value)
        output["alpha"][field]=nominal_alpha(units.values())
        for a,b in combinations(raters,2):
            shared=sorted({w for rr,w in lookup if rr==a}&{w for rr,w in lookup if rr==b})
            output["pairwise"].append({"field":field,"rater_a":a,"rater_b":b,
                **cohen([lookup[a,w] for w in shared],[lookup[b,w] for w in shared])})
    output["label_counts"]={r:dict(Counter(x["morphology"] for x in rows if x["annotator_id"]==r)) for r in raters}
    return output

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--packet",type=Path,required=True)
    parser.add_argument("--inputs",type=Path,nargs="+",required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    packet=json.loads(args.packet.read_text(encoding="utf8"))
    payloads=[json.loads(p.read_text(encoding="utf-8-sig")) for p in args.inputs]
    rows,duplicates=merge_payloads(payloads,packet)
    report=agreement(rows);report.update(packet_id=packet["packet_id"],superseded_response_versions=duplicates)
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/"agreement.json").write_text(json.dumps(report,ensure_ascii=False,indent=2))
    if rows:
        with (args.output/"ratings_long.csv").open("w",newline="",encoding="utf8") as handle:
            writer=csv.DictWriter(handle,fieldnames=list(rows[0]))
            writer.writeheader();writer.writerows(rows)
    print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
