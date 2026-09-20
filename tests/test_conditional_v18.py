from pathlib import Path
import sys
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"script"))
from conditional_structure_v18 import conditional_scores, counts_for


def test_information_remaining_after_direction_is_explicit():
    a = np.tile([0, 1], 100)
    c = counts_for(a, a, np.repeat([0, 1], 100), 2, 2)
    mi, normalized, remaining = conditional_scores(c)
    np.testing.assert_allclose(mi, np.log(2))
    np.testing.assert_allclose(normalized, 1)
    np.testing.assert_allclose(remaining, 1)


def test_condition_determining_labels_leaves_zero_entropy():
    a = np.repeat([0, 1], 100)
    c = counts_for(a, a, a, 2, 2)
    mi, normalized, remaining = conditional_scores(c)
    assert mi[0] == 0 and np.isnan(normalized[0]) and remaining[0] == 0
