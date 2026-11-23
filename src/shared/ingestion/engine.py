import json
from pathlib import Path
from typing import Dict, Tuple, Union, List
import pandas as pd
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from ..schema_models import DataPackage, TableResource
from .models import SourceData, IngestionReport, TableIngestionReport, FKInfo
from .exceptions import (
    DataIngestionError,
    DataPackageNotFound,
    ResourceFileNotFound,
    SchemaMismatchError
)




class DataLoader:
    def __init__(self, strict_type_validation: bool = False):
        self.strict_type_validation = strict_type_validation

    def load_integration_input(self, root_path: str | Path) -> Tuple[SourceData, IngestionReport, SourceData, IngestionReport]:
        """
        Loads Source A and Source B from a unified root directory.
        Expected structure: root/source_a/... and root/source_b/...
        """
        root = Path(root_path).resolve()
        
        source_a_path = root / "source_a"
        source_b_path = root / "source_b"
        
        if not source_a_path.exists():
            raise DataPackageNotFound(f"Source A directory missing: {source_a_path}")
        if not source_b_path.exists():
            raise DataPackageNotFound(f"Source B directory missing: {source_b_path}")
            
        source_a, report_a = self.load_source(source_a_path)
        source_b, report_b = self.load_source(source_b_path)
        
        return source_a, report_a, source_b, report_b

    def load_source(self, source_root: Path) -> Tuple[SourceData, IngestionReport]:
        """Loads a single source package."""
        source_root = Path(source_root).resolve()
        descriptor_path = source_root / "datapackage.json"
        
        if not descriptor_path.exists():
            raise DataPackageNotFound(f"datapackage.json not found at {descriptor_path}")
            
        with open(descriptor_path, "r") as f:
            data = json.load(f)
            package = DataPackage.model_validate(data)
            
        source_name = package.name
        tables = {}
        table_reports = {}
        total_rows = 0

        for resource in package.resources:
            df = self._load_resource(resource, source_root)
            self._validate_columns(df, resource)
            if self.strict_type_validation:
                self._validate_types(df, resource)
            
            tables[resource.name] = df
            
            # Create report for this table
            fk_infos = []
            for fk in resource.schema_info.foreignKeys:
                fk_infos.append(FKInfo(
                    local_fields=[fk.fields] if isinstance(fk.fields, str) else fk.fields,
                    target_resource=fk.reference.resource,
                    target_fields=[fk.reference.fields] if isinstance(fk.reference.fields, str) else fk.reference.fields
                ))

            report = TableIngestionReport(
                name=resource.name,
                row_count=len(df),
                col_count=len(df.columns),
                columns={f.name: f.type for f in resource.schema_info.fields},
                primary_keys=resource.schema_info.primary_key_columns,
                foreign_keys=fk_infos
            )
            table_reports[resource.name] = report
            total_rows += len(df)

        final_report = IngestionReport(
            source_name=source_name,
            base_path=str(source_root),
            tables=table_reports,
            total_rows=total_rows
        )

        return SourceData(package=package, tables=tables, base_path=source_root), final_report

    def _load_resource(self, resource: TableResource, root: Path) -> pd.DataFrame:
        """Loads a parquet file for a specific resource."""
        abs_path = root / resource.path
        if not abs_path.exists():
            raise ResourceFileNotFound(f"Parquet file for resource '{resource.name}' missing at {abs_path}")
            
        try:
            return pd.read_parquet(abs_path)
        except Exception as e:
            raise DataIngestionError(f"Failed to read parquet file at {abs_path}: {e}")

    def _validate_columns(self, df: pd.DataFrame, resource: TableResource) -> None:
        """Ensures all columns declared in the schema are present in the DataFrame."""
        schema_cols = {f.name for f in resource.schema_info.fields}
        df_cols = set(df.columns)
        
        missing = schema_cols - df_cols
        if missing:
            raise SchemaMismatchError(
                f"Resource '{resource.name}' missing columns defined in schema: {list(missing)}"
            )

    def _validate_types(self, df: pd.DataFrame, resource: TableResource) -> None:
        """
        Soft type validation. Currently just logs warnings if types seem mismatched.
        """
        # console.print(f"[yellow]Note: Strict type validation check for resource '{resource.name}' is enabled but currently informative.[/yellow]")
        pass
