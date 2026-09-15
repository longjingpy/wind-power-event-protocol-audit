"""Refit the recorded v14 cohort and expose convergence and clustered inference."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.stats.multitest import multipletests
from scipy.stats import t

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "outputs/weather_adjusted_v14"
OUT = ROOT / "outputs/weather_diagnostics_v17"


def main():
    data = pd.read_csv(SRC / "analysis_population.csv.gz", dtype={"turbine": str})
    calendar = pd.read_csv(ROOT / "outputs/dynamic_events_v6/weather_mechanism/weather_mechanism_panel.csv.gz",
                           usecols=["turbine", "time", "hour", "month"], dtype={"turbine": str})
    data["time"] = pd.to_datetime(data.time, utc=True)
    calendar["time"] = pd.to_datetime(calendar.time, utc=True)
    data = data.merge(calendar, on=["turbine", "time"], how="left", validate="one_to_one")
    assert data[["hour", "month"]].notna().all().all()
    prior = json.loads((SRC / "adjusted_weather_association.json").read_text())
    model = smf.glm(prior["formula"], data=data, family=sm.families.Binomial()).fit(
        cov_type="cluster", cov_kwds={"groups": data.block})
    previous = pd.read_csv(SRC / "coefficients.csv").set_index("term")
    np.testing.assert_allclose(model.params.loc[previous.index], previous.estimate, atol=1e-8, rtol=1e-8)
    np.testing.assert_allclose(model.bse.loc[previous.index], previous.cluster_se, atol=1e-8, rtol=1e-8)
    degrees = int(data.block.nunique()) - 1
    stat = np.asarray(model.params / model.bse)
    pvalues = 2 * t.sf(np.abs(stat), degrees)
    table = pd.DataFrame({"term": model.params.index, "estimate": model.params.values,
                          "cluster_se": model.bse.values, "block_t_statistic": stat,
                          "block_t_df": degrees, "block_t_pvalue": pvalues,
                          "bh_qvalue_block_t": multipletests(pvalues, method="fdr_bh")[1],
                          "legacy_normal_pvalue": model.pvalues.values,
                          "legacy_normal_bh_qvalue": multipletests(model.pvalues.values, method="fdr_bh")[1]})
    diagnostics = {"converged": bool(model.converged), "iterations": model.fit_history.get("iteration"),
                   "observations": int(model.nobs), "blocks": int(data.block.nunique()),
                   "df_resid": float(model.df_resid), "deviance": float(model.deviance),
                   "pearson_chi2": float(model.pearson_chi2), "covariance_type": model.cov_type,
                   "coefficient_count": len(table), "block_t_df": degrees,
                   "max_coefficient_difference_v14": float(np.max(np.abs(model.params.loc[previous.index] - previous.estimate))),
                   "max_cluster_se_difference_v14": float(np.max(np.abs(model.bse.loc[previous.index] - previous.cluster_se))),
                   "fdr_family": "all coefficients in this single 4h model, including intercept and categorical indicators",
                   "scope": "coefficient-wise BH is not simultaneous correction of the separate ERA5/NOAA horizon risk contrasts",
                   "inference_update": "block-t p-values align coefficient tests with the existing blocks-1 t-based confidence intervals"}
    assert diagnostics["converged"]
    OUT.mkdir(parents=True, exist_ok=True)
    table.to_csv(OUT / "coefficients.csv", index=False)
    (OUT / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2))
    print(json.dumps(diagnostics, indent=2))
    print(table[table.term.eq("a")].to_string(index=False))


if __name__ == "__main__":
    main()
