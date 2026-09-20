"""Render the authoritative editable workflow with installed draw.io.

Uses native draw.io CLI exports and waits for new artifacts before returning.
The actual app is at its installed vendor location. No UI automation or
alternative schematic can overwrite the exported figure during plot builds.
"""
from pathlib import Path
import os,time,subprocess,shutil,json
ROOT=Path(__file__).resolve().parents[1]
EXE=Path('D:/Program Files/draw.io/draw.io.exe')
SOURCE=ROOT/'manuscript/figures_v22/fig01_workflow.drawio'
OUT=SOURCE.parent
TMP=ROOT/'temp/drawio_v23';TMP.mkdir(parents=True,exist_ok=True)
def main():
    records=[]
    for ext in ['svg','png','pdf']:
        path=TMP/f'fig01_{time.time_ns()}.{ext}'
        cmd=[str(EXE),'--export','--format',ext,'--theme','light','--border','8','--output',str(path),str(SOURCE)]
        if ext=='pdf':cmd.insert(1,'--crop')
        if ext=='svg':cmd[1:1]=['--embed-svg-fonts','false']
        res=subprocess.run(cmd,capture_output=True,text=True,timeout=50)
        for _ in range(40):
            if path.exists() and path.stat().st_size>1000:break
            time.sleep(.25)
        if not path.exists():raise RuntimeError(f'draw.io export missing: {ext}; {res.stdout} {res.stderr}')
        shutil.copy2(path,OUT/f'fig01_workflow.{ext}');records.append(dict(format=ext,bytes=path.stat().st_size,native_export=True))
        print(ext,path.stat().st_size,flush=True)
    (OUT/'drawio_export_verification.json').write_text(json.dumps(dict(source=str(SOURCE),exports=records),indent=2))
if __name__=='__main__':main()
