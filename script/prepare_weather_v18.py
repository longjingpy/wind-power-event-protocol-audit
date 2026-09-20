"""Direct, bounded acquisition of independent weather and reserved Hill data.

NOAA ISD: Smith et al. (2011), doi:10.1175/2011BAMS3015.1, database and QC
sections. Download full records to retain quality flags and accumulation
periods. Hill of Towie v2.1: doi:10.5281/zenodo.22662930. New 2021 power is
reserved for a frozen temporal confirmation and is not evaluated here.
"""
from pathlib import Path
import argparse
from concurrent.futures import ThreadPoolExecutor
import gzip
import json
import math
import os
import subprocess
import zipfile
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/"outputs/protocol_benchmark_v18/weather"
DATA = ROOT/"data/weather_v18"
HILL = ROOT/"data/external_samples/hill_of_towie_v21"


def download(url, target, expected=None):
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and (expected is None or target.stat().st_size == expected):
        return {"url": url, "path": str(target.relative_to(ROOT)), "bytes": target.stat().st_size, "status": "PRESENT"}
    part = target.with_suffix(target.suffix+".part")
    transport = os.environ.get("WPF_DOWNLOAD_TRANSPORT", "requests")
    if transport == "windows-curl":
        windows_path = str(part) if os.name == "nt" else subprocess.check_output(["wslpath", "-w", str(part)], text=True).strip()
        executable = "curl.exe" if os.name == "nt" else "/mnt/c/Windows/System32/curl.exe"
        subprocess.run([executable, "--noproxy", "*", "--fail", "--location",
                        "--silent", "--show-error", "--connect-timeout", "20", "--retry", "2", "--retry-delay", "3",
                        "--max-time", "300", "--speed-limit", "1024", "--speed-time", "90", "--continue-at", "-", "--output", windows_path, url], check=True)
    elif transport == "requests":
        import requests
        session = requests.Session()
        session.trust_env = False
        offset = part.stat().st_size if part.exists() else 0
        headers = {"Range": f"bytes={offset}-"} if offset else {}
        with session.get(url, headers=headers, stream=True, timeout=(20, 90)) as response:
            response.raise_for_status()
            resume = offset > 0 and response.status_code == 206
            with part.open("ab" if resume else "wb") as handle:
                for chunk in response.iter_content(1024*1024):
                    if chunk:
                        handle.write(chunk)
    else:
        raise ValueError("Unknown download transport")
    if expected is not None and part.stat().st_size != expected:
        raise ValueError(f"Size mismatch for {target.name}: {part.stat().st_size} vs {expected}")
    if target.suffix == ".gz":
        with gzip.open(part, "rb") as handle:
            while handle.read(1024*1024):
                pass
    if target.suffix == ".zip":
        with zipfile.ZipFile(part) as archive:
            # Inventory only: reserved 2021 SCADA values remain unread.
            if not archive.namelist():
                raise ValueError("Empty archive")
    part.replace(target)
    return {"url": url, "path": str(target.relative_to(ROOT)), "bytes": target.stat().st_size, "status": "DOWNLOADED"}


def distance(lat, lon, lat2, lon2):
    p1, p2 = math.radians(lat), math.radians(lat2)
    dp, dl = p2-p1, math.radians(lon2-lon)
    return 6371*2*math.asin(min(1, math.sqrt(math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2)))


def noaa_jobs():
    path = DATA/"isd-history.csv"
    download("https://www.ncei.noaa.gov/pub/data/noaa/isd-history.csv", path)
    inventory = pd.read_csv(path, dtype={"USAF": str, "WBAN": str, "BEGIN": str, "END": str})
    inventory = inventory.dropna(subset=["LAT", "LON", "BEGIN", "END"])
    requests_list = [("pizhou_suining", "580270", "99999", year) for year in (2023, 2024, 2025)]
    requests_list += [("yandun", "522030", "99999", year) for year in (2023, 2024)]
    sites = [("lahaute", 48.7168, 5.56, [2014, 2015]), ("hill", 57.5, -3.086, [2020, 2021, 2026])]
    selection = []
    for site, lat, lon, years in sites:
        for year in years:
            candidates = inventory[(inventory.BEGIN <= f"{year}1231") & (inventory.END >= f"{year}0101")].copy()
            candidates["distance_km"] = [distance(lat, lon, a, b) for a, b in zip(candidates.LAT, candidates.LON)]
            candidates = candidates[candidates.distance_km <= 150].sort_values(["distance_km", "USAF", "WBAN"]).head(3)
            for row in candidates.to_dict("records"):
                selection.append({"site": site, "year": year, "site_latitude": lat, "site_longitude": lon, **row})
                requests_list.append((site, row["USAF"], row["WBAN"], year))
    pd.DataFrame(selection).to_csv(OUT/"ground_station_candidates.csv", index=False)
    jobs = []
    for site, usaf, wban, year in requests_list:
        name = f"{usaf}-{wban}-{year}.gz"
        jobs.append({"site": site, "year": year, "usaf": usaf, "wban": wban,
                     "url": f"https://www.ncei.noaa.gov/pub/data/noaa/{year}/{name}", "target": DATA/"noaa_isd"/name})
    return jobs


def hill_jobs(large=False):
    record_path = HILL/"source_record.json"
    download("https://zenodo.org/api/records/22662930", record_path)
    record = json.loads(record_path.read_text())
    desired = {"README.md", "CHANGELOG.md", "Hill_of_Towie_data_dictionary.md", "Hill_of_Towie_turbine_metadata.csv",
               "Hill_of_Towie_alarms_description.csv", "Hill_of_Towie_turbine_fields_description.csv",
               "Hill_of_Towie_AeroUp_install_dates.csv", "ZXMS-RES029-REP01-01.pdf", "ZXMS-RES035-REP01-01.pdf"}
    if large:
        desired |= {"2021.zip", "2026.zip", "lidar_data.zip", "Hill_of_Towie_ShutdownDuration.zip"}
    files = [item for item in record["files"] if item["key"] in desired]
    size = sum(item["size"] for item in files)
    if size > 5_000_000_000:
        raise ValueError(f"Hill subtask exceeds 5GB budget: {size}")
    if desired != {item["key"] for item in files}:
        raise ValueError("Requested file absent from official record")
    return [{"site": "hill", "url": "https://zenodo.org/records/22662930/files/"+item["key"], "target": HILL/item["key"], "expected": item["size"]}
            for item in files]


def run_job(job):
    details = {key: value for key, value in job.items() if key not in ("target", "expected")}
    try:
        result = download(job["url"], job["target"], job.get("expected"))
        print(result["status"], job["target"].name, result["bytes"], flush=True)
        return details | result
    except Exception as error:
        print("FAILED", job["target"].name, type(error).__name__, flush=True)
        return details | {"status": "FAILED", "error": str(error), "path": str(job["target"].relative_to(ROOT))}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--hill-large", action="store_true")
    parser.add_argument("--only", choices=["all", "noaa", "hill"], default="all")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    jobs, setup_errors = [], []
    for label, factory in [("noaa", noaa_jobs), ("hill", lambda: hill_jobs(args.hill_large))]:
        if args.only not in ("all", label):
            continue
        try:
            jobs.extend(factory())
        except Exception as error:
            setup_errors.append({"source": label, "error": str(error)})
    results = []
    with ThreadPoolExecutor(max_workers=3) as pool:
        for result in pool.map(run_job, jobs):
            results.append(result)
            (OUT/f"download_{args.only}.json").write_text(json.dumps({"results": results, "setup_errors": setup_errors,
                "network": "direct_no_proxy", "reserved_confirmation": "Hill 2021-01 to 2021-06, values not read"}, indent=2))
    final = {"results": results, "setup_errors": setup_errors, "network": "direct_no_proxy",
             "reserved_confirmation": "Hill 2021-01 to 2021-06, values not read"}
    (OUT/f"download_{args.only}.json").write_text(json.dumps(final, indent=2))
    print(json.dumps({"completed": sum(r["status"] != "FAILED" for r in results), "failed": sum(r["status"] == "FAILED" for r in results), "setup_errors": setup_errors}), flush=True)


if __name__ == "__main__":
    main()
