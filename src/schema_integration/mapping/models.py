"""Models for schema mapping step."""

from __future__ import annotations

from typing import Annotated, List, Literal, Union

from pydantic import BaseModel, Field


class DirectCopy(BaseModel):
    """Direct copy transformation with no extra parameters."""

    type: Literal["direct_copy"] = "direct_copy"


class Concatenate(BaseModel):
    """Concatenate multiple source columns with a delimiter."""

    type: Literal["concatenate"] = "concatenate"
    delimiter: str = Field(
        ...,
        description="Delimiter string to join source column values.",
    )


class SplitExtract(BaseModel):
    """Split column value by delimiter and extract item at index."""

    type: Literal["split_extract"] = "split_extract"
    delimiter: str = Field(..., description="Delimiter string to split on.")
    index: int = Field(
        ...,
        description="0-based index of element to extract after split.",
    )


class SplitUnnest(BaseModel):
    """Split delimited string array column and unnest/duplicate rows."""

    type: Literal["split_unnest"] = "split_unnest"
    delimiter: str = Field(
        default=",",
        description="Delimiter string to split and unnest on (e.g. ',').",
    )


class Substring(BaseModel):
    """Extract substring from start to end index."""

    type: Literal["substring"] = "substring"
    start: int = Field(..., description="0-based start index (inclusive).")
    end: int = Field(..., description="0-based end index (exclusive).")


class TypeCast(BaseModel):
    """Cast series to target Frictionless data type."""

    type: Literal["type_cast"] = "type_cast"
    target_type: str = Field(
        ...,
        description="Target Frictionless data type.",
    )


class Arithmetic(BaseModel):
    """Apply basic arithmetic operation with scalar operand."""

    type: Literal["arithmetic"] = "arithmetic"
    operator: Literal["+", "-", "*", "/"] = Field(
        ...,
        description="Arithmetic operator.",
    )
    operand: float = Field(..., description="Scalar numeric operand.")


Transformation = Annotated[
    Union[
        DirectCopy,
        Concatenate,
        SplitExtract,
        SplitUnnest,
        Substring,
        TypeCast,
        Arithmetic,
    ],
    Field(discriminator="type"),
]


class MappingRule(BaseModel):
    """Mapping rule establishing source-to-target column correspondence."""

    target_table: str = Field(..., description="Target table name.")
    target_column: str = Field(..., description="Target column name.")
    source_label: str = Field(..., description="Source label identifier.")
    source_table: str = Field(..., description="Source table name.")
    source_columns: List[str] = Field(
        default_factory=list,
        description=(
            "List of source column names mapped to this target, "
            "or empty list if unmapped."
        ),
    )
    transformations: List[Transformation] = Field(
        default_factory=list,
        description="Ordered sequence of transformations to execute.",
    )


class MappingReport(BaseModel):
    """Collection of mapping rules for a single source schema."""

    rules: List[MappingRule] = Field(
        ...,
        description="List of mapping rules mapping source to target schema.",
    )
