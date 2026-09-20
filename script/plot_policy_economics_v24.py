"""Draw the two current economic figures from saved test predictions only."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'outputs/protocol_benchmark_v24/economics'
if not DATA.exists():
    DATA = ROOT / 'results/protocol_benchmark_v24/economics'
OUT = ROOT / 'manuscript/figures_v24'
OUT.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':12,'axes.labelsize':12,
    'axes.titlesize':13,'xtick.labelsize':11,'ytick.labelsize':11,'legend.fontsize':11,
    'pdf.fonttype':42,'svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False})
BLUE, GREY, ORANGE = '#0072B2', '#66727D', '#D55E00'


def save(fig, name):
    for extension in ['pdf','svg','png']:
        fig.savefig(OUT / f'{name}.{extension}', dpi=200, facecolor='white')
    plt.close(fig)


def main():
    summary = pd.read_csv(DATA / 'primary_policy_results.csv')
    intervals = pd.read_csv(DATA / 'primary_policy_intervals.csv')
    fig, axes = plt.subplots(1,2,figsize=(8.6,3.6),layout='constrained',sharey=True)
    all_daily=[]
    for ax, (_, row), panel in zip(axes,summary.iterrows(),'ab'):
        source=DATA/'jiangsu_native'
        if row.weather!='none':source/=row.weather
        if (source/'test_predictions.parquet').exists():
            p=pd.read_parquet(source/'test_predictions.parquet')
            p=p[p.horizon_minutes.eq(row.horizon_minutes)&p.model.isin(['persistence',row.representation])].copy()
            p['day']=pd.to_datetime(p.target_time,utc=True).dt.tz_convert('Asia/Shanghai').dt.floor('D')
            daily=p.groupby(['day','model']).fee_cny.sum().unstack(fill_value=0)
            daily.index=daily.index.tz_localize(None)
        else:
            published=pd.read_csv(OUT/'fig12_policy_fees.csv',parse_dates=['day'])
            daily=published[published.horizon_minutes.eq(row.horizon_minutes)].set_index('day')[['persistence','shape_pipeline']].rename(columns={'shape_pipeline':row.representation})
        for model,label,color in [('persistence','Persistence',GREY),(row.representation,'Shape pipeline',BLUE)]:
            ax.plot(daily.index,daily[model].cumsum()/1000,color=color,lw=2.0,label=label)
        d=daily.rename(columns={row.representation:'shape_pipeline'}).reset_index()
        d['horizon_minutes']=row.horizon_minutes;all_daily.append(d)
        ci=intervals[intervals.comparison.eq(f'{row.horizon_minutes}min_primary_vs_persistence')&intervals.block_days.eq(7)].iloc[0]
        ax.text(.04,.61,f'Saved CNY {row.saved_cny:,.0f}\n{row.fee_reduction_pct:.2f}% ({ci.low:.2f}–{ci.high:.2f}%)',
                transform=ax.transAxes,fontsize=11,color=BLUE,va='top')
        ax.set_title(f'{panel}   '+('15-minute lead' if row.horizon_minutes==15 else 'Four-hour lead'),loc='left',fontweight='bold')
        ax.set_ylim(0,160);ax.grid(axis='y',alpha=.16)
        ax.xaxis.set_major_locator(mdates.MonthLocator());ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
        ax.set_xlabel('Test calendar: Oct 2024–Feb 2025')
        ax.legend(loc='upper left',frameon=False,handlelength=1.5)
    axes[0].set_ylabel('Cumulative charge\n(CNY 1,000)')
    pd.concat(all_daily,ignore_index=True).to_csv(OUT/'fig12_policy_fees.csv',index=False)
    save(fig,'fig12_policy_fees')
    table=pd.read_csv(DATA/'jiangsu_native/test_summary.csv')
    rows=table[table.horizon_minutes.eq(240)&table.model.isin(['raw25_mean_action','raw25'])].set_index('model').loc[['raw25_mean_action','raw25']]
    rows.to_csv(OUT/'fig13_action_value.csv')
    fig,axes=plt.subplots(1,2,figsize=(8.6,3.5),layout='constrained')
    for ax,column,mult,title,label,limits in [
        (axes[0],'nmae',100,'a   Average error','nMAE (%)',(0,21)),
        (axes[1],'accuracy_charge_cny',.001,'b   Rule-based cost','Accuracy charge (CNY 1,000)',(0,175))]:
        values=rows[column].to_numpy()*mult
        bars=ax.bar([0,1],values,width=.52,color=[GREY,ORANGE])
        for bar,value in zip(bars,values):
            ax.text(bar.get_x()+bar.get_width()/2,value+limits[1]*.025,f'{value:.2f}',ha='center',fontsize=12,fontweight='bold')
        ax.set_xticks([0,1],['Conditional\nmean','Admissible-band\naction'])
        ax.set_ylim(*limits);ax.set_ylabel(label);ax.set_title(title,loc='left',fontweight='bold')
        ax.grid(axis='y',alpha=.16);ax.set_axisbelow(True)
    save(fig,'fig13_action_value')
    print(json.dumps({'figures':2,'source':'saved v24 predictions; no fitting or reselection','files':len(list(OUT.iterdir()))}))


if __name__=='__main__':main()
