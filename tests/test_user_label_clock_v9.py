"""Regression check for mixed-clock window metadata; no annotation is edited."""
from pathlib import Path
import sys
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'script'))
from merge_user_labels_v9 import naive
def test_mixed_source_and_utc_anchors():
    sample = pd.Series(['2020-06-05 13:00:00', '2024-07-13 12:00:00+00:00'])
    parsed = sample.map(naive)
    assert parsed.notna().all()
    assert parsed.iloc[1] == pd.Timestamp('2024-07-13 12:00:00')
    assert parsed.iloc[0] == pd.Timestamp('2020-06-05 13:00:00')
