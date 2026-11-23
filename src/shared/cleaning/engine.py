import pandas as pd
import numpy as np
import unicodedata
import re
import warnings
import time
from typing import Dict, Tuple, List
from pandas.api.types import (
    is_string_dtype, 
    is_numeric_dtype, 
    is_object_dtype
)

from shared.ingestion import SourceData
from .models import CleaningReport, CleaningExample




def _native_clean_text(series: pd.Series) -> pd.Series:
    """
    Native implementation of text cleaning without recordlinkage dependency.
    - NFC Normalization
    - Lowercase
    - Remove punctuation (optional, common for ER)
    - Strip accents
    """
    def clean_val(val):
        if pd.isna(val):
            return val
        s = str(val)
        # Unicode normalization (NFC)
        s = unicodedata.normalize('NFC', s)
        # Lowercase
        s = s.lower()
        # Accent stripping (Manual native implementation)
        s = ''.join(c for c in unicodedata.normalize('NFD', s)
                   if unicodedata.category(c) != 'Mn')
        # Normalize back to NFC
        s = unicodedata.normalize('NFC', s)
        # Basic regex to strip extra whitespace and non-alphanumeric (common for ER preprocessing)
        s = re.sub(r'[^\w\s]', '', s)
        s = re.sub(r'\s+', ' ', s).strip()
        return s

    return series.apply(clean_val)

def _infer_column_type(col_series: pd.Series, col_name: str) -> Tuple[pd.Series, List[CleaningExample]]:
    """Heuristically promotes object/string columns to datetime or numeric if applicable."""
    examples = []
    sample = col_series.dropna().head(10)
    if sample.empty:
        return col_series, examples

    # A. Try Numeric (Priority)
    try:
        # Check if they are actually numbers and not just large integers that look like dates
        num_sample = pd.to_numeric(sample, errors='coerce')
        if (num_sample.notnull().sum() / len(sample)) > 0.8:
            new_series = pd.to_numeric(col_series, errors='coerce')
            examples.append(CleaningExample(
                column=col_name, operation="type_promotion_numeric",
                before=str(sample.iloc[0]), after=str(new_series.loc[sample.index[0]])
            ))
            return new_series, examples
    except Exception:
        pass

    # B. Try Datetime
    try:
        # Avoid false positives for small numbers (like 10.5 which pd.to_datetime makes 1970...)
        if is_numeric_dtype(sample):
             return col_series, examples

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            dt_sample = pd.to_datetime(sample, errors='coerce')
        
        if (dt_sample.notnull().sum() / len(sample)) > 0.8:
            # Additional heuristic: if all timestamps are very close to 1970-01-01, it's likely numeric noise
            if dt_sample.dt.year.max() < 1971 and dt_sample.dt.year.min() >= 1970:
                 # Check if the original sample was actually numeric-like
                 if pd.to_numeric(sample, errors='coerce').notnull().all():
                      return col_series, examples

            new_series = pd.to_datetime(col_series, errors='coerce', format='mixed').dt.tz_localize(None)
            examples.append(CleaningExample(
                column=col_name, operation="type_promotion_datetime",
                before=str(sample.iloc[0]), after=str(new_series.loc[sample.index[0]])
            ))
            return new_series, examples
    except Exception:
        pass

    return col_series, examples

def _handle_whitespace(col_series: pd.Series, col_name: str) -> Tuple[pd.Series, int, List[CleaningExample]]:
    """Converts whitespace-only strings to NaN."""
    examples = []
    if not (is_object_dtype(col_series) or is_string_dtype(col_series)):
        return col_series, 0, []

    # Efficient vectorized check
    mask_whitespace = col_series.astype(str).str.strip() == ""
    mask_not_null = col_series.notnull()
    affected = mask_whitespace & mask_not_null
    
    count = affected.sum()
    if count > 0:
        idx = col_series[affected].index[0]
        examples.append(CleaningExample(
            column=col_name, operation="whitespace_to_nan",
            before=str(col_series.loc[idx]), after=None
        ))
        col_series = col_series.copy()
        col_series.loc[affected] = np.nan
        
    return col_series, count, examples

def clean_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, CleaningReport]:
    """
    Core cleaning engine standardized for shared use.
    Handles: Unicode, accents, whitespace, and basic type inference.
    """
    start_time = time.perf_counter()
    df_clean = df.copy()
    rows_before = len(df_clean)
    examples = []
    ws_count = 0
    total_transforms = 0

    # 1. Column-level cleaning
    for col_name in df_clean.columns:
        col_series = df_clean[col_name]
        col_start = col_series.copy()

        # A. Whitespace
        col_series, c, ex = _handle_whitespace(col_series, col_name)
        ws_count += c
        examples.extend(ex)

        # B. Potential Type Promotion (Run first if object-like)
        is_string_like = is_string_dtype(col_series) or is_object_dtype(col_series)
        
        if is_string_like:
            # Check if it looks like a number/date first
            col_series, type_ex = _infer_column_type(col_series, col_name)
            examples.extend(type_ex)
            
            # Re-check if it's still string-like after promotion
            if is_string_dtype(col_series) or is_object_dtype(col_series):
                # Sample for "before" example
                sample_idx = col_series.first_valid_index()
                before_val = str(col_series.loc[sample_idx]) if sample_idx is not None else None
                
                col_series = _native_clean_text(col_series)
                
                if sample_idx is not None and before_val != str(col_series.loc[sample_idx]):
                     examples.append(CleaningExample(
                          column=col_name, operation="text_normalization",
                          before=before_val, after=str(col_series.loc[sample_idx])
                      ))

        # Track total cells changed in this column (excluding nulls that stayed null)
        changed_mask = (col_series != col_start) & (col_series.notnull() | col_start.notnull())
        total_transforms += changed_mask.sum()
        
        df_clean[col_name] = col_series

    # 2. Duplicate Removal
    df_no_dupes = df_clean.drop_duplicates()
    dupes_removed = rows_before - len(df_no_dupes)
    
    end_time = time.perf_counter()

    report = CleaningReport(
        rows_before=rows_before,
        rows_after=len(df_no_dupes),
        duplicates_removed=dupes_removed,
        whitespace_cells_nullified=ws_count,
        total_transformations=int(total_transforms),
        processing_time_ms=(end_time - start_time) * 1000,
        examples=examples
    )
    
    return df_no_dupes, report

def clean_source_data(source: SourceData) -> Tuple[SourceData, Dict[str, CleaningReport]]:
    """
    Helper to clean an entire SourceData package.
    Returns a new SourceData instance with cleaned tables and a map of reports.
    """
    cleaned_tables = {}
    reports = {}
    
    for table_name, df in source.tables.items():
        df_clean, report = clean_data(df)
        cleaned_tables[table_name] = df_clean
        reports[table_name] = report

    new_source = SourceData(
        package=source.package,
        tables=cleaned_tables,
        base_path=source.base_path
    )
    
    return new_source, reports
