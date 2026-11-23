from __future__ import annotations
from typing import List, Optional, Union, Dict, Literal
from pydantic import BaseModel, Field
import pandas as pd
from dataclasses import dataclass
from shared.schema_models import DataPackage

# ===========================================================================
# 1. AST Transformation Models
# ===========================================================================

class DirectMap(BaseModel):
    type: Literal["direct"] = "direct"
    source_label: str
    source_column: str

class Concat(BaseModel):
    type: Literal["concat"] = "concat"
    source_label: str
    source_columns: List[str]
    delimiter: str

class Split(BaseModel):
    type: Literal["split"] = "split"
    source_label: str
    source_column: str
    delimiter: str
    index: int

class Slice(BaseModel):
    type: Literal["slice"] = "slice"
    source_label: str
    source_column: str
    start: int
    end: int

class TypeCast(BaseModel):
    type: Literal["type_cast"] = "type_cast"
    source_label: str
    source_column: str
    target_type: str                            # 'integer', 'number', 'string', 'boolean', 'date', 'datetime'

class MathOperation(BaseModel):
    type: Literal["math_operation"] = "math_operation"
    source_label: str
    source_column: str
    operator: Literal["+", "-", "*", "/"]
    operand: float

Transformation = Union[DirectMap, Concat, Split, Slice, TypeCast, MathOperation]

# ===========================================================================
# 2. Recipe Models
# ===========================================================================

class SingleTable(BaseModel):
    type: Literal["single"] = "single"
    source_label: str
    table_name: str

class JoinTables(BaseModel):
    type: Literal["join"] = "join"
    left_source: str
    left_table: str
    right_source: str
    right_table: str
    join_type: Literal["inner", "left", "right", "outer"]
    left_on: str
    right_on: str

ConstructionRecipe = Union[SingleTable, JoinTables]

# ===========================================================================
# 3. Instruction Report Models
# ===========================================================================

class TablePortingInstruction(BaseModel):
    construction_recipes: List[ConstructionRecipe] = Field(default_factory=list)
    field_transformations: Dict[str, List[Transformation]] = Field(default_factory=dict)

class PortingInstructionsReport(BaseModel):
    global_table_instructions: Dict[str, TablePortingInstruction] = Field(
        ..., description="Mapping of global table name to its porting instructions"
    )

# ===========================================================================
# 4. Execution Data Classes
# ===========================================================================

@dataclass
class PortingWarning:
    """
    Metadata about a soft issue during the porting process (e.g., a bad type cast).
    """
    global_table: str
    global_column: str
    source_label: str        # "source_a" | "source_b"
    message: str

@dataclass
class PortingReport:
    """
    Summary of the data porting process.
    """
    total_tables: int
    total_rows_source_a: int
    total_rows_source_b: int
    total_warnings: int
    processing_time_ms: float

@dataclass
class PortedTable:
    """
    The result of porting a single global entity from both sources.
    """
    global_table_name: str
    df_a: pd.DataFrame
    df_b: pd.DataFrame
    warnings: List[PortingWarning]

# ===========================================================================
# 5. Exceptions
# ===========================================================================

class DataPortingError(Exception):
    """Base class for data porting errors."""
    pass

class UnresolvableColumnError(DataPortingError):
    """Raised when a mapped column cannot be found in the source DataFrame."""
    pass

class TableNotFoundError(DataPortingError):
    """Raised when a global table has no mapped source tables or a source table is missing."""
    pass

class TypeCastError(DataPortingError):
    """Raised when a hard type cast failure occurs (though currently soft casting is preferred)."""
    pass
