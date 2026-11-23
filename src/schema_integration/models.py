"""Top-level models for schema integration pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from schema_integration.alignment.models import AlignmentReport
from schema_integration.execution.models import ExecutionResult
from schema_integration.mapping.models import MappingReport
from shared.agents import ExecutionMetadata


@dataclass
class SchemaIntegrationResult:
    """Complete aggregated results of schema integration pipeline."""

    alignment_report: AlignmentReport
    alignment_metadata: ExecutionMetadata
    mapping_reports: Dict[str, MappingReport]
    mapping_metadata: Dict[str, ExecutionMetadata]
    execution_results: Dict[str, ExecutionResult]
