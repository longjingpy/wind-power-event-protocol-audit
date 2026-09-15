from pathlib import Path
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "script"))
from confirm_detection_v16 import rule_scores, f1


def test_simple_rule_matches_rolling_reference():
    x = np.random.default_rng(13).normal(size=(20, 96)).astype(np.float32)
    frame = pd.DataFrame(x.T)
    for window in [2, 4, 8, 16]:
        reference = (frame.rolling(window).mean() - frame.shift(window).rolling(window).mean()).abs().fillna(0).to_numpy().T
        np.testing.assert_allclose(rule_scores(x, window), reference, atol=1e-12, rtol=1e-12)


def test_f1_counts_and_empty_predictions():
    np.testing.assert_allclose(f1(np.array([[2, 0, 0], [0, 0, 0], [2, 1, 1]])), [1., 0., 2 / 3])
