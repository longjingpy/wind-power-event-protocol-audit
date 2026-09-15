"""Independent public-schema, relative-clock and archive-membership audit."""
from pathlib import Path
import json
import re
import zipfile
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "outputs/processed_public_v17"


def main():
    meta = json.loads((BASE / "metadata.json").read_text())
    index = pd.read_csv(BASE / "file_index.csv")
    assert len(index) == 333 and index.rows.sum() == meta["rows"]
    assert not index.duplicated(["site_id", "turbine_id"]).any()
    total = 0
    for row in index.itertuples():
        assert re.fullmatch(r"WF\d{2}", row.site_id) and re.fullmatch(r"T\d{3}", row.turbine_id)
        path = BASE / row.file
        assert path.resolve().is_relative_to(BASE.resolve())
        table = pd.read_parquet(path)
        assert list(table.columns) == meta["columns"]
        assert len(table) == row.rows and table.site_id.eq(row.site_id).all() and table.turbine_id.eq(row.turbine_id).all()
        assert not any(pd.api.types.is_datetime64_any_dtype(t) for t in table.dtypes)
        assert np.diff(table.time_index).min() == 1 and np.diff(table.time_index).max() == 1
        first, last = table.time_index.iloc[0], table.time_index.iloc[-1]
        expected = np.where(table.time_index < first + .6 * (last-first), "train",
                            np.where(table.time_index < first + .8 * (last-first), "validation", "test"))
        assert np.array_equal(table.split, expected)
        assert np.isfinite(table.loc[table.power_valid, "power_norm"]).all()
        assert table.loc[~table.power_valid, "power_norm"].isna().all()
        assert table.loc[table.wind_valid, "wind_speed_ms"].between(0, 60).all()
        assert table.loc[~table.wind_valid, "wind_speed_ms"].isna().all()
        pandas_meta = json.loads(pq.ParquetFile(path).metadata.metadata[b"pandas"])
        assert pandas_meta["index_columns"] == []
        total += len(table)
    with zipfile.ZipFile(ROOT / "outputs/processed_scada_v17.zip") as archive:
        assert archive.testzip() is None
        parquet_members = {name for name in archive.namelist() if name.endswith(".parquet")}
        assert parquet_members == set(index.file)
        assert not any("private" in name or "raw" in name or "mapping" in name for name in archive.namelist())
        assert len(archive.namelist()) == 338
    report = {"status": "PASS_PROCESSED_RELEASE_AUDIT", "turbines": len(index), "rows": total,
              "checks": ["schema whitelist", "relative indices", "chronological splits", "numeric validity",
                         "no hidden timestamp index", "no private map in archive", "all archive CRCs"],
              "limitation": "pseudonymization removes direct fields; it cannot recall old downloads or guarantee non-reidentification"}
    (ROOT / "outputs/processed_public_v17_verification.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
