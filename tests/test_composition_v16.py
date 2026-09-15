from pathlib import Path
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "script"))
from matched_composition_v16 import prewindow


def test_prewindow_uses_only_four_earlier_bins():
    stamp = pd.date_range("2024-01-01", periods=8, freq="30min", tz="UTC")
    source = np.arange(8, dtype=float)
    a, _ = prewindow(stamp, source, 1)
    source[4:] = 1000
    b, _ = prewindow(stamp, source, 1)
    assert a.iloc[4] == b.iloc[4] == 1.5
    assert a.iloc[:4].isna().all()


def test_missing_bin_and_duplicate_clock_are_excluded():
    stamp = pd.date_range("2024-01-01", periods=8, freq="30min", tz="UTC")
    index = stamp.insert(2, stamp[2])
    result, duplicates = prewindow(index, np.ones(len(index)), 1)
    assert duplicates == 2
    assert result.iloc[4:7].isna().all()
