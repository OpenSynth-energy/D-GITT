# Region mapping

`snapshot_timestamps.txt` pins the exact 190 public RTE7K snapshots used to build
`substation_region.csv`. `build_substation_region.py` downloads only those files
from the year-partitioned OpenSynth Hugging Face datasets and reuses the local
Hugging Face cache on later runs.

Install the dependencies, then run:

```sh
pip install -r requirements.txt
python3 build_substation_region.py
```

Every public-grid substation is retained. Substations that cannot be matched to an
administrative region receive the valid `Unassigned` value.
