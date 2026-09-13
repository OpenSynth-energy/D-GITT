# RTE7000 : Baseline Reconstruction

This package provides a baseline method for reconstructing the missing electrical injections
(loads, generators, dangling lines) in the RTE7000 public dataset. It serves as a simple and
reproducible starting point for the challenge.

> **Important**: the scripts operate on enriched XIIDM snapshots, not
> on the raw RTE7000 files. The enriched snapshots restore operational limits on dangling lines
> and add fictitious HVDC generators at converter buses, which are required for the
> reconstruction of cross-border flows.

## Method

The baseline reconstructs three types of injections from publicly available data:

**Loads**: the éCO2mix regional consumption is distributed uniformly across all connected loads
within each RTE region. Every load in the same region receives the same active power (MW).

**Generators**: the éCO2mix regional production is split by energy type (Thermal, Wind, Solar,
Hydro) and distributed across connected generators proportionally to their `max_p`, with
clipping (no generator exceeds its rated capacity). Nuclear is handled nationally: the sum
across all regions is distributed over all connected NUCLEAR generators regardless of their
region, because the geographic file is incomplete for some nuclear substations. For non-nuclear
generators whose substation is missing from the geographic file (no assigned region), the
unallocated surplus arising from regional saturation or missing generators is redistributed
across them at the national level, grouped by energy type.

**cross-border interconnections**: the physical cross-border flows from the
ENTSO-E Transparency Platform are distributed uniformly across the connected dangling lines
and HVDC generators of each neighboring country.

## Package structure

```
rte7000-baseline-reconstruction/
├── README.md
├── constants.py                         # Mappings: regions, energy types, countries, departments
├── utils.py                             # Shared functions: XIIDM reading, éCO2mix parsing, ENTSO-E flows
│
├── 01_baseline_load.py                  # Step 1: reconstruct loads
├── 02_baseline_gen.py                   # Step 2: reconstruct generators
├── 03_baseline_interconnections.py      # Step 3: reconstruct dangling lines and HVDC generators
├── 04_build_reconstructed_xiidm.py      # Step 4: assemble the reconstructed XIIDM
├── 05_export_submission.py              # Step 5: export to the challenge Parquet format
│
└── data/
    ├── geo/
    │   └── postes-electriques-rte.csv   # RTE substation geographic file (ODRÉ export)
    ├── eco2mix/
    │   ├── eco2mix_Auvergne-Rhône-Alpes_2022.csv
    │   ├── eco2mix_Bretagne_2022.csv
    │   └── ...                          # One CSV per RTE region per year (downloaded from éCO2mix)
    ├── entsoe/
    │   └── entsoe_flows_2022-11-01T1100.csv  # Cross-border flows
    ├── recollement-auto-YYYYMMDD-HHMM-enrichi.xiidm.bz2  # Enriched XIIDM snapshot to reconstruct (not the raw RTE7000 file)
    └── output/                          # Generated files (CSV, XIIDM, Parquet)
```

## Requirements

```
pypowsybl
pandas
```

## How to run

All commands are run from the `rte7000-baseline-reconstruction/` directory. The only required
arguments for steps 1–3 are `--timestamp` and `--network-xiidm`; other paths default
to `data/` subfolders.

### Step 1: Reconstruct loads

```bash
python 01_baseline_load.py \
    --timestamp "2022-11-01 11:00:00" \
    --network-xiidm data/recollement-auto-20221101-1100-enrichi.xiidm.bz2
```

Output: `data/output/load_baseline.csv`

### Step 2: Reconstruct generators

```bash
python 02_baseline_gen.py \
    --timestamp "2022-11-01 11:00:00" \
    --network-xiidm data/recollement-auto-20221101-1100-enrichi.xiidm.bz2
```

Output: `data/output/gen_baseline.csv`

### Step 3: Reconstruct dangling lines and HVDC generators

```bash
python 03_baseline_interconnections.py \
    --network-xiidm data/recollement-auto-20221101-1100-enrichi.xiidm.bz2 \
    --entsoe-flows-csv data/entsoe/entsoe_flows_2022-11-01T1100.csv
```

Output: `data/output/dangling_line_baseline.csv`, `data/output/hvdc_gen_baseline.csv`

### Step 4: Build the reconstructed XIIDM

Assembles the three CSV outputs into a single XIIDM network file.

```bash
python 04_build_reconstructed_xiidm.py \
    --base-xiidm data/recollement-auto-20221101-1100-enrichi.xiidm.bz2 \
    --output-xiidm data/output/recollement-auto-20221101-1100-baseline.xiidm
```

Output: `data/output/recollement-auto-20221101-1100-baseline.xiidm`

### Step 5: Export submission

Aggregates the reconstructed XIIDM into the challenge submission format
(`datetime`, `substation_id`, `net_p_mw`).

```bash
python 05_export_submission.py \
    --timestamp "2022-11-01 11:00:00"
```

Output: `data/output/submission_baseline.parquet` and `data/output/submission_baseline.zip`

## Data sources

| Data | Source | Format |
|------|--------|--------|
| Regional consumption & production | [éCO2mix](https://www.rte-france.com/donnees-publications/eco2mix-donnees-temps-reel/telecharger-indicateurs) | CSV, one file per region per year |
| Cross-border physical flows | [ENTSO-E Transparency Platform](https://transparency.entsoe.eu/) | CSV (columns `country`, `net_fr_to_country`) |
| Substation geographic mapping | [ODRÉ](https://odre.opendatasoft.com/explore/dataset/postes-electriques-rte/information/?flg=fr-fr&disjunctive.tension&disjunctive.fonction&disjunctive.etat&disjunctive.departement) | CSV semicolon-separated (columns `Code poste`, `departement`) |
| Network snapshots | RTE7000 public dataset | XIIDM (`.xiidm.bz2`) |

### Note on ENTSO-E flows

The cross-border flow CSV file (`entsoe_flows_2022-11-01T1100.csv`) was obtained by querying
the ENTSO-E Transparency Platform REST API, which returns data in XML format. This XML was
then converted to CSV with columns `country` and `net_fr_to_country`.

Access to the ENTSO-E API is not open: you must first request an access key (security token)
by sending an email to ENTSO-E support. The CSV file provided in this package allows you to skip this
step for the example snapshot.

## Submission format

The Parquet file contains one row per active substation:

| Column | Type | Description |
|--------|------|-------------|
| `datetime` | `Timestamp` (tz=`Etc/GMT-1`) | Snapshot timestamp |
| `substation_id` | `str` | Substation identifier from the XIIDM |
| `net_p_mw` | `float64` | Net active power injection (positive = net generation, negative = net consumption) |