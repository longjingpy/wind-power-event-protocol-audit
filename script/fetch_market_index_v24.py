"""Direct Elexon market-index acquisition for complete-revenue research replay.

Elexon Market Index Data (MID) is a realised volume-weighted market reference,
not an executable historical order quote or a price available to our forecast.
It supplies the missing schedule-revenue leg; zero-volume providers are excluded.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json, os
import pandas as pd
from prepare_weather_v18 import download, ROOT

DATA = ROOT/'data/policy_v24/market_index'
OUT = ROOT/'outputs/protocol_benchmark_v24/economics'


def batch(bounds):
    start, end = bounds
    url = ('https://data.elexon.co.uk/bmrs/api/v1/balancing/pricing/market-index'
           f'?from={start:%Y-%m-%d}T00%3A00Z&to={end:%Y-%m-%d}T00%3A00Z&format=json')
    path = DATA/f'{start:%Y%m%d}_{end:%Y%m%d}.json'
    record = download(url, path)
    values = json.loads(path.read_text(encoding='utf-8'))['data']
    if not values:
        raise ValueError(f'Empty market-index response: {start}')
    return record, pd.DataFrame(values)


def main():
    os.environ['WPF_DOWNLOAD_TRANSPORT'] = 'windows-curl'
    DATA.mkdir(parents=True,exist_ok=True); OUT.mkdir(parents=True,exist_ok=True)
    dates = list(pd.date_range('2020-01-01','2021-07-01',freq='7D'))
    dates.append(pd.Timestamp('2021-07-01'))
    records,frames = [],[]
    with ThreadPoolExecutor(max_workers=3) as pool:
        for record,frame in pool.map(batch,zip(dates[:-1],dates[1:])):
            records.append(record);frames.append(frame)
            if len(records)%10==0:print('batches',len(records),flush=True)
    raw=pd.concat(frames,ignore_index=True).drop_duplicates()
    raw['startTime']=pd.to_datetime(raw.startTime,utc=True)
    raw=raw[raw.startTime.ge('2020-01-01')&raw.startTime.lt('2021-07-01')]
    if raw.duplicated(['startTime','dataProvider']).any():raise ValueError('Conflicting provider rows')
    good=raw[raw.volume.gt(0)].copy();good['price_volume']=good.price*good.volume
    out=good.groupby('startTime')[['price_volume','volume']].sum()
    out['market_index_price']=out.price_volume/out.volume
    expected=pd.date_range('2020-01-01','2021-07-01',freq='30min',inclusive='left',tz='UTC')
    out=out.reindex(expected);out.index.name='startTime'
    raw.to_parquet(DATA/'provider_rows.parquet',index=False)
    out.to_parquet(DATA/'market_index_2020_2021H1.parquet')
    report={'status':'COMPLETE' if out.market_index_price.notna().all() else 'PARTIAL',
        'expected_intervals':len(expected),'available_intervals':int(out.market_index_price.notna().sum()),
        'currency':'GBP/MWh','role':'realised market-index execution reference for scoring, never future feature',
        'zero_volume_provider_rows_excluded':int(raw.volume.eq(0).sum()),'downloads':records}
    (OUT/'market_index_source.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({k:v for k,v in report.items() if k!='downloads'},indent=2))


if __name__=='__main__':main()
