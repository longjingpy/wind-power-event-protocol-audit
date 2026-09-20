"""Publication-scale vector figures for the itemized September 19 revision.

All text is authored at final column width. Empirical distributions use real
configuration scores or calendar-block replicates, never distributions fitted
to interval endpoints. Original experiments remain in their own populations.
"""
from pathlib import Path
import json, sys, shutil
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.lines import Line2D
from sklearn.metrics import roc_curve,roc_auc_score
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'outputs/protocol_benchmark_v18'
OLD=ROOT/'manuscript/figures_v18'
OUT=ROOT/'manuscript/figures_v22'
OUT.mkdir(parents=True,exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.labelsize':11,'axes.titlesize':11,
    'xtick.labelsize':10,'ytick.labelsize':10,'legend.fontsize':10,'pdf.fonttype':42,'svg.fonttype':'none',
    'axes.spines.top':False,'axes.spines.right':False,'axes.linewidth':.8,'savefig.facecolor':'white'})
SITES=['pizhou','suining','yandun','lahaute','hill','greece','sdwpf','hill_2021']
NAMES=dict(zip(SITES,['Pizhou','Suining','Yandun','La Haute Borne','Hill 2020','Greece','SDWPF','Hill 2021']))
COL={'raw25':'#21618C','raw_pca6':'#71A4C4','statistics9':'#B87818','gaf_pca6':'#168A73','gaf_signed_pca6':'#68B5A5','gaf_bit6':'#A33378','scalar_controls5':'#666D78'}
LABEL={'raw25':'Raw25','raw_pca6':'Raw/PCA6','statistics9':'Statistics9','gaf_pca6':'GAF/PCA6','gaf_signed_pca6':'Signed GAF/PCA6','gaf_bit6':'GAF + polarity'}
MAN=[]

def save(fig,name,old_number,sources,caption,panels=None):
    fig.canvas.draw()
    for ext in ['pdf','svg','png']:fig.savefig(OUT/f'{name}.{ext}',dpi=240)
    if panels:
        renderer=fig.canvas.get_renderer()
        for letter,ax in panels:
            bbox=ax.get_tightbbox(renderer).transformed(fig.dpi_scale_trans.inverted()).expanded(1.04,1.08)
            for ext in ['pdf','svg','png']:fig.savefig(OUT/f'{name}_{letter}.{ext}',bbox_inches=bbox,dpi=240)
    (OUT/f'{name}_caption.md').write_text(caption+'\n',encoding='utf-8')
    MAN.append(dict(name=name,old_number=old_number,sources=sources,caption=caption,
        width_inches=fig.get_figwidth(),height_inches=fig.get_figheight(),body_font_pt=11,
        smallest_text_pt=min(t.get_fontsize() for t in fig.findobj(matplotlib.text.Text) if t.get_text()),
        svg_editable_text=True))
    plt.close(fig)

def axis(ax):
    ax.set_axisbelow(True);ax.grid(axis='y',color='#DFE5EB',lw=.6)

def overview():
    fig,ax=plt.subplots(figsize=(6.5,4.5));fig.subplots_adjust(left=.015,right=.985,bottom=.035,top=.99)
    ax.set(xlim=(0,100),ylim=(0,100));ax.axis('off')
    def box(name,x,y,w,h,text,face,edge,fs=12):
        p=FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.3,rounding_size=2.2',facecolor=face,edgecolor=edge,lw=1.2)
        p.set_gid(name);ax.add_patch(p);t=ax.text(x+w/2,y+h/2,text,ha='center',va='center',fontsize=fs,linespacing=1.3);t.set_gid(name+'_text')
    def arrow(name,points,dashed=False):
        for a,b in zip(points[:-2],points[1:-1]):ax.plot([a[0],b[0]],[a[1],b[1]],color='#425363',lw=1.1,ls='--' if dashed else '-')
        a=FancyArrowPatch(points[-2],points[-1],arrowstyle='-|>',mutation_scale=10,color='#425363',lw=1.1,linestyle='--' if dashed else '-',shrinkA=1,shrinkB=2);a.set_gid(name);ax.add_patch(a)
    ax.text(50,97,'Event measurement → independent validation',ha='center',fontsize=15,fontweight='bold')
    box('china',1,79,46,12,'China: 4 archives · 298 turbines','#E9F3F9','#23749B')
    box('europe',53,79,46,12,'Europe: 4 archives · 42 turbines','#FFF1E5','#C47731')
    ax.text(50,72,'Shared clock, quality flags and training-only scaling',ha='center',fontsize=12)
    box('detector',1,47,29,18,'1  Detection\nIntervals + turns','#E1F0F5','#95C8D5')
    box('matching',35.5,47,29,18,'2  Matching\nOne-to-one IoU','#E9F1DC','#AFC68D')
    box('representation',71,47,28,18,'3  Representation\nShapes + partitions','#FFF0CB','#DFC16A')
    arrow('data_down',[(24,79),(24,67),(15.5,67),(15.5,65)])
    arrow('europe_down',[(76,79),(76,67),(15.5,67),(15.5,65)])
    arrow('detect_match',[(30,56),(35.5,56)]);arrow('match_encode',[(64.5,56),(71,56)])
    ax.text(1,39,'4  Evaluation and decision',fontweight='bold',fontsize=14)
    box('structure',1,17,30,17,'Structural survival\nARI · NMI · coverage','#F0E9F5','#B49DC4')
    box('physical',35,17,30,17,'Physical tracking\nWind · LiDAR','#F0E9F5','#B49DC4')
    box('decision',69,17,30,17,'Forecast-to-cost\nPrices · storage','#F0E9F5','#B49DC4')
    arrow('representation_evaluation',[(85,47),(85,42),(97,42),(97,34)])
    arrow('matching_structure',[(50,47),(50,43),(16,43),(16,34)])
    arrow('representation_physical',[(85,47),(85,36),(50,36),(50,34)])
    box('references',1,1,98,11,'Independent references: blind ratings · weather · LiDAR · prices','#F5F6F7','#CCD2D8',10)
    for x in [16,50,84]:arrow(f'reference_{x}',[(x,12),(x,17)],True)
    save(fig,'fig01_workflow',1,['catalogues; instrumented SMARTEOLE; study protocol'],
        'Four layers connect eight wind-farm archives (340 distinct turbines) to three validation criteria. Detection defines intervals, matching establishes comparable events, and representations describe their structure. Structural survival evaluates correspondence across protocols; external references test physical tracking and forecast-to-cost use. The European total includes the seven SMARTEOLE turbines; Hill 2021 and the 2026 instrument records are additional periods from the same farm. Dashed arrows introduce independent reference evidence.')

def detection():
    signal=pd.read_csv(OLD/'fig2_signal.csv');bounds=pd.read_csv(OLD/'fig2_protocol_comparison.csv')
    fig,(top,bottom)=plt.subplots(2,1,figsize=(6.5,3.65),sharex=True,gridspec_kw={'height_ratios':[1.3,1]})
    fig.subplots_adjust(left=.16,right=.97,top=.95,bottom=.18,hspace=.13)
    top.plot(signal.relative_hours,signal.power_training_reference_units,color='#253744',lw=1.8,marker='o',ms=3)
    top.set_ylabel('Power / scale');top.tick_params(labelbottom=False);axis(top)
    labels=['Threshold','Financial tail','Mean shift','OpSDA']
    for i,(_,r) in enumerate(bounds.iterrows()):
        color=['#28719D','#B97820','#168A73','#A33378'][i]
        bottom.plot([r.start_relative_hours,r.end_relative_hours],[3-i,3-i],lw=6,solid_capstyle='butt',color=color)
        bottom.scatter([r.start_relative_hours,r.end_relative_hours],[3-i]*2,s=30,color=color,zorder=4)
        bottom.text(3.05,3-i,f'IoU {r.iou_with_reference:.2f}',va='center',fontsize=10)
    bottom.set_yticks(range(4),labels[::-1]);bottom.set(xlabel='Hours relative to reference onset',ylim=(-.6,3.6))
    top.set_xlim(signal.relative_hours.min(),max(signal.relative_hours.max(),4.8));bottom.spines[['left','top','right']].set_visible(False)
    bounds.to_csv(OUT/'fig02_detection.csv',index=False);signal.to_csv(OUT/'fig02_signal.csv',index=False)
    save(fig,'fig02_detection',2,['manuscript/figures_v18/fig2_signal.csv','manuscript/figures_v18/fig2_protocol_comparison.csv'],
        'The same observed trajectory yields different event boundaries. The lower tracks show the four detector intervals on the same physical-time axis; threshold and financial-tail boundaries coincide in this example. IoU is measured against the threshold reference. Track labels replace an overlapping legend.')

def compression():
    d=pd.read_csv(ROOT/'outputs/protocol_benchmark_v21/representation_audit/method_score_differences.csv')
    d=d[d.reference.eq('raw25')].set_index('site').loc[SITES].reset_index()
    labels=pd.read_csv(ROOT/'outputs/protocol_benchmark_v21/representation_audit/test_partition_equivalence.csv')
    labels=labels[labels.reference.eq('raw25')].groupby('site').partition_ari.agg(['median','min','max']).reindex(SITES)
    d['partition_ari_median']=labels['median'].to_numpy();d.to_csv(OUT/'fig03_compression.csv',index=False)
    fig,(a,b)=plt.subplots(1,2,figsize=(6.5,2.95),gridspec_kw={'width_ratios':[1.05,1]});fig.subplots_adjust(left=.21,right=.98,top=.88,bottom=.22,wspace=.40)
    y=np.arange(8)
    for col,c in [('reference_median',COL['raw25']),('candidate_median',COL['raw_pca6'])]:a.scatter(d[col],y,s=32,c=c,edgecolor='white',lw=.4,zorder=4,label='Raw25' if col=='reference_median' else 'Raw/PCA6')
    a.set_yticks(y,[NAMES[s] for s in SITES]);a.invert_yaxis();a.set(xlim=(.66,.90),xlabel='Cross-protocol ARI',title='a  Trajectory compression')
    a.legend(loc='lower right',bbox_to_anchor=(.98,.03),frameon=True,facecolor='white',edgecolor='#D7DEE6',fontsize=8,handletextpad=.3,columnspacing=.7)
    b.axvline(0,color='#9AA4AF',ls='--',lw=.8);b.hlines(y,0,d.difference_of_medians*1000,color=COL['raw_pca6'],lw=2)
    b.scatter(d.difference_of_medians*1000,y,s=28,color=COL['raw25']);b.set_yticks(y,[]);b.invert_yaxis()
    b.set(xlim=(-3.5,3.5),xticks=[-3,0,3],xlabel='PCA − raw ARI (×10⁻³)',title='b  Full-precision differences')
    save(fig,'fig03_compression',3,['outputs/protocol_benchmark_v21/representation_audit/'],
        'Raw/PCA6 provides a compression control for the same 25-point trajectory. Panel a shows current common-support v18 results; panel b resolves differences hidden by two-decimal rounding. PCA retains 93.4% of standardized training variance. The separate event-label partition comparison is reported in the accompanying data; it differs from cross-protocol ARI.',panels=[('a',a),('b',b)])

def structural():
    d=pd.read_csv(BASE/'tables/structural_common_support.csv');reps=list(LABEL)
    mat=d.pivot(index='target_site',columns='representation',values='median_ari').reindex(index=SITES,columns=reps)
    fig,ax=plt.subplots(figsize=(6.5,3.95));fig.subplots_adjust(left=.24,right=.89,bottom=.3,top=.97)
    cmap=plt.get_cmap('Blues');norm=matplotlib.colors.Normalize(0,1)
    im=ax.imshow(mat,cmap=cmap,vmin=0,vmax=1,aspect='auto')
    ax.set_yticks(range(8),[NAMES[s] for s in SITES]);ax.set_xticks(range(6),[LABEL[r] for r in reps],rotation=38,ha='right')
    for i in range(8):
        for j in range(6):
            value=mat.iloc[i,j];rgb=cmap(norm(value))[:3];luma=.2126*rgb[0]+.7152*rgb[1]+.0722*rgb[2]
            ax.text(j,i,f'{value:.3f}',ha='center',va='center',fontsize=10,color='white' if luma<.48 else '#14212E')
    cb=fig.colorbar(im,ax=ax,fraction=.045,pad=.04);cb.set_label('Median ARI')
    d.to_csv(OUT/'fig04_structure.csv',index=False)
    save(fig,'fig04_structure',4,['outputs/protocol_benchmark_v18/tables/structural_common_support.csv'],
        'Structural survival across seven archives and the Hill 2021 temporal holdout. Darker blue represents higher ARI; label contrast follows cell luminance. Each cell is the median over common detector-configuration pairs after the median over three training seeds. Raw/PCA6 and the angular variants are related ablations, whose differences are resolved in Fig. 3 and the full-precision data.')

def sampling():
    frames=[pd.read_csv(BASE/'resolution/cross_resolution_metrics.csv')]
    frames.append(pd.read_csv(ROOT/'outputs/protocol_benchmark_v22/sampling/cross_resolution_metrics.csv'))
    d=pd.concat(frames,ignore_index=True);d=d[d.block_days.eq(7)].copy();d['coverage']=d[['left_coverage','right_coverage']].min(axis=1)
    keys=[('greece',10,30),('greece',30,60),('yandun',15,30),('yandun',30,60),('lahaute',30,60),('hill',30,60)]
    d.to_csv(OUT/'fig05_sampling.csv',index=False)
    fig,(a,b)=plt.subplots(1,2,figsize=(6.5,3.45),sharey=True);fig.subplots_adjust(left=.265,right=.895,top=.87,bottom=.21,wspace=.35)
    rng=np.random.default_rng(41)
    for i,(site,l,r) in enumerate(keys):
        q=d[d.site.eq(site)&d.left_minutes.eq(l)&d.right_minutes.eq(r)]
        color='#B8792A' if site!='yandun' else '#28759C'
        for ax,col in [(a,'ari'),(b,'coverage')]:
            # No-match/constant partitions stay in CSV; ARI needs informative support.
            valid=q[col].notna()&(q.informative if col=='ari' else True)&q.matched_pairs.gt(0)
            vals=q.loc[valid,col].to_numpy();jitter=rng.uniform(-.14,.14,len(vals))
            ax.scatter(vals,i+jitter,color=color,s=13,alpha=.5,lw=0)
            if len(vals):
                lo,med,hi=np.quantile(vals,[.25,.5,.75]);ax.plot([lo,hi],[i,i],color=color,lw=3);ax.scatter(med,i,marker='D',s=24,c='white',edgecolor=color,zorder=4)
        b.text(1.08,i,f'{q.matched_pairs.gt(0).sum()}/17',fontsize=9,va='center',ha='left',transform=b.get_yaxis_transform(),clip_on=False)
    a.set_yticks(range(len(keys)),[f'{NAMES[s]}\n{l}–{r} min' for s,l,r in keys]);a.invert_yaxis()
    for ax in [a,b]:ax.set_xlim(-.06,1.05);ax.set_xticks([0,.5,1]);ax.grid(axis='x',color='#E4E9EE',lw=.5)
    a.set(xlabel='Matched-event ARI',title='a  Structural survival');b.set(xlabel='Smaller-side coverage',title='b  Event support')
    save(fig,'fig05_sampling',5,['outputs/protocol_benchmark_v18/resolution/cross_resolution_metrics.csv','outputs/protocol_benchmark_v22/sampling/cross_resolution_metrics.csv'],
        'Sampling sensitivity now includes Greece, Yandun, La Haute Borne and Hill of Towie. Dots are detector configurations; diamonds and bars are medians and interquartile ranges across informative configurations. Counts give configurations with at least one match out of 17. Scale, prototype, split and physical context remain fixed. All eight grid comparisons, including Greece 10/60 and Yandun 15/60, remain in the data table; plotted comparisons connect native/30-minute and common 30/60-minute grids.')

def conditional():
    d=pd.read_csv(BASE/'conditional/conditional_information_protocol_conditioned.csv');d=d[d.condition.eq('joint')&d.block_days.eq(7)]
    fig,ax=plt.subplots(figsize=(6.5,4.2));fig.subplots_adjust(left=.27,right=.98,top=.84,bottom=.2)
    for j,rep in enumerate(['raw25','gaf_pca6','gaf_bit6']):
        q=d[d.representation.eq(rep)].set_index('site').loc[SITES]
        ax.scatter(q.conditional_mi_above_permutation,np.arange(8)+(j-1)*.15,color=COL[rep],marker=['o','s','D'][j],s=28,label=LABEL[rep],zorder=4)
    ax.set_yticks(range(8),[NAMES[s] for s in SITES]);ax.invert_yaxis();ax.set(xlim=(-.015,.53),xlabel='Conditional shared information (nats)')
    ax.legend(loc='lower left',bbox_to_anchor=(-.26,1.02),ncol=3,frameon=False,columnspacing=.9,handletextpad=.3)
    ax.grid(axis='x',color='#E4E9EE',lw=.6);d.to_csv(OUT/'fig06_conditional.csv',index=False)
    save(fig,'fig06_conditional',6,['outputs/protocol_benchmark_v18/conditional/conditional_information_protocol_conditioned.csv'],
        'Shared geometry after conditioning on protocol pair, direction, amplitude, duration and pre-window power. Values subtract the mean within-stratum permutation reference. The near-overlap of the angular variants shows similar geometry under these controls. Protected polarity targets directional information, tested with independent wind measurements in the following figures; it is not selected to maximize this conditioned score.')

def paths():
    d=pd.read_csv(OLD/'fig3_polarity_paths.csv');fig,ax=plt.subplots(figsize=(6.5,2.6));fig.subplots_adjust(left=.14,right=.98,top=.90,bottom=.25)
    ax.plot(d.coordinate,d.x,color=COL['raw25'],lw=2,label='Observed path, x');ax.plot(d.coordinate,d.negative_x,color=COL['gaf_bit6'],lw=2,ls='--',label='Sign reversal, −x')
    ax.set(xlabel='Shape coordinate',ylabel='Signed value');axis(ax);ax.legend(frameon=False,loc='center right',ncol=1)
    d.to_csv(OUT/'fig07_polarity_paths.csv',index=False)
    save(fig,'fig07_polarity_paths',7,['manuscript/figures_v18/fig3_polarity_paths.csv'],
        'An observed 25-coordinate path and its controlled global sign reversal. These two paths have opposite polarity and the same signed-domain Gramian angular summation field.')
    x=d.x.to_numpy();c=np.sqrt(np.maximum(0,1-x*x));g=np.outer(x,x)-np.outer(c,c)
    fig,ax=plt.subplots(figsize=(4.4,3.45));fig.subplots_adjust(left=.16,right=.80,top=.88,bottom=.19)
    im=ax.pcolormesh(g,cmap='RdBu_r',vmin=-1,vmax=1,rasterized=False);ax.set(xlabel='Shape coordinate',ylabel='Shape coordinate',title='G(x) = G(−x)')
    ax.set_aspect('equal',adjustable='box');ax.xaxis.label.set_size(11);ax.yaxis.label.set_size(11)
    ax.xaxis.label.set_weight('normal');ax.yaxis.label.set_weight('normal')
    fig.colorbar(im,ax=ax,pad=.025,fraction=.035,label='Angular field')
    pd.DataFrame(g).to_csv(OUT/'fig08_shared_gasf.csv',index=False)
    save(fig,'fig08_shared_gasf',8,['manuscript/figures_v18/fig3_polarity_paths.csv'],
        'The common Gramian angular summation field for the two paths in Fig. 7. The identity G(x)=G(−x) motivates retaining a sign coordinate alongside the compressed angular representation.')

def lidar():
    folder=BASE/'lidar_confirmation/chronological_calibration'
    names=['standalone_gaf_pca6','standalone_gaf_bit6','scalar_controls5']
    colors=[COL['gaf_pca6'],COL['gaf_bit6'],COL['scalar_controls5']]
    labels=['GAF/PCA6','GAF + polarity','Scalar controls']
    fig,axs=plt.subplots(1,2,figsize=(6.5,3.15));fig.subplots_adjust(left=.10,right=.985,top=.90,bottom=.31,wspace=.28)
    curves=[];draws=[]
    for ax,turb in zip(axs,['T11','T07']):
        d=pd.read_parquet(folder/f'{turb}_predictions.parquet');q=d[d.outcome.ne(1)].copy();y=q.outcome.eq(2).to_numpy()
        timecol=next(c for c in ['time_start','timestamp','time','event_time'] if c in q.columns)
        clock=pd.DatetimeIndex(pd.to_datetime(q[timecol],utc=True)).as_unit('ns').asi8
        _,bi=np.unique(clock//pd.Timedelta(days=7).value,return_inverse=True);blocks=int(bi.max()+1)
        weights=np.random.default_rng(41).multinomial(blocks,np.full(blocks,1/blocks),size=2000)
        for name,color,label in zip(names,colors,labels):
            p=(q[f'p_{name}_2']/(q[f'p_{name}_0']+q[f'p_{name}_2'])).to_numpy()
            fpr,tpr,_=roc_curve(y,p);au=roc_auc_score(y,p)
            ax.plot(fpr,tpr,color=color,lw=1.6,label=label)
            curves.extend(dict(turbine=turb,representation=name,fpr=x,tpr=z,auroc=au,events=len(q)) for x,z in zip(fpr,tpr))
            for j,w in enumerate(weights):
                sw=w[bi]
                if sw[y].sum() and sw[~y].sum():draws.append(dict(turbine=turb,representation=name,draw=j,auroc=roc_auc_score(y,p,sample_weight=sw),blocks=blocks,events=len(q)))
        ax.plot([0,1],[0,1],color='#ADB6C0',lw=.8,ls='--');ax.set(xlim=(0,1),ylim=(0,1.02),xticks=[0,.5,1],yticks=[0,.5,1],xlabel='False-positive rate',title=f'{turb} · n = {len(q)}')
    axs[0].set_ylabel('True-positive rate');fig.legend(*axs[0].get_legend_handles_labels(),loc='lower center',bbox_to_anchor=(.5,.02),ncol=3,frameon=False,columnspacing=.9,handlelength=1.7)
    pd.DataFrame(curves).to_csv(OUT/'fig09_lidar_roc.csv',index=False);pd.DataFrame(draws).to_csv(OUT/'fig10_lidar_bootstrap.csv',index=False)
    save(fig,'fig09_lidar_roc','9+10',[str(folder.relative_to(ROOT))],
        'Independent LiDAR direction discrimination after chronological calibration. T11 and T07 occupy the left and right panels, with 705 and 285 measured increase/decrease events. Small-net-change observations are retained in the separate three-class score. Both instruments use the same representation colors and axes.',panels=[('a',axs[0]),('b',axs[1])])
    # Real bootstrap samples, not violin shapes inferred from confidence bounds.
    boot=pd.DataFrame(draws);sm=pd.read_csv(ROOT/'outputs/protocol_benchmark_v19/smarteole/scores/physical_scores.csv')
    fig,(a,b)=plt.subplots(2,1,figsize=(6.5,6.45));fig.subplots_adjust(left=.14,right=.98,top=.93,bottom=.13,hspace=.62)
    pos=[];strings=[]
    for t,turb in enumerate(['T11','T07']):
        for j,(name,color,label) in enumerate(zip(names,colors,labels)):
            x=t*4+j;v=boot[(boot.turbine==turb)&(boot.representation==name)].auroc.to_numpy()
            artist=a.violinplot(v,positions=[x],widths=.7,showextrema=False)
            artist['bodies'][0].set(facecolor=color,edgecolor=color,alpha=.33)
            lo,med,hi=np.quantile(v,[.025,.5,.975]);a.plot([x,x],[lo,hi],c=color,lw=1.4);a.scatter(x,med,c=color,s=23,zorder=3)
            pos.append(x);strings.append(['GAF','+ bit','Scalars'][j])
        a.text(t*4+1,1.08,turb,ha='center',fontsize=11,fontweight='bold')
    a.set(xticks=pos,xticklabels=strings,ylim=(.15,1.15),yticks=[.2,.4,.6,.8,1],ylabel='Directional AUROC',title='a  LiDAR: 2,000 seven-day block resamples')
    a.axhline(.5,ls='--',lw=.7,color='#ADB6C0');axis(a)
    for rep in ['raw25','gaf_pca6','gaf_bit6']:
        q=sm[sm.representation.eq(rep)].sort_values('turbine');b.plot(range(7),q.direction_auroc,color=COL[rep],marker='o',ms=4,lw=1.4,label=LABEL[rep])
    b.set(xticks=range(7),xticklabels=[f'SMV{i}' for i in range(1,8)],ylim=(.82,.96),yticks=[.84,.88,.92,.96],ylabel='Directional AUROC',title='b  SMARTEOLE: frozen WindCube transfer')
    axis(b);b.legend(loc='upper center',bbox_to_anchor=(.5,-.20),ncol=3,frameon=False,handlelength=1.5,columnspacing=.8)
    sm.to_csv(OUT/'fig10_smarteole_physical.csv',index=False)
    save(fig,'fig10_external_validation',11,['LiDAR chronological predictions; SMARTEOLE physical_scores.csv'],
        'External physical validation across two instrumented fields. Top: empirical directional-AUROC distributions from 2,000 resamples of four occupied seven-day blocks per Hill instrument; bars show percentile intervals and dots medians. Bottom: seven turbine responses paired with the same SMARTEOLE WindCube reference, with scalar controls shared across representations. SMARTEOLE structural agreement has a raw25 median of 1.000 across 77 high-support rows, of which 45 equal 1.000; pair-weighted ARI is 0.964 and all-row pair-weighted ARI is 0.887. Structural row distributions are supplied separately.',panels=[('a',a),('b',b)])
    structure=pd.read_csv(ROOT/'outputs/protocol_benchmark_v19/smarteole/scores/structure_scores.csv')
    structure=structure[structure.pairs.ge(100)&structure.informative]
    fig,ax=plt.subplots(figsize=(6.5,2.9));fig.subplots_adjust(left=.13,right=.98,bottom=.22,top=.93)
    for j,rep in enumerate(['raw25','gaf_pca6','gaf_bit6','statistics9']):
        v=structure[structure.representation.eq(rep)].ari.to_numpy();a=ax.violinplot(v,positions=[j],widths=.65,showextrema=False)
        a['bodies'][0].set(facecolor=COL[rep],edgecolor=COL[rep],alpha=.35);ax.scatter(np.full(len(v),j)+np.random.default_rng(41).uniform(-.1,.1,len(v)),v,color=COL[rep],s=5,alpha=.5)
        ax.text(j,1.08,f'{np.median(v):.3f}',ha='center',fontsize=10)
    ax.set(xticks=range(4),xticklabels=['Raw25','GAF/PCA6','GAF + bit','Statistics9'],ylabel='Matched-event ARI',ylim=(-.05,1.17));axis(ax)
    structure.to_csv(OUT/'supp_smarteole_structure.csv',index=False)
    save(fig,'supp_smarteole_structure','11 supplement',['SMARTEOLE structure_scores.csv'],
        'Distribution over supported turbine-by-configuration rows. Each representation has 77 rows. Forty-five raw25 rows attain ARI 1.000; its median is 1.000, supported pair-weighted ARI 0.964 and all-row pair-weighted ARI 0.887. Density illustrates protocol variation, not independent-sample uncertainty.')

def economics():
    d=pd.read_csv(ROOT/'outputs/protocol_benchmark_v20/economics/selected_test_scores.csv')
    names=['persistence','selected_weather','selected_weather_events','predicted_ramp_historical_events']
    labs=['Persistence','Weather','Weather + events','Legacy event mixture'];colors=['#536474','#19836A','#A33378','#BE8533']
    fig,(a,b)=plt.subplots(1,2,figsize=(6.5,3.45),gridspec_kw={'width_ratios':[1,1.08]});fig.subplots_adjust(left=.16,right=.98,top=.82,bottom=.22,wspace=.32)
    for name,label,c in zip(names,labs,colors):
        q=d[d.model.eq(name)].sort_values('horizon_hours');a.plot(q.horizon_hours,q.nmae*100,'o-',color=c,label=label,ms=5,lw=1.6)
        b.plot(q.horizon_hours,q.gross_debit_gbp/1000,'o-',color=c,label=label,ms=5,lw=1.6)
    a.set(title='a  Forecast error',ylabel='nMAE (%)');b.set(title='b  Price exposure',ylabel='Gross debits (£k)',xlabel='Forecast lead (h)')
    for ax in [a,b]:ax.set_xticks([1,2,4]);axis(ax)
    legend_labels=['Persistence','Weather','Weather + events','Legacy mixture']
    fig.legend(a.get_legend_handles_labels()[0],legend_labels,loc='upper center',bbox_to_anchor=(.5,1.0),ncol=4,frameon=False,columnspacing=.65,handlelength=1.2,fontsize=9)
    d.to_csv(OUT/'fig13_forecast_cost.csv',index=False)
    save(fig,'fig13_forecast_cost',14,['outputs/protocol_benchmark_v20/economics/selected_test_scores.csv'],
        'Forecast error and gross imbalance debits at 1-, 2- and 4-hour leads. Left and right panels use the same model colors and common eligible test targets within each horizon. Forecast candidates were selected on validation nMAE; the reused test calendar is exploratory. Both weather-only and persistence baselines accompany the event-aware forecast.',panels=[('a',a),('b',b)])
    d=pd.read_csv(ROOT/'outputs/protocol_benchmark_v22/economics/capability_frontier.csv');ci=pd.read_csv(ROOT/'outputs/protocol_benchmark_v22/economics/capability_intervals.csv')
    q=d[d.split.eq('test')&d.horizon_hours.eq(2)&d.model.isin(names[:3])]
    fig,(a,b)=plt.subplots(1,2,figsize=(6.5,3.45),gridspec_kw={'width_ratios':[1.08,1]});fig.subplots_adjust(left=.16,right=.98,top=.82,bottom=.22,wspace=.32)
    for name,label,c in zip(names[:3],labs[:3],colors[:3]):
        g=q[q.model.eq(name)].sort_values('power_fraction');a.plot(g.power_fraction*100,g.gross_after_gbp/1000,'o-',c=c,lw=1.6,label=label,ms=5)
        gain=g.signed_after_gbp-g.signed_before_gbp;b.plot(g.power_fraction*100,gain/1000,'o-',c=c,lw=1.6,ms=5)
    a.set(title='a  Gross debit',ylabel='Gross debits (£k)');b.set(title='b  Signed-cost change',ylabel='Cost change (£k)')
    fig.supxlabel('Battery power / farm capacity (%)',y=.045,fontsize=11)
    for ax in [a,b]:axis(ax);ax.set_xticks([0,5,10,20])
    fig.legend(*a.get_legend_handles_labels(),loc='upper center',bbox_to_anchor=(.55,1),ncol=3,frameon=False,columnspacing=.9,handlelength=1.5)
    q.to_csv(OUT/'fig14_storage.csv',index=False);ci.to_csv(OUT/'fig14_storage_intervals.csv',index=False)
    save(fig,'fig14_storage',15,['outputs/protocol_benchmark_v22/economics/'],
        'Physically feasible ex-post correction capability under observed single-price settlement over 58 complete test days. The benchmark observes the realised half-hour mean and applies a power- and SOC-constrained correction, including settlement of the actions required to restore daily terminal inventory; it is not an issue-time forecast gain. Left: gross debits after correction, with a separate baseline for each model schedule. Right: signed settlement cost change for each model-specific schedule; positive values indicate higher signed cost. The 20%-power event-aware case reduces gross debit by 27.1% while its signed cost increases, because settlement credits fall by more than debits.',panels=[('a',a),('b',b)])

def unchanged_resized():
    # Original event-localization table uses individual seed observations.
    p=OLD/'fig8_event_localization.csv'
    if p.exists():
        d=pd.read_csv(p);print('LOCALIZATION',d.columns.tolist(),flush=True)
    d=pd.read_csv(OLD/'fig6_ramp_cost_concentration.csv')
    fig,ax=plt.subplots(figsize=(6.5,2.8));fig.subplots_adjust(left=.12,right=.98,top=.76,bottom=.24)
    x=np.arange(len(d));ax.bar(x-.16,100*d.ramp_intervals/d.intervals,width=.29,color='#B6BEC6',label='Evaluated intervals')
    ax.bar(x+.16,100*d.ramp_gross_debit_share,width=.29,color=COL['gaf_bit6'],label='Gross debits')
    ax.set(xticks=x,xticklabels=[f'{h} h' for h in d.horizon_hours],ylabel='Share (%)',ylim=(0,82),xlabel='Forecast lead to interval start')
    ax.legend(loc='lower left',bbox_to_anchor=(0,1.02),ncol=2,frameon=False);axis(ax);d.to_csv(OUT/'fig12_ramp_exposure.csv',index=False)
    save(fig,'fig12_ramp_exposure',13,['manuscript/figures_v18/fig6_ramp_cost_concentration.csv'],
        'Large-ramp periods concentrate settlement debit exposure. Grey bars show the eligible interval share with at least 20% fleet-capacity change; magenta bars show their share of persistence gross debits on the same targets and observed prices.')

def localization():
    methods=['TimesNet','KAN-AD','TCN-AE','Transformer-AE']
    source=pd.read_csv(ROOT/'outputs/detection_benchmark_v9/protocol_ablation_metrics.csv')
    method_codes=dict(zip(methods,['timesnet','kanad','tcn_ae','transformer_ae']))
    stages={'Training q99':'default','Threshold calibrated':'threshold_only','Threshold + grouping':'full_protocol'}
    source=source[source.split.eq('test')&source.model.isin(method_codes.values())]
    values={m:{name:source[source.model.eq(code)&source.policy.eq(policy)].sort_values('seed').f1.to_numpy() for name,policy in stages.items()} for m,code in method_codes.items()}
    assert len(source)==36 and all(len(v)==3 for a in values.values() for v in a.values())
    labels=list(values[methods[0]]);colors=['#90A8B5','#DF9844','#39738E']
    rows=[]
    for method in methods:
        for label in labels:
            seeds=source[source.model.eq(method_codes[method])&source.policy.eq(stages[label])].sort_values('seed').seed
            for seed,val in zip(seeds,values[method][label]):rows.append(dict(model=method,stage=label,seed=int(seed),f1=val))
    out=pd.DataFrame(rows);out.to_csv(OUT/'fig11_localization.csv',index=False)
    fig,(a,b)=plt.subplots(2,1,figsize=(6.5,6.25),gridspec_kw={'height_ratios':[1.15,1]});fig.subplots_adjust(left=.15,right=.98,top=.90,bottom=.14,hspace=.56)
    for i,method in enumerate(methods):
        for j,label in enumerate(labels):
            v=np.asarray(values[method][label]);x=i*4+j
            if np.ptp(v)>1e-10:
                vp=a.violinplot(v,positions=[x],widths=.72,showextrema=False)
                vp['bodies'][0].set(facecolor=colors[j],edgecolor=colors[j],alpha=.38)
            a.scatter(np.full(3,x)+np.linspace(-.10,.10,3),v,color=colors[j],s=17,zorder=3,edgecolor='white',lw=.4)
            a.plot([x,x],[v.min(),v.max()],color=colors[j],lw=1.3,zorder=2)
    a.set(xticks=[1,5,9,13],xticklabels=methods,ylabel='Event-level F1 (IoU ≥ 0.3)',ylim=(0,.85),title='a  Seed-level localization distributions')
    a.grid(axis='y',color='#E1E6EA',lw=.6)
    for j,label in enumerate(labels):
        med=[np.median(values[m][label]) for m in methods];q1=[np.min(values[m][label]) for m in methods];q3=[np.max(values[m][label]) for m in methods]
        b.errorbar(np.arange(4)+(j-1)*.18,med,yerr=[np.array(med)-q1,np.array(q3)-med],fmt='o-',color=colors[j],lw=1.5,ms=4,capsize=3,label=label)
    b.set(xticks=range(4),xticklabels=methods,ylabel='F1 range across three seeds',ylim=(0,.85),title='b  From scores to event intervals')
    b.grid(axis='y',color='#E1E6EA',lw=.6)
    fig.legend(*b.get_legend_handles_labels(),frameon=False,loc='upper center',ncol=3,fontsize=9)
    save(fig,'fig11_localization',11,['outputs/detection_benchmark_v9/protocol_ablation_metrics.csv'],
        'Event-level localization after score calibration and interval grouping. The upper panel shows the three archived seed values as a compact violin and point distribution; the lower panel compares the corresponding median and min–max range across seeds. The grouping rule is evaluated at a fixed IoU threshold, so it measures the complete score-to-interval interface rather than the anomaly score alone.',panels=[('a',a),('b',b)])

def main():
    # Figure 1 is exported from the authoritative draw.io file by the build
    # pipeline. Re-running result plots must never replace it with overview().
    detection();compression();structural();sampling();conditional();paths();lidar();localization();economics();unchanged_resized()
    (OUT/'manifest.json').write_text(json.dumps(MAN,indent=2,ensure_ascii=False),encoding='utf-8')
    print('generated',len(MAN),'figures',flush=True)

if __name__=='__main__':main()
