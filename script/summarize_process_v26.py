"""Report all frozen primary choices, matched controls and process metrics."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from sklearn.metrics import f1_score,precision_score,recall_score,roc_auc_score,average_precision_score
from physical_process_v26 import OUT,measures,paired
from wind_events.paired_probability import block_design,auc_draws


def load_prediction(choice):
    folder=OUT/choice['dataset']
    if choice['track'] in ['physical','residual']:folder/='physical_calibration'
    arrays=np.load(folder/'test_predictions.npz')
    events=pd.read_parquet(folder/'test_events.parquet')
    return events,arrays['actual'],arrays[choice['arm']]


def classification_draws(actual,predicted,times,days=7):
    index,weights=block_design(times,days,2000);both=np.vstack([np.ones((1,weights.shape[1])),weights])
    cells=np.zeros((weights.shape[1],16))
    np.add.at(cells,(index,4*actual+predicted),1)
    matrix=(both@cells).reshape(-1,4,4)
    tp=np.diagonal(matrix,axis1=1,axis2=2);den=matrix.sum(axis=1)+matrix.sum(axis=2)
    f1=np.divide(2*tp,den,out=np.zeros_like(tp),where=den>0)
    return f1.mean(axis=1),f1[:,3]


def return_score(prediction):
    curve=np.c_[np.zeros(len(prediction)),prediction]
    up=(curve-np.minimum.accumulate(curve,axis=1)).max(axis=1)
    down=(np.maximum.accumulate(curve,axis=1)-curve).max(axis=1)
    return np.minimum(up,down)


def main():
    locked=json.loads((OUT/'final_validation_lock.json').read_text())
    rows=[];intervals=[];classification=[];component=[]
    candidates=pd.read_csv(OUT/'final_validation_candidates.csv')
    for item in locked['choices']:
        if item['scope']!='native10':continue
        source=item['source'];base=item['baseline'];method=item['pipeline']
        events,y,p=load_prediction(method);b_events,b_y,b=load_prediction(base)
        assert list(events.event_id)==list(b_events.event_id) and np.array_equal(y,b_y)
        pm,bm=measures(y,p),measures(y,b)
        old=candidates[candidates.source.eq(source)&candidates.scalar_only&candidates.power_minutes.eq(30)].sort_values(['validation_mse','track','arm']).iloc[0].to_dict()
        old_events,old_y,old_p=load_prediction(old)
        assert list(old_events.event_id)==list(events.event_id) and np.array_equal(old_y,y)
        om=measures(y,old_p)
        row={'source':source,'events':len(events),'baseline':base['track']+'/'+base['arm'],'pipeline':method['track']+'/'+method['arm'],
            'old30_scalar_rmse_ms':float(np.sqrt(om['mse'].mean())),
            'native_scalar_rmse_ms':float(np.sqrt(bm['mse'].mean())),
            'pipeline_rmse_ms':float(np.sqrt(pm['mse'].mean())),
            'shape_increment_rmse_pct':100*(1-np.sqrt(pm['mse'].mean()/bm['mse'].mean())),
            'whole_protocol_rmse_pct':100*(1-np.sqrt(pm['mse'].mean()/om['mse'].mean())),
            'geometry_increment_rmse_pct':100*(1-np.sqrt(pm['geometry_mse'].mean()/bm['geometry_mse'].mean())),
            'excursion_mae_reduction_pct':100*(1-pm['excursion_abs_error'].mean()/bm['excursion_abs_error'].mean()),
            'endpoint_mae_change_ms':float(pm['endpoint_abs_error'].mean()-bm['endpoint_abs_error'].mean())}
        for label,values,prediction in [('baseline',bm,b),('pipeline',pm,p)]:
            truth=values['actual_class'];pred=values['predicted_class']
            row[label+'_macro_f1']=f1_score(truth,pred,labels=[0,1,2,3],average='macro',zero_division=0)
            row[label+'_return_f1']=f1_score(truth==3,pred==3,zero_division=0)
            row[label+'_return_precision']=precision_score(truth==3,pred==3,zero_division=0)
            row[label+'_return_recall']=recall_score(truth==3,pred==3,zero_division=0)
            score=return_score(prediction)
            row[label+'_return_auroc']=roc_auc_score(truth==3,score)
            row[label+'_return_average_precision']=average_precision_score(truth==3,score)
        prevalence=float((pm['actual_class']==3).mean())
        row['constant_return_precision']=prevalence
        row['constant_return_f1']=2*prevalence/(1+prevalence)
        row['return_events']=int((pm['actual_class']==3).sum());rows.append(row)
        for name,a,c in [('same_resolution_full',pm['mse'],bm['mse']),('same_resolution_geometry',pm['geometry_mse'],bm['geometry_mse']),
                         ('whole_protocol_full',pm['mse'],om['mse']),('sampling_scalar_only',bm['mse'],om['mse'])]:
            for days in [3,7,14]:
                intervals.append({'source':source,'comparison':name,**paired(events.time_start,a,c,days)})
        for days in [3,7,14]:
            pf,pr=classification_draws(pm['actual_class'],pm['predicted_class'],events.time_start,days)
            bf,br=classification_draws(bm['actual_class'],bm['predicted_class'],events.time_start,days)
            for name,v in [('macro_f1',pf-bf),('return_f1',pr-br)]:
                lo,hi=np.quantile(v[1:],[.025,.975])
                classification.append({'source':source,'metric':name,'block_days':days,'gain':v[0],'low':lo,'high':hi})
            index,weights=block_design(events.time_start,days,2000)
            weights=np.vstack([np.ones((1,weights.shape[1])),weights])
            au=auc_draws(pm['actual_class']==3,return_score(p),index,weights)
            bu=auc_draws(pm['actual_class']==3,return_score(b),index,weights)
            gain=au-bu;lo,hi=np.nanquantile(gain[1:],[.025,.975])
            classification.append({'source':source,'metric':'return_auroc','block_days':days,'gain':gain[0],'low':lo,'high':hi})
        for name,mask in [('all',np.ones(len(events),bool)),('composite',events.has_composite.to_numpy(bool)),
                         ('primitive_only',~events.has_composite.to_numpy(bool)),('wind_return',pm['actual_class']==3)]:
            if not mask.any():continue
            component.append({'source':source,'population':name,'events':int(mask.sum()),
                'full_rmse_reduction_pct':100*(1-np.sqrt(pm['mse'][mask].mean()/bm['mse'][mask].mean())),
                'geometry_rmse_reduction_pct':100*(1-np.sqrt(pm['geometry_mse'][mask].mean()/bm['geometry_mse'][mask].mean()))})
    pd.DataFrame(rows).to_csv(OUT/'primary_results.csv',index=False)
    pd.DataFrame(intervals).to_csv(OUT/'primary_intervals.csv',index=False)
    pd.DataFrame(classification).to_csv(OUT/'process_class_intervals.csv',index=False)
    pd.DataFrame(component).to_csv(OUT/'primary_subgroups.csv',index=False)
    print(pd.DataFrame(rows).to_string(index=False))
    print(pd.DataFrame(intervals).query('block_days==7').to_string(index=False))
    print(pd.DataFrame(classification).query('block_days==7').to_string(index=False))
    status={'status':'COMPLETE_FROZEN_CHOICES_ALL_REPORTED','primary_practical_gate_pct':10,
        'same_resolution_full_curve_gate_count':int(sum(r['shape_increment_rmse_pct']>=10 for r in rows)),
        'total_populations':len(rows),'higher_secondary_geometry_gain':'reported separately; not substituted for the full-curve primary endpoint',
        'no_new_human_or_AI_ratings':True}
    (OUT/'status.json').write_text(json.dumps(status,indent=2))


if __name__=='__main__':main()
