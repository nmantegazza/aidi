from enum import Enum
from pydantic import BaseModel, Field, model_validator
from typing import List, Dict, Any

class FusionStrategy(str, Enum):
    TRUST_SOURCE = "trust_source"
    COALESCE = "coalesce"
    LONGEST_STRING = "longest_string"
    SHORTEST_STRING = "shortest_string"
    MOST_RECENT = "most_recent"
    NUMERIC_MAX = "numeric_max"
    NUMERIC_MIN = "numeric_min"
    NUMERIC_AVG = "numeric_avg"
    UNION = "union"
    INTERSECTION = "intersection"
    MOST_WORDS = "most_words"
    FORMAT_PRESERVING = "format_preserving"

class ColumnPolicy(BaseModel):
    column_name: str
    strategy: FusionStrategy
    delimiters: List[str] | None = None
    reasoning: str

class FusionGroup(BaseModel):
    group_name: str
    columns: List[str]
    leader_column: str
    strategy: FusionStrategy
    delimiters: List[str] | None = None
    reasoning: str

    @model_validator(mode="after")
    def validate_group(self) -> "FusionGroup":
        if self.leader_column not in self.columns:
            raise ValueError(
                f"leader_column '{self.leader_column}' must be one of the group columns: {self.columns}"
            )
        if len(self.columns) < 2:
            raise ValueError("FusionGroup must contain at least 2 columns")
        return self

class TableFusionPolicy(BaseModel):
    table_name: str
    fusion_groups: List[FusionGroup] = Field(default_factory=list)
    column_policies: List[ColumnPolicy] = Field(default_factory=list)
    reasoning: str

class MultiTableFusionPolicy(BaseModel):
    tables: Dict[str, TableFusionPolicy]


class PhysicalType(str, Enum):
    INTEGER = "INTEGER"
    FLOAT = "FLOAT"
    BOOLEAN = "BOOLEAN"
    DATETIME = "DATETIME"
    TEXT = "TEXT"


class SemanticType(str, Enum):
    EMAIL = "EMAIL"
    PHONE = "PHONE"
    URL = "URL"
    GEOSPATIAL = "GEOSPATIAL"
    UUID = "UUID"
    NONE = "NONE"

    @property
    def regex_pattern(self) -> str | None:
        patterns = {
            "EMAIL": r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$",
            "PHONE": r"^(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}$",
            "URL": r"^(https?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w \.-]*)*\/?$",
            "GEOSPATIAL": r"^[-+]?([1-8]?\d(\.\d+)?|90(\.0+)?),\s*[-+]?(180(\.0+)?|((1[0-7]\d)|([1-9]?\d))(\.\d+)?)$",
            "UUID": r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
        }
        return patterns.get(self.value)


class ConflictSample(BaseModel):
    value_a: Any
    value_b: Any


class ColumnConflictProfile(BaseModel):
    column_name: str
    physical_type: PhysicalType
    semantic_type: SemanticType
    conflict_rate: float
    source_a_null_rate: float
    source_b_null_rate: float
    source_trust_score: float
    samples: List[ConflictSample] = Field(default_factory=list)


class TableFusionProfile(BaseModel):
    table_name: str
    total_pairs: int
    columns: Dict[str, ColumnConflictProfile]


class MultiTableFusionProfile(BaseModel):
    source_a_origin: str
    source_b_origin: str
    tables: Dict[str, TableFusionProfile]

