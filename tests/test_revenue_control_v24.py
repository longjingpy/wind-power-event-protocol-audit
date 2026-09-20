from pathlib import Path
import sys
import numpy as np
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from wind_events.economics import Battery
from wind_events.revenue_control import complete_revenue,plan_storage,deliver_storage


def test_forward_sales_remove_spurious_schedule_profit():
    np.testing.assert_allclose(complete_revenue([10,10],[0,20],[50,50],[50,50],[50,50]),[250,250])


def test_fixed_contract_difference_equals_metered_price_value():
    p=np.array([100,-30]);base=complete_revenue([10,10],[15,15],[50,50],p,p)
    changed=complete_revenue([12,8],[15,15],[50,50],p,p)
    np.testing.assert_allclose(changed-base,np.array([2,-2])*p*.5)


def test_forecast_plan_closes_soc_and_avoids_simultaneous_cycling():
    b=Battery(2,4);p=plan_storage([5]*8,[10,10,10,10,100,100,100,100],.4,b)
    assert p['charge'][:4].sum()>0 and p['discharge'][4:].sum()>0
    assert p['inventory'][-1]==pytest.approx(.4)
    assert np.max(np.minimum(p['charge'],p['discharge']))<1e-7


def test_negative_prices_allow_curtailment_without_fabricated_energy():
    p=plan_storage([5,5],[-100,50],0.,Battery(0,0))
    assert p['curtail'][0]==pytest.approx(5)
    assert p['curtail'][1]==pytest.approx(0)


def test_actual_wind_limits_charge_and_forces_terminal_inventory():
    b=Battery(2,4)
    r=deliver_storage(.2,2,0,0,.4,b,7)
    assert r['charge']==pytest.approx(.2)
    q=deliver_storage(48.3,0,0,0,.9,b,0)
    assert q['inventory']==pytest.approx(.4)
    assert q['delivered']<=48.3 and q['curtail']>0


def test_unavailable_future_observation_does_not_enter_plan():
    b=Battery(2,4);wind=[4.]*8;prices=[20.]*4+[80.]*4
    a=plan_storage(wind,prices,.4,b);unseen_actual=np.arange(8.)
    unseen_actual[:]=1000
    c=plan_storage(wind,prices,.4,b)
    np.testing.assert_array_equal(a['charge'],c['charge'])


def test_publication_time_blocks_late_reports_and_forecast_revisions():
    import pandas as pd
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'script'))
    from economic_value_v24 import published_price_features,issued_wind_features
    clock=pd.date_range('2020-01-01T02:00Z',periods=3,freq='30min')
    reports=pd.DataFrame({'startTime':['2020-01-01T00:00Z','2020-01-01T00:30Z'],
        'createdDateTime':['2020-01-01T00:55Z','2020-01-01T03:00Z'],
        'systemBuyPrice':[20,900],'netImbalanceVolume':[10,99]})
    before=published_price_features(clock,reports)
    reports.loc[1,'systemBuyPrice']=999999
    after=published_price_features(clock,reports)
    np.testing.assert_allclose(before.market_price_lag0,after.market_price_lag0)
    forecasts=pd.DataFrame({'publishTime':['2020-01-01T01:00Z','2020-01-01T04:00Z'],
        'startTime':['2020-01-01T03:00Z']*2,'generation':[1000,8000]})
    result=issued_wind_features(clock,forecasts)
    assert result.market_issued_wind_h1.iloc[0]==1.


def test_causal_shape_distances_ignore_later_power(tmp_path,monkeypatch):
    import pandas as pd
    import economic_value_v24 as ev
    monkeypatch.setattr(ev,'OUT',tmp_path)
    monkeypatch.setattr(ev,'B1',pd.Timestamp('2020-01-04',tz='UTC'))
    clock=pd.date_range('2020-01-01',periods=240,freq='30min',tz='UTC')
    f=pd.DataFrame({'power_mw':np.random.default_rng(41).uniform(1,40,len(clock))},index=clock)
    original=ev.ongoing_geometry(f,fit=True)
    changed=f.copy();changed.iloc[101:]*=10
    altered=ev.ongoing_geometry(changed,fit=False)
    np.testing.assert_allclose(original.iloc[:101],altered.iloc[:101],equal_nan=True)


def test_schedule_cannot_read_future_actual_or_execution_prices():
    import pandas as pd
    from trade_value_v24 import issue_schedule
    t=pd.DataFrame({'persistence':[12.,20.],'actual':[10.,25.],'price':[10.,100.],'forward':[20.,50.]})
    args=(np.array([14.,18.]),np.array([5.,-5.]),.5,0.,.025,20.)
    first=issue_schedule(t,*args)
    t[['actual','price','forward']]=99999
    np.testing.assert_array_equal(first,issue_schedule(t,*args))
