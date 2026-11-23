"""Unit tests for the new dataset_loader module."""

import json
import logging
import os
from pathlib import Path

import pandas as pd
import pytest

from entity_resolution.dataset_loader import (
    DatasetLoadError,
    DatasetNotFoundError,
    GroundTruthType,
    MissingFileError,
    discover_and_load,
    load_dataset,
)


def test_load_dataset_happy_path(tmp_path):
    """Test loading a dataset that follows the canonical layout."""
    dataset_dir = tmp_path / "mock_dataset"
    dataset_dir.mkdir(parents=True)

    table_a_data = pd.DataFrame({"id": ["1", "2"], "name": ["Alice", "Bob"]})
    table_b_data = pd.DataFrame({"id": ["3", "4"], "title": ["Alce", "Bobby"]})
    gt_data = pd.DataFrame({"id1": ["1", "2"], "id2": ["3", "4"]})

    table_a_data.to_csv(dataset_dir / "table_a.csv", index=False)
    table_b_data.to_csv(dataset_dir / "table_b.csv", index=False)
    gt_data.to_csv(dataset_dir / "matches.csv", index=False)

    metadata = {
        "name": "mock_dataset",
        "domain": "synthetic",
        "ground_truth_type": "exhaustive",
        "table_a": {"file": "table_a.csv", "id_column": "id"},
        "table_b": {"file": "table_b.csv", "id_column": "id"},
        "ground_truth": {
            "file": "matches.csv",
            "column_a": "id1",
            "column_b": "id2",
            "label_column": None,
        },
        "candidates": None,
    }

    with open(dataset_dir / "metadata.json", "w") as f:
        json.dump(metadata, f)

    dataset = load_dataset(str(dataset_dir))

    assert dataset.name == "mock_dataset"
    assert dataset.domain == "synthetic"
    assert dataset.ground_truth_type == GroundTruthType.EXHAUSTIVE
    assert list(dataset.table_a.index) == ["1", "2"]
    assert list(dataset.table_b.index) == ["3", "4"]
    assert dataset.ground_truth == {("1", "3"), ("2", "4")}
    assert dataset.candidates is None


def test_load_dataset_not_found():
    """Test loading a dataset when the directory does not exist."""
    with pytest.raises(DatasetNotFoundError):
        load_dataset("/nonexistent/directory/path")


def test_load_dataset_missing_metadata(tmp_path):
    """Test loading a dataset when metadata.json is missing."""
    dataset_dir = tmp_path / "mock_dataset"
    dataset_dir.mkdir(parents=True)
    with pytest.raises(MissingFileError):
        load_dataset(str(dataset_dir))


def test_load_dataset_missing_csv(tmp_path):
    """Test loading a dataset when a CSV file listed in metadata is missing."""
    dataset_dir = tmp_path / "mock_dataset"
    dataset_dir.mkdir(parents=True)

    metadata = {
        "name": "mock_dataset",
        "domain": "synthetic",
        "ground_truth_type": "exhaustive",
        "table_a": {"file": "table_a.csv", "id_column": "id"},
        "table_b": {"file": "table_b.csv", "id_column": "id"},
        "ground_truth": {
            "file": "matches.csv",
            "column_a": "id1",
            "column_b": "id2",
            "label_column": None,
        },
        "candidates": None,
    }

    with open(dataset_dir / "metadata.json", "w") as f:
        json.dump(metadata, f)

    with pytest.raises(DatasetLoadError) as exc_info:
        load_dataset(str(dataset_dir))
    assert "Required file 'table_a.csv' not found" in str(exc_info.value)


def test_load_dataset_with_label_column(tmp_path):
    """Test loading ground truth and filtering by label column."""
    dataset_dir = tmp_path / "mock_dataset"
    dataset_dir.mkdir(parents=True)

    table_a_data = pd.DataFrame({"id": ["1", "2"], "name": ["Alice", "Bob"]})
    table_b_data = pd.DataFrame({"id": ["3", "4"], "title": ["Alce", "Bobby"]})
    # One match (label=1), one non-match (label=0)
    gt_data = pd.DataFrame(
        {"id1": ["1", "2"], "id2": ["3", "4"], "match_label": ["1", "0"]}
    )

    table_a_data.to_csv(dataset_dir / "table_a.csv", index=False)
    table_b_data.to_csv(dataset_dir / "table_b.csv", index=False)
    gt_data.to_csv(dataset_dir / "matches.csv", index=False)

    metadata = {
        "name": "mock_dataset",
        "domain": "synthetic",
        "ground_truth_type": "sampled",
        "table_a": {"file": "table_a.csv", "id_column": "id"},
        "table_b": {"file": "table_b.csv", "id_column": "id"},
        "ground_truth": {
            "file": "matches.csv",
            "column_a": "id1",
            "column_b": "id2",
            "label_column": "match_label",
        },
        "candidates": None,
    }

    with open(dataset_dir / "metadata.json", "w") as f:
        json.dump(metadata, f)

    dataset = load_dataset(str(dataset_dir))
    assert dataset.ground_truth_type == GroundTruthType.SAMPLED
    # Only ("1", "3") should be present
    assert dataset.ground_truth == {("1", "3")}


def test_load_dataset_with_candidates(tmp_path):
    """Test loading dataset with candidates MultiIndex."""
    dataset_dir = tmp_path / "mock_dataset"
    dataset_dir.mkdir(parents=True)

    table_a_data = pd.DataFrame({"id": ["1", "2"], "name": ["Alice", "Bob"]})
    table_b_data = pd.DataFrame({"id": ["3", "4"], "title": ["Alce", "Bobby"]})
    gt_data = pd.DataFrame({"id1": ["1", "2"], "id2": ["3", "4"]})
    cand_data = pd.DataFrame({"c1": ["1", "2"], "c2": ["4", "3"]})

    table_a_data.to_csv(dataset_dir / "table_a.csv", index=False)
    table_b_data.to_csv(dataset_dir / "table_b.csv", index=False)
    gt_data.to_csv(dataset_dir / "matches.csv", index=False)
    cand_data.to_csv(dataset_dir / "candidates.csv", index=False)

    metadata = {
        "name": "mock_dataset",
        "domain": "synthetic",
        "ground_truth_type": "exhaustive",
        "table_a": {"file": "table_a.csv", "id_column": "id"},
        "table_b": {"file": "table_b.csv", "id_column": "id"},
        "ground_truth": {
            "file": "matches.csv",
            "column_a": "id1",
            "column_b": "id2",
            "label_column": None,
        },
        "candidates": {
            "file": "candidates.csv",
            "column_a": "c1",
            "column_b": "c2",
        },
    }

    with open(dataset_dir / "metadata.json", "w") as f:
        json.dump(metadata, f)

    dataset = load_dataset(str(dataset_dir))
    assert dataset.candidates is not None
    assert len(dataset.candidates) == 2
    assert ("1", "4") in dataset.candidates
    assert ("2", "3") in dataset.candidates


def test_discover_and_load(tmp_path):
    """Test discovery and filtering of multiple canonical datasets."""
    # Set up two datasets
    ds1_dir = tmp_path / "ds1"
    ds1_dir.mkdir()
    ds2_dir = tmp_path / "ds2"
    ds2_dir.mkdir()

    table_data = pd.DataFrame({"id": ["1"], "name": ["X"]})
    gt_data = pd.DataFrame({"id1": ["1"], "id2": ["1"]})

    for d in [ds1_dir, ds2_dir]:
        table_data.to_csv(d / "t.csv", index=False)
        gt_data.to_csv(d / "gt.csv", index=False)

    meta1 = {
        "name": "dataset_one",
        "domain": "e-commerce",
        "ground_truth_type": "exhaustive",
        "table_a": {"file": "t.csv", "id_column": "id"},
        "table_b": {"file": "t.csv", "id_column": "id"},
        "ground_truth": {
            "file": "gt.csv",
            "column_a": "id1",
            "column_b": "id2",
        },
        "candidates": None,
    }
    meta2 = {
        "name": "dataset_two",
        "domain": "citations",
        "ground_truth_type": "exhaustive",
        "table_a": {"file": "t.csv", "id_column": "id"},
        "table_b": {"file": "t.csv", "id_column": "id"},
        "ground_truth": {
            "file": "gt.csv",
            "column_a": "id1",
            "column_b": "id2",
        },
        "candidates": None,
    }

    with open(ds1_dir / "metadata.json", "w") as f:
        json.dump(meta1, f)
    with open(ds2_dir / "metadata.json", "w") as f:
        json.dump(meta2, f)

    # Discover all
    datasets = discover_and_load(str(tmp_path), domain="all")
    assert len(datasets) == 2
    assert datasets[0].name == "dataset_one"
    assert datasets[1].name == "dataset_two"

    # Filter by domain
    datasets_ecommerce = discover_and_load(str(tmp_path), domain="e-commerce")
    assert len(datasets_ecommerce) == 1
    assert datasets_ecommerce[0].name == "dataset_one"

    # Filter by name
    datasets_name = discover_and_load(
        str(tmp_path), domain="all", dataset_names=["dataset_two"]
    )
    assert len(datasets_name) == 1
    assert datasets_name[0].name == "dataset_two"
