"""Verify common event/target support, train-only fitting records and locks."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/protocol_benchmark_v26'


def main():
    lock=json.loads((OUT/'final_validation_lock.json').read_text())
    assert lock['status']=='LOCKED_BEFORE_V26_TEST'
    result=[]
    for source in ['lidar_T11','lidar_T07','smarteole']:
        old=pd.read_parquet(OUT/source/'events.parquet');new=pd.read_parquet(OUT/(source+'_native10')/'events.parquet')
        a=np.load(OUT/source/'arrays.npz');b=np.load(OUT/(source+'_native10')/'arrays.npz')
        assert list(old.event_id)==list(new.event_id)
        assert np.array_equal(a['wind_change'],b['wind_change'])
        assert np.array_equal(a['process_class'],b['process_class'])
        assert old.split.equals(new.split)
        for suffix in ['', '_native10']:
            dataset=source+suffix;folder=OUT/dataset
            d=pd.read_parquet(folder/'events.parquet');data=np.load(folder/'arrays.npz')
            assert not d.duplicated(['turbine','time_start','time_end']).any()
            assert data['shape'].shape[1]==25 and data['scalar'].shape[1]==19 and data['wind_change'].shape[1]==17
            assert np.allclose(data['shape'][:,4],0) and np.allclose(data['wind_change'][:,0],0)
            assert np.isfinite(data['shape']).all() and np.isfinite(data['scalar']).all() and np.isfinite(data['wind_change']).all()
            base=json.loads((folder/'selection.json').read_text())
            phys=json.loads((folder/'physical_calibration/selection.json').read_text())
            resid=json.loads((folder/'physical_calibration/residual_selection.json').read_text())
            assert len(base['selected'])==12 and len(phys['selected'])==9 and len(resid['selected'])==5
            assert sum(f['held_events'] for f in resid['folds'])==int(d.split.eq('train').sum())
            for path in [folder/'test_predictions.npz',folder/'physical_calibration/test_predictions.npz']:
                predictions=np.load(path)
                assert np.array_equal(predictions['actual'],data['wind_change'][d.split.eq('test'),1:])
            result.append({'dataset':dataset,'events':len(d),'train':int(d.split.eq('train').sum()),
                'validation':int(d.split.eq('validation').sum()),'test':int(d.split.eq('test').sum()),
                'composite_backed':int(d.has_composite.sum()),'verification':'PASS'})
    pd.DataFrame(result).to_csv(OUT/'verification.csv',index=False)
    print(pd.DataFrame(result).to_string(index=False))


if __name__=='__main__':main()
