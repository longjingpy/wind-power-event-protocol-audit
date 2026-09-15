from pathlib import Path
import sys
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "script"))
from conditional_agreement_v17 import pair_metric


def test_one_constant_partition_is_zero_not_missing():
    nmi, ari, status = pair_metric(np.array([0, 0, 0, 0]), np.array([0, 1, 0, 1]))
    assert nmi == 0 and ari == 0 and status == "VALID_ONE_SIDE_CONSTANT"


def test_both_constant_partitions_are_flagged():
    nmi, ari, status = pair_metric(np.array([0, 0]), np.array([1, 1]))
    assert np.isnan(nmi) and np.isnan(ari) and status == "DEGENERATE_BOTH_CONSTANT"
