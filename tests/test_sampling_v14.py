import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'script'))
from yandun_sampling_v14 import threshold_anchors

def test_four_hour_physical_lag():
    for minutes in [15, 30, 60]:
        p = pd.Series(np.arange(40)*minutes/60*.1)
        eligible, delta, hit = threshold_anchors(p, pd.Series(True, index=p.index), minutes, 4)
        np.testing.assert_allclose(delta[eligible], .4)
        assert hit[eligible].all()

def test_missing_middle_excludes_entire_window():
    p = pd.Series(np.arange(30)/30)
    valid = pd.Series(True, index=p.index)
    valid.iloc[10] = False
    eligible, _, _ = threshold_anchors(p, valid, 30, 4)
    assert not eligible.iloc[10:19].any()
