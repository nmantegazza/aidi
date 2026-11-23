"""Executor for deterministic schema porting transformations."""

from __future__ import annotations

import time
from typing import Dict, List, Optional, Set, Tuple, Union

import pandas as pd

from schema_integration.execution.exceptions import (
    TableNotFoundError,
    UnresolvableColumnError,
    UnresolvableJoinError,
)
from schema_integration.execution.models import (
    ExecutionResult,
    PortedTable,
    PortingWarning,
)
from schema_integration.mapping.models import (
    Arithmetic,
    Concatenate,
    DirectCopy,
    MappingReport,
    MappingRule,
    SplitExtract,
    SplitUnnest,
    Substring,
    TypeCast,
)
from shared.ingestion.models import SourceData
from shared.schema_models import DataPackage


def _resolve_pandas_type(
    series: pd.Series,
    field_type: str,
    target_table: str,
    target_column: str,
    source_label: str,
    warnings: List[PortingWarning],
) -> pd.Series:
    """Coerce a Pandas Series to the target Frictionless Data type.

    Args:
        series: Input Pandas Series.
        field_type: Target Frictionless data type string.
        target_table: Target table name.
        target_column: Target column name.
        source_label: Source label identifier.
        warnings: List to append warning records to.

    Returns:
        Coerced Pandas Series.
    """
    try:
        if field_type == "integer":
            return pd.to_numeric(series, errors="coerce").astype("Int64")

        elif field_type == "number":
            return pd.to_numeric(series, errors="coerce")

        elif field_type == "boolean":
            mapping = {
                "true": True,
                "True": True,
                "TRUE": True,
                "1": True,
                True: True,
                "t": True,
                "T": True,
                "yes": True,
                "Yes": True,
                "YES": True,
                "y": True,
                "Y": True,
                "false": False,
                "False": False,
                "FALSE": False,
                "0": False,
                False: False,
                "f": False,
                "F": False,
                "no": False,
                "No": False,
                "NO": False,
                "n": False,
                "N": False,
            }
            return series.map(mapping).astype(pd.BooleanDtype())

        elif field_type == "date":
            return pd.to_datetime(series, errors="coerce").dt.date

        elif field_type == "datetime":
            return pd.to_datetime(series, errors="coerce")

        elif field_type in ["string", "text"]:
            return series.astype("string")

        else:
            warnings.append(
                PortingWarning(
                    target_table=target_table,
                    target_column=target_column,
                    source_label=source_label,
                    message=(
                        f"Unknown field type '{field_type}'. "
                        "Returning column as-is."
                    ),
                )
            )
            return series

    except Exception as exc:
        warnings.append(
            PortingWarning(
                target_table=target_table,
                target_column=target_column,
                source_label=source_label,
                message=f"Type cast failed for type '{field_type}': {exc}",
            )
        )
        return series


def _split_delimited_values(val: object, delimiter: str) -> List[str]:
    """Split a scalar string or JSON-like array into a list of cleaned tokens.

    Args:
        val: Input cell value.
        delimiter: Delimiter string to split on.

    Returns:
        List of non-empty string tokens.
    """
    if pd.isna(val) or val is None:
        return []
    s = str(val).strip()
    if not s or s in ["\\N", "nan", "None", "NULL"]:
        return []
    if s.startswith("[") and s.endswith("]"):
        try:
            import json

            parsed = json.loads(s)
            if isinstance(parsed, list):
                return [str(x).strip() for x in parsed if str(x).strip()]
        except Exception:
            pass
    return [part.strip() for part in s.split(delimiter) if part.strip()]


def _resolve_left_fk_cols(
    joined_df: pd.DataFrame,
    t_joined: str,
    left_col: Union[str, List[str]],
) -> Union[str, List[str]]:
    """Resolve foreign key column name(s) in joined_df.

    Args:
        joined_df: Current joined DataFrame.
        t_joined: Name of table already joined.
        left_col: Field or fields from foreign key definition.

    Returns:
        Resolved column name(s) present in joined_df.
    """
    if isinstance(left_col, str):
        if left_col in joined_df.columns:
            return left_col
        suffixed = f"{left_col}_{t_joined}"
        if suffixed in joined_df.columns:
            return suffixed
        return left_col
    else:
        return [
            col if col in joined_df.columns else f"{col}_{t_joined}"
            for col in left_col
        ]


def _get_staging_column(
    staging_df: pd.DataFrame,
    source_table: str,
    col: str,
) -> str:
    """Resolve column name in staging DataFrame for a specific source table.

    Args:
        staging_df: Joined staging DataFrame.
        source_table: Source table name.
        col: Source column name.

    Returns:
        Exact column name in staging_df.

    Raises:
        UnresolvableColumnError: If col cannot be resolved.
    """
    suffixed_col = f"{col}_{source_table}"
    if suffixed_col in staging_df.columns:
        return suffixed_col
    if col in staging_df.columns:
        return col
    raise UnresolvableColumnError(
        f"Source column '{col}' not found in source table '{source_table}'."
    )


def _build_source_staging_frame(
    target_table: str,
    table_rules: List[MappingRule],
    source_data: SourceData,
) -> pd.DataFrame:
    """Build joined staging DataFrame for a target table's source mapping rules.

    Args:
        target_table: Target table name.
        table_rules: Mapping rules targeting target_table.
        source_data: Source data containing dataframes and package schema.

    Returns:
        Joined Pandas DataFrame containing aligned rows from source tables.

    Raises:
        TableNotFoundError: If a mapped source table is missing in source_data.
        UnresolvableJoinError: If multi-table join cannot be resolved via FKs.
    """
    source_tables: List[str] = []
    for rule in table_rules:
        if rule.source_table not in source_data.tables:
            raise TableNotFoundError(
                f"Source table '{rule.source_table}' mapped for "
                f"source '{rule.source_label}' but not found in data."
            )
        if rule.source_table not in source_tables:
            source_tables.append(rule.source_table)

    if not source_tables:
        return pd.DataFrame()

    if len(source_tables) == 1:
        return source_data.tables[source_tables[0]].copy()

    joined_df = source_data.tables[source_tables[0]].copy()
    joined_table_names: Set[str] = {source_tables[0]}
    remaining_tables = source_tables[1:]

    resources_by_name = {r.name: r for r in source_data.package.resources}

    while remaining_tables:
        joined_any = False
        for t_next in list(remaining_tables):
            fk_match: Optional[
                Tuple[str, Union[str, List[str]], Union[str, List[str]]]
            ] = None

            # 1) Search FK on t_next referencing an already joined table
            res_next = resources_by_name.get(t_next)
            if res_next and res_next.schema_info:
                for fk in res_next.schema_info.foreignKeys:
                    if fk.reference.resource in joined_table_names:
                        fk_match = (
                            fk.reference.resource,
                            fk.reference.fields,
                            fk.fields,
                        )
                        break

            # 2) Search FK on an already joined table referencing t_next
            if not fk_match:
                for t_joined in joined_table_names:
                    res_joined = resources_by_name.get(t_joined)
                    if res_joined and res_joined.schema_info:
                        for fk in res_joined.schema_info.foreignKeys:
                            if fk.reference.resource == t_next:
                                fk_match = (
                                    t_joined,
                                    fk.fields,
                                    fk.reference.fields,
                                )
                                break
                        if fk_match:
                            break

            if fk_match:
                t_joined, left_col, right_col = fk_match
                left_on = _resolve_left_fk_cols(joined_df, t_joined, left_col)
                joined_df = pd.merge(
                    joined_df,
                    source_data.tables[t_next],
                    left_on=left_on,
                    right_on=right_col,
                    how="inner",
                    suffixes=("", f"_{t_next}"),
                )
                joined_table_names.add(t_next)
                remaining_tables.remove(t_next)
                joined_any = True
                break

        if not joined_any:
            raise UnresolvableJoinError(
                f"Target table '{target_table}' maps multiple source tables "
                f"{source_tables}, but no Foreign Key relationship is "
                f"declared in the source DataPackage between remaining tables "
                f"{remaining_tables} and existing tables {joined_table_names}."
            )

    return joined_df


def execute_porting(
    mapping_report: MappingReport,
    source_data: SourceData,
    target_schema: DataPackage,
) -> ExecutionResult:
    """Port raw source data into target schema according to mapping rules.

    Args:
        mapping_report: Validated MappingReport for the source dataset.
        source_data: SourceData containing raw DataFrames and metadata.
        target_schema: Target schema DataPackage.

    Returns:
        ExecutionResult containing ported tables and execution stats.

    Raises:
        TableNotFoundError: If a mapped source table is missing.
        UnresolvableColumnError: If a mapped source column is missing.
        UnresolvableJoinError: If a multi-table join cannot be resolved.
    """
    start_time = time.perf_counter()

    # Group rules by target_table
    rules_by_table: Dict[str, List[MappingRule]] = {}
    for rule in mapping_report.rules:
        rules_by_table.setdefault(rule.target_table, []).append(rule)

    ported_tables: Dict[str, PortedTable] = {}

    for target_resource in target_schema.resources:
        table_name = target_resource.name
        warnings: List[PortingWarning] = []
        output_data: Dict[str, pd.Series] = {}

        table_rules = rules_by_table.get(table_name, [])

        if not table_rules:
            # Table not involved for this source: return empty DataFrame
            cols = [f.name for f in target_resource.schema_info.fields]
            df_empty = pd.DataFrame(columns=cols)
            ported_tables[table_name] = PortedTable(
                target_table_name=table_name,
                dataframe=df_empty,
                warnings=warnings,
            )
            continue

        staging_df = _build_source_staging_frame(
            table_name, table_rules, source_data
        )

        # Apply any SplitUnnest transformations to staging_df first
        for rule in table_rules:
            for trans in rule.transformations:
                if isinstance(trans, SplitUnnest):
                    if rule.source_columns:
                        col_name = _get_staging_column(
                            staging_df,
                            rule.source_table,
                            rule.source_columns[0],
                        )
                        staging_df[col_name] = staging_df[col_name].apply(
                            lambda v, d=trans.delimiter: _split_delimited_values(
                                v, d
                            )
                        )
                        staging_df = staging_df.explode(col_name).reset_index(
                            drop=True
                        )

        num_rows = len(staging_df)

        for rule in table_rules:
            src_raw = source_data.tables[rule.source_table]
            for col in rule.source_columns:
                if col not in src_raw.columns:
                    raise UnresolvableColumnError(
                        f"Source column '{col}' not found in source table "
                        f"'{rule.source_table}'."
                    )

            series: Optional[pd.Series] = None
            if len(rule.source_columns) == 1:
                col_name = _get_staging_column(
                    staging_df, rule.source_table, rule.source_columns[0]
                )
                series = staging_df[col_name].copy()

            for trans in rule.transformations:
                if isinstance(trans, DirectCopy):
                    if series is None and rule.source_columns:
                        col_name = _get_staging_column(
                            staging_df,
                            rule.source_table,
                            rule.source_columns[0],
                        )
                        series = staging_df[col_name].copy()

                elif isinstance(trans, SplitUnnest):
                    if series is None and rule.source_columns:
                        col_name = _get_staging_column(
                            staging_df,
                            rule.source_table,
                            rule.source_columns[0],
                        )
                        series = staging_df[col_name].copy()

                elif isinstance(trans, Concatenate):
                    valid_cols = [
                        staging_df[
                            _get_staging_column(
                                staging_df, rule.source_table, c
                            )
                        ]
                        for c in rule.source_columns
                    ]
                    series = (
                        pd.concat(valid_cols, axis=1)
                        .astype(str)
                        .agg(trans.delimiter.join, axis=1)
                    )

                elif isinstance(trans, SplitExtract):
                    base_s = (
                        series
                        if series is not None
                        else staging_df[
                            _get_staging_column(
                                staging_df,
                                rule.source_table,
                                rule.source_columns[0],
                            )
                        ]
                    )
                    series = (
                        base_s.astype(str)
                        .str.split(trans.delimiter)
                        .str.get(trans.index)
                    )

                elif isinstance(trans, Substring):
                    base_s = (
                        series
                        if series is not None
                        else staging_df[
                            _get_staging_column(
                                staging_df,
                                rule.source_table,
                                rule.source_columns[0],
                            )
                        ]
                    )
                    series = base_s.astype(str).str.slice(
                        trans.start, trans.end
                    )

                elif isinstance(trans, TypeCast):
                    base_s = (
                        series
                        if series is not None
                        else staging_df[
                            _get_staging_column(
                                staging_df,
                                rule.source_table,
                                rule.source_columns[0],
                            )
                        ]
                    )
                    series = _resolve_pandas_type(
                        base_s,
                        trans.target_type,
                        rule.target_table,
                        rule.target_column,
                        rule.source_label,
                        warnings,
                    )

                elif isinstance(trans, Arithmetic):
                    base_s = (
                        series
                        if series is not None
                        else staging_df[
                            _get_staging_column(
                                staging_df,
                                rule.source_table,
                                rule.source_columns[0],
                            )
                        ]
                    )
                    numeric = pd.to_numeric(base_s, errors="coerce")
                    null_before = (
                        base_s.isna().sum() if base_s is not None else 0
                    )
                    null_after = numeric.isna().sum()
                    if null_after > null_before:
                        warnings.append(
                            PortingWarning(
                                target_table=rule.target_table,
                                target_column=rule.target_column,
                                source_label=rule.source_label,
                                message=(
                                    f"Arithmetic operation coerced "
                                    f"{null_after - null_before} values to NaN."
                                ),
                            )
                        )

                    ops = {
                        "+": lambda s, o: s + o,
                        "-": lambda s, o: s - o,
                        "*": lambda s, o: s * o,
                        "/": lambda s, o: s / o,
                    }
                    series = ops[trans.operator](numeric, trans.operand)

            if series is None:
                series = pd.Series([pd.NA] * num_rows)

            field_def = target_resource.schema_info.get_field(
                rule.target_column
            )
            field_type = field_def.type if field_def else "string"

            series = _resolve_pandas_type(
                series,
                field_type,
                rule.target_table,
                rule.target_column,
                rule.source_label,
                warnings,
            )

            output_data[rule.target_column] = series

        for f in target_resource.schema_info.fields:
            if f.name not in output_data:
                output_data[f.name] = pd.Series([pd.NA] * num_rows)

        df_result = pd.DataFrame(output_data)
        final_cols = [f.name for f in target_resource.schema_info.fields]
        df_result = df_result[final_cols]

        ported_tables[table_name] = PortedTable(
            target_table_name=table_name,
            dataframe=df_result,
            warnings=warnings,
        )

    total_rows = sum(pt.dataframe.shape[0] for pt in ported_tables.values())
    processing_time_ms = (time.perf_counter() - start_time) * 1000

    return ExecutionResult(
        tables=ported_tables,
        total_rows=total_rows,
        processing_time_ms=processing_time_ms,
    )

