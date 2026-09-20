from pathlib import Path
import sys
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'script'));sys.path.insert(0,str(ROOT/'src'))
from prepare_process_v26 import wind_curves,process_class
from physical_process_v26 import paired


def test_wind_curve_rejects_missing_internal_measurement():
    t=pd.date_range('2020-01-01',periods=13,freq='10min',tz='UTC')
    d=pd.DataFrame({'time_start':[t[0]],'time_end':[t[-1]]})
    w=pd.Series(np.linspace(4,8,13),index=t)
    ix,y=wind_curves(d,w);assert list(ix)==[0] and y.shape==(1,17)
    np.testing.assert_allclose(y[0],np.linspace(0,4,17))
    w.iloc[5]=np.nan;ix,_=wind_curves(d,w);assert len(ix)==0


def test_drawup_and_drawdown_keep_return_process():
    x=np.array([[0,1,2],[0,-1,-2],[0,2,0],[0,.1,0]])
    assert list(process_class(x))==[1,2,3,0]


def test_paired_identical_error_has_zero_gain():
    t=pd.date_range('2020-01-01',periods=40,freq='D',tz='UTC')
    v=np.linspace(.1,1,40);r=paired(t,v,v)
    assert r['relative_rmse_reduction_pct']==r['low']==r['high']==0
