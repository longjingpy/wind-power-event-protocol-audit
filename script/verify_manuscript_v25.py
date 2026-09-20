"""Validate the v25 source distinctions, result tables and actual PDF assets."""
from pathlib import Path
import json,re
import numpy as np
import pandas as pd
import pymupdf as fitz
ROOT=Path(__file__).resolve().parents[1];DOC=ROOT/'manuscript/applied_energy'
OUT=ROOT/'temp/v25_pdf_review';OUT.mkdir(parents=True,exist_ok=True)
body=(DOC/'manuscript_body.md').read_text()
supp=(DOC/'supplementary_complete.md').read_text();methods=(DOC/'supplementary_methods.md').read_text()
abstract=body.split('## Abstract')[1].split('## 1. Introduction')[0].strip()
assert abstract==json.loads((DOC/'frontmatter.json').read_text())['abstract']
assert 150<=len(abstract.split())<=200 and 'among matched, encodable events' in abstract
assert supp.startswith(methods.rstrip())
assert 'seven AI review sessions' in body and 'ten human respondents' in supp
assert len(re.findall(r'^### Table S\d+\.',supp,re.M))==75
assert '17,557' not in body and '18.22%' in body
assert 'alpha is 0.528' not in body
assert all(t in supp for t in ['0.958','0.707','0.741','S24.','S25.'])
tables=ROOT/'outputs/protocol_benchmark_v25'
scores=pd.read_csv(tables/'polarity/all_scores.csv')
assert len(scores)==8*13*3*3
for _,g in scores.groupby('dataset'):assert g.events.nunique()==1 and g.direction_events.nunique()==1
alpha=pd.read_csv(tables/'ai_reference/agreement_intervals.csv')
human=alpha[alpha.population.eq('human3')&alpha.block_days.eq(7)].set_index('field').alpha
np.testing.assert_allclose(human.loc[['event_presence','morphology']],[.5278970819456374,.4761146496815287],atol=1e-12)
allvotes=pd.read_csv(tables/'ai_reference/ratings_with_source.csv')
assert allvotes.groupby('source_type').size().to_dict()=={'AI':2240,'human':960}
reports=[]
for name,text,build in [('main',body,'v19_manuscript_build'),('supplementary',supp,'v19_supplementary_build')]:
    pdf=fitz.open(DOC/f'{name}.pdf');rendered=[]
    for relative in re.findall(r'!\[[^\]]*\]\((figures_v\d+/[^)]+)\)',text):
        source=ROOT/'manuscript'/relative
        assert source.read_bytes()==(ROOT/'temp'/build/source.name).read_bytes()
    for i,page in enumerate(pdf):
        content=page.get_text()
        hits=['Scalar descriptors provide','scalar-controlled factorial','reviewer-triggered','S24.','S25.',
              'Table S65.','Table S66.','Table S67.','Table S68.','Table S69.','Table S70.','Table S71.','Table S72.','Table S73.',
              'AI-only presence','same seven-day','original structural protocol']
        if i==0 or any(word in content for word in hits):
            page.get_pixmap(dpi=115).save(OUT/f'{name}_{i+1:02d}.png');rendered.append(i+1)
    log=(ROOT/'temp'/build/f'{name}.log').read_text(errors='replace')
    assert not re.search(r'There were undefined references|Citation .* undefined|Float too large',log)
    boxes=[float(x) for x in re.findall(r'Overfull \\hbox \(([0-9.]+)pt',log)]
    reports.append({'document':name,'pages':len(pdf),'review_pages':rendered,'max_overfull_pt':max(boxes,default=0)})
record={'status':'CONTENT_AND_ASSET_CHECKS_PASS_VISUAL_PENDING','abstract_words':len(abstract.split()),'documents':reports,
        'AI_sessions':7,'human_observers':3,'total_votes':3200,'source_feature_evaluations':104}
(OUT/'report.json').write_text(json.dumps(record,indent=2))
print(json.dumps(record,indent=2))
