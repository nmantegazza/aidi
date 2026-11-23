from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple
import pandas as pd
from ..contracts import (
    IngestionResult, CleaningResult, SchemaMatchingResult,
    DataPortingResult, RecordLinkageResult, FinalReportResult,
    DataFusionConfigResult, DataFusionResult
)
from entity_resolution.models import ERPipelineConfiguration

@dataclass
class CanvasState:
    pass

@dataclass
class IngestionCanvasState(CanvasState):
    ingested: bool = False
    ingestion_result: Optional[IngestionResult] = None
    cleaned: bool = False
    cleaning_result: Optional[CleaningResult] = None

@dataclass
class MatchingCanvasState(CanvasState):
    matching_result: Optional[SchemaMatchingResult] = None

@dataclass
class PortingCanvasState(CanvasState):
    porting_result: Optional[DataPortingResult] = None
    cleaning_result: Optional[CleaningResult] = None

@dataclass
class ERConfigCanvasState(CanvasState):
    matching_result: Optional[SchemaMatchingResult] = None
    porting_result: Optional[DataPortingResult] = None
    er_configs: Dict[str, ERPipelineConfiguration] = field(default_factory=dict)
    er_config_dfs: Dict[str, pd.DataFrame] = field(default_factory=dict)

@dataclass
class ERReviewCanvasState(CanvasState):
    linkage_result: Optional[RecordLinkageResult] = None

@dataclass
class DataFusionConfigCanvasState(CanvasState):
    config_result: Optional[DataFusionConfigResult] = None
    linkage_result: Optional[RecordLinkageResult] = None
    porting_result: Optional[DataPortingResult] = None
    tables: Dict[str, Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]] = field(default_factory=dict)

@dataclass
class DataFusionResultCanvasState(CanvasState):
    fusion_result: Optional[DataFusionResult] = None

@dataclass
class ResultsCanvasState(CanvasState):
    final_report: Optional[FinalReportResult] = None
