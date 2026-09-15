"""Structural manuscript checks; numerical claims need independent experiment audits."""
from pathlib import Path
import re,json
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"manuscript/applied_energy"
def main():
    bibliography=(BASE/"references.bib").read_text()
    entries=re.findall(r"@(\w+)\s*\{\s*([^,]+),",bibliography)
    keys=[key for _,key in entries]
    assert len(keys)==len(set(keys))
    text=(BASE/"manuscript_body.md").read_text()+"\n"+(BASE/"supplementary_methods.md").read_text()
    citations=set(re.findall(r"@([A-Za-z0-9_-]+)",text))
    assert not citations-set(keys),citations-set(keys)
    papers={key for kind,key in entries if kind.lower() in ["article","inproceedings"]}|{"wang2015gaf"}
    assert len(citations&papers)>=35,len(citations&papers)
    manifest=json.loads((BASE/"supplementary_table_manifest.json").read_text())
    assert {item["table"] for item in manifest}==set(range(1,33))
    assert all(item["rows"]>0 for item in manifest)
    result={"references":len(keys),"cited_references":len(citations),"cited_papers":len(citations&papers),
            "supplementary_tables":len(manifest),"status":"STRUCTURAL_CHECK_PASS"}
    (ROOT/"temp/v14_manuscript_checks.json").write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))
if __name__=="__main__":main()
