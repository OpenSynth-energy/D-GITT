"""Build the scorer's substation-to-region lookup using exact identifiers."""

from __future__ import annotations

import bz2
import json
import re
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
from typing import BinaryIO

import pandas as pd
from huggingface_hub import hf_hub_download


def local_name(tag: str) -> str:
    """Return an XML tag without its namespace.

    :param tag: Qualified XML tag.
    :return: Unqualified tag name.
    """
    if "}" in tag:
        name: str = tag.rsplit("}", 1)[1]
    else:
        name = tag
    return name


def open_xiidm(path: Path) -> BinaryIO:
    """Open a plain or bzip2-compressed XIIDM file.

    :param path: XIIDM path.
    :return: Binary input stream.
    """
    if path.suffix == ".bz2":
        stream: BinaryIO = bz2.open(path, "rb")
    else:
        stream = path.open("rb")
    return stream


def load_snapshot_tokens(path: Path) -> list[str]:
    """Load the exact public-snapshot tokens used to build the region map.

    :param path: Text file containing one ``YYYYMMDD-HHMM`` token per line.
    :return: Unique tokens in file order.
    """
    tokens: list[str] = list()
    with path.open("r", encoding="utf-8") as file_in:
        for raw_line in file_in:
            token: str = raw_line.strip()
            if token and not token.startswith("#"):
                if re.fullmatch(r"\d{8}-\d{4}", token) is None:
                    raise ValueError(f"Invalid snapshot timestamp token: {token!r}")
                else:
                    tokens.append(token)
            else:
                pass

    if not tokens:
        raise ValueError(f"No snapshot timestamp tokens found in {path}")
    elif len(tokens) != len(set(tokens)):
        raise ValueError(f"Duplicate snapshot timestamp tokens found in {path}")
    else:
        return tokens


def download_public_grids(tokens: list[str], dataset_prefix: str) -> list[Path]:
    """Download exactly the selected public RTE7K snapshots through the HF cache.

    :param tokens: Snapshot tokens in ``YYYYMMDD-HHMM`` form.
    :param dataset_prefix: Hugging Face dataset name before the year suffix.
    :return: Cached paths to the compressed public XIIDM snapshots.
    """
    grid_paths: list[Path] = [Path()] * len(tokens)
    for index, token in enumerate(tokens):
        # Public snapshots are partitioned by year and calendar date.
        year: str = token[:4]
        month: str = token[4:6]
        day: str = token[6:8]
        remote_name: str = (
            f"{year}/{month}/{day}/"
            f"recollement-auto-{token}-enrichi.xiidm.bz2"
        )
        cached_path: str = hf_hub_download(
            repo_id=f"{dataset_prefix}{year}",
            filename=remote_name,
            repo_type="dataset",
        )
        grid_paths[index] = Path(cached_path)
        print(f"Resolved public snapshot {index + 1}/{len(tokens)}: {token}")
    return grid_paths


def load_postes(path: Path) -> tuple[dict[str, list[str]], dict[str, str]]:
    """Load exact RTE poste codes and their departments.

    :param path: ODRE poste JSON path.
    :return: Identifier index and department lookup.
    """
    with path.open("r", encoding="utf-8") as file_in:
        records: object = json.load(file_in)

    if not isinstance(records, list):
        raise ValueError("The RTE postes JSON must contain a list of records.")
    else:
        code_index: defaultdict[str, list[str]] = defaultdict(list)
        departments: dict[str, str] = dict()
        for record in records:
            if not isinstance(record, dict):
                raise ValueError("Every RTE poste record must be an object.")
            else:
                code: str = str(record.get("code_poste", ""))
                department: str = str(record.get("departement", ""))
                if code:
                    code_index[code.strip().upper()].append(code)
                    departments[code] = department
                else:
                    pass
        return dict(code_index), departments


def parse_grid(path: Path) -> tuple[list[dict[str, str]], dict[str, str], list[str]]:
    """Read only identifiers needed for matching from an XIIDM grid.

    :param path: XIIDM path.
    :return: Equipment rows, voltage-level ownership, and substation IDs.
    """
    equipment_tags: set[str] = {
        "substation", "voltageLevel", "busbarSection", "switch", "bus",
        "configuredBus", "generator", "battery", "load", "shunt",
        "shuntCompensator", "staticVarCompensator", "line", "danglingLine",
        "tieLine", "twoWindingsTransformer", "threeWindingsTransformer",
        "hvdcLine", "vscConverterStation", "lccConverterStation",
    }
    rows: list[dict[str, str]] = list()
    voltage_to_substation: dict[str, str] = dict()
    substations: list[str] = list()
    current_substation: str = ""
    current_voltage_level: str = ""
    current_nominal_voltage: str = ""

    with open_xiidm(path) as file_in:
        events: object = ET.iterparse(file_in, events=("start", "end"))
        for event, element in events:
            tag: str = local_name(element.tag)
            if event == "start":
                attributes: dict[str, str] = dict(element.attrib)
                if tag == "substation":
                    current_substation = attributes.get("id", "")
                    current_voltage_level = ""
                    current_nominal_voltage = ""
                    substations.append(current_substation)
                elif tag == "voltageLevel":
                    current_voltage_level = attributes.get("id", "")
                    current_nominal_voltage = attributes.get("nominalV", "")
                    voltage_to_substation[current_voltage_level] = current_substation
                else:
                    pass

                if tag in equipment_tags:
                    element_id: str = attributes.get("id", "")
                    row_substation: str = element_id if tag == "substation" else current_substation
                    row_voltage_level: str = element_id if tag == "voltageLevel" else current_voltage_level
                    row_nominal_voltage: str = attributes.get("nominalV", "") if tag == "voltageLevel" else current_nominal_voltage
                    rows.append({
                        "element_id": element_id,
                        "substation_id": row_substation,
                        "voltage_level_id": row_voltage_level,
                        "voltage_level_id1": attributes.get("voltageLevelId1", ""),
                        "voltage_level_id2": attributes.get("voltageLevelId2", ""),
                        "voltage_level_id3": attributes.get("voltageLevelId3", ""),
                        "nominal_v": row_nominal_voltage,
                    })
                else:
                    pass
            else:
                if tag == "voltageLevel":
                    current_voltage_level = ""
                    current_nominal_voltage = ""
                elif tag == "substation":
                    current_substation = ""
                    current_voltage_level = ""
                    current_nominal_voltage = ""
                else:
                    pass
                element.clear()
    return rows, voltage_to_substation, substations


def match_grid_to_postes(xiidm_path: Path, postes_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Match grid equipment to ODRE postes by exact identifier.

    :param xiidm_path: XIIDM grid path.
    :param postes_path: ODRE poste JSON path.
    :return: Match rows and all grid substations.
    """
    code_index: dict[str, list[str]]
    departments: dict[str, str]
    code_index, departments = load_postes(postes_path)
    rows: list[dict[str, str]]
    voltage_to_substation: dict[str, str]
    substations: list[str]
    rows, voltage_to_substation, substations = parse_grid(xiidm_path)
    matches: list[dict[str, str]] = list()

    for row in rows:
        identifiers: list[str] = [
            row["substation_id"], row["voltage_level_id"], row["element_id"],
        ]
        for key in ("voltage_level_id1", "voltage_level_id2", "voltage_level_id3"):
            voltage_level_id: str = row[key]
            if voltage_level_id:
                identifiers.append(voltage_level_id)
                identifiers.append(voltage_to_substation.get(voltage_level_id, ""))
            else:
                pass

        codes: set[str] = set()
        for identifier in identifiers:
            codes.update(code_index.get(identifier.strip().upper(), list()))
        for code in sorted(codes):
            matches.append({
                "substation_id": row["substation_id"],
                "nominal_v": row["nominal_v"],
                "json_departement": departments[code],
            })

    pairs: pd.DataFrame = pd.DataFrame(matches)
    elements: pd.DataFrame = pd.DataFrame({"substation_id": sorted(set(substations))})
    return pairs, elements


def choose_region(group: pd.DataFrame) -> str:
    """Choose the majority region, breaking ties by maximum nominal voltage.

    :param group: Aggregated region votes belonging to one grid substation.
    :return: Selected administrative region.
    """
    ranked: pd.DataFrame = group.sort_values(
        ["vote_count", "nominal_v"],
        ascending=[False, False],
        kind="stable",
    )
    region: str = str(ranked["region"].iloc[0])
    return region


def build(
    grid_paths: list[Path],
    postes_path: Path,
    department_regions_path: Path,
) -> pd.DataFrame:
    """Build one region assignment for every grid substation.

    :param grid_paths: XIIDM grid paths sampled across the dataset.
    :param postes_path: ODRE poste JSON path.
    :param department_regions_path: Department-to-region CSV path.
    :return: Sorted substation-to-region table.
    """
    # Aggregate repeated equipment matches per grid immediately. Retaining every
    # raw match for all 190 snapshots consumes several gigabytes without changing
    # the majority vote.
    vote_tables: list[pd.DataFrame] = list()
    substation_tables: list[pd.DataFrame] = list()
    department_regions: pd.DataFrame = pd.read_csv(department_regions_path, dtype=str)
    department_to_region: dict[str, str] = dict(
        zip(department_regions["department"], department_regions["region"])
    )
    for grid_path in grid_paths:
        pairs_for_grid: pd.DataFrame
        substations_for_grid: pd.DataFrame
        pairs_for_grid, substations_for_grid = match_grid_to_postes(grid_path, postes_path)
        pairs_for_grid["region"] = pairs_for_grid["json_departement"].map(
            department_to_region
        )
        pairs_for_grid["nominal_v"] = pd.to_numeric(
            pairs_for_grid["nominal_v"], errors="coerce"
        ).fillna(0.0)
        voted_for_grid: pd.DataFrame = pairs_for_grid[
            pairs_for_grid["region"].notna()
        ]
        votes_for_grid: pd.DataFrame = (
            voted_for_grid.groupby(["substation_id", "region"], sort=False)
            .agg(vote_count=("region", "size"), nominal_v=("nominal_v", "max"))
            .reset_index()
        )
        vote_tables.append(votes_for_grid)
        substation_tables.append(substations_for_grid)

    votes: pd.DataFrame = pd.concat(vote_tables, ignore_index=True)
    votes = (
        votes.groupby(["substation_id", "region"], sort=False)
        .agg(vote_count=("vote_count", "sum"), nominal_v=("nominal_v", "max"))
        .reset_index()
    )
    substations: pd.DataFrame = pd.concat(substation_tables, ignore_index=True).drop_duplicates()
    regions: pd.Series = votes.groupby("substation_id", sort=False).apply(choose_region)
    output: pd.DataFrame = substations.copy()
    output["region"] = output["substation_id"].map(regions).fillna("Unassigned")
    return output


def main() -> None:
    """Build ``substation_region.csv`` from the pinned public snapshots."""
    # Configuration: edit these paths when the input filenames change.
    directory: Path = Path(__file__).resolve().parent
    timestamps_path: Path = directory / "snapshot_timestamps.txt"
    postes_path: Path = directory / "postes-electriques-rte.json"
    department_regions_path: Path = directory / "department_region_mapping.csv"
    output_path: Path = directory / "substation_region.csv"
    dataset_prefix: str = "OpenSynth/D-GITT-RTE7000-"

    required_paths: tuple[Path, ...] = (
        timestamps_path,
        postes_path,
        department_regions_path,
    )
    missing_paths: list[Path] = [path for path in required_paths if not path.exists()]
    if missing_paths:
        missing_text: str = ", ".join(str(path) for path in missing_paths)
        raise FileNotFoundError(f"Required input missing: {missing_text}")
    else:
        # A checked-in manifest makes the generated mapping independent of any
        # unrelated grid files that happen to exist in a local directory.
        tokens: list[str] = load_snapshot_tokens(timestamps_path)
        grid_paths: list[Path] = download_public_grids(tokens, dataset_prefix)
        output: pd.DataFrame = build(grid_paths, postes_path, department_regions_path)
        output.to_csv(output_path, index=False)
        counts: pd.Series = output["region"].value_counts()
        print(f"Wrote {output_path} from {len(grid_paths)} snapshots ({len(output)} substations)")
        print(counts.to_string())


if __name__ == "__main__":
    main()
else:
    pass
