"""Weather associations with exact pre-exposure covariates and a numeric event outcome."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.stats.multitest import multipletests
from patsy import build_design_matrices
from scipy.special import expit
from scipy.stats import t

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/weather_adjusted_v14"
SOURCE = ROOT / "outputs/dynamic_events_v6/weather_mechanism/weather_mechanism_panel.csv.gz"

def main():
    d = pd.read_csv(SOURCE, dtype={"turbine": str})
    d["time"] = pd.to_datetime(d.time, utc=True)
    assert not d.duplicated(["turbine", "time"]).any()
    earlier = d[["turbine", "time", "power", "speed100_ref", "u100_ref", "v100_ref"]].copy()
    earlier["covariate_time"] = earlier.time
    earlier["time"] += pd.Timedelta(hours=4)
    earlier = earlier.rename(columns={"power": "pre_power4", "speed100_ref": "pre_speed4",
                                      "u100_ref": "pre_u4", "v100_ref": "pre_v4"})
    d = d.merge(earlier, on=["turbine", "time"], how="left", validate="one_to_one")
    old = pd.read_csv(SOURCE, usecols=["turbine", "time", "power"], dtype={"turbine": str})
    old["time"] = pd.to_datetime(old.time, utc=True) + pd.Timedelta(hours=5)
    d = d.merge(old.rename(columns={"power": "pre_power5"}), on=["turbine", "time"], how="left", validate="one_to_one")
    d["pre_change4"] = (d.pre_power4-d.pre_power5)/1000
    d["pre_power4"] /= 1000
    angle = np.arctan2(d.pre_v4, d.pre_u4)
    d["pre_sin"] = np.sin(angle)
    d["pre_cos"] = np.cos(angle)
    d["a"] = d.treatment.astype(int)
    d["y"] = d.outcome_4h.astype(int)
    assert set(d.y.unique()).issubset({0,1})
    covs = ["pre_power4", "pre_speed4", "pre_change4", "pre_sin", "pre_cos"]
    d = d.dropna(subset=covs+["covariate_time"]).copy()
    assert (d.covariate_time < d.time-pd.Timedelta(hours=3)).all()
    d["block"] = ((d.time-pd.Timestamp("1970-01-05",tz="UTC")).dt.total_seconds()//(86400*7)).astype(int)
    formula = "y ~ a + pre_power4 + pre_speed4 + pre_change4 + pre_sin + pre_cos + C(hour) + C(month) + C(turbine)"
    model = smf.glm(formula, data=d, family=sm.families.Binomial()).fit(cov_type="cluster", cov_kwds={"groups":d.block})
    assert np.array_equal(model.model.endog, d.y.to_numpy())
    zero, one = d.assign(a=0), d.assign(a=1)
    x0 = np.asarray(build_design_matrices([model.model.data.design_info],zero)[0])
    x1 = np.asarray(build_design_matrices([model.model.data.design_info],one)[0])
    p0,p1 = expit(x0@model.params),expit(x1@model.params)
    gradient = np.mean(x1*(p1*(1-p1))[:,None]-x0*(p0*(1-p0))[:,None],axis=0)
    rd = float(np.mean(p1-p0))
    se = float(np.sqrt(max(gradient@model.cov_params()@gradient,0)))
    cutoff = float(t.ppf(.975,d.block.nunique()-1))
    raw = float(d.loc[d.a.eq(1),"y"].mean()-d.loc[d.a.eq(0),"y"].mean())
    result = {"rows":len(d),"blocks":int(d.block.nunique()),"treated":int(d.a.sum()),
              "control":int((1-d.a).sum()),"unadjusted_same_population":raw,
              "standardized_risk_difference":rd,"standardized_rd_ci95":[rd-cutoff*se,rd+cutoff*se],
              "odds_ratio":float(np.exp(model.params.a)),
              "odds_ratio_ci95":[float(np.exp(model.params.a-cutoff*model.bse.a)),
                                  float(np.exp(model.params.a+cutoff*model.bse.a))],
              "formula":formula,"outcome":"integer 1 means an event start in the following 4 h",
              "covariate_time":"exact t-4h; previous power contrast t-4h minus t-5h",
              "interval":"cluster covariance delta method with t critical value, blocks-1 df",
              "status":"OBSERVATIONAL_ASSOCIATION"}
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"adjusted_weather_association.json").write_text(json.dumps(result,indent=2))
    coeff=pd.DataFrame({"term":model.params.index,"estimate":model.params.values,
                        "cluster_se":model.bse.values,"pvalue":model.pvalues.values})
    coeff["bh_qvalue"]=multipletests(coeff.pvalue,method="fdr_bh")[1]
    coeff.to_csv(OUT/"coefficients.csv",index=False)
    d[["turbine","time","covariate_time","block","a","y"]+covs].to_csv(OUT/"analysis_population.csv.gz",index=False)
    print(json.dumps(result,indent=2))
if __name__=="__main__":
    main()
