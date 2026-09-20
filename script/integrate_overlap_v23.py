"""Integrate the completed overlap experiment into the existing supplement."""
from pathlib import Path
import json,re
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1];DOC=ROOT/'manuscript/applied_energy'
OUT=ROOT/'outputs/protocol_benchmark_v23/many_to_many'

def main():
    d=pd.read_csv(OUT/'site_summary.csv');pairs=pd.read_csv(OUT/'configuration_pairs.csv')
    for col in ['left_coverage','right_coverage','component_mean_overlap']:assert d[col].between(0,1).all()
    assert (d[['one_to_one_components','one_to_many_components','many_to_one_components','many_to_many_components']].sum(axis=1)==d.components).all()
    assert len(d)==40 and len(pairs)==8*5*136
    by=d.pivot(index='site',columns='arm',values='edges')
    assert (by.hierarchy_iou30>=by.hierarchy_iou50).all() and (by.hierarchy_iou50>=by.hierarchy_iou70).all()
    primary=d[d.arm.eq('primitive_iou50')];hier=d[d.arm.eq('hierarchy_iou50')]
    assert (primary.left_coverage>=primary.one_to_one_left_coverage).all()
    verification=dict(status='PASS',populations=8,arms=5,configuration_rows=len(pairs),
        component_type_totals=True,coverage_bounds=True,edge_threshold_nesting=True,
        primitive_coverage_exceeds_or_equals_one_to_one=True,
        primary_non_one_to_one_range=primary.non_one_to_one_fraction.agg(['min','max']).tolist(),
        hierarchy_non_one_to_one_range=hier.non_one_to_one_fraction.agg(['min','max']).tolist())
    (OUT/'verification.json').write_text(json.dumps(verification,indent=2))
    low,high=100*hier.non_one_to_one_fraction.min(),100*hier.non_one_to_one_fraction.max()
    mainparagraph=(f'An overlap graph extends correspondence to event splitting and merging. At IoU ≥ 0.5, '
        f'{100*primary.non_one_to_one_fraction.min():.1f}–{100*primary.non_one_to_one_fraction.max():.1f}% of primitive-event overlap components contain more than one event on at least one side. '
        f'Including primitive and composite V/inverted-V intervals raises this share to {low:.1f}–{high:.1f}% across the seven archives and Hill 2021. '
        'This quantifies the additional correspondence revealed when a single compound change is represented as several detector intervals. '
        'One-to-one pairing supports event-level partition agreement, whereas the overlap graph preserves the split/merge composition of shared episodes (Supplementary Table S58 and Fig. S1).')
    body=(DOC/'manuscript_body.md').read_text(encoding='utf-8')
    anchor='### 2.2. Protocol perturbations identify a stable core and complementary geometry'
    if mainparagraph not in body:body=body.replace(anchor,anchor+'\n\n'+mainparagraph)
    method=(
        'The many-to-many extension builds a bipartite graph for each site, turbine, test split and configuration pair. All edges satisfying IoU ≥ 0.5 are retained, with 0.3/0.7 sensitivities. Connected components classify one-to-one, one-to-many, many-to-one and many-to-many correspondence. A primitive-only arm keeps the original event population; a hierarchy-inclusive arm allows primitive intervals to correspond to composite V/inverted-V episodes. Coverage counts unique connected nodes on each side, never edge multiplicity. Each component receives one vote when comparing label composition: if p_a and p_b are its four-class frequency vectors, composition overlap is sum_j min(p_aj,p_bj). This descriptive score preserves mixture proportions, while within-component temporal order is represented by the stored intervals and turning points. It is distinct from ARI. A separate containment sensitivity uses intersection/minimum duration ≥ 0.5, allowing a short leg to belong to a longer episode. Components longer than four hours remain explicitly counted as linked measurement supports. Shared seven-day calendar blocks anchor each component at its earliest start; 2,000 draws quantify conditional temporal variation. Per-event predictions use the frozen Pizhou raw25 k=4 seed-41 model.')
    label='### 4.4. Representations, clustering and information preservation'
    weighting=('Configuration names fix the left/right order lexicographically. A supported component pair contains at least 100 connected components; this count is descriptive and does not filter the all-configuration site summary. Site composition scores and topology proportions weight components equally across all 136 configuration pairs. Pooled coverage divides total unique connected nodes by total eligible nodes across those comparisons; an event can contribute once within each comparison. The main one-to-one coverage table instead averages the 136 configuration-specific fractions equally. An exact count reconciliation confirms identical primitive populations and one-to-one matches under both summaries (coverage_aggregation_reconciliation.csv).')
    method=method+'\n\n'+weighting
    pattern=r'The many-to-many extension builds a bipartite graph.*?(?=### 4\.4\.)'
    if re.search(pattern,body,flags=re.S):body=re.sub(pattern,lambda m:method+'\n\n',body,flags=re.S)
    else:body=body.replace(label,method+'\n\n'+label)
    # Correct the meaning of a median versus rows exactly attaining one.
    body=body.replace('The raw25 median is 1.000 on 45 of 77 high-support rows;',
        'Across 77 high-support rows, the raw25 median is 1.000 and 45 rows equal 1.000;')
    body=body.replace('contributes about 0.225% of the six-dimensional PCA variance',
        'has a variance share bounded above by approximately 0.225% in the six-dimensional encoding')
    (DOC/'manuscript_body.md').write_text(body,encoding='utf-8')
    methods=(DOC/'supplementary_methods.md').read_text(encoding='utf-8')
    heading='## S21. Many-to-many correspondence and hierarchy'
    if heading in methods:methods=methods[:methods.index(heading)].rstrip()
    methods=methods.rstrip()+'\n\n'+heading+'\n\n'+method+'\n'
    (DOC/'supplementary_methods.md').write_text(methods,encoding='utf-8')
    full=(DOC/'supplementary_complete.md').read_text(encoding='utf-8');tables=full[full.index('## Supplementary result tables'):]
    if '### Table S58.' in tables:tables=tables[:tables.index('### Table S58.')].rstrip()
    rows=['### Table S58. Many-to-many correspondence at IoU 0.5','',
          'The hierarchy-inclusive graph contains primitive and composite intervals. A split/merge component has more than one node on at least one side. Coverage pools unique connected nodes over eligible nodes across all configuration pairs. Component counts are summed over configuration pairs, not unique independent weather episodes. Full IoU 0.3/0.5/0.7 and containment configuration tables accompany this summary. The local component ledger retains individual interval clocks.','',
          '| Population | Components | Split/merge (%) | Both sides multiple (%) | Mixed hierarchy (%) | Left/right coverage (%) |',
          '|:--|--:|--:|--:|--:|--:|']
    for r in hier.itertuples():rows.append(f'| {r.site} | {r.components:,} | {r.non_one_to_one_fraction*100:.1f} | {r.many_to_many_components/r.components*100:.1f} | {r.mixed_level_components/r.components*100:.1f} | {r.left_coverage*100:.1f}/{r.right_coverage*100:.1f} |')
    rows+=['','### Figure S1. Split and merge structure in the overlap graph','',
        '![Primitive and hierarchy-inclusive correspondence at IoU 0.5. Each segment gives the fraction of overlap components with one-to-one, one-to-many, many-to-one or many-to-many topology. All 136 configuration pairs are retained in each population.](figures_v23/supp_overlap_topology.pdf)','']
    (DOC/'supplementary_complete.md').write_text(methods.rstrip()+'\n\n'+tables+'\n\n'+'\n'.join(rows),encoding='utf-8')
    figdir=ROOT/'manuscript/figures_v23';figdir.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'svg.fonttype':'none','pdf.fonttype':42,'axes.spines.top':False,'axes.spines.right':False})
    fig,axs=plt.subplots(1,2,figsize=(6.5,3.5),sharey=True);fig.subplots_adjust(left=.18,right=.98,top=.83,bottom=.2,wspace=.2)
    cols=['one_to_one_components','one_to_many_components','many_to_one_components','many_to_many_components']
    for ax,(arm,title) in zip(axs,[('primitive_iou50','a  Primitive intervals'),('hierarchy_iou50','b  With V/peak episodes')]):
        q=d[d.arm.eq(arm)].sort_values('site');left=np.zeros(len(q))
        for col,color,name in zip(cols,['#CFDDE5','#89C1C0','#3E949B','#234E68'],['1:1','1:many','many:1','many:many']):
            values=q[col]/q.components;ax.barh(range(len(q)),values,left=left,color=color,label=name);left+=values
        ax.set(yticks=range(len(q)),yticklabels=q.site,xlim=(0,1),xlabel='Fraction of overlap components',title=title)
    axs[0].invert_yaxis();fig.legend(*axs[0].get_legend_handles_labels(),ncol=4,loc='upper center',frameon=False)
    for ext in ['pdf','svg','png']:fig.savefig(figdir/f'supp_overlap_topology.{ext}',dpi=230)
    d.to_csv(figdir/'supp_overlap_topology.csv',index=False)
    print(json.dumps(verification,indent=2))

if __name__=='__main__':main()
