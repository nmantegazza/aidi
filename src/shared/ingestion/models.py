from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List
from pydantic import BaseModel, Field
import pandas as pd
from ..schema_models import DataPackage

class FKInfo(BaseModel):
    local_fields: List[str]
    target_resource: str
    target_fields: List[str]

class TableIngestionReport(BaseModel):
    name: str
    row_count: int
    col_count: int
    columns: Dict[str, str]                       # name -> type
    primary_keys: List[str] = Field(default_factory=list)
    foreign_keys: List[FKInfo] = Field(default_factory=list)

class IngestionReport(BaseModel):
    source_name: str
    base_path: str
    tables: Dict[str, TableIngestionReport]
    total_rows: int = 0

@dataclass
class SourceData:
    package: DataPackage                          # parsed schema descriptor
    tables: Dict[str, pd.DataFrame]               # table_name → DataFrame
    base_path: Path                               # absolute root dir of this source
