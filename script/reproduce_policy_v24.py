"""Recompute v24 policy fee totals from the released model-input bundle."""
from pathlib import Path
import sys,json
import numpy as np
import joblib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from forecast_penalty_v24 import CENTERS,tolerance_action,point_fee


def main():
    records=[]
    for r in json.loads((ROOT/'cases.json').read_text()):
        d=np.load(ROOT/'inputs'/f'{r["case"]}.npz');test=d['split']==2
        artifact=joblib.load(ROOT/'models'/f'{r["case"]}.joblib');model=artifact['model'];config=artifact['config']
        p=np.zeros((int(test.sum()),len(CENTERS)));p[:,model.classes_]=model.predict_proba(d['features'][test])
        if config['action']=='mean':q=p@CENTERS
        elif config['action']=='median':q=CENTERS[(np.cumsum(p,axis=1)>=.5).argmax(axis=1)]
        else:q=tolerance_action(p,r['tolerance'])
        base=d['persistence_pu'][test];y=d['actual_pu'][test]
        q=np.clip((1-config['blend'])*base+config['blend']*q,0,1)
        fee=point_fee(y,q,r['tolerance'],r['capacity_mw']).sum()
        baseline=point_fee(y,base,r['tolerance'],r['capacity_mw']).sum()
        np.testing.assert_allclose(fee,r['expected_fee_cny'],rtol=0,atol=.005)
        np.testing.assert_allclose(np.abs(y-q).mean(),r['expected_nmae'],rtol=0,atol=1e-8)
        records.append({'case':r['case'],'points':len(q),'fee_cny':round(float(fee),2),
                        'saved_cny':round(float(baseline-fee),2),'nmae':float(np.abs(y-q).mean())})
    print(json.dumps(records,indent=2))


if __name__=='__main__':main()
