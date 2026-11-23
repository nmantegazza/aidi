from __future__ import annotations
from enum import Enum
from typing import List, Optional, Union, Dict, Any, Literal
from pydantic import BaseModel, Field, ConfigDict
import pandas as pd

class FieldConstraints(BaseModel):
    required: bool = False


class TableField(BaseModel):
    name: str
    type: str = "string"  # Standard type string (integer, number, etc.)
    description: Optional[str] = None
    constraints: FieldConstraints = FieldConstraints()
    source_provenance: list[str] | None = Field(
        default=None,
        description=(
            "Qualified source references, e.g. "
            "['source_a.table.col', 'source_b.table.col']"
        ),
    )

    def is_primary_key(self, schema: TableSchema) -> bool:
        """Helper to determine if this field is part of its parent schema's primary key."""
        return self.name in schema.primary_key_columns

class ForeignKeyReference(BaseModel):
    resource: str                               # name of the referenced resource
    fields: Union[str, List[str]]               # one or many columns

class ForeignKey(BaseModel):
    fields: Union[str, List[str]]               # local column(s)
    reference: ForeignKeyReference

class TableSchema(BaseModel):
    primaryKey: Union[str, List[str], None] = None
    fields: List[TableField]
    foreignKeys: List[ForeignKey] = []

    @property
    def primary_key_columns(self) -> List[str]:
        """Returns primary key as a list of column names, even if it's a single string."""
        if self.primaryKey is None:
            return []
        if isinstance(self.primaryKey, str):
            return [self.primaryKey]
        return self.primaryKey

    def get_field(self, name: str) -> Optional[TableField]:
        """Lookup a field by name."""
        for field in self.fields:
            if field.name == name:
                return field
        return None

        


class TableResource(BaseModel):
    name: str                                   # logical table name
    path: Optional[str] = None                  # relative path to .parquet (optional for virtual/global tables)
    schema_info: TableSchema = Field(..., alias="schema")
    model_config = ConfigDict(populate_by_name=True)

class DataPackage(BaseModel):
    name: str = Field(..., alias="schema_name")
    title: Optional[str] = None
    resources: List[TableResource] = []
    model_config = ConfigDict(populate_by_name=True)


class ConflictType(str, Enum):
    NAMING = "Naming Conflict"
    TYPE = "Type Conflict"
    DATA_SEMANTIC = "Data Semantic Conflict"
    STRUCTURE = "Structure Conflict"
    CARDINALITY = "Cardinality Conflict"
    KEY = "Key Conflict"


class Conflict(BaseModel):
    source_items: List[str] = Field(..., description="List of conflicting items of first source (dot notation: source.table.column).")
    target_items: List[str] = Field(..., description="List of conflicting items of second source (dot notation: source.table.column).")
    description: str = Field(..., description="Brief explanation of the conflict.")
    resolution_strategy: str = Field(..., description="Brief explanation of how this conflict is resolved in the Global Schema.")


class ConflictReport(BaseModel):
    conflict_type: ConflictType = Field(..., description="The type of conflict being reported.")
    conflicts: List[Conflict] = Field(default=[], description="List of conflict instances of this type.")


class IntegrationReport(BaseModel):
    conflicts_report: List[ConflictReport] = Field(..., description="Detailed conflict analysis grouped by conflict type.")
    global_schema: DataPackage = Field(..., description="Integrated Global Schema (Standard DataPackage).")

