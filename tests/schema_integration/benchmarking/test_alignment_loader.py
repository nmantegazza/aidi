"""Tests for SchemaAlignmentLoader and SchemaAlignmentDataset."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from schema_integration.benchmarking.alignment.loader import (
    SchemaAlignmentDataset,
    SchemaAlignmentLoader,
)
from shared.schema_models import (
    DataPackage,
    TableField,
    TableResource,
    TableSchema,
)


@pytest.fixture
def mock_schemanet_dir(tmp_path: Path) -> Path:
    """Create a mock standardized SchemaNet dataset directory."""
    ds_dir = tmp_path / "mock_dataset"
    ds_dir.mkdir(parents=True)

    pkg_a = DataPackage(
        schema_name="source_a",
        resources=[
            TableResource(
                name="users",
                schema=TableSchema(
                    primaryKey="user_id",
                    fields=[
                        TableField(name="user_id", type="integer"),
                        TableField(name="username", type="string"),
                    ],
                ),
            )
        ],
    )
    pkg_b = DataPackage(
        schema_name="source_b",
        resources=[
            TableResource(
                name="accounts",
                schema=TableSchema(
                    primaryKey="acc_id",
                    fields=[
                        TableField(name="acc_id", type="integer"),
                        TableField(name="acc_name", type="string"),
                    ],
                ),
            )
        ],
    )

    with open(ds_dir / "source_a.json", "w", encoding="utf-8") as f:
        f.write(pkg_a.model_dump_json(indent=2, by_alias=True))

    with open(ds_dir / "source_b.json", "w", encoding="utf-8") as f:
        f.write(pkg_b.model_dump_json(indent=2, by_alias=True))

    gt_data = [
        {"source_a": "users.user_id", "source_b": "accounts.acc_id"},
        {"source_a": "users.username", "source_b": "accounts.acc_name"},
    ]
    with open(ds_dir / "ground_truth.json", "w", encoding="utf-8") as f:
        json.dump(gt_data, f, indent=2)

    metadata = {
        "dataset_name": "mock_dataset",
        "domain": "Accounts",
        "source_a": {"table_count": 1, "column_count": 2},
        "source_b": {"table_count": 1, "column_count": 2},
        "ground_truth_synonyms_count": 2,
    }
    with open(ds_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    return ds_dir


def test_load_alignment_dataset(mock_schemanet_dir: Path) -> None:
    """Test loading a single standardized SchemaNet dataset."""
    ds = SchemaAlignmentLoader.load_dataset(mock_schemanet_dir)

    assert isinstance(ds, SchemaAlignmentDataset)
    assert ds.name == "mock_dataset"
    assert ds.domain == "Accounts"
    assert len(ds.source_a.resources) == 1
    assert len(ds.source_b.resources) == 1
    assert len(ds.ground_truth) == 2
    assert ds.ground_truth[0].canonical_key == ("users.user_id", "accounts.acc_id")


def test_load_alignment_suite(tmp_path: Path, mock_schemanet_dir: Path) -> None:
    """Test loading a suite of SchemaNet datasets with filtering."""
    # Create second dataset
    ds_dir_2 = tmp_path / "mock_clinical"
    ds_dir_2.mkdir()
    pkg = DataPackage(schema_name="src", resources=[])
    with open(ds_dir_2 / "source_a.json", "w") as f:
        f.write(pkg.model_dump_json())
    with open(ds_dir_2 / "source_b.json", "w") as f:
        f.write(pkg.model_dump_json())

    suite = SchemaAlignmentLoader.load_suite(tmp_path)
    assert len(suite) == 2

    filtered = SchemaAlignmentLoader.load_suite(tmp_path, dataset_filter="clinical")
    assert len(filtered) == 1
    assert filtered[0].name == "mock_clinical"


def test_load_dataset_without_ground_truth(tmp_path: Path) -> None:
    """Test loading a dataset when ground_truth.json is absent."""
    ds_dir = tmp_path / "no_gt_dataset"
    ds_dir.mkdir()
    pkg = DataPackage(schema_name="src", resources=[])
    with open(ds_dir / "source_a.json", "w") as f:
        f.write(pkg.model_dump_json())
    with open(ds_dir / "source_b.json", "w") as f:
        f.write(pkg.model_dump_json())

    ds = SchemaAlignmentLoader.load_dataset(ds_dir)
    assert ds.name == "no_gt_dataset"
    assert ds.ground_truth == []

