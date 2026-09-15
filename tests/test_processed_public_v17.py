from pathlib import Path
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "script"))
from prepare_processed_public_v17 import regular, make_frame, COLUMNS


def test_series_values_use_position_and_gaps_stay_missing():
    stamps = pd.to_datetime(["2024-01-01 00:00", "2024-01-01 01:00"], utc=True)
    values = pd.Series([1., 2.])
    result, valid, duplicates = regular(values, stamps, 30)
    np.testing.assert_allclose(result, [1., np.nan, 2.], equal_nan=True)
    assert valid.tolist() == [True, False, True]
    assert duplicates == 0


def test_public_frame_drops_direct_identifiers_and_dates():
    index = pd.date_range("2024-01-01 16:00", periods=10, freq="30min", tz="UTC").as_unit("us")
    frame = make_frame("WF01", "T001", index, np.arange(10.), np.ones(10, bool),
                       np.ones(10) * 5, np.ones(10, bool), 10., 30, index[0])
    assert frame.columns.tolist() == COLUMNS
    assert frame.time_index.tolist() == list(range(10))
    assert not any(pd.api.types.is_datetime64_any_dtype(dtype) for dtype in frame.dtypes)
    assert set(frame.split) == {"train", "validation", "test"}
