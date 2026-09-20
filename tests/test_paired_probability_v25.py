import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from wind_events.paired_probability import auc_draws,paired_rows


def test_block_auc_equals_explicit_weighting_with_ties():
    rng=np.random.default_rng(41);y=rng.integers(0,2,100);p=rng.choice([.1,.3,.7,.9],100);block=rng.integers(0,4,100)
    weights=np.vstack([np.ones(4),rng.multinomial(4,np.ones(4)/4,size=20)])
    actual=auc_draws(y,p,block,weights)
    expected=[roc_auc_score(y,p,sample_weight=w[block]) for w in weights]
    np.testing.assert_allclose(actual,expected,atol=1e-12)


def test_identical_predictions_have_zero_paired_interval():
    y=np.tile([0,1,2],20);p=np.full((60,3),.2);p[np.arange(60),y]=.6
    frame=pd.DataFrame({'outcome':y,'time_start':pd.date_range('2020-01-01',periods=60,freq='D',tz='UTC')})
    _,rows=paired_rows(frame,{'a':p,'b':p},[('a','b')],repetitions=100)
    assert all(r['gain']==r['low']==r['high']==0 for r in rows)
