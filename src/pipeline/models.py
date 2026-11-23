from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, ConfigDict, computed_field

from shared.schema_models import TableResource, DataPackage, IntegrationReport
from shared.ingestion import SourceData, IngestionReport
from shared.cleaning.models import CleaningReport
from shared.profiling.models import TableProfile
from shared.porting import PortedTable, PortingWarning, PortingReport
from shared.agents import ExecutionMetadata
from shared.porting.models import PortingInstructionsReport
from entity_resolution.models import ERPipelineConfiguration, EntityResolutionResult

@dataclass
class StepResults:
    """Intermediate results from every pipeline stage (non-Pydantic for DataFrames)."""
    # Ingestion
    source_a: SourceData
    source_b: SourceData
    ingestion_report_a: IngestionReport
    ingestion_report_b: IngestionReport
    
    # Cleaning
    clean_source_a: SourceData
    clean_source_b: SourceData
    cleaning_reports_a: Dict[str, CleaningReport]
    cleaning_reports_b: Dict[str, CleaningReport]
    
    # Profiling
    profiles_a: Dict[str, TableProfile]
    profiles_b: Dict[str, TableProfile]
    
    # GAV
    integration_report: IntegrationReport
    porting_instructions: PortingInstructionsReport
    gav_metadata: Dict[str, ExecutionMetadata]
    
    # Porting
    ported_tables: Dict[str, PortedTable]
    porting_report: PortingReport
    
    # ER (per global table)
    er_results: Dict[str, EntityResolutionResult]   # global_table_name → PipelineResult

class TableRunResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    global_table_name: str
    source_a_table: str          # source table name mapped to this global entity
    source_b_table: str
    porting_warnings: List[PortingWarning]
    num_rows_a: int
    num_rows_b: int
    num_matches: int
    num_uncertain: int
    num_non_matches: int
    er_config: ERPipelineConfiguration

class PipelineRunReport(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    data_root: str
    timestamp: datetime = Field(default_factory=datetime.now)
    model_name: str
    
    # GAV stage
    gav_metadata: Dict[str, ExecutionMetadata]
    integration_report: IntegrationReport
    porting_instructions: PortingInstructionsReport
    
    # Per-table ER results (serializable summary)
    table_results: Dict[str, TableRunResult]
    
    # Raw step data (non-serializable, for in-process HTML rendering)
    step_results: StepResults

    @computed_field
    @property
    def total_tables(self) -> int:
        return len(self.table_results)

    @computed_field
    @property
    def matched_count(self) -> int:
        return sum(tr.num_matches for tr in self.table_results.values())

    @computed_field
    @property
    def total_porting_warnings(self) -> int:
        return sum(len(tr.porting_warnings) for tr in self.table_results.values())
