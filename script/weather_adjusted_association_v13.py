"""Adjusted observational weather association with pre-treatment covariates."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

ROOT=Path(__file__).resolve().parents[1]; SRC=ROOT/'outputs/dynamic_events_v6/weather_mechanism'; OUT=ROOT/'outputs/weather_adjusted_v13'; OUT.mkdir(parents=True,exist_ok=True)
def main():
    d=pd.read_csv(SRC/'weather_mechanism_panel.csv.gz'); d['time']=pd.to_datetime(d.time,utc=True); d['block']=((d.time-pd.Timestamp('1970-01-05',tz='UTC')).dt.total_seconds()//(86400*7)).astype(int)
    cols=['outcome_4h','treatment','pre_power','pre_speed','pre_power_change','hour','month','turbine','block']; d=d[cols].dropna().copy(); d['treatment']=d.treatment.astype(int)
    formula='outcome_4h ~ treatment + pre_power + pre_speed + pre_power_change + C(hour) + C(month)'
    fit=smf.glm(formula,data=d,family=sm.families.Binomial()).fit(cov_type='cluster',cov_kwds={'groups':d.block})
    x0=d.copy(); x1=d.copy(); x0['treatment']=0; x1['treatment']=1
    rd=float(np.mean(fit.predict(x1)-fit.predict(x0))); coef=float(fit.params['treatment']); se=float(fit.bse['treatment'])
    result={'rows':len(d),'blocks':int(d.block.nunique()),'formula':formula,'treatment_log_odds':coef,'cluster_se':se,'standardized_risk_difference':rd,'odds_ratio':float(np.exp(coef)),'pre_treatment_covariates':['pre_power','pre_speed','pre_power_change','hour','month'],'status':'ASSOCIATION_ADJUSTED_OBSERVATIONAL'}
    (OUT/'adjusted_weather_association.json').write_text(json.dumps(result,indent=2)); pd.DataFrame({'term':fit.params.index,'estimate':fit.params.values,'cluster_se':fit.bse.values,'pvalue':fit.pvalues.values}).to_csv(OUT/'glm_coefficients.csv',index=False); print(json.dumps(result,indent=2))
if __name__=='__main__':main()
