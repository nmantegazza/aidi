from dataclasses import dataclass
from typing import Dict, Any
import pandas as pd

from shared.ingestion import SourceData, IngestionReport
from shared.profiling.models import GUITableProfile
from shared.porting import PortedTable, PortingReport
from shared.porting.models import PortingInstructionsReport
from shared.schema_models import IntegrationReport
from entity_resolution.models import EntityResolutionResult
from data_fusion.models import MultiTableFusionProfile, MultiTableFusionPolicy

@dataclass(eq=False)
class IngestionResult:
    source_a: SourceData
    report_a: IngestionReport
    source_b: SourceData
    report_b: IngestionReport
    profiles_a: Dict[str, GUITableProfile]
    profiles_b: Dict[str, GUITableProfile]
    data_root: str

@dataclass(eq=False)
class CleaningResult:
    clean_a: SourceData
    clean_b: SourceData
    reports_a: Dict[str, Any]
    reports_b: Dict[str, Any]

@dataclass(eq=False)
class SchemaMatchingResult:
    integration_report: IntegrationReport
    architect_metadata: Dict[str, Any]

@dataclass(eq=False)
class DataPortingResult:
    porting_instructions: PortingInstructionsReport
    ported_tables: Dict[str, PortedTable]
    porting_report: PortingReport
    engineer_metadata: Dict[str, Any]

@dataclass(eq=False)
class RecordLinkageResult:
    er_results: Dict[str, EntityResolutionResult]

@dataclass(eq=False)
class DataFusionConfigResult:
    fusion_profile: MultiTableFusionProfile
    fusion_policy: MultiTableFusionPolicy   # mutable in-place during review

@dataclass(eq=False)
class DataFusionResult:
    fused_tables: Dict[str, pd.DataFrame]
    fusion_policy: MultiTableFusionPolicy   # finalized policy as applied
    fusion_profile: MultiTableFusionProfile  # carried for display in canvas 6b

@dataclass(eq=False)
class FinalReportResult:
    report_path: str
    summary: Dict[str, Any]
