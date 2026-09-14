"""Redraw the manuscript figures as single-question, vector data graphics."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'manuscript/applied_energy/figures'; DATA=ROOT/'outputs/dynamic_events_v6'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.titlesize':12,'axes.titleweight':'bold','pdf.fonttype':42,'svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False})
FARMS=['Pizhou','Suining','Yandun','La Haute Borne','Hill of Towie']; MAP={'pizhou':'Pizhou','suining':'Suining','yandun':'Yandun','lahaute':'La Haute Borne','hill':'Hill of Towie'}
COL={'raw25':'#216E8C','event_row_permutation':'#B9C7D0','raw_pca6':'#3B8C7A','statistics9':'#D88B3D','gaf_pca6':'#7A6AA6','signed_gaf_pca6':'#D05B58'}
def save(fig,n):
    for ext in ('pdf','svg','png'): fig.savefig(OUT/f'fig{n}.{ext}',bbox_inches='tight',dpi=220)
    plt.close(fig)
def style(ax,title,ylabel):
    ax.set_title(title,loc='left',pad=12); ax.set_ylabel(ylabel); ax.grid(axis='y',alpha=.18); ax.set_axisbelow(True)
def main():
    OUT.mkdir(parents=True,exist_ok=True); rep=pd.read_csv(DATA/'representation_summary_primary.csv')
    # Fig 2: one question, correspondence versus its permutation control.
    d=rep[(rep.k==4)&rep.group.isin(['hill','lahaute','pizhou','suining','yandun'])&rep.representation.isin(['raw25','event_row_permutation'])].copy(); d['site']=d.group.map(MAP)
    fig,ax=plt.subplots(figsize=(7.2,4.2)); x=np.arange(5); w=.34
    for j,key in enumerate(['raw25','event_row_permutation']):
        vals=[d[(d.site==s)&(d.representation==key)].nmi.iloc[0] for s in FARMS]; ax.bar(x+(j-.5)*w,vals,w,label='Ordered raw25' if j==0 else 'Event-row permutation',color=COL[key])
        for p,v in zip(x+(j-.5)*w,vals): ax.text(p,v+.018,f'{v:.3f}',ha='center',fontsize=8)
    ax.set_xticks(x,FARMS,rotation=18,ha='right'); ax.set_ylim(0, .8); style(ax,'Fig. 2 | Temporal correspondence carries shared event structure','NMI (k = 4)'); ax.legend(frameon=False,ncol=2); save(fig,2)
    # Fig 3: one question, representation choice changes retained information.
    keys=['raw25','raw_pca6','statistics9','gaf_pca6','gaf_signed_pca6']; labels=['Raw25','Raw-PCA6','Statistics9','GAF-PCA6','Signed-GAF-PCA6']
    d=rep[(rep.k==4)&rep.group.isin(['hill','lahaute','pizhou','suining','yandun'])&rep.representation.isin(keys)].copy(); means=d.groupby('representation')[['nmi','ari']].mean().reindex(keys)
    fig,ax=plt.subplots(figsize=(7.2,4.3)); x=np.arange(len(keys)); ax.bar(x-.19,means.nmi,.36,label='NMI',color='#267A8B'); ax.bar(x+.19,means.ari,.36,label='ARI',color='#D99348')
    for i,(a,b) in enumerate(zip(means.nmi,means.ari)): ax.text(i-.19,a+.02,f'{a:.3f}',ha='center',fontsize=8); ax.text(i+.19,b+.02,f'{b:.3f}',ha='center',fontsize=8)
    ax.set_xticks(x,labels,rotation=15,ha='right'); ax.set_ylim(0, .8); style(ax,'Fig. 3 | Representation choice changes preserved correspondence','Five-farm mean agreement (k = 4)'); ax.legend(frameon=False,ncol=2); save(fig,3)
    # Fig 4: one question, resolution sensitivity of raw ordered shapes.
    d=pd.read_csv(DATA/'representation_summary_sensitivity.csv'); d=d[(d.representation=='raw25')&d.group.isin(['hill','lahaute','pizhou','suining','yandun'])]; d['site']=d.group.map(MAP)
    k4=rep[(rep.representation=='raw25')&rep.group.isin(['hill','lahaute','pizhou','suining','yandun'])].copy(); k4['site']=k4.group.map(MAP); d=pd.concat([d,k4],ignore_index=True)
    fig,ax=plt.subplots(figsize=(7.2,4.2)); x=np.arange(5)
    for k,color in zip([2,4,6],['#6A9FB5','#216E8C','#173B5D']):
        v=[d[(d.site==s)&(d.k==k)].nmi.iloc[0] for s in FARMS]; ax.plot(x,v,'o-',label=f'k = {k}',color=color,lw=2,ms=6)
    ax.set_xticks(x,FARMS,rotation=18,ha='right'); ax.set_ylim(0,1); style(ax,'Fig. 4 | Ordered-shape agreement persists across cluster resolutions','NMI'); ax.legend(frameon=False,ncol=3); save(fig,4)
    # Fig 5: one question, external transfer with support shown explicitly.
    g=pd.read_csv(DATA/'external_greece/summary_by_sample_size.csv');
    sd=pd.read_csv(ROOT/'outputs/sdwpf_v7/learned_forward_metrics.csv'); sd=sd[(sd.k==4)&(sd.representation.isin(['tcn','transformer']))]
    fig,ax=plt.subplots(figsize=(7.2,4.2)); x=np.arange(len(g)); ax.plot(x,g.median_nmi,'o-',lw=2,color='#216E8C',label='Greek median NMI'); ax.fill_between(x,g.min_nmi,g.max_nmi,color='#216E8C',alpha=.14,label='Greek observed range'); ax.set_xticks(x,g.sample_bin); ax.set_ylim(0,1); style(ax,'Fig. 5 | External transfer retains agreement as support grows','NMI'); ax.set_xlabel('Matched events per configuration pair'); ax.legend(frameon=False,loc='lower left'); ax.text(.98,.96,'SDWPF transferred models: TCN 0.626; Transformer 0.589',transform=ax.transAxes,ha='right',va='top',fontsize=8); save(fig,5)
    # Fig 6: one question, weather-defined periods and subsequent risk.
    w=pd.read_csv(ROOT/'outputs/weather_uncertainty_v12/risk_block_intervals.csv'); w=w[w.block_days.eq(7)]
    fig,ax=plt.subplots(figsize=(7.2,4.4))
    for source,offset,color,marker in [('ERA5',-.09,'#216E8C','o'),('NOAA',.09,'#C45C35','s')]:
        part=w[w.source.eq(source)].sort_values('horizon_h'); y=100*part.risk_difference.to_numpy()
        interval=np.array([y-100*part.ci95_low.to_numpy(),100*part.ci95_high.to_numpy()-y])
        ax.errorbar(part.horizon_h.to_numpy()+offset,y,yerr=interval,fmt=marker,color=color,capsize=4,markersize=6,lw=1.5,label=source)
    ax.axhline(0,color='#8795A0',lw=.8); ax.set_xticks([1,2,4]); ax.set_xlabel('Outcome horizon (h)'); ax.set_ylim(-6,16)
    style(ax,'Fig. 6 | Weather context and uncertainty in subsequent event risk','Risk difference (percentage points)'); ax.legend(frameon=False,ncol=2,loc='upper left')
    fig.text(.5,-.04,'ERA5: 21,300 / 84,761 records; NOAA: 41,163 / 19,668 (exposed / unexposed)',ha='center',fontsize=8); save(fig,6)
if __name__=='__main__': main()
