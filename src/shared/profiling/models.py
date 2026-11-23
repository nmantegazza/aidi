from __future__ import annotations
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class ColumnProfile(BaseModel):
    """Profile metadata for a single column."""
    name: str
    dtype: str
    null_count: int
    null_percentage: float
    cardinality: int
    uniqueness_percentage: float
    distinct_samples: List[str]
    avg_length: Optional[float] = None
    min_value: Optional[Any] = None
    max_value: Optional[Any] = None

class GUIColumnProfile(ColumnProfile):
    """Extended profile metadata for GUI visualization."""
    top_frequencies: Dict[str, float] = Field(default_factory=dict) # Value -> Percentage
    numeric_stats: Optional[Dict[str, float]] = None                # min, max, mean, median
    string_stats: Optional[Dict[str, float]] = None                 # min_length, max_length, avg_length

class TableProfile(BaseModel):
    """Profile metadata for a full table/dataframe."""
    table_name: str
    total_rows: int
    total_columns: int
    completeness_score: float = 0.0                # Avg non-null % across columns
    processing_time_ms: float = 0.0
    column_profiles: Dict[str, ColumnProfile]
    sample_rows: List[Dict[str, Any]] = Field(default_factory=list)

    def get_column(self, name: str) -> Optional[ColumnProfile]:
        return self.column_profiles.get(name)

class GUITableProfile(BaseModel):
    """Extended table profile for GUI visualization."""
    table_name: str
    total_rows: int
    total_columns: int
    completeness_score: float = 0.0
    processing_time_ms: float = 0.0
    column_profiles: Dict[str, GUIColumnProfile]
    sample_rows: List[Dict[str, Any]] = Field(default_factory=list)
