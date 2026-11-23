"""Dataset loader for schema mapping benchmarking suite (Valentine)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from schema_integration.benchmarking.mapping.models import (
    ColumnSchemaInfo,
    DatasetSchemaInfo,
    TableSchemaInfo,
)
from shared.schema_models import (
    DataPackage,
    FieldConstraints,
    TableField,
    TableResource,
    TableSchema,
)


@dataclass
class BenchmarkDataset:
    """Benchmark dataset pair with schema definitions and ground truth."""

    name: str
    domain: str
    scenario: str
    source_package: DataPackage
    target_package: DataPackage
    source_df: pd.DataFrame
    target_df: pd.DataFrame
    ground_truth: set[tuple[str, str]]
    category: str = "single_table"

    def to_schema_info(self) -> DatasetSchemaInfo:
        """Convert BenchmarkDataset to structured DatasetSchemaInfo."""
        src_tables: list[TableSchemaInfo] = []
        for r in self.source_package.resources:
            src_cols: list[ColumnSchemaInfo] = []
            for f in r.schema_info.fields:
                constraints = (
                    f.constraints.model_dump() if f.constraints else {}
                )
                src_cols.append(
                    ColumnSchemaInfo(
                        name=f.name,
                        type=f.type,
                        constraints=constraints,
                    )
                )
            row_count = (
                len(self.source_df)
                if self.category == "single_table" and not self.source_df.empty
                else 0
            )
            src_tables.append(
                TableSchemaInfo(
                    table_name=r.name,
                    row_count=row_count,
                    column_count=len(src_cols),
                    columns=src_cols,
                )
            )

        tgt_tables: list[TableSchemaInfo] = []
        for r in self.target_package.resources:
            tgt_cols: list[ColumnSchemaInfo] = []
            for f in r.schema_info.fields:
                constraints = (
                    f.constraints.model_dump() if f.constraints else {}
                )
                tgt_cols.append(
                    ColumnSchemaInfo(
                        name=f.name,
                        type=f.type,
                        constraints=constraints,
                    )
                )
            row_count = (
                len(self.target_df)
                if self.category == "single_table" and not self.target_df.empty
                else 0
            )
            tgt_tables.append(
                TableSchemaInfo(
                    table_name=r.name,
                    row_count=row_count,
                    column_count=len(tgt_cols),
                    columns=tgt_cols,
                )
            )

        return DatasetSchemaInfo(
            dataset_name=self.name,
            domain=self.domain,
            scenario=self.scenario,
            category=self.category,
            source_table=src_tables[0] if src_tables else None,
            target_table=tgt_tables[0] if tgt_tables else None,
            source_tables=src_tables,
            target_tables=tgt_tables,
            ground_truth_pairs=sorted(self.ground_truth),
        )


class SchemaMappingLoader:
    """Loads standardized Valentine benchmark datasets from disk."""

    @staticmethod
    def _map_dtype_to_frictionless(
        dtype: Any,
        type_str: str | None = None,
    ) -> str:
        """Map pandas dtype or type hint string to Frictionless data type.

        Args:
            dtype: Pandas column dtype.
            type_str: Optional raw type string from metadata JSON.

        Returns:
            Standard Frictionless data type string.
        """
        if type_str:
            t = type_str.lower()
            if "int" in t:
                return "integer"
            if any(k in t for k in ["real", "float", "double", "numeric"]):
                return "number"
            if "bool" in t:
                return "boolean"
            if "date" in t or "time" in t:
                return "datetime"
            return "string"

        dt_str = str(dtype).lower()
        if "int" in dt_str:
            return "integer"
        if "float" in dt_str:
            return "number"
        if "bool" in dt_str:
            return "boolean"
        if "datetime" in dt_str:
            return "datetime"
        return "string"

    @classmethod
    def _build_data_package(
        cls,
        table_name: str,
        df: pd.DataFrame,
        meta_json: dict[str, Any] | None = None,
    ) -> DataPackage:
        """Construct a DataPackage model from a DataFrame and optional metadata.

        Args:
            table_name: Identifier for the table resource and schema.
            df: Pandas DataFrame representing the tabular dataset.
            meta_json: Optional dictionary of column-level metadata.

        Returns:
            Populated DataPackage model.
        """
        fields: list[TableField] = []
        for col in df.columns:
            raw_type = None
            if meta_json and col in meta_json:
                col_meta = meta_json[col]
                if isinstance(col_meta, dict):
                    raw_type = col_meta.get("type")

            f_type = cls._map_dtype_to_frictionless(df[col].dtype, raw_type)
            fields.append(
                TableField(
                    name=str(col),
                    type=f_type,
                    constraints=FieldConstraints(required=False),
                )
            )

        table_schema = TableSchema(fields=fields)
        resource = TableResource(
            name=table_name,
            schema=table_schema,
        )
        return DataPackage(
            schema_name=table_name,
            title=table_name,
            resources=[resource],
        )

    @classmethod
    def load_dataset(cls, dataset_dir: Path) -> BenchmarkDataset:
        """Load a single standardized benchmark dataset directory.

        Supports both single-table (with CSVs) and multi-table (schema-only) datasets.

        Args:
            dataset_dir: Path to dataset folder containing CSVs and/or JSONs.

        Returns:
            BenchmarkDataset with DataPackages, DataFrames, and ground truth.

        Raises:
            FileNotFoundError: If core mapping or schema files are not found.
        """
        dataset_name = dataset_dir.name
        files = list(dataset_dir.iterdir())

        meta_json = next(
            (f for f in files if f.name == "metadata.json"),
            None,
        )
        map_json = next(
            (
                f
                for f in files
                if f.name.endswith("_mapping.json") or f.name == "ground_truth.json"
            ),
            None,
        )

        domain = "Unknown"
        scenario = "Unknown"
        category = "single_table"

        if meta_json and meta_json.exists():
            with open(meta_json, "r", encoding="utf-8") as f:
                meta_dict = json.load(f)
                domain = meta_dict.get("domain", domain)
                scenario = meta_dict.get("scenario", scenario)
                category = meta_dict.get("category", category)

        if dataset_dir.parent.name == "multi_table":
            category = "multi_table"
        elif dataset_dir.parent.name == "single_table":
            category = "single_table"

        if not map_json:
            raise FileNotFoundError(
                f"Missing mapping JSON file in {dataset_dir}"
            )

        with open(map_json, "r", encoding="utf-8") as f:
            mapping_data = json.load(f)
            if domain == "Unknown" and isinstance(mapping_data, dict):
                domain = mapping_data.get("domain", domain)
            if scenario == "Unknown" and isinstance(mapping_data, dict):
                scenario = mapping_data.get("scenario", scenario)
            if category == "single_table" and isinstance(mapping_data, dict):
                category = mapping_data.get("category", category)

        # Multi-table schema-only dataset loading
        if category == "multi_table":
            src_json = next(
                (
                    f
                    for f in files
                    if ("source" in f.name or "source_a" in f.name)
                    and f.name.endswith(".json")
                ),
                None,
            )
            tgt_json = next(
                (
                    f
                    for f in files
                    if ("target" in f.name or "source_b" in f.name)
                    and f.name.endswith(".json")
                ),
                None,
            )

            if not src_json or not tgt_json:
                raise FileNotFoundError(
                    f"Missing source or target schema JSON files in multi-table dataset {dataset_dir}"
                )

            with open(src_json, "r", encoding="utf-8") as f:
                source_package = DataPackage.model_validate_json(f.read())
            with open(tgt_json, "r", encoding="utf-8") as f:
                target_package = DataPackage.model_validate_json(f.read())

            ground_truth: set[tuple[str, str]] = set()
            raw_matches = (
                mapping_data.get("matches", [])
                if isinstance(mapping_data, dict)
                else mapping_data
            )

            for match in raw_matches:
                if isinstance(match, dict):
                    s_tbl = match.get("source_table")
                    s_col = match.get("source_column")
                    t_tbl = match.get("target_table")
                    t_col = match.get("target_column")
                    if s_tbl and s_col and t_tbl and t_col:
                        ground_truth.add((f"{s_tbl}.{s_col}", f"{t_tbl}.{t_col}"))
                    elif "source_a" in match and "source_b" in match:
                        ground_truth.add((match["source_a"], match["source_b"]))
                    elif s_col and t_col:
                        ground_truth.add((s_col, t_col))

            return BenchmarkDataset(
                name=dataset_name,
                domain=domain,
                scenario=scenario,
                source_package=source_package,
                target_package=target_package,
                source_df=pd.DataFrame(),
                target_df=pd.DataFrame(),
                ground_truth=ground_truth,
                category="multi_table",
            )

        # Single-table dataset loading (with CSVs)
        src_csv = next(
            (f for f in files if "source" in f.name and f.name.endswith(".csv")),
            None,
        )
        tgt_csv = next(
            (f for f in files if "target" in f.name and f.name.endswith(".csv")),
            None,
        )
        src_json = next(
            (f for f in files if "source" in f.name and f.name.endswith(".json")),
            None,
        )
        tgt_json = next(
            (f for f in files if "target" in f.name and f.name.endswith(".json")),
            None,
        )

        if not src_csv or not tgt_csv:
            raise FileNotFoundError(
                f"Missing required CSV files in single-table dataset {dataset_dir}"
            )

        df_src = pd.read_csv(src_csv, low_memory=False)
        df_tgt = pd.read_csv(tgt_csv, low_memory=False)

        src_meta = None
        if src_json and src_json.exists():
            with open(src_json, "r", encoding="utf-8") as f:
                src_meta = json.load(f)

        tgt_meta = None
        if tgt_json and tgt_json.exists():
            with open(tgt_json, "r", encoding="utf-8") as f:
                tgt_meta = json.load(f)

        ground_truth = set()
        raw_matches = (
            mapping_data.get("matches", [])
            if isinstance(mapping_data, dict)
            else mapping_data
        )
        for match in raw_matches:
            if isinstance(match, dict):
                s_col = match.get("source_column")
                t_col = match.get("target_column")
                if s_col and t_col:
                    ground_truth.add((s_col, t_col))

        source_package = cls._build_data_package(
            table_name=f"{dataset_name}_source",
            df=df_src,
            meta_json=src_meta,
        )
        target_package = cls._build_data_package(
            table_name=f"{dataset_name}_target",
            df=df_tgt,
            meta_json=tgt_meta,
        )

        return BenchmarkDataset(
            name=dataset_name,
            domain=domain,
            scenario=scenario,
            source_package=source_package,
            target_package=target_package,
            source_df=df_src,
            target_df=df_tgt,
            ground_truth=ground_truth,
            category="single_table",
        )

    @classmethod
    def load_suite(
        cls,
        base_dir: Path,
        dataset_filter: list[str] | str | None = None,
        category_filter: str | None = None,
    ) -> list[BenchmarkDataset]:
        """Load benchmark suite from base directory with optional filtering.

        Args:
            base_dir: Path to directory containing benchmark dataset folders.
            dataset_filter: Optional dataset name(s), substring(s), or 'all'.
            category_filter: Optional category ('all', 'single_table', 'multi_table').

        Returns:
            List of loaded BenchmarkDataset instances.

        Raises:
            FileNotFoundError: If base_dir does not exist or no datasets found.
            ValueError: If no datasets match the provided filters.
        """
        if not base_dir.exists():
            raise FileNotFoundError(
                f"Benchmark base directory not found: {base_dir}"
            )

        # Check for partitioned structure (single_table/ and multi_table/)
        has_single = (base_dir / "single_table").is_dir()
        has_multi = (base_dir / "multi_table").is_dir()

        dataset_dirs: list[Path] = []
        norm_cat = category_filter.strip().lower() if category_filter else "all"

        if has_single or has_multi:
            if norm_cat in ["all", "single_table", "single-table", "single"]:
                st_dir = base_dir / "single_table"
                if st_dir.is_dir():
                    dataset_dirs.extend(
                        [d for d in st_dir.iterdir() if d.is_dir() and not d.name.startswith(".")]
                    )
            if norm_cat in ["all", "multi_table", "multi-table", "multi"]:
                mt_dir = base_dir / "multi_table"
                if mt_dir.is_dir():
                    dataset_dirs.extend(
                        [d for d in mt_dir.iterdir() if d.is_dir() and not d.name.startswith(".")]
                    )
        else:
            dataset_dirs = [
                d
                for d in base_dir.iterdir()
                if d.is_dir() and not d.name.startswith(".") and d.name != "archive"
            ]

        if not dataset_dirs:
            raise FileNotFoundError(
                f"No benchmark dataset folders found in {base_dir} (category={category_filter})"
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

        dataset_dirs.sort(key=lambda p: (p.parent.name, p.name))

        suite: list[BenchmarkDataset] = []
        for d in dataset_dirs:
            suite.append(cls.load_dataset(d))

        return suite


# Alias for backwards compatibility
BenchmarkDataLoader = SchemaMappingLoader
