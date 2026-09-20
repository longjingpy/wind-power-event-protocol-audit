"""Inspect current embedded figures and render their actual manuscript pages."""
from pathlib import Path
import json,re,hashlib
import pymupdf as fitz
ROOT=Path(__file__).resolve().parents[1]
DOC=ROOT/'manuscript/applied_energy';OUT=ROOT/'temp/v23_pdf_review';OUT.mkdir(parents=True,exist_ok=True)
pdf=fitz.open(DOC/'main.pdf');body=(DOC/'manuscript_body.md').read_text(encoding='utf-8')
figs=re.findall(r'!\[[^\]]*\]\((figures_v\d+/[^)]+)\)',body)
records=[]
for n,p in enumerate(figs,1):
    matches=[(i,page) for i,page in enumerate(pdf) if re.search(r'Figure\s+'+str(n)+r'\s*:',page.get_text())]
    if len(matches)!=1:raise ValueError((n,len(matches)))
    i,page=matches[0]; words=len(page.get_text().split())
    standalone=DOC.parent/p;copied=ROOT/'temp/v19_manuscript_build'/standalone.name
    digest=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
    assert digest(standalone)==digest(copied),p
    records.append(dict(figure=n,page=i+1,page_words=words,source=p,source_equals_build=True))
    if n in [1,3,5,8,10,11,13,14]:page.get_pixmap(dpi=135).save(OUT/f'figure{n:02d}_page{i+1:02d}.png')
plain=re.sub(r'!\[[^\]]*\]\([^)]+\)','',body)
assert all(re.search(r'(?:Fig\.|Figure)\s+'+str(n)+r'\b',plain) for n in range(1,15))
assert not re.search('not yet been pushed|not yet published',body)
wordcount=len(body.split('## Abstract')[1].split('## 1. Introduction')[0].split())
report=dict(pages=len(pdf),abstract_words=wordcount,figures=records,all_figures_called_in_text=True,
            artifact_state='Rendered for visual inspection; not automatic aesthetic PASS')
for i,page in enumerate(pdf):
    text=page.get_text()
    if any(token in text for token in ['union duration','rank-one','experimental scheduled','study-defined symmetric']):
        page.get_pixmap(dpi=135).save(OUT/f'methods_page{i+1:02d}.png')
sup=fitz.open(DOC/'supplementary.pdf');suppages=[]
for i,page in enumerate(sup):
    text=page.get_text()
    if any(token in text for token in ['Table S57.', 'Table S58.', 'Figure S1:', 'signed settlement cost is']):
        page.get_pixmap(dpi=135).save(OUT/f'supp_page{i+1:02d}.png');suppages.append(i+1)
report['supplementary_review_pages']=suppages
(OUT/'report.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
