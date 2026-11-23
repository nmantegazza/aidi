"""Dataset loader module for canonical entity resolution datasets."""

import json
import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import pandas as pd
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class GroundTruthType(str, Enum):
    """Ground truth type of an entity resolution dataset."""

    EXHAUSTIVE = "exhaustive"
    SAMPLED = "sampled"


class DatasetLoadError(Exception):
    """Raised when loading or parsing a dataset fails."""

    pass


class DatasetNotFoundError(DatasetLoadError):
    """Raised when the specified dataset directory does not exist."""

    pass


class MissingFileError(DatasetLoadError):
    """Raised when a mandatory dataset file is missing."""

    pass


class TableRef(BaseModel):
    """Reference to a table file and its ID column."""

    file: str
    id_column: str


class GroundTruthRef(BaseModel):
    """Reference to a ground truth file and its ID mapping columns."""

    file: str
    column_a: str
    column_b: str
    label_column: str | None = None


class CandidatesRef(BaseModel):
    """Reference to a candidate pairs file."""

    file: str
    column_a: str
    column_b: str


class DatasetMetadata(BaseModel):
    """Validates the structure of metadata.json."""

    name: str
    domain: str
    ground_truth_type: GroundTruthType
    table_a: TableRef
    table_b: TableRef
    ground_truth: GroundTruthRef
    candidates: CandidatesRef | None = None


@dataclass
class LoadedDataset:
    """Represents a fully loaded entity resolution dataset."""

    metadata: DatasetMetadata
    table_a: pd.DataFrame
    table_b: pd.DataFrame
    ground_truth: set[tuple[str, str]]
    candidates: pd.MultiIndex | None
    dataset_dir: Path | None = None

    @property
    def name(self) -> str:
        """Name of the dataset."""
        return self.metadata.name

    @property
    def domain(self) -> str:
        """Domain of the dataset."""
        return self.metadata.domain

    @property
    def ground_truth_type(self) -> GroundTruthType:
        """Ground truth type of the dataset."""
        return self.metadata.ground_truth_type


def load_dataset(directory_path: str) -> LoadedDataset:
    """Loads a canonical dataset from the given directory.

    Args:
        directory_path: Absolute or relative path to the dataset directory.

    Returns:
        A LoadedDataset object containing tables and ground truth.

    Raises:
        DatasetNotFoundError: If the directory does not exist.
        MissingFileError: If metadata.json is missing.
        DatasetLoadError: If parsing or file loading fails.
    """
    dir_path = Path(directory_path)
    if not dir_path.is_dir():
        raise DatasetNotFoundError(
            f"Dataset directory does not exist: {directory_path}"
        )

    metadata_path = dir_path / "metadata.json"
    if not metadata_path.is_file():
        raise MissingFileError(
            f"metadata.json is missing in directory: {directory_path}"
        )

    try:
        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata_content = f.read()
        metadata = DatasetMetadata.model_validate_json(metadata_content)
    except Exception as e:
        raise DatasetLoadError(
            f"Failed to parse metadata.json in {directory_path}: {e}"
        ) from e

    # Helper function to check existence and load a CSV
    def _read_csv(filename: str) -> pd.DataFrame:
        csv_path = dir_path / filename
        if not csv_path.is_file():
            raise DatasetLoadError(
                f"Required file '{filename}' not found in {directory_path}"
            )
        try:
            return pd.read_csv(csv_path, dtype=str)
        except Exception as e:
            raise DatasetLoadError(
                f"Error reading CSV file '{filename}': {e}"
            ) from e

    # Load Table A
    df_a = _read_csv(metadata.table_a.file)
    id_col_a = metadata.table_a.id_column
    if id_col_a not in df_a.columns:
        raise DatasetLoadError(
            f"ID column '{id_col_a}' not found in {metadata.table_a.file}"
        )
    df_a = df_a.set_index(id_col_a, drop=False)
    df_a.index = df_a.index.astype(str)

    # Load Table B
    df_b = _read_csv(metadata.table_b.file)
    id_col_b = metadata.table_b.id_column
    if id_col_b not in df_b.columns:
        raise DatasetLoadError(
            f"ID column '{id_col_b}' not found in {metadata.table_b.file}"
        )
    df_b = df_b.set_index(id_col_b, drop=False)
    df_b.index = df_b.index.astype(str)

    # Load Ground Truth
    df_gt = _read_csv(metadata.ground_truth.file)
    col_a = metadata.ground_truth.column_a
    col_b = metadata.ground_truth.column_b
    if col_a not in df_gt.columns or col_b not in df_gt.columns:
        raise DatasetLoadError(
            f"Columns '{col_a}' or '{col_b}' not found in "
            f"{metadata.ground_truth.file}"
        )

    # Filter by label if needed
    if metadata.ground_truth.label_column is not None:
        lbl = metadata.ground_truth.label_column
        if lbl not in df_gt.columns:
            raise DatasetLoadError(
                f"Label column '{lbl}' not found in {metadata.ground_truth.file}"
            )
        # Match where label is 1, 1.0, True, etc.
        mask = df_gt[lbl].astype(str).str.strip().isin({"1", "1.0", "True", "true"})
        df_gt = df_gt[mask]

    gt_set = set(
        zip(df_gt[col_a].astype(str), df_gt[col_b].astype(str))
    )

    # Load candidates
    candidates = None
    if metadata.candidates is not None:
        cand_path = dir_path / metadata.candidates.file
        if cand_path.is_file():
            try:
                df_cand = pd.read_csv(cand_path, dtype=str)
                cand_col_a = metadata.candidates.column_a
                cand_col_b = metadata.candidates.column_b
                if cand_col_a not in df_cand.columns or cand_col_b not in df_cand.columns:
                    raise DatasetLoadError(
                        f"Candidate columns '{cand_col_a}' or '{cand_col_b}' "
                        f"not found in {metadata.candidates.file}"
                    )
                candidates = pd.MultiIndex.from_arrays(
                    [df_cand[cand_col_a].astype(str), df_cand[cand_col_b].astype(str)],
                    names=[cand_col_a, cand_col_b]
                )
            except Exception as e:
                raise DatasetLoadError(
                    f"Error loading candidates from {metadata.candidates.file}: {e}"
                ) from e
        else:
            logger.warning(
                f"Candidates file '{metadata.candidates.file}' not found in "
                f"{directory_path}. Setting candidates to None."
            )

    return LoadedDataset(
        metadata=metadata,
        table_a=df_a,
        table_b=df_b,
        ground_truth=gt_set,
        candidates=candidates,
        dataset_dir=dir_path,
    )


def discover_and_load(
    data_dir: str,
    domain: str = "all",
    dataset_names: list[str] | None = None,
) -> list[LoadedDataset]:
    """Scans the data directory and loads matching canonical datasets.

    Args:
        data_dir: Root directory to scan for datasets.
        domain: Domain filter (case-insensitive, "all" for no filter).
        dataset_names: List of specific dataset names to load.

    Returns:
        List of LoadedDataset objects, sorted by name.
    """
    root_path = Path(data_dir)
    if not root_path.is_dir():
        return []

    loaded_datasets: list[LoadedDataset] = []
    # Search one level deep for subdirectories with metadata.json
    for path in root_path.iterdir():
        if not path.is_dir():
            continue
        metadata_path = path / "metadata.json"
        if not metadata_path.is_file():
            continue

        # Partially parse metadata to apply filters
        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                meta_dict = json.load(f)
            name = meta_dict.get("name")
            domain_val = meta_dict.get("domain")
        except Exception as e:
            logger.warning(
                f"Could not parse metadata.json in {path}: {e}. Skipping."
            )
            continue

        if not name or not domain_val:
            logger.warning(
                f"Invalid name or domain in metadata.json in {path}. Skipping."
            )
            continue

        # Filter domain
        if domain.lower() != "all":
            if domain_val.lower() != domain.lower():
                continue

        # Filter dataset_names
        if dataset_names is not None:
            if name not in dataset_names:
                continue

        # Load dataset
        try:
            dataset = load_dataset(str(path))
            loaded_datasets.append(dataset)
        except DatasetLoadError as e:
            logger.warning(
                f"Failed to load dataset at {path}: {e}. Skipping."
            )
            continue

    # Return sorted by name
    return sorted(loaded_datasets, key=lambda d: d.name)


def save_candidate_set(
    dataset: LoadedDataset,
    candidate_pairs: pd.MultiIndex,
    filename: str = "candidate_pairs.csv",
) -> Path | None:
    """Saves candidate pairs to a CSV file in the dataset directory and updates metadata.json.

    Only saves if candidate set is not already present in the dataset.

    Args:
        dataset: LoadedDataset instance.
        candidate_pairs: MultiIndex of candidate record pairs.
        filename: Name of candidate CSV file to save.

    Returns:
        Path to the saved candidate set CSV file, or None if skipped.
    """
    if dataset.dataset_dir is None:
        logger.warning(
            f"Cannot save candidates: dataset_dir is None for '{dataset.name}'."
        )
        return None

    if (
        dataset.ground_truth_type == GroundTruthType.SAMPLED
        or dataset.ground_truth_type.value == "sampled"
    ):
        logger.info(
            f"Dataset '{dataset.name}' uses sampled ground truth; skipping candidate set update."
        )
        return None

    cand_path = dataset.dataset_dir / filename
    if (
        dataset.metadata.candidates is not None
        or dataset.candidates is not None
        or cand_path.is_file()
    ):
        logger.info(
            f"Candidate set already present for dataset '{dataset.name}'. Skipping save."
        )
        return None

    col_a = dataset.metadata.ground_truth.column_a
    col_b = dataset.metadata.ground_truth.column_b

    # Convert MultiIndex candidate pairs to DataFrame
    cand_df = pd.DataFrame(list(candidate_pairs), columns=[col_a, col_b])
    cand_df.to_csv(cand_path, index=False)

    # Update metadata
    dataset.metadata.candidates = CandidatesRef(
        file=filename,
        column_a=col_a,
        column_b=col_b,
    )
    metadata_path = dataset.dataset_dir / "metadata.json"
    metadata_dict = (
        dataset.metadata.model_dump()
        if hasattr(dataset.metadata, "model_dump")
        else dataset.metadata.dict()
    )
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata_dict, f, indent=2)

    dataset.candidates = candidate_pairs
    return cand_path
