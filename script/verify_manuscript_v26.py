"""Check v26 integration against completed results and render changed PDF pages."""
from pathlib import Path
import json
import re
import numpy as np
import pandas as pd
import pymupdf as fitz

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "manuscript/applied_energy"
RESULTS = ROOT / "outputs/protocol_benchmark_v26"
OUT = ROOT / "temp/v26_pdf_review"
OUT.mkdir(parents=True, exist_ok=True)
body = (DOC / "manuscript_body.md").read_text()
supp = (DOC / "supplementary_complete.md").read_text()
methods = (DOC / "supplementary_methods.md").read_text()
abstract = body.split("## Abstract")[1].split("## 1. Introduction")[0].strip()
front = json.loads((DOC / "frontmatter.json").read_text())
assert abstract == front["abstract"]
assert 150 <= len(abstract.split()) <= 200
assert "among matched, encodable events" in abstract
assert supp.startswith(methods.rstrip())
assert len(re.findall(r"^### Table S\d+\.", supp, re.M)) == 84
assert len(re.findall(r"^## S\d+\.", methods, re.M)) == 26
assert "### 2.8. Linking" in body and "Section 2.8" in body
assert "#### Complete wind-process reconstruction" in body
assert all(("Table " + str(n) + ".") in body for n in range(1, 5))
assert "figures_v26/fig10_physical_process.pdf" in body
assert "figures_v26/fig07_polarity_mechanism.pdf" in body
assert "18.22%" in body and "seven AI review sessions" in body
assert "ten human respondents" in supp
assert not any(ord(c) < 32 and c not in "\n\t" for c in body + supp)
h = pd.read_csv(RESULTS / "hierarchy_intervals.csv")
p = pd.read_csv(RESULTS / "primary_intervals.csv")
for source, compound, geometry in [("lidar_T11", 11.665010, 11.087592),
                                  ("lidar_T07", 24.450824, 26.944770),
                                  ("smarteole", 5.809471, 9.583636)]:
    a = h[(h.source == source) & (h.block_days == 7) &
          (h.population == "composite") & (h.task == "mse")].iloc[0]
    b = p[(p.source == source) & (p.block_days == 7) &
          (p.comparison == "same_resolution_geometry")].iloc[0]
    np.testing.assert_allclose([a.gain_pct_or_pp, b.relative_rmse_reduction_pct],
                               [compound, geometry], atol=1e-5)
    for value in [a.gain_pct_or_pp, a.low, a.high, b.relative_rmse_reduction_pct, b.low, b.high]:
        assert f"{value:.2f}" in body.replace("−", "-"), (source, value)
    assert a.occupied_farm_blocks == 4 and b.occupied_blocks == 4
reports = []
for name, text, build in [("main", body, "v19_manuscript_build"),
                          ("supplementary", supp, "v19_supplementary_build")]:
    pdf = fitz.open(DOC / f"{name}.pdf")
    rendered = []
    for relative in re.findall(r"!\[[^\]]*\]\((figures_v\d+/[^)]+)\)", text):
        source = ROOT / "manuscript" / relative
        assert source.read_bytes() == (ROOT / "temp" / build / source.name).read_bytes()
    hits = ["Ordered trajectories recover", "Scale-restored ordered", "Here n counts",
            "Duration alone", "Complete wind-process", "S26.", "Table S75.",
            "Table S76.", "Table S77.", "Table S78.", "Table S79.", "Table S80.",
            "Decoder selection", "Paired uncertainty", "Reproduction and result",
            "This study establishes", "Limitations and scope", "v18–v26",
            "Table S81.", "Table S82.", "Table S83.", "leave_out_1"]
    for i, page in enumerate(pdf):
        content = page.get_text()
        if i == 0 or any(s in content for s in hits):
            page.get_pixmap(dpi=115).save(OUT / f"{name}_{i+1:02d}.png")
            rendered.append(i+1)
    extracted = "\n".join(page.get_text() for page in pdf)
    assert "??" not in extracted
    log = (ROOT / "temp" / build / f"{name}.log").read_text(errors="replace")
    assert not re.search(r"There were undefined references|Citation .* undefined|Float too large", log)
    assert "Missing character:" not in log
    boxes = [float(x) for x in re.findall(r"Overfull \\hbox \(([0-9.]+)pt", log)]
    assert max(boxes, default=0) < 1, (name, max(boxes, default=0))
    assert max(boxes, default=0) < 1, (name, boxes)
    reports.append({"document": name, "pages": len(pdf), "review_pages": rendered,
                    "max_overfull_pt": max(boxes, default=0)})
record = {"status": "CONTENT_ASSETS_PASS_VISUAL_PENDING",
          "abstract_words": len(abstract.split()), "supplementary_tables": 84,
          "supplementary_methods": 26, "main_figures": 13, "documents": reports}
(OUT / "report.json").write_text(json.dumps(record, indent=2))
print(json.dumps(record, indent=2))
