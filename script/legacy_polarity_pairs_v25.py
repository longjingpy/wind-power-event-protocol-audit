"""Compute requested paired differences on existing LiDAR predictions unchanged."""
from pathlib import Path
import sys
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from wind_events.paired_probability import paired_rows
BASE=ROOT/'outputs/protocol_benchmark_v18/lidar_confirmation/chronological_calibration'
OUT=ROOT/'outputs/protocol_benchmark_v25/polarity'


def main():
    OUT.mkdir(parents=True,exist_ok=True);rows=[];effects=[]
    names=['scalar_controls5','standalone_gaf_pca6','standalone_gaf_bit6','standalone_raw25','controlled_raw25']
    for turbine in ['T11','T07']:
        frame=pd.read_parquet(BASE/f'{turbine}_predictions.parquet')
        probabilities={n:frame[[f'p_{n}_{k}' for k in range(3)]].to_numpy() for n in names}
        for days in [3,7,14]:
            a,b=paired_rows(frame,probabilities,[('standalone_gaf_bit6','scalar_controls5'),
                ('standalone_gaf_bit6','standalone_gaf_pca6'),('controlled_raw25','scalar_controls5')],days)
            rows += [{'dataset':turbine,**r} for r in a];effects += [{'dataset':turbine,**r} for r in b]
    pd.DataFrame(rows).to_csv(OUT/'legacy_lidar_scores.csv',index=False)
    pd.DataFrame(effects).to_csv(OUT/'legacy_lidar_paired.csv',index=False)
    print(pd.DataFrame(effects).query("block_days==7 and candidate=='standalone_gaf_bit6'").to_string(index=False))


if __name__=='__main__':main()
