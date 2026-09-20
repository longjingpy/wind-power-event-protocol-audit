"""Freeze the loss/lead-specific pipeline from validation records only."""
from pathlib import Path
import json
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'outputs/protocol_benchmark_v24/economics/jiangsu_native'
tables=[]
for weather,folder in [('none',BASE),('jma',BASE/'jma'),('jma_gfs',BASE/'jma_gfs')]:
    d=pd.read_csv(folder/'selection.csv');d['weather']=weather;tables.append(d)
d=pd.concat(tables,ignore_index=True);selected=[]
for h,g in d.groupby('horizon_steps'):
    for role,subset in [('morphology_pipeline',g[g.representation.ne('scalar')]),('scalar_baseline',g[g.representation.eq('scalar')])]:
        row=subset.sort_values(['validation_failed_points','validation_nmae','blend']).iloc[0].to_dict()
        selected.append({'role':role,**row})
file=BASE/'pipeline_selection_before_weather_test.json'
if file.exists():raise RuntimeError('Selection already frozen')
file.write_text(json.dumps({'status':'FROZEN_FROM_VALIDATION_ONLY','selected':selected,
    'evidence_identity':'New weather variants on the existing Pizhou chronology; earlier SCADA-only test already examined. Not a newly acquired independent farm.'},indent=2))
print(pd.DataFrame(selected).to_string(index=False))
