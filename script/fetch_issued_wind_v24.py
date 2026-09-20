"""Archive actual publication vintages of GB wind-generation forecasts.

Elexon WINDFOR dataset endpoint preserves publishTime and target startTime.
The opinionated latest endpoint ignores historical publish-time selection;
it is deliberately not used. This is a national power forecast, not local NWP.
"""
from concurrent.futures import ThreadPoolExecutor
import json,os
import pandas as pd
from prepare_weather_v18 import download,ROOT
DATA=ROOT/'data/policy_v24/issued_wind'
OUT=ROOT/'outputs/protocol_benchmark_v24/economics'


def batch(bounds):
    start,end=bounds;path=DATA/f'{start:%Y%m%d}_{end:%Y%m%d}.json'
    url=('https://data.elexon.co.uk/bmrs/api/v1/datasets/WINDFOR'
         f'?publishDateTimeFrom={start:%Y-%m-%d}T00%3A00Z&publishDateTimeTo={end:%Y-%m-%d}T00%3A00Z&format=json')
    record=download(url,path);d=pd.DataFrame(json.loads(path.read_text())['data'])
    if d.empty:raise ValueError(f'No issued wind data at {start}')
    d.publishTime=pd.to_datetime(d.publishTime,utc=True);d.startTime=pd.to_datetime(d.startTime,utc=True)
    if not d.publishTime.between(start.tz_localize('UTC'),end.tz_localize('UTC')).all():
        raise ValueError('API returned wrong forecast publication period')
    return record,d


def main():
    DATA.mkdir(parents=True,exist_ok=True);os.environ['WPF_DOWNLOAD_TRANSPORT']='windows-curl'
    dates=list(pd.date_range('2019-12-30','2021-07-01',freq='7D'));dates.append(pd.Timestamp('2021-07-01'))
    records=[];frames=[]
    with ThreadPoolExecutor(max_workers=3) as pool:
        for record,d in pool.map(batch,zip(dates[:-1],dates[1:])):
            records.append(record);frames.append(d)
            if len(records)%10==0:print('issued-wind batches',len(records),flush=True)
    data=pd.concat(frames,ignore_index=True).drop_duplicates()
    if data.duplicated(['publishTime','startTime']).any():raise ValueError('Ambiguous forecast vintage')
    data.to_parquet(DATA/'vintages_2020_2021H1.parquet',index=False)
    report={'status':'COMPLETE','rows':len(data),'publications':data.publishTime.nunique(),
        'scope':'GB national wind generation forecast; MW; preserve publication vintages',
        'feature_gate':'publishTime+5min <= issue_time; never choose a later vintage','downloads':records}
    (OUT/'issued_wind_source.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({k:v for k,v in report.items() if k!='downloads'},indent=2))


if __name__=='__main__':main()
