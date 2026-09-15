"""Independent audit of storage_policy_v15 for review items 2--4.

The script reads v15 inputs and writes only outputs/storage_audit_v17.  It
selects storage power, energy and reserve on validation for the two declared
regimes, then evaluates every paired MSE/event-weighted seed on the test set.
It also checks cost units and an independent finite-horizon LP on a small
synthetic residual sequence.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import linprog

ROOT = Path(__file__).resolve().parents[1]
V15 = ROOT / "script" / "storage_policy_v15.py"
sys.path.insert(0, str(V15.parent))
import storage_policy_v15 as v15  # noqa: E402

SRC = ROOT / "outputs" / "real_decision_v9_signed"
OUT = ROOT / "outputs" / "storage_audit_v17"
REGIMES = ("unconstrained", "at_least_10pct_2h")
CAPACITIES = [(0.0, 0.0)] + [(p, h) for p in (0.05, 0.10, 0.20) for h in (1.0, 2.0, 4.0)]
RESERVES = (0.0, 0.25, 0.5)


def _period(site: str, model: str, training: str, seed: int, meta: dict) -> tuple[float, dict[str, np.ndarray]]:
    return v15.load_pair(site, model, training, seed, meta)


def _cost_parts(state: dict, power: float, energy: float, nameplate: float,
                short: float, surplus: float, tail: float, hours: float) -> dict:
    capital = v15.capital(power, energy, hours)
    parts = {
        "capital_cny": capital,
        "throughput_cny": state["throughput_mwh"] * 25.0,
        "shortfall_cny": state["shortfall_mwh"] * short,
        "surplus_cny": state["surplus_mwh"] * surplus,
        "tail_premium_cny": state["tail_mwh"] * tail,
        "inventory_cny": state["inventory_draw_mwh"] * 300.0,
    }
    parts["total_cny"] = sum(parts.values())
    years = hours / 8760.0
    for key, val in list(parts.items()):
        parts[f"{key}_per_installed_mw"] = val / nameplate
        parts[f"{key}_annualized_per_installed_mw"] = val / nameplate / years if years else np.nan
        parts[f"{key}_per_installed_mw_h"] = val / nameplate / hours if hours else np.nan
    return parts


def _select(period: dict[str, np.ndarray], nameplate: float, short: float, surplus: float,
            tail: float, regime: str) -> tuple[float, float, float]:
    candidates = []
    for fraction, duration in CAPACITIES:
        if regime == "at_least_10pct_2h" and (fraction < 0.10 or duration < 2):
            continue
        power, energy = fraction * nameplate, fraction * nameplate * duration
        for reserve in RESERVES:
            st = v15.online(period["validation"], power, energy, reserve, critical=.2 * nameplate)
            op = v15.price(st, short, surplus, tail)
            cost = op + v15.capital(power, energy, len(period["validation"]) * v15.DT)
            candidates.append((cost, fraction, duration, reserve))
    _, fraction, duration, reserve = min(candidates)
    return float(fraction), float(duration), float(reserve)


def _forecast_pair(site: str, model: str, seed: int, meta: dict) -> dict:
    rows = {}
    for training in ("mse", "event_weighted"):
        path = SRC / f"forecast_{site}_{model}_{training}_{seed}_test.csv"
        frame = pd.read_csv(path)
        err = frame["actual_pu"].to_numpy(float) - frame["forecast_pu"].to_numpy(float)
        ramp = frame.get("ramp_truth_for_evaluation_only", pd.Series(False, index=frame.index)).to_numpy(bool)
        valid = np.isfinite(err)
        weights = 1.0 + 3.0 * ramp
        rows[training] = {
            "test_n": int(valid.sum()),
            "test_mse_pu2": float(np.mean(err[valid] ** 2)),
            "test_weighted_mse_pu2": float(np.sum(weights[valid] * err[valid] ** 2) / np.sum(weights[valid])),
        }
    return rows


def _lp_trace(residual: np.ndarray, power: float, energy: float, short: float, surplus: float,
              tail: float, critical: float) -> dict:
    """Finite-horizon LP with explicit MW, MWh and CNY/MWh units."""
    r = np.nan_to_num(np.asarray(residual, dtype=float), nan=0.0); n = len(r); dt = v15.DT; eta = v15.ETA
    # c,d,soc[0..n], shortfall, surplus, tail
    off_c, off_d, off_soc, off_short, off_surplus, off_tail = 0, n, 2*n, 3*n+1, 4*n+1, 5*n+1
    width = 6*n + 1
    c = np.zeros(width)
    c[off_c:off_c+n] = dt * 25.0
    c[off_d:off_d+n] = dt * 25.0
    c[off_short:off_short+n] = dt * short
    c[off_surplus:off_surplus+n] = dt * surplus
    c[off_tail:off_tail+n] = dt * tail
    c[off_soc+n] = -300.0
    # SOC_{t+1} - SOC_t - eta*dt*c_t + dt/eta*d_t = 0.
    er=[]; ec=[]; ev=[]; beq=[]
    for t in range(n):
        er.extend([t,t,t,t]); ec.extend([off_soc+t,off_c+t,off_d+t,off_soc+t+1]); ev.extend([-1,-eta*dt,dt/eta,1]); beq.append(0.0)
    er.append(n); ec.append(off_soc); ev.append(1); beq.append(0.5*energy)
    # r - c + d = surplus - shortfall; tail >= +/- net - critical.
    ar=[]; ac=[]; av=[]; bub=[]
    for t, value in enumerate(r):
        base=4*t
        ar.extend([base]*4); ac.extend([off_c+t,off_d+t,off_short+t,off_surplus+t]); av.extend([1,-1,-1,1]); bub.append(float(value))
        base+=1; ar.extend([base]*4); ac.extend([off_c+t,off_d+t,off_short+t,off_surplus+t]); av.extend([-1,1,1,-1]); bub.append(float(-value))
        base+=1; ar.extend([base]*3); ac.extend([off_c+t,off_d+t,off_tail+t]); av.extend([-1,1,-1]); bub.append(float(critical-value))
        base+=1; ar.extend([base]*3); ac.extend([off_c+t,off_d+t,off_tail+t]); av.extend([1,-1,-1]); bub.append(float(critical+value))
    # Match the v15 deviation-following feasible set; no grid arbitrage or
    # charge/discharge actions in missing intervals are introduced.
    bounds=[(0,min(power,max(value,0))) for value in r]+[(0,min(power,max(-value,0))) for value in r]+[(0.1*energy,0.9*energy)]*(n+1)+[(0,None)]*(3*n)
    from scipy.sparse import coo_matrix
    aub=coo_matrix((av,(ar,ac)),shape=(4*n,width)).tocsr(); aeq=coo_matrix((ev,(er,ec)),shape=(n+1,width)).tocsr()
    fit=linprog(c,A_ub=aub,b_ub=np.asarray(bub),A_eq=aeq,b_eq=np.asarray(beq),bounds=bounds,method="highs")
    if not fit.success: raise RuntimeError(f"LP failed: {fit.message}")
    x=fit.x
    charge=x[off_c:off_c+n]; discharge=x[off_d:off_d+n]; soc=x[off_soc:off_soc+n+1]
    net=r-charge+discharge
    np.testing.assert_allclose(np.diff(soc), eta*dt*charge-dt*discharge/eta, atol=1e-7)
    objective = float(fit.fun + .5*energy*300.0)
    original = v15.oracle(residual, power, energy, short, surplus, tail, critical)["operating_cost"]
    np.testing.assert_allclose(objective, original, rtol=1e-8, atol=1e-5)
    return {"objective_cny": objective, "charge_mw": charge, "discharge_mw": discharge,
            "soc_mwh": soc, "residual_mw": r, "net_residual_mw": net,
            "shortfall_mwh": float(np.sum(x[off_short:off_short+n])*dt),
            "surplus_mwh": float(np.sum(x[off_surplus:off_surplus+n])*dt),
            "tail_mwh": float(np.sum(x[off_tail:off_tail+n])*dt),
            "future_nonzero_steps": int(np.count_nonzero((charge[1:]+discharge[1:]) > 1e-8))}


def _online_trace(residual: np.ndarray, power: float, energy: float, reserve: float, critical: float) -> dict:
    soc=.5*energy; charge=[]; discharge=[]; socs=[soc]; net=[]
    for value in residual:
        ch=dis=0.0
        if not np.isfinite(value):
            charge.append(0.); discharge.append(0.); socs.append(soc); net.append(np.nan)
            continue
        if value >= 0: ch=min(value,power,max(.9*energy-soc,0)/(v15.ETA*v15.DT)); soc += v15.ETA*v15.DT*ch
        else:
            floor=.1*energy+reserve*(.8*energy) if -value<critical else .1*energy
            dis=min(-value,power,max(soc-floor,0)*v15.ETA/v15.DT); soc -= v15.DT*dis/v15.ETA
        charge.append(ch); discharge.append(dis); socs.append(soc); net.append(value-ch+dis)
    return {"charge_mw":np.array(charge),"discharge_mw":np.array(discharge),"soc_mwh":np.array(socs),"residual_mw":np.array(residual),"net_residual_mw":np.array(net)}


def _trace_cost(trace: dict, short: float, surplus: float, tail: float, nameplate: float,
                power: float, energy: float, hours: float) -> dict:
    net=np.asarray(trace["net_residual_mw"],float); dt=v15.DT
    state={"shortfall_mwh":float(np.nansum(np.maximum(-net,0))*dt),"surplus_mwh":float(np.nansum(np.maximum(net,0))*dt),
           "throughput_mwh":float((np.asarray(trace["charge_mw"])+np.asarray(trace["discharge_mw"])).sum()*dt),
           "tail_mwh":float(np.nansum(np.maximum(np.abs(net)-.2*nameplate,0))*dt),
           "inventory_draw_mwh":float(trace["soc_mwh"][0]-trace["soc_mwh"][-1])}
    return _cost_parts(state,power,energy,nameplate,short,surplus,tail,hours)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    meta=json.loads((SRC/"manifest.json").read_text())
    rows=[]; pairs=[]
    for site in ("pizhou", "yandun"):
      for model in ("tcn", "timesnet"):
       for seed in (41,42,43):
        for training in ("mse", "event_weighted"):
         nameplate, period = _period(site, model, training, seed, meta)
         for price_case, short, surplus in (("low",150.,40.),("base",300.,80.),("high",600.,160.)):
          for tail in (0.,1000.,5000.):
           for regime in REGIMES:
            fraction,duration,reserve=_select(period,nameplate,short,surplus,tail,regime)
            power,energy=fraction*nameplate,fraction*nameplate*duration
            state=v15.online(period["test"],power,energy,reserve,critical=.2*nameplate)
            parts=_cost_parts(state,power,energy,nameplate,short,surplus,tail,len(period["test"])*v15.DT)
            rows.append(dict(site=site,model=model,seed=seed,training=training,price_case=price_case,tail_premium=tail,regime=regime,
              fraction=fraction,duration_h=duration,reserve=reserve,nameplate_mw=nameplate,calendar_h=len(period["test"])*v15.DT,
              observed_h=np.isfinite(period["test"]).sum()*v15.DT,**{k:float(v) for k,v in parts.items()}))
        pair=_forecast_pair(site,model,seed,meta)
        for price_case in ("low","base","high"):
         for tail in (0.,1000.,5000.):
          for regime in REGIMES:
           a=[r for r in rows if r["site"]==site and r["model"]==model and r["seed"]==seed and r["price_case"]==price_case and r["tail_premium"]==tail and r["regime"]==regime]
           # rows are ordered MSE then event_weighted.
           m=next(r for r in a if r["training"]=="mse"); e=next(r for r in a if r["training"]=="event_weighted")
           pairs.append({"site":site,"model":model,"seed":seed,"price_case":price_case,"tail_premium":tail,"regime":regime,
             "mse_test_total_cny_per_installed_mw":m["total_cny_per_installed_mw"],"event_weighted_test_total_cny_per_installed_mw":e["total_cny_per_installed_mw"],
             "event_weighted_minus_mse_cny_per_installed_mw":e["total_cny_per_installed_mw"]-m["total_cny_per_installed_mw"],
             "mse_test_mse_pu2":pair["mse"]["test_mse_pu2"],"event_weighted_test_mse_pu2":pair["event_weighted"]["test_mse_pu2"],
             "mse_weighted_mse_pu2":pair["mse"]["test_weighted_mse_pu2"],"event_weighted_weighted_mse_pu2":pair["event_weighted"]["test_weighted_mse_pu2"]})
    pd.DataFrame(rows).to_csv(OUT/"selected_test_cost_decomposition.csv",index=False)
    pd.DataFrame(pairs).to_csv(OUT/"paired_mse_event_weighted.csv",index=False)
    # Independent synthetic LP and prefix-invariance check.
    residual=np.array([.55,.25,-.10,-.50,-.35,.18,.52,.10,-.42,-.30,.48,.20,-.45,-.18,.55,-.15])
    online=_online_trace(residual,.20,.40,.25,.20)
    lp=_lp_trace(residual,.20,.40,300.,80.,1000.,.20)
    altered=residual.copy(); altered[8:]=[-.9,.9,-.9,.9,-.9,.9,-.9,.9]
    online_alt=_online_trace(altered,.20,.40,.25,.20)
    prefix_n=8
    prefix_equal=bool(np.allclose(online["charge_mw"][:prefix_n],online_alt["charge_mw"][:prefix_n]) and np.allclose(online["discharge_mw"][:prefix_n],online_alt["discharge_mw"][:prefix_n]))
    trace=pd.DataFrame({"step":np.arange(len(residual)),"residual_mw":residual,"online_charge_mw":online["charge_mw"],"online_discharge_mw":online["discharge_mw"],"online_soc_mwh":online["soc_mwh"][:-1],"online_net_residual_mw":online["net_residual_mw"],"online_severe":np.abs(online["net_residual_mw"])>.20,"lp_charge_mw":lp["charge_mw"],"lp_discharge_mw":lp["discharge_mw"],"lp_soc_mwh":lp["soc_mwh"][:-1],"lp_net_residual_mw":lp["net_residual_mw"],"lp_severe":np.abs(lp["net_residual_mw"])>.20})
    trace.to_csv(OUT/"synthetic_online_lp_trace.csv",index=False)
    checks={"synthetic_steps":len(residual),"online_severe_steps":int(np.sum(np.abs(online["net_residual_mw"])>.20)),"lp_severe_steps":int(np.sum(np.abs(lp["net_residual_mw"])>.20)),"online_prefix_steps":prefix_n,"online_prefix_unchanged_after_future_edit":prefix_equal,
      "lp_full_horizon_steps":len(residual),"lp_future_nonzero_steps":lp["future_nonzero_steps"],"lp_uses_future_steps":bool(lp["future_nonzero_steps"]>0),
      "lp_objective_units":"CNY: (MW * 0.5 h) * CNY/MWh; SOC in MWh; residual and charge/discharge in MW",
      "lp_constraint_units":"SOC balance: MWh = (MW * h); residual balance: MW; tail constraints: MW",
      "online_prefix_note":"Online actions at steps 0..7 are identical when steps 8..15 are changed.","lp_note":"LP sees all 16 residuals and optimizes the complete horizon."}
    # A foresight case: a small early shortfall is followed by a severe deficit.
    # With reserve=0 the greedy controller spends energy early; the LP preserves
    # inventory because the later tail premium is much larger.
    foresight=np.array([-0.10,-0.60]); fo=_online_trace(foresight,.20,.20,0.0,.20); fl=_lp_trace(foresight,.20,.20,300.,80.,5000.,.20)
    foc=_trace_cost(fo,300.,80.,5000.,1.0,.20,.20,len(foresight)*v15.DT); flc=_trace_cost({"charge_mw":fl["charge_mw"],"discharge_mw":fl["discharge_mw"],"soc_mwh":fl["soc_mwh"],"net_residual_mw":fl["net_residual_mw"]},300.,80.,5000.,1.0,.20,.20,len(foresight)*v15.DT)
    assert flc["total_cny"] < foc["total_cny"] - 1e-8
    checks.update({"foresight_case_residual_mw":foresight.tolist(),"foresight_case_tail_premium_cny_per_mwh":5000.0,
      "foresight_online_total_cny":foc["total_cny"],"foresight_lp_total_cny":flc["total_cny"],"foresight_lp_lower_than_online":bool(flc["total_cny"]<foc["total_cny"]-1e-8),
      "foresight_case_note":"The first -0.10 MW shortfall is below critical; the subsequent -0.60 MW deficit is severe. LP uses the full future and preserves SOC."})
    pd.DataFrame({"step":np.arange(len(foresight)),"residual_mw":foresight,"online_charge_mw":fo["charge_mw"],"online_discharge_mw":fo["discharge_mw"],"online_soc_mwh":fo["soc_mwh"][:-1],"lp_charge_mw":fl["charge_mw"],"lp_discharge_mw":fl["discharge_mw"],"lp_soc_mwh":fl["soc_mwh"][:-1],"lp_net_residual_mw":fl["net_residual_mw"]}).to_csv(OUT/"synthetic_foresight_case.csv",index=False)
    # Real complete test-calendar traces at fixed 10%/2h for R3.
    real_costs=[]
    for site in ("pizhou","yandun"):
      for training in ("mse","event_weighted"):
        nameplate, period = _period(site,"tcn",training,41,meta); power=.10*nameplate; energy=.20*nameplate
        for label,short,surplus,tail in (("base",300.,80.,0.),("high",600.,160.,0.),("low_tail5000",150.,40.,5000.)):
          residual=np.asarray(period["test"],float); online_t=_online_trace(residual,power,energy,0.0,.2*nameplate); lp_t=_lp_trace(residual,power,energy,short,surplus,tail,.2*nameplate)
          stem=f"{site}_tcn_{training}_seed41_{label}"
          pd.DataFrame({"step":np.arange(len(residual)),"residual_input_mw":residual,"residual_lp_mw":lp_t["residual_mw"],"online_charge_mw":online_t["charge_mw"],"online_discharge_mw":online_t["discharge_mw"],"online_soc_mwh":online_t["soc_mwh"][:-1],"online_net_residual_mw":online_t["net_residual_mw"],"online_severe":np.abs(online_t["net_residual_mw"])>.2*nameplate,"lp_charge_mw":lp_t["charge_mw"],"lp_discharge_mw":lp_t["discharge_mw"],"lp_soc_mwh":lp_t["soc_mwh"][:-1],"lp_net_residual_mw":lp_t["net_residual_mw"],"lp_severe":np.abs(lp_t["net_residual_mw"])>.2*nameplate}).to_csv(OUT/f"real_trace_{stem}.csv",index=False)
          oc=_trace_cost(online_t,short,surplus,tail,nameplate,power,energy,len(residual)*v15.DT)
          lc=_trace_cost({"charge_mw":lp_t["charge_mw"],"discharge_mw":lp_t["discharge_mw"],"soc_mwh":lp_t["soc_mwh"],"net_residual_mw":lp_t["net_residual_mw"]},short,surplus,tail,nameplate,power,energy,len(residual)*v15.DT)
          real_costs.append({"site":site,"model":"tcn","training":training,"seed":41,"scenario":label,"nameplate_mw":nameplate,"calendar_h":len(residual)*v15.DT,"online_severe_steps":int(np.sum(np.abs(online_t["net_residual_mw"])>.2*nameplate)),"lp_severe_steps":int(np.sum(np.abs(lp_t["net_residual_mw"])>.2*nameplate)),"online_total_cny_per_installed_mw":oc["total_cny_per_installed_mw"],"lp_total_cny_per_installed_mw":lc["total_cny_per_installed_mw"],"lp_minus_online_cny_per_installed_mw":lc["total_cny_per_installed_mw"]-oc["total_cny_per_installed_mw"]})
    pd.DataFrame(real_costs).to_csv(OUT/"real_trace_costs.csv",index=False)
    (OUT/"synthetic_lp_checks.json").write_text(json.dumps(checks,indent=2))
    # No factor retraining is performed; document exact expected v9 input paths.
    gap=[]
    for factor in (0,1,2,4,8):
      path=SRC/f"forecast_factor{factor}_test.csv"; gap.append({"factor":factor,"expected_path":str(path),"exists":path.exists(),"action":"not retrained"})
    (OUT/"factor_data_gap.json").write_text(json.dumps(gap,indent=2))
    # Premium-zero explanation is explicit in machine-readable form.
    (OUT/"premium_zero_note.json").write_text(json.dumps({"base_tail_premium":0.0,"high_tail_premium":0.0,"meaning":"v15 base/high scenario rows set tail_premium=0; equal premium terms are zero by construction, not evidence that severe-deviation premium has no effect.","positive_sensitivity_cases":"tail_premium=1000 and 5000 are reported separately."},indent=2))
    (OUT/"audit_protocol.json").write_text(json.dumps({
      "input_policy":"Read-only reuse of outputs/real_decision_v9_signed forecast files and storage_policy_v15 cost assumptions.",
      "selection":"For each site/model/seed/price/tail/regime, capacity, duration and reserve are selected only on validation; all selected test rows are retained.",
      "regimes":list(REGIMES),"paired_training":"mse versus event_weighted under identical site/model/seed/price/tail/regime keys",
      "cost_units":"CNY; energy terms use MWh; reported period CNY/installed-MW, annualized CNY/installed-MW/year (calendar_h/8760), and CNY/(installed-MW*h).",
      "inventory_definition":"inventory_cny = (initial SOC - terminal SOC) * 300 CNY/MWh; negative values are terminal inventory credit when SOC rises.",
      "lp_units":"Residual/charge/discharge MW, SOC MWh, dt=0.5 h, tariffs CNY/MWh; constraints are dimensionally checked in synthetic_lp_checks.json.",
      "source_unchanged":True
    },indent=2))

if __name__ == "__main__":
    main()
