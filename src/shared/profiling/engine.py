import pandas as pd
import numpy as np
import time
from typing import Optional, List, Dict, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from .models import TableProfile, ColumnProfile, GUITableProfile, GUIColumnProfile
from shared.ingestion import SourceData




class DataProfiler:
    """
    Engine for profiling pandas DataFrames to extract metadata for LLM agents.
    """

    @staticmethod
    def profile_source_data(source: SourceData) -> Dict[str, TableProfile]:
        """
        Profiles all tables in a SourceData package with rich console output.
        """
        profiles = {}
        for name, df in source.tables.items():
            profiles[name] = DataProfiler.profile_dataframe(df, name)

        
        return profiles

    @staticmethod
    def profile_dataframe(
        df: pd.DataFrame, 
        name: str, 
        sample_size: int = 5,
        max_distinct_samples: int = 5
    ) -> TableProfile:
        """
        Generates a comprehensive profile of the provided DataFrame.
        """
        start_time = time.perf_counter()
        total_rows = len(df)
        total_columns = len(df.columns)
        
        column_profiles = {}
        total_null_pct = 0.0

        for col in df.columns:
            prof = DataProfiler._profile_column(
                df, col, total_rows, max_distinct_samples
            )
            column_profiles[col] = prof
            total_null_pct += prof.null_percentage

        # Extract sample rows (safely handling NaN for JSON serialization)
        sample_df = df.head(sample_size).replace({np.nan: None})
        sample_rows = sample_df.to_dict(orient="records")

        # Calculate completeness (avg non-null percentage)
        avg_null_pct = total_null_pct / total_columns if total_columns > 0 else 0.0
        completeness = 100.0 - avg_null_pct
        
        end_time = time.perf_counter()

        return TableProfile(
            table_name=name,
            total_rows=total_rows,
            total_columns=total_columns,
            completeness_score=float(completeness),
            processing_time_ms=(end_time - start_time) * 1000,
            column_profiles=column_profiles,
            sample_rows=sample_rows
        )

    @staticmethod
    def _profile_column(
        df: pd.DataFrame, 
        col: str, 
        total_rows: int,
        max_distinct_samples: int
    ) -> ColumnProfile:
        """
        Profiles a single column.
        """
        series = df[col]
        null_count = int(series.isnull().sum())
        null_percentage = float(round((null_count / total_rows) * 100, 2)) if total_rows > 0 else 100.0
        
        # Unique values (excluding nulls)
        non_null_series = series.dropna()
        unique_values = non_null_series.unique()
        cardinality = len(unique_values)
        uniqueness_percentage = float(round((cardinality / total_rows) * 100, 2)) if total_rows > 0 else 0.0
        
        # Samples
        distinct_samples = [str(x) for x in unique_values[:max_distinct_samples]]
        
        # Length stats for strings
        avg_length = None
        if non_null_series.dtype == object or non_null_series.dtype == 'string':
            try:
                avg_length = float(round(non_null_series.astype(str).str.len().mean(), 2))
            except:
                pass

        # Min/Max (if applicable)
        min_val = None
        max_val = None
        if not non_null_series.empty:
            try:
                # Basic types only for serialization safety
                raw_min = non_null_series.min()
                raw_max = non_null_series.max()
                min_val = raw_min if isinstance(raw_min, (int, float, str)) else str(raw_min)
                max_val = raw_max if isinstance(raw_max, (int, float, str)) else str(raw_max)
            except:
                pass

        return ColumnProfile(
            name=col,
            dtype=str(series.dtype),
            null_count=null_count,
            null_percentage=null_percentage,
            cardinality=cardinality,
            uniqueness_percentage=uniqueness_percentage,
            distinct_samples=distinct_samples,
            avg_length=avg_length,
            min_value=min_val,
            max_value=max_val
        )


class GUIProfiler:
    """
    Engine for profiling pandas DataFrames to extract rich statistics for the GUI.
    """

    @staticmethod
    def profile_source_data(source: SourceData) -> Dict[str, GUITableProfile]:
        """
        Profiles all tables in a SourceData package.
        """
        profiles = {}
        for name, df in source.tables.items():
            profiles[name] = GUIProfiler.profile_dataframe(df, name)
        return profiles

    @staticmethod
    def profile_dataframe(
        df: pd.DataFrame,
        name: str,
        sample_size: int = 5,
        max_distinct_samples: int = 5
    ) -> GUITableProfile:
        """
        Generates a rich profile of the provided DataFrame for GUI use.
        """
        start_time = time.perf_counter()
        total_rows = len(df)
        total_columns = len(df.columns)
        column_profiles = {}
        total_null_pct = 0.0

        for col in df.columns:
            prof = GUIProfiler._profile_column(
                df, col, total_rows, max_distinct_samples
            )
            column_profiles[col] = prof
            total_null_pct += prof.null_percentage

        # Extract sample rows
        sample_df = df.head(sample_size).replace({np.nan: None})
        sample_rows = sample_df.to_dict(orient="records")

        # Calculate completeness (avg non-null percentage)
        avg_null_pct = total_null_pct / total_columns if total_columns > 0 else 0.0
        completeness = 100.0 - avg_null_pct
        
        end_time = time.perf_counter()

        return GUITableProfile(
            table_name=name,
            total_rows=total_rows,
            total_columns=total_columns,
            completeness_score=float(completeness),
            processing_time_ms=(end_time - start_time) * 1000,
            column_profiles=column_profiles,
            sample_rows=sample_rows
        )

    @staticmethod
    def _profile_column(
        df: pd.DataFrame,
        col: str,
        total_rows: int,
        max_distinct_samples: int
    ) -> GUIColumnProfile:
        """
        Profiles a single column with rich stats.
        """
        # Get base profile first by reusing DataProfiler logic
        base = DataProfiler._profile_column(df, col, total_rows, max_distinct_samples)

        series = df[col]
        non_null_series = series.dropna()

        # 1. Top Frequencies
        top_freqs = {}
        if not non_null_series.empty:
            counts = non_null_series.value_counts(normalize=True).head(5)
            top_freqs = {str(k): float(round(v * 100, 1)) for k, v in counts.items()}

        # 2. Numeric Stats
        numeric_stats = None
        if pd.api.types.is_numeric_dtype(series) and not non_null_series.empty:
            try:
                numeric_stats = {
                    "min": float(non_null_series.min()),
                    "max": float(non_null_series.max()),
                    "mean": float(round(non_null_series.mean(), 2)),
                    "median": float(round(non_null_series.median(), 2))
                }
            except:
                pass

        # 3. String Stats
        string_stats = None
        if (series.dtype == object or series.dtype == 'string') and not non_null_series.empty:
            try:
                lens = non_null_series.astype(str).str.len()
                string_stats = {
                    "min_length": float(lens.min()),
                    "max_length": float(lens.max()),
                    "avg_length": float(round(lens.mean(), 2))
                }
            except:
                pass

        return GUIColumnProfile(
            **base.model_dump(),
            top_frequencies=top_freqs,
            numeric_stats=numeric_stats,
            string_stats=string_stats
        )
