"""Check every primary event and eligible context against source-clock splits."""
from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "outputs/dynamic_events_v6"
OUT = ROOT / "outputs/context_boundaries_v16"


def main():
    source = pd.read_csv(SRC / "source_series.csv", dtype={"turbine": str})
    assert not source.duplicated(["site", "turbine"]).any()
    for column in ["start", "end", "b1", "b2"]:
        source[column] = pd.to_datetime(source[column], utc=True)
    columns = ["event_id", "site", "turbine", "split", "time_start", "time_end", "start_index", "end_index", "representation_eligible"]
    events = pd.read_csv(SRC / "candidate_intervals.csv.gz", usecols=columns, dtype={"turbine": str})
    assert events.event_id.is_unique
    events = events.merge(source[["site", "turbine", "start", "end", "b1", "b2"]], on=["site", "turbine"], validate="many_to_one", indicator=True)
    assert events._merge.eq("both").all()
    for column in ["time_start", "time_end"]:
        events[column] = pd.to_datetime(events[column], utc=True)
    step = pd.Timedelta(minutes=30)
    assert events.time_start.eq(events.start + pd.to_timedelta(events.start_index * 30, unit="min")).all()
    assert events.time_end.eq(events.start + pd.to_timedelta(events.end_index * 30, unit="min")).all()
    lower = events.start.where(events.split.eq("train"), events.b1.where(events.split.eq("validation"), events.b2))
    upper = events.b1.where(events.split.eq("train"), events.b2.where(events.split.eq("validation"), events.end + step))
    assert (events.time_start >= lower).all() and (events.time_end < upper).all()
    eligible = events.representation_eligible
    context_ok = (events.time_start - 4 * step >= lower) & (events.time_end + 4 * step < upper)
    bad = events[eligible & ~context_ok]
    OUT.mkdir(parents=True, exist_ok=True)
    bad.to_csv(OUT / "boundary_violations.csv", index=False)
    counts = events.groupby(["site", "split"]).agg(events=("event_id", "size"), shapes=("representation_eligible", "sum"))
    counts.to_csv(OUT / "checked_counts.csv")
    report = {"status": "PASS_PRIMARY_TEMPORAL_CONTEXT_BOUNDS" if bad.empty else "FAIL",
              "candidate_events": len(events), "complete_shapes": int(eligible.sum()), "turbines": len(source),
              "violations": len(bad), "context_margin_minutes_each_side": 120,
              "scope": "all five primary farms; event and context index/time/split checks, not an audit of all model leakage channels"}
    (OUT / "report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    assert bad.empty, "Context crosses a chronological split"


if __name__ == "__main__":
    main()
