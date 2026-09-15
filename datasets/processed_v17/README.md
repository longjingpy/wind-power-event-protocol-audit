# Processed SCADA v17

This resource contains seven pseudonymous study archives, 333 turbines and 7,548,467 regular time-grid rows. It distributes processed variables rather than original provider files. Direct turbine names, location fields, absolute dates and identity/clock mapping tables are excluded.

`metadata.json`, `file_index.csv` and `data_dictionary.json` describe the complete bundle. Missing measurements remain explicit; `power_valid` and `wind_valid` have independent meanings. Primary sources retain their audited half-hour input rules. WF06 retains ten-minute source-clock sampling; WF07 uses half-hour available means. Month and hour remain for seasonal and diurnal context. Pseudonymization cannot prevent every inference from external information or recall earlier public downloads.

After extracting the release ZIP:

```python
from pathlib import Path
import pandas as pd

root = Path("processed_scada_v17")
inventory = pd.read_csv(root / "file_index.csv")
data = pd.read_parquet(root / inventory.iloc[0]["file"])
valid = data["power_valid"]
# Keep the complete index when computing differences; do not close missing gaps.
power = data["power_norm"].where(valid)
four_hour_steps = int(240 / data["interval_minutes"].iloc[0])
change = power.diff(four_hour_steps)
complete = valid.rolling(four_hour_steps + 1).sum().eq(four_hour_steps + 1)
threshold_anchor = change.abs().ge(0.20) & complete
```

The example computes threshold anchors, not merged physical event lifetimes. Source-normalization conventions and split rules are explicit in the metadata. The code and selected-checkpoint reproduction remain in the same repository. Original public data attribution and conditions remain applicable, as stated in the ZIP README and licence notice.
