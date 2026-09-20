from pathlib import Path
import sys
import numpy as np
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'script'))
from forecast_penalty_v24 import point_fee,tolerance_action,CENTERS


def test_native_point_rule_has_no_energy_multiplier_or_day_ahead_allowance():
    np.testing.assert_allclose(point_fee([0,.03,.031],[0,0,0],.03,10),[0,0,4])
    np.testing.assert_allclose(point_fee([.14],[0],.13,100),[40])


def test_invalid_meter_is_not_a_free_pass():
    with pytest.raises(ValueError):point_fee([np.nan],[0],.03)


def test_bimodal_distribution_requires_a_loss_matched_action():
    p=np.zeros((1,121));p[0,20]=.5;p[0,80]=.5
    mean=(p@CENTERS).item();q=tolerance_action(p,.03)[0]
    assert abs(mean-.5)<1e-10
    assert min(abs(q-.2),abs(q-.8))<.03
    assert point_fee([.2,.8],[q,q],.03).sum()<point_fee([.2,.8],[mean,mean],.03).sum()
