"""Models for schema alignment step."""

from __future__ import annotations

from enum import Enum
from typing import List

from pydantic import BaseModel, Field

from shared.schema_models import DataPackage


class ConflictType(str, Enum):
    """Canonical conflict types for schema alignment."""

    NAMING = "Naming"
    TYPE = "Type"
    DATA_SEMANTIC = "Data Semantic"
    STRUCTURE = "Structure"
    CARDINALITY = "Cardinality"
    KEY = "Key"


class ConceptualConflict(BaseModel):
    """Represents a single conceptual conflict resolved during alignment."""

    source_references: List[str] = Field(
        ...,
        description="Dot-notation paths referencing source schema elements.",
    )
    description: str = Field(
        ...,
        description="Detailed description of the conceptual conflict.",
    )
    resolution: str = Field(
        ...,
        description="Explanation of how the conflict was resolved.",
    )


class ConflictGroup(BaseModel):
    """Groups conceptual conflicts by canonical conflict type."""

    conflict_type: ConflictType = Field(
        ...,
        description="The canonical conflict type category.",
    )
    conflicts: List[ConceptualConflict] = Field(
        default_factory=list,
        description="List of conceptual conflicts in this group.",
    )


class AlignmentReport(BaseModel):
    """Unified alignment report containing global schema and conflict audit log."""

    target_schema: DataPackage = Field(
        ...,
        description="The unified target schema data package.",
    )
    conflict_report: List[ConflictGroup] = Field(
        ...,
        description="Conceptual audit log of conflicts grouped by type.",
    )
