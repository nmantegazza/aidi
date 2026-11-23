"""Models for schema integration execution step."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

import pandas as pd


@dataclass
class PortingWarning:
    """Warning emitted during data porting execution."""

    target_table: str
    target_column: str
    source_label: str
    message: str


@dataclass
class PortedTable:
    """A ported table containing transformed DataFrame and warnings."""

    target_table_name: str
    dataframe: pd.DataFrame
    warnings: List[PortingWarning] = field(default_factory=list)


@dataclass
class ExecutionResult:
    """Result of porting execution for a single source dataset."""

    tables: Dict[str, PortedTable]
    total_rows: int
    processing_time_ms: float
