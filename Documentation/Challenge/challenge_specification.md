# RTE 7k Power Injection Replication Challenge

## 1. Introduction

The RTE 7k challenge is a technical competition focused on replicating power injections (generation and load) for the French high-voltage transmission network operated by RTE (Reseau de Transport d'Electricite). The challenge uses the RTE 7k dataset, a detailed node-breaker model of the French grid comprising approximately 4,800 substations, 7,800 lines, 5,700 generators, and 6,900 loads across voltage levels ranging from 63 kV to 400 kV.

The challenge is organised jointly by RTE, CRESYM, and eRoots, and will be hosted on the LF Energy platform.

### Timeline

| Milestone | Date |
|---|---|
| Challenge launch at LF Energy | Autumn 2026 |
| Evaluation period | January -- March 2027 |

## 2. Objective

Given the network topology and a limited set of publicly available or explicitly provided measurements, participants must reconstruct the **net active power injection at every substation** for each hour of the evaluation period.

In other words: given the grid structure and partial observations, recover what was injected where and when.

## 3. Data Provided to Participants

Participants will receive the following data:

### 3.1 Network Model

- **Node-breaker topology** of the RTE 7k network in XIIDM format, as available in the [RTE 7k dataset](https://huggingface.co/datasets/OpenSynth/).
- **Asset list** for all generators and loads, including:
  - Maximum active power (`Pmax`)
  - Minimum active power (`Pmin`)
  - Connection details (substation, voltage level)

### 3.2 Boundary Data (Cross-Border Flows)

- Hourly import/export power flows at each interconnection with neighbouring countries.
- Participants must source this data from publicly available platforms such as [ENTSO-E Transparency Platform](https://transparency.entsoe.eu/) or [eco2mix](https://www.rte-france.com/eco2mix).
- The list of dangling lines representing cross-border interconnections will be provided to help participants map boundary data to the correct network elements.

### 3.3 Selected Branch Measurements

- Active power flows on a selected set of transmission lines and transformers across key network corridors.
- These measurements may include added noise for confidentiality protection.
- The monitored branches are chosen such that individual substation injections cannot be inferred from the measurements alone.

### 3.4 Data Not Provided

- **No geographic information**: neither OpenStreetMap (OSM) data nor any GIS (Geographic Information System) coordinates will be provided by the organisers.
- **No individual plant-level dispatch**: only the asset list with capacity bounds is given, not the actual dispatch.

## 4. Submission Format

### 4.1 Granularity

- **Spatial**: net active power injection at the **substation level**. This means the algebraic sum of all generation minus all load at each substation. Injections are not required at the individual busbar or plant level, avoiding confidentiality issues and topology-change ambiguity.
- **Temporal**: **hourly** resolution (one value per substation per hour).

### 4.2 File Format

Participants must submit their results as **Apache Parquet** files with the following schema:

| Column | Type | Description |
|---|---|---|
| `datetime` | `timestamp[ns, UTC]` | Start of the hour (e.g. `2021-01-01T00:00:00Z`) |
| `substation_id` | `string` | Substation identifier, consistent with the provided network model |
| `net_p_mw` | `float64` | Net active power injection in MW (generation positive, load negative) |

The evaluation will be conducted in multiple stages to manage data volume. Specific snapshots will be selected for each stage, and participants will be asked to submit only the corresponding rows.

## 5. Challenge Phases

### Phase 1: DC Power Flow (Baseline)

The primary challenge scope. Participants reconstruct active power injections under the DC power flow approximation:

- Voltage magnitudes are assumed to be 1.0 p.u. at all buses.
- Reactive power is ignored.
- Line flows depend linearly on voltage angle differences.

All feasibility constraints (Section 6) and evaluation metrics (Section 7) apply under this DC formulation.

### Phase 2: AC Power Flow (Optional Extension)

If Phase 1 results are strong, a second evaluation round may be introduced under full AC power flow conditions. This would additionally require:

- Voltage magnitude and reactive power estimation.
- Satisfaction of reactive power limits and voltage bounds.

Details for Phase 2 will be defined based on Phase 1 outcomes.

## 6. Feasibility Constraints

Every submitted snapshot must satisfy the following physical and operational constraints. Snapshots that violate these constraints will incur penalties (see Section 7).

### 6.1 Asset Limits

For every generator $g$ at every hour:

$$P_{\min,g} \leq P_g \leq P_{\max,g}$$

where $P_{\min,g}$ and $P_{\max,g}$ are the declared bounds from the asset list.

### 6.2 Zonal Balance

The total generation minus total load in each French administrative region must match the known zonal balance within a tight tolerance:

$$\left| \sum_{g \in \text{zone}} P_g - \sum_{l \in \text{zone}} P_l - P_{\text{balance, zone}} \right| \leq 0.1 \text{ MW}$$

### 6.3 Power Flow Convergence

The submitted injections must produce a converged power flow solution when applied to the network model. Snapshots for which no power flow solution exists are considered physically invalid.

### 6.4 No Thermal Overloads

All line and transformer apparent power flows must remain within their permanent admissible ratings:

$$|S_{\mathrm{branch}}| \leq S_{\max,\mathrm{branch}} \quad \forall \ \mathrm{branches}$$

### 6.5 Voltage Angle Bounds

Under the DC approximation, voltage angle differences must remain within reasonable bounds:

$$|\theta_i| \leq 30^{\circ} \quad \forall \ \mathrm{buses} \ i$$

where angles are measured relative to the slack bus.

## 7. Evaluation Methodology

### 7.1 Accuracy Metrics

Submissions are evaluated using two complementary metrics:

**Metric 1 -- Injection Error**

Weighted mean absolute error on net substation injections compared to ground truth:

$$E_{\text{inj}} = \frac{\sum_{s} w_s \, | \hat{P}_s - P_s^* |}{\sum_{s} w_s}$$

where $\hat{P}_s$ is the submitted injection at substation $s$, $P_s^*$ is the ground truth, and $w_s$ is a weight proportional to the substation size (e.g. installed capacity or peak load).

**Metric 2 -- Measurement Error**

Error on the provided branch flow measurements and/or bus angle measurements:

$$E_{\text{meas}} = \frac{1}{M} \sum_{m=1}^{M} | \hat{y}_m - y_m^* |$$

where $\hat{y}_m$ are the measurement values computed from the submitted injections and $y_m^*$ are the provided (possibly noisy) measurements.

### 7.2 Feasibility Penalty

A penalty term is added for physically invalid snapshots:

$$\text{Penalty} = \alpha \cdot N_{\text{overload}} + \beta \cdot N_{\text{diverged}} + \gamma \cdot N_{\text{angle}}$$

where:
- $N_{\text{overload}}$: number of thermal limit violations
- $N_{\text{diverged}}$: number of non-converging snapshots
- $N_{\text{angle}}$: number of angle bound violations
- $\alpha, \beta, \gamma$: penalty coefficients (to be defined)

### 7.3 Multi-Stage Evaluation

To manage data volume and provide progressive feedback, the evaluation proceeds in three stages. Each stage combines **scattered snapshots** (isolated hours spread across the year, testing generalisation) with **consecutive blocks** (contiguous days, testing temporal consistency).

#### Stage 1 -- Sanity Check (48 snapshots)

Purpose: format validation and early feedback.

- **24 scattered hours**: one randomly selected hour per month across 2 years (covering diverse seasons, weekdays/weekends, day/night).
- **24 consecutive hours**: one full day (e.g. a Wednesday in spring), testing whether solutions maintain coherence over consecutive time steps.

#### Stage 2 -- Intermediate Ranking (~400 snapshots)

Purpose: meaningful accuracy assessment.

- **72 scattered hours**: 3 hours per month across 2 years, stratified by load level (low, medium, peak).
- **336 consecutive hours (14 days)**: one winter week (high load, high cross-border flows) and one summer week (high solar, low demand), testing performance under sustained and contrasting operating conditions.

#### Stage 3 -- Final Ranking (~2,200 snapshots)

Purpose: comprehensive evaluation across the full operational envelope.

- **168 scattered hours**: 7 hours per month across 2 years, stratified by load level and day type (weekday/weekend/holiday).
- **2,016 consecutive hours (84 days)**: four continuous periods of 21 days each, one per season (winter, spring, summer, autumn), capturing seasonal patterns, weekly cycles, and multi-day weather events.

#### Snapshot Selection Principles

- The exact timestamps for each stage will be communicated to participants before the submission deadline.
- Scattered snapshots are drawn to cover the full range of system operating conditions (load levels, renewable output, import/export balance).
- Consecutive blocks are chosen to include operationally interesting periods (e.g. cold spells, heat waves, high wind events) where possible.
- Submissions for each stage are Parquet files containing only the requested snapshot rows.

### 7.4 Final Score

The final ranking combines accuracy and feasibility:

$$\text{Score} = E_{\text{inj}} + \lambda \cdot E_{\text{meas}} + \text{Penalty}$$

Lower scores are better. The weighting parameter $\lambda$ and penalty coefficients will be published before the evaluation period begins.

## 8. Summary of Rules

1. Participants receive the network topology, asset bounds, boundary power schedules, and selected branch measurements.
2. Participants submit hourly net active power injections at the substation level as Parquet files.
3. Submissions must satisfy all feasibility constraints (asset limits, zonal balance, convergence, thermal limits, angle bounds).
4. No geographic data (OSM, GIS) is provided by the organisers.
5. Evaluation combines injection accuracy, measurement fit, and physical feasibility.
6. Phase 1 uses DC power flow; Phase 2 (AC) is optional and conditional on Phase 1 results.
