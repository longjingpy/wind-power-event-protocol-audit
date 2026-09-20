"""Check the integrated claims, SI preservation and embedded v24 figures."""
from pathlib import Path
import json,re
import pymupdf as fitz
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
DOC=ROOT/'manuscript/applied_energy';OUT=ROOT/'temp/v24_pdf_review'
OUT.mkdir(parents=True,exist_ok=True)
body=(DOC/'manuscript_body.md').read_text(encoding='utf-8')
suptext=(DOC/'supplementary_complete.md').read_text(encoding='utf-8')
methods=(DOC/'supplementary_methods.md').read_text(encoding='utf-8')
abstract=body.split('## Abstract')[1].split('## 1. Introduction')[0].strip()
assert abstract==json.loads((DOC/'frontmatter.json').read_text())['abstract']
assert 150<=len(abstract.split())<=200
assert suptext.startswith(methods.rstrip())
assert '71,075' not in body and '71,075' in suptext
assert 'zero incremental storage' not in body and 'selects zero additional storage' in suptext
assert '27,109.50' in body and '-26,310.43' in suptext
assert 'Scalar + weather' in body and 'nMAE-selected reference' in body
assert r'\sum_{t\in\mathcal T_h}' in body and r'\widehat P_t' in body
assert r'\arg\max_a' in suptext
assert '\t' not in body
assert set(map(int,re.findall(r'^### Table S(\d+)\.',suptext,re.M)))==set(range(65))
figs=re.findall(r'!\[[^\]]*\]\((figures_v\d+/[^)]+)\)',body)
plain=re.sub(r'!\[[^\]]*\]\([^)]+\)','',body)
assert len(figs)==13
assert all(re.search(r'(?:Fig\.|Figure)\s+'+str(n)+r'\b',plain) for n in range(1,len(figs)+1))
assert not re.search('not yet been pushed|not yet published',body)
records=[];review_pages=[]
for name,source,build in [('main',body,'v19_manuscript_build'),('supplementary',suptext,'v19_supplementary_build')]:
    pdf=fitz.open(DOC/f'{name}.pdf')
    for relative in re.findall(r'!\[[^\]]*\]\((figures_v\d+/[^)]+)\)',source):
        original=ROOT/'manuscript'/relative
        assert original.read_bytes()==(ROOT/'temp'/build/original.name).read_bytes(),relative
    for i,page in enumerate(pdf):
        text=page.get_text()
        interesting=(name=='main' and (i==0 or any(t in text for t in ['2.7.','Figure 12:', 'Figure 13:', '27,109.50','Jiangsu calculation','97% at 15','Acknowledgements']))) or (name=='supplementary' and any(t in text for t in ['S22. Native','S23. British','Table S59.', 'Table S60.','Table S61.','Table S62.','Table S63.','Table S64.','Figure S2:', 'Figure S3:', 'Figure S4:']))
        if interesting:
            page.get_pixmap(dpi=120).save(OUT/f'{name}_{i+1:02d}.png')
            review_pages.append(f'{name}:{i+1}')
    log=(ROOT/'temp'/build/(name+'.log')).read_text(encoding='utf-8',errors='replace')
    over=[float(x) for x in re.findall(r'Overfull \\hbox \(([0-9.]+)pt',log)]
    assert not re.search(r'Citation .* undefined|There were undefined references|Float too large',log)
    records.append({'document':name,'pages':len(pdf),'max_overfull_pt':max(over,default=0)})
daily=pd.read_csv(ROOT/'manuscript/figures_v24/fig12_policy_fees.csv')
primary=pd.read_csv(ROOT/'outputs/protocol_benchmark_v24/economics/primary_policy_results.csv')
for row in primary.itertuples():
    z=daily[daily.horizon_minutes.eq(row.horizon_minutes)]
    assert abs(z.persistence.sum()-row.baseline_fee_cny)<1e-6
    assert abs(z.shape_pipeline.sum()-row.pipeline_fee_cny)<1e-6
report={'status':'CONTENT_AND_ASSET_CHECKS_PASS_VISUAL_REVIEW_REQUIRED','abstract_words':len(abstract.split()),'main_figures':len(figs),'supplementary_tables':65,'documents':records,'review_pages':review_pages}
(OUT/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
