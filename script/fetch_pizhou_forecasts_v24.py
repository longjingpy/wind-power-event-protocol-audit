"""Fixed-24h-lead forecasts, not reanalysis or zero-lead stitched weather.

Open-Meteo Previous Runs documentation defines previous_day1 as the forecast
24h before valid time. All target leads here are <=4h, leaving a >=20h issue
margin. These fixed-lead fields need not come from one common model cycle.
Coordinates are the archived administrative proxy, not surveyed turbine sites.
"""
from concurrent.futures import ThreadPoolExecutor
import json,os
import numpy as np
import pandas as pd
from prepare_weather_v18 import download,ROOT
DATA=ROOT/'data/weather_v24/pizhou_fixed_lead'
OUT=ROOT/'outputs/protocol_benchmark_v24/economics/jiangsu_native'


def one(job):
    model,level,a,b=job
    variables=[f'wind_speed_{level}m_previous_day1',f'wind_direction_{level}m_previous_day1',
               'temperature_2m_previous_day1','pressure_msl_previous_day1']
    url=('https://previous-runs-api.open-meteo.com/v1/forecast?latitude=34.3403&longitude=118.0068'
         f'&start_date={a:%Y-%m-%d}&end_date={b:%Y-%m-%d}&models={model}&hourly='+','.join(variables)+
         '&wind_speed_unit=ms&timezone=UTC&elevation=nan&cell_selection=nearest')
    file=DATA/f'{model}_{a:%Y%m}.json';record=download(url,file)
    j=json.loads(file.read_text());d=pd.DataFrame(j['hourly']);d.index=pd.to_datetime(d.pop('time'),utc=True)
    d=d.apply(pd.to_numeric,errors='coerce')
    speed=d[variables[0]];theta=np.deg2rad(d[variables[1]])
    frame=pd.DataFrame({f'{model}_u':-speed*np.sin(theta),f'{model}_v':-speed*np.cos(theta),
        f'{model}_temperature':d[variables[2]],f'{model}_pressure':d[variables[3]]},index=d.index)
    record.update(model=model,height_m=level,returned_latitude=j['latitude'],returned_longitude=j['longitude'],
                  valid_wind_hours=int(speed.notna().sum()))
    return record,frame


def main():
    DATA.mkdir(parents=True,exist_ok=True);os.environ['WPF_DOWNLOAD_TRANSPORT']='windows-curl'
    months=pd.date_range('2023-09-01','2025-02-01',freq='MS');jobs=[]
    for model,level in [('jma_gsm',10),('gfs_global',100)]:
        for a in months:
            end=min(a+pd.offsets.MonthEnd(1),pd.Timestamp('2025-02-02'))
            jobs.append((model,level,a,end))
    records=[];parts={'jma_gsm':[],'gfs_global':[]}
    with ThreadPoolExecutor(max_workers=2) as pool:
        for record,frame in pool.map(one,jobs):
            records.append(record);parts[record['model']].append(frame)
            print(record['model'],record['path'],record['valid_wind_hours'],flush=True)
    result=pd.concat([pd.concat(v).sort_index() for v in parts.values()],axis=1)
    if not result.index.is_unique:raise ValueError('Repeated forecast validity time')
    result.to_parquet(DATA/'fixed_lead_hourly.parquet')
    report={'status':'ACQUIRED_WITH_MODEL_SPECIFIC_COVERAGE','fixed_lead_hours':24,
        'coordinates':[34.3403,118.0068],'location_quality':'administrative proxy from existing metadata',
        'documentation':'https://open-meteo.com/en/docs/previous-runs-api',
        'feature_rule':'valid_time - 24h <= issue_time; maximum task lead 4h',
        'not_reanalysis':True,'interpolation':'u/v components; no interpolation across missing forecast hours',
        'coverage':{c:int(result[c].notna().sum()) for c in result},'downloads':records}
    (OUT/'forecast_source.json').write_text(json.dumps(report,indent=2))
    print({k:v for k,v in report.items() if k!='downloads'})


if __name__=='__main__':main()
