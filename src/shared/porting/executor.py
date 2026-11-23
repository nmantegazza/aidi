from __future__ import annotations
import pandas as pd
import time
from typing import List, Dict, Optional, Tuple, Any

from shared.ingestion import SourceData
from shared.schema_models import TableResource, IntegrationReport
from shared.porting.models import (
    PortingWarning,
    PortingReport,
    PortedTable,
    PortingInstructionsReport,
    DataPortingError,
    UnresolvableColumnError,
    TableNotFoundError,
    TypeCastError,
)

def _resolve_pandas_type(
    series: pd.Series,
    field_type: str,
    column_name: str,
    global_table: str,
    warnings: List[PortingWarning],
    source_label: str,
) -> pd.Series:
    """
    Coerces a Pandas Series to the target Frictionless Data type.
    Uses 'coerce' for numeric/date types so invalid values become NaN/NaT.
    """
    try:
        if field_type == "integer":
            # Using Int64 for nullable integer support
            return pd.to_numeric(series, errors='coerce').astype('Int64')
        
        elif field_type == "number":
            return pd.to_numeric(series, errors='coerce')
        
        elif field_type == "boolean":
            # Handle string-based and mixed booleans by coercing unknowns to <NA>
            mapping = {
                'true': True, 'True': True, 'TRUE': True, '1': True, 1: True, True: True, 't': True, 'T': True, 'yes': True, 'Yes': True, 'YES': True, 'y': True, 'Y': True,
                'false': False, 'False': False, 'FALSE': False, '0': False, 0: False, False: False, 'f': False, 'F': False, 'no': False, 'No': False, 'NO': False, 'n': False, 'N': False
            }
            return series.map(mapping).astype(pd.BooleanDtype())
        
        elif field_type == "date":
            return pd.to_datetime(series, errors='coerce').dt.date
        
        elif field_type == "datetime":
            return pd.to_datetime(series, errors='coerce')
        
        elif field_type in ["string", "text"]:
            # 'string' dtype safely preserves missing values (pd.NA, None, np.nan)
            # without destroying valid strings like "None" or "nan"
            return series.astype("string")
        
        else:
            warnings.append(PortingWarning(
                global_table=global_table,
                global_column=column_name,
                source_label=source_label,
                message=f"Unknown type '{field_type}'. Returning column as-is."
            ))
            return series

    except Exception as e:
        warnings.append(PortingWarning(
            global_table=global_table,
            global_column=column_name,
            source_label=source_label,
            message=f"Type cast failed for type '{field_type}': {e}"
        ))
        return series

class DataPorter:
    def __init__(
        self,
        source_a: SourceData,
        source_b: SourceData,
        integration_report: IntegrationReport,
        porting_instructions: PortingInstructionsReport,
    ):
        self.source_a = source_a
        self.source_b = source_b
        self.report = integration_report
        self.porting_instructions = porting_instructions

    def port(self) -> Tuple[Dict[str, PortedTable], PortingReport]:
        """
        Executes the porting process for all tables in the global schema.
        """
        start_time = time.perf_counter()
        results = {}
        total_rows_a = 0
        total_rows_b = 0
        total_warnings = 0

        for resource in self.report.global_schema.resources:
            global_table_name = resource.name
            warnings = []

            # 1. Port Source A
            df_a = self._port_single_table(resource, self.source_a.package.name, self.source_a, warnings)

            # 2. Port Source B
            df_b = self._port_single_table(resource, self.source_b.package.name, self.source_b, warnings)

            results[global_table_name] = PortedTable(
                global_table_name=global_table_name,
                df_a=df_a,
                df_b=df_b,
                warnings=warnings
            )

            # Track metrics
            total_rows_a += len(df_a)
            total_rows_b += len(df_b)
            total_warnings += len(warnings)
        
        end_time = time.perf_counter()
        processing_time_ms = (end_time - start_time) * 1000

        report = PortingReport(
            total_tables=len(results),
            total_rows_source_a=total_rows_a,
            total_rows_source_b=total_rows_b,
            total_warnings=total_warnings,
            processing_time_ms=processing_time_ms
        )

        return results, report

    def _port_single_table(
        self,
        global_resource: TableResource,
        source_label: str,
        source_data: SourceData,
        warnings: List[PortingWarning],
    ) -> pd.DataFrame:
        """
        Aligns a source DataFrame to a single global table schema using the AST instructions.
        """
        instructions = self.porting_instructions.global_table_instructions.get(global_resource.name)
        if not instructions:
            # No instructions for this global table
            cols = [f.name for f in global_resource.schema_info.fields]
            return pd.DataFrame(columns=cols)

        # Step 1: Construction
        df_staging = None
        for recipe in instructions.construction_recipes:
            # Check if this recipe applies to the current source
            if recipe.type == "single" and recipe.source_label == source_label:
                if recipe.table_name in source_data.tables:
                    if df_staging is None:
                        df_staging = source_data.tables[recipe.table_name].copy()
                    else:
                        # Fallback for chaining single tables if they have identical schemas (unlikely but possible)
                        df_staging = pd.concat([df_staging, source_data.tables[recipe.table_name]], ignore_index=True)
                else:
                    raise TableNotFoundError(f"Source table '{recipe.table_name}' mapped for '{source_label}' but not found in loaded data.")
            
            elif recipe.type == "join" and recipe.left_source == source_label and recipe.right_source == source_label:
                if recipe.left_table not in source_data.tables:
                    raise TableNotFoundError(f"Left source table '{recipe.left_table}' mapped for '{source_label}' but not found.")
                if recipe.right_table not in source_data.tables:
                    raise TableNotFoundError(f"Right source table '{recipe.right_table}' mapped for '{source_label}' but not found.")

                df_left = source_data.tables[recipe.left_table].copy()
                df_right = source_data.tables[recipe.right_table].copy()

                if recipe.left_on not in df_left.columns:
                    raise UnresolvableColumnError(f"Join key '{recipe.left_on}' not found in left table '{recipe.left_table}'.")
                if recipe.right_on not in df_right.columns:
                    raise UnresolvableColumnError(f"Join key '{recipe.right_on}' not found in right table '{recipe.right_table}'.")

                # Perform the join, prefixing suffixes with table names to help resolve collisions if any
                merged_df = pd.merge(
                    df_left, 
                    df_right, 
                    how=recipe.join_type, 
                    left_on=recipe.left_on, 
                    right_on=recipe.right_on,
                    suffixes=(f"_{recipe.left_table}", f"_{recipe.right_table}")
                )

                if df_staging is None:
                    df_staging = merged_df
                else:
                    # Multiple recipes for the same table typically act as a UNION.
                    # We concatenate them instead of invalidly merging them again.
                    df_staging = pd.concat([df_staging, merged_df], ignore_index=True)
        
        if df_staging is None or df_staging.empty:
            # Source not involved in this global table
            cols = [f.name for f in global_resource.schema_info.fields]
            return pd.DataFrame(columns=cols)

        # Step 2: Column Transformations
        
        def _get_column(df: pd.DataFrame, col_name: str) -> Optional[pd.Series]:
            """Helper to extract a column, resolving dot-notation and join collisions."""
            if not col_name:
                return None
            
            # 1. Exact match
            if col_name in df.columns:
                return df[col_name]
                
            # 2. Dot notation match (table.column or source.table.column)
            parts = col_name.split(".")
            if len(parts) >= 2:
                table = parts[-2]
                col = parts[-1]
                suffix_col = f"{col}_{table}"
                if suffix_col in df.columns:
                    return df[suffix_col]
                # If pandas merge didn't add a suffix (e.g. column name was unique)
                if col in df.columns:
                    return df[col]
                    
            # 3. Fallback to startswith if unambiguous
            matches = [c for c in df.columns if c.startswith(f"{col_name}_")]
            if len(matches) == 1:
                return df[matches[0]]
                
            return None

        output_data = {}
        for field in global_resource.schema_info.fields:
            trans_list = instructions.field_transformations.get(field.name, [])
            series = None
            
            for trans in trans_list:
                if trans.source_label != source_label:
                    continue
                
                # Fetch base series: either the current accumulated series, or from df_staging
                if trans.type == "direct":
                    col_series = _get_column(df_staging, trans.source_column)
                    if col_series is not None:
                        series = col_series
                elif trans.type == "concat":
                    valid_series = [_get_column(df_staging, c) for c in trans.source_columns]
                    valid_series = [s for s in valid_series if s is not None]
                    if valid_series:
                        series = pd.concat(valid_series, axis=1).astype(str).agg(trans.delimiter.join, axis=1)
                elif trans.type == "split":
                    col_series = _get_column(df_staging, trans.source_column)
                    if col_series is not None:
                        series = col_series.astype(str).str.split(trans.delimiter).str.get(trans.index)
                elif trans.type == "slice":
                    col_series = _get_column(df_staging, trans.source_column)
                    if col_series is not None:
                        series = col_series.astype(str).str.slice(trans.start, trans.end)
                else:
                    # For cumulative operations, use `series` if it exists, otherwise fetch `source_column` from staging
                    base_series = series if series is not None else _get_column(df_staging, getattr(trans, 'source_column', None))
                    
                    if base_series is not None:
                        if trans.type == "type_cast":
                            series = _resolve_pandas_type(
                                base_series,
                                trans.target_type,
                                field.name,
                                global_resource.name,
                                warnings,
                                source_label
                             )
                        elif trans.type == "math_operation":
                            numeric_series = pd.to_numeric(base_series, errors='coerce')
                            # Log warnings for dropped data
                            null_before = base_series.isna().sum()
                            null_after = numeric_series.isna().sum()
                            if null_after > null_before:
                                warnings.append(PortingWarning(
                                    global_table=global_resource.name,
                                    global_column=field.name,
                                    source_label=source_label,
                                    message=f"Math operation coerced {null_after - null_before} values to NaN."
                                ))
                            
                            if trans.operator == "+":
                                series = numeric_series + trans.operand
                            elif trans.operator == "-":
                                series = numeric_series - trans.operand
                            elif trans.operator == "*":
                                series = numeric_series * trans.operand
                            elif trans.operator == "/":
                                series = numeric_series / trans.operand

            if series is None:
                series = pd.Series([pd.NA] * len(df_staging), index=df_staging.index)
            
            # Final Type Resolution
            output_data[field.name] = _resolve_pandas_type(
                series,
                field.type,
                field.name,
                global_resource.name,
                warnings,
                source_label
            )

        # Ensure correct column order
        final_cols = [f.name for f in global_resource.schema_info.fields]
        return pd.DataFrame(output_data)[final_cols]

def port_data_to_global_schema(
    source_a: SourceData,
    source_b: SourceData,
    integration_report: IntegrationReport,
    porting_instructions: PortingInstructionsReport,
) -> Tuple[Dict[str, PortedTable], PortingReport]:
    """
    Convenience functional API for data porting.
    """
    return DataPorter(source_a, source_b, integration_report, porting_instructions).port()
