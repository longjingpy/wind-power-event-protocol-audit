from pathlib import Path
import sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'script'))
from storage_policy_v15 import online, price, oracle, capital, CRF

def test_zero_capacity_and_missing_time():
    r=np.array([1.,np.nan,-1.])
    state=online(r,0,0,critical=.2)
    assert state['shortfall_mwh']==.5 and state['surplus_mwh']==.5
    assert price(state,300,80,0)==190
    assert capital(0,0,10)==0

def test_constraints_and_oracle_bound():
    r=np.array([1.,-1.,.2,-.7,0.,1.,-1.])
    state=online(r,.5,1.,critical=.2)
    assert .1-1e-9<=state['terminal_soc_mwh']<=.9+1e-9
    result=oracle(r,.5,1.,300,80,0,.2)
    assert result['operating_cost']<=price(state,300,80,0)+1e-8
    assert 0<CRF<1
