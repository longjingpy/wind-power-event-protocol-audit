from pathlib import Path
import sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from wind_events.process_encoding import gadf
from wind_events.representation import gasf


def test_even_odd_fields_and_zero_anchor_recovery():
    x=np.random.default_rng(41).uniform(-1,1,(20,25));x[:,4]=0
    np.testing.assert_allclose(gasf(x),gasf(-x))
    np.testing.assert_allclose(gadf(x),-gadf(-x))
    np.testing.assert_allclose(gadf(x)[:,4,:],x)
    np.testing.assert_allclose(gadf(x),-gadf(x).transpose(0,2,1))
