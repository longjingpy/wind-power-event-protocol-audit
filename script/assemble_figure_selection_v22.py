"""Build a clean numbered figure gallery for author selection."""
from pathlib import Path
import json,shutil
ROOT=Path(__file__).resolve().parents[1]; SRC=ROOT/'manuscript/figures_v22';OUT=ROOT/'manuscript/figure_selection_v22'
entries=[
('F01','workflow','fig01_workflow.pdf','Study route; recommended graphical abstract'),
('F02','detection','fig02_detection.pdf','Protocol boundaries without legend overlap'),
('F03','compression','fig03_compression.pdf','Raw/PCA6 full-precision equivalence; lower-right legend'),
('F04','structure','fig04_structure.pdf','Readable cross-archive ARI matrix'),
('F05','sampling','fig05_sampling.pdf','Six archive/grid comparisons with configuration distributions'),
('F06','conditional','fig06_conditional.pdf','Conditioned shared information'),
('F07','polarity_paths','fig07_polarity_paths.pdf','Polarity path construction'),
('F08','shared_gasf','fig08_shared_gasf.pdf','G(x)=G(-x) ambiguity'),
('F09','lidar_roc','fig09_lidar_roc.pdf','Paired T11/T07 ROC panels'),
('F10','external_validation','fig10_external_validation.pdf','LiDAR and SMARTEOLE violin/transfer panels'),
('F11','localization','fig11_localization.pdf','Seed-level localization distributions and grouping step'),
('F12','ramp_exposure','fig12_ramp_exposure.pdf','Ramp concentration'),
('F13','forecast_cost','fig13_forecast_cost.pdf','Forecast error and price exposure'),
('F14','storage','fig14_storage.pdf','Corrected storage capability and signed cost'),
]
OUT.mkdir(parents=True,exist_ok=True)
for no,name,src,note in entries:
    d=OUT/f'{no}_{name}';d.mkdir(parents=True,exist_ok=True)
    source=(SRC/src) if not src.startswith('..') else (ROOT/'manuscript'/src)
    for ext in ['pdf','svg','png','drawio']:
        p=source.with_suffix('.'+ext)
        if p.exists():shutil.copy2(p,d/p.name)
    for p in [source.with_suffix('.csv'),source.with_name(source.stem+'_caption.md')]:
        if p.exists():shutil.copy2(p,d/p.name)
    (d/'README.md').write_text(f'# {no} {name}\n\n{note}\n\nSource: {source.relative_to(ROOT)}\n',encoding='utf-8')
manifest=[dict(id=no,name=name,source=src,note=note) for no,name,src,note in entries]
(OUT/'figure_manifest_v22.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf-8')
(OUT/'INDEX.md').write_text('# Current figure selection (updated v23)\n\n'+ '\n'.join(f'- **{a}** {b}: {d}' for a,b,c,d in entries)+'\n\n'
'''F01 is the native draw.io export with editable event/overlap/encoding modules. F03 is compact; F04 uses luminance-aware text; F05 places support counts outside the data area. F08 has a square data axis. F09 uses left-right ROC panels. F10 and F11 have taller, separated vertical panels; F11 plots actual archived seeds. F13 and F14 use side-by-side panels. The supplementary split/merge graph is in manuscript/figures_v23/supp_overlap_topology.pdf. Historical method-only diagrams are excluded.\n''',encoding='utf-8')
print('gallery',OUT,'figures',len(entries))
