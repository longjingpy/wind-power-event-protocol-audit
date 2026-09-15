"""Package only the explicitly authorized wind-event study inputs."""
from pathlib import Path
import json,hashlib,zipfile
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"temp/data_release_v14"
def files(folder):
    return [p for p in (ROOT/folder).rglob("*") if p.is_file() and ".corrupt-" not in p.name and not p.name.startswith(".") and p.suffix not in [".log",".lock"]]
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    groups={
      "chinese_raw": files("data/whole-SCADA-data/wind_power/jiangsu/xuzhou/pizhou")
                    +files("data/whole-SCADA-data/wind_power/jiangsu/xuzhou/suining")
                    +files("data/whole-SCADA-data/wind_power/xinjiang/yandun")
                    +list((ROOT/"data/real").glob("HRPZ*.csv")),
      "analysis_inputs": files("data/event_clean_v2")+files("data/external_samples/hill_of_towie/clean_native")
                         +files("data/external_samples/greece_smd10towfgr/clean_native")
                         +files("data/external_samples/la_haute_borne")+files("data/external_public/sdwpf"),
      "weather": list((ROOT/"data/era5/raw").glob("*.nc"))
                 +list((ROOT/"data/era5_remote_subset_20260911").glob("*.nc"))
                 +files("data/ground_obs")
                 +[ROOT/"outputs/dynamic_events_v3/pizhou_surface_hourly.csv.gz"],
      "event_catalogue": [p for p in (ROOT/"outputs/dynamic_events_v6").glob("*") if p.is_file() and p.suffix in [".gz",".npy",".npz",".csv",".json"]]
                         +files("outputs/dynamic_events_v6/external_greece"),
      "human_labels": files("outputs/annotation_v9/submissions")+files("outputs/user_labels_v9")
    }
    manifest={"version":"v0.2.0","authorization":"User explicitly authorized all data in this wind-event study on 2026-09-15",
              "scope":"Seven wind farms, weather inputs, event catalogue and human labels; unrelated GNSS and personal attachments excluded",
              "external_licenses":"Original public-data licenses remain applicable; see source records",
              "groups":[]}
    for name,paths in groups.items():
        paths=sorted(set(paths))
        missing=[str(p) for p in paths if not p.exists()]
        assert not missing,missing
        target=OUT/f"{name}.zip"
        entries=[]
        with zipfile.ZipFile(target,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=3,allowZip64=True) as archive:
            for p in paths:
                rel=p.relative_to(ROOT).as_posix()
                assert "huawei" not in rel and "gnss" not in rel.lower(),rel
                archive.write(p,rel,compress_type=zipfile.ZIP_STORED if p.suffix in [".gz",".zip",".parquet"] else zipfile.ZIP_DEFLATED)
                entries.append({"path":rel,"bytes":p.stat().st_size})
        with zipfile.ZipFile(target) as archive:
            assert archive.testzip() is None
        with target.open("rb") as stream:digest=hashlib.file_digest(stream,"sha256").hexdigest()
        manifest["groups"].append({"asset":target.name,"bytes":target.stat().st_size,"sha256":digest,"files":entries})
        print(name,len(entries),target.stat().st_size,flush=True)
        (OUT/"data_manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
    print("PASS: all archives readable, selected-study scope validated")
if __name__=="__main__":main()
