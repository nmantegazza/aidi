"""Dataset loader for schema alignment benchmarking suite."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from schema_integration.benchmarking.alignment.models import SynonymPair
from shared.schema_models import DataPackage


@dataclass
class SchemaAlignmentDataset:
    """Multi-table schema alignment dataset container."""

    name: str
    domain: str
    source_a: DataPackage
    source_b: DataPackage
    ground_truth: list[SynonymPair] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class SchemaAlignmentLoader:
    """Loader for standardized SchemaNet benchmark datasets."""

    @classmethod
    def load_dataset(cls, dataset_dir: Path) -> SchemaAlignmentDataset:
        """Load a single schema alignment dataset directory.

        Args:
            dataset_dir: Path to dataset folder containing source_a.json,
                source_b.json, optional ground_truth.json, and metadata.json.

        Returns:
            SchemaAlignmentDataset container with schemas and optional ground truth.

        Raises:
            FileNotFoundError: If required source_a or source_b schema files are missing.
        """
        src_a_file = dataset_dir / "source_a.json"
        src_b_file = dataset_dir / "source_b.json"
        gt_file = dataset_dir / "ground_truth.json"
        meta_file = dataset_dir / "metadata.json"

        if not src_a_file.exists() or not src_b_file.exists():
            raise FileNotFoundError(
                f"Missing source_a.json or source_b.json in {dataset_dir}"
            )

        with open(src_a_file, "r", encoding="utf-8") as f:
            pkg_a = DataPackage.model_validate_json(f.read())

        with open(src_b_file, "r", encoding="utf-8") as f:
            pkg_b = DataPackage.model_validate_json(f.read())

        gt_pairs: list[SynonymPair] = []
        if gt_file.exists():
            with open(gt_file, "r", encoding="utf-8") as f:
                gt_data = json.load(f)
                for item in gt_data:
                    gt_pairs.append(
                        SynonymPair(
                            source_a=item["source_a"],
                            source_b=item["source_b"],
                        )
                    )

        metadata: dict[str, Any] = {}
        domain = "Unknown"
        if meta_file.exists():
            with open(meta_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)
                domain = metadata.get("domain", domain)

        return SchemaAlignmentDataset(
            name=dataset_dir.name,
            domain=domain,
            source_a=pkg_a,
            source_b=pkg_b,
            ground_truth=gt_pairs,
            metadata=metadata,
        )

    @classmethod
    def load_suite(
        cls,
        base_dir: Path,
        dataset_filter: list[str] | str | None = None,
    ) -> list[SchemaAlignmentDataset]:
        """Load alignment benchmark datasets with optional filtering.

        Args:
            base_dir: Path to directory containing dataset subdirectories.
            dataset_filter: Optional dataset name(s), substring(s), or 'all'.

        Returns:
            List of loaded SchemaAlignmentDataset instances.

        Raises:
            FileNotFoundError: If base_dir does not exist or has no datasets.
            ValueError: If no datasets match the provided filters.
        """
        if not base_dir.exists():
            raise FileNotFoundError(
                f"Alignment benchmark base directory not found: {base_dir}"
            )

        dataset_dirs = [d for d in base_dir.iterdir() if d.is_dir()]
        if not dataset_dirs:
            raise FileNotFoundError(
                f"No alignment dataset folders found in {base_dir}"
            )

        if dataset_filter:
            if isinstance(dataset_filter, str):
                filter_list = [dataset_filter]
            else:
                filter_list = list(dataset_filter)

            normalized_filters = [
                f.strip().lower() for f in filter_list if f and f.strip()
            ]

            if normalized_filters and "all" not in normalized_filters:
                dataset_dirs = [
                    d
                    for d in dataset_dirs
                    if any(nf in d.name.lower() for nf in normalized_filters)
                ]
                if not dataset_dirs:
                    raise ValueError(
                        f"No datasets matched filter(s) '{dataset_filter}'."
                    )

        dataset_dirs.sort(key=lambda p: p.name)

        suite: list[SchemaAlignmentDataset] = []
        for d in dataset_dirs:
            suite.append(cls.load_dataset(d))

        return suite
