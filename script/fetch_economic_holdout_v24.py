"""Prepare the untouched 2021H2 economic period without evaluating outcomes.

Original H1 validation results remain archived. This acquisition supplies
published forecast vintages and scoring prices, not retrospective predictors.
"""
from concurrent.futures import ThreadPoolExecutor
import json,os
import pandas as pd
from prepare_weather_v18 import download,ROOT
DATA=ROOT/'data/policy_v24/holdout_2021H2'
OUT=ROOT/'outputs/protocol_benchmark_v24/economics'


def one(job):
    kind,start,end=job
    if kind=='prices':
        url=f'https://data.elexon.co.uk/bmrs/api/v1/balancing/settlement/system-prices/{start:%Y-%m-%d}?format=json'
    elif kind=='wind':
        url=('https://data.elexon.co.uk/bmrs/api/v1/datasets/WINDFOR'
             f'?publishDateTimeFrom={start:%Y-%m-%d}T00%3A00Z&publishDateTimeTo={end:%Y-%m-%d}T00%3A00Z&format=json')
    else:
        url=('https://data.elexon.co.uk/bmrs/api/v1/balancing/pricing/market-index'
             f'?from={start:%Y-%m-%d}T00%3A00Z&to={end:%Y-%m-%d}T00%3A00Z&format=json')
    path=DATA/kind/f'{start:%Y%m%d}.json'
    record=download(url,path);d=pd.DataFrame(json.loads(path.read_text()).get('data',[]))
    return kind,record,d


def main():
    os.environ['WPF_DOWNLOAD_TRANSPORT']='windows-curl';DATA.mkdir(parents=True,exist_ok=True)
    days=pd.date_range('2021-07-01','2022-01-01',freq='D')
    weeks=list(pd.date_range('2021-07-01','2022-01-01',freq='7D'))+[pd.Timestamp('2022-01-01')]
    jobs=[('prices',day,day+pd.Timedelta(days=1)) for day in days]
    jobs += [(kind,a,b) for kind in ['wind','market_index'] for a,b in zip(weeks[:-1],weeks[1:])]
    frames={k:[] for k in ['prices','wind','market_index']};records=[]
    with ThreadPoolExecutor(max_workers=3) as pool:
        for kind,r,d in pool.map(one,jobs):
            records.append(r);frames[kind].append(d)
            if len(records)%25==0:print('H2 acquisitions',len(records),'of',len(jobs),flush=True)
    for kind,parts in frames.items():
        d=pd.concat(parts,ignore_index=True).drop_duplicates();d.to_parquet(DATA/f'{kind}.parquet',index=False)
    # Keep partial source days. Missing prices remain missing, never interpolated.
    old=pd.read_parquet(ROOT/'data/policy_v18/elexon/system_prices_2020_2021H1.parquet')
    extra=pd.read_parquet(DATA/'prices.parquet')
    prices=pd.concat([old,extra],ignore_index=True).drop_duplicates()
    prices['startTime']=pd.to_datetime(prices.startTime,utc=True)
    if prices.duplicated('startTime').any():raise ValueError('Ambiguous price merge')
    prices.to_parquet(DATA/'system_prices_2020_2021.parquet',index=False)
    wind=pd.concat([pd.read_parquet(ROOT/'data/policy_v24/issued_wind/vintages_2020_2021H1.parquet'),pd.read_parquet(DATA/'wind.parquet')],ignore_index=True)
    for c in ['startTime','publishTime']:wind[c]=pd.to_datetime(wind[c],utc=True)
    wind=wind.drop_duplicates()
    if wind.duplicated(['startTime','publishTime']).any():raise ValueError('Ambiguous forecast merge')
    wind.to_parquet(DATA/'wind_vintages_2020_2021.parquet',index=False)
    market=pd.concat([pd.read_parquet(ROOT/'data/policy_v24/market_index/provider_rows.parquet'),pd.read_parquet(DATA/'market_index.parquet')],ignore_index=True)
    market.startTime=pd.to_datetime(market.startTime,utc=True);market=market.drop_duplicates()
    if market.duplicated(['startTime','dataProvider']).any():raise ValueError('Ambiguous index merge')
    market=market[market.volume.gt(0)].copy();market['weighted']=market.price*market.volume
    mid=market.groupby('startTime')[['weighted','volume']].sum();mid['market_index_price']=mid.weighted/mid.volume
    mid.to_parquet(DATA/'market_index_2020_2021.parquet')
    report={'status':'ACQUIRED_WITH_GAPS_RETAINED','prices':len(prices),'forecast_rows':len(wind),'market_index_rows':len(mid),
            'test_economic_results_read':False,'downloads':records}
    (OUT/'holdout_acquisition.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({k:v for k,v in report.items() if k!='downloads'},indent=2))


if __name__=='__main__':main()
