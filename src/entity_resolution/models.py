import logging
from dataclasses import dataclass, field
from enum import Enum

import pandas as pd
from pydantic import (
    BaseModel,
    Field,
    ValidationInfo,
    field_validator,
)

from shared.agents import ExecutionMetadata
from shared.cleaning.models import CleaningReport
from shared.profiling.models import TableProfile
from shared.schema_models import TableResource

logger = logging.getLogger(__name__)



class ClassificationMode(str, Enum):
    """Classification paradigm for entity resolution matching strategies."""

    BINARY = "binary"
    TERNARY = "ternary"
    BOTH = "both"


class SimilarityAlgorithm(str, Enum):
    """Supported similarity algorithms for feature comparison."""

    JAROWINKLER = "jarowinkler"
    DAMERAU_LEVENSHTEIN = "damerau_levenshtein"
    COSINE = "cosine"
    EXACT = "exact"
    NUMERIC_LINEAR = "numeric_linear"
    NUMERIC_RELATIVE = "numeric_relative"
    DATE = "date"


class ECMColumnConfig(BaseModel):
    """Configuration for a single column comparison in ECM strategy."""

    algorithm: SimilarityAlgorithm = Field(
        description="Scoring algorithm for feature similarity."
    )


class ECMMatchingConfig(BaseModel):
    """Configuration for ECM strategy defining columns and algorithms."""

    reasoning: str = Field(
        description="Step-by-step reasoning following the mandatory 4-step protocol.",
    )
    matching_columns: dict[str, ECMColumnConfig] = Field(
        description="Mapping of column names to ECMColumnConfig."
    )

    @field_validator("matching_columns")
    @classmethod
    def validate_matching_columns(
        cls, v: dict[str, ECMColumnConfig]
    ) -> dict[str, ECMColumnConfig]:
        if not v:
            raise ValueError("matching_columns cannot be empty")
        return v


class KMeansColumnConfig(BaseModel):
    """Configuration for a single column comparison in KMeans strategy."""

    algorithm: SimilarityAlgorithm = Field(
        description="Scoring algorithm for feature similarity."
    )


class KMeansMatchingConfig(BaseModel):
    """Configuration for KMeans strategy defining columns and algorithms."""

    reasoning: str = Field(
        description="Step-by-step reasoning following the mandatory 4-step protocol.",
    )
    matching_columns: dict[str, KMeansColumnConfig] = Field(
        description="Mapping of column names to KMeansColumnConfig."
    )

    @field_validator("matching_columns")
    @classmethod
    def validate_matching_columns(
        cls, v: dict[str, KMeansColumnConfig], info: ValidationInfo
    ) -> dict[str, KMeansColumnConfig]:
        """Asserts that matching columns mapping is non-empty."""
        if not v:
            raise ValueError("matching_columns cannot be empty")
        if info.context and "available_columns" in info.context:
            available = set(info.context["available_columns"])
            valid_cols = set(v.keys()) & available
            if not valid_cols:
                raise ValueError(
                    f"None of the configured matching columns {list(v.keys())} "
                    f"exist in the dataset schema. "
                    f"Available columns: {sorted(available)}"
                )
        return v


class ColumnMatchConfig(BaseModel):
    """Configuration for a single matching column, including its comparison

    algorithm and importance weight for aggregate scoring.
    """

    algorithm: SimilarityAlgorithm = Field(
        description="Comparison algorithm to compute pairwise feature similarity."
    )
    weight: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description=(
            "Relative importance weight (0.0–1.0). Higher values make the "
            "column more decisive."
        ),
    )


class ERPipelineConfiguration(BaseModel):
    """The structured response from the LLM defining the full ER pipeline

    configuration using TF-IDF candidate indexing.
    """

    reasoning: str = Field(
        description=(
            "Step-by-step chain-of-thought rationale for the full configuration "
            "following the prescribed protocol."
        )
    )
    indexing_keys: list[str] = Field(
        description=(
            "An ordered list of column names from the global schema to concatenate "
            "for TF-IDF candidate indexing. Must contain at least one column. "
            "MUST NOT be source-specific IDs unless shared across sources."
        )
    )
    indexing_threshold: float = Field(
        default=0.10,
        ge=0.0,
        le=1.0,
        description=(
            "Cosine similarity threshold for TF-IDF candidate pairing (0.0 to 1.0). "
            "Default is 0.10."
        ),
    )
    matching_columns: dict[str, ColumnMatchConfig] = Field(
        description=(
            "A mapping of column names to their ColumnMatchConfig (algorithm + "
            "weight). ONLY include columns that are meaningful for "
            "cross-source comparison. Exclude noisy, redundant, or "
            "source-specific keys."
        )
    )

    @field_validator("indexing_keys")
    @classmethod
    def validate_indexing_keys(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("indexing_keys cannot be empty")
        cleaned = [k.strip() for k in v if k and k.strip()]
        if not cleaned:
            raise ValueError(
                "indexing_keys must contain at least one valid non-empty column name"
            )
        return cleaned

    @field_validator("matching_columns")
    @classmethod
    def validate_matching_columns(
        cls, v: dict[str, ColumnMatchConfig]
    ) -> dict[str, ColumnMatchConfig]:
        if not v:
            raise ValueError("At least one matching column must be selected")
        return v


class SortedNeighborhoodIndexConfig(BaseModel):
    """
    The structured response from the LLM defining the Sorted Neighborhood configuration.
    """
    sorting_keys: list[str] = Field(
        description="An ordered list of column names from the global schema to sort by for multi-pass Sorted Neighborhood indexing. Must contain at least one column."
    )
    window_size: int = Field(
        default=11,
        description="The window size for Sorted Neighborhood. MUST BE AN ODD NUMBER (3-51). Choose based on data quality."
    )
    reasoning: str = Field(
        description="Step-by-step reasoning for the configuration."
    )

    @field_validator('sorting_keys')
    @classmethod
    def validate_sorting_keys(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("sorting_keys cannot be empty")
        cleaned = [k.strip() for k in v if k and k.strip()]
        if not cleaned:
            raise ValueError("sorting_keys must contain at least one valid non-empty column name")
        return cleaned

    @field_validator('window_size')
    @classmethod
    def ensure_odd(cls, v: int) -> int:
        if v % 2 == 0:
            new_v = v + 1 if v < 51 else v - 1
            return new_v
        return v


class MinHashLSHIndexConfig(BaseModel):
    """
    The structured response from the LLM defining the MinHash LSH configuration.
    """
    blocking_keys: list[str] = Field(
        description="An ordered list of column names from the global schema to concatenate for MinHash LSH indexing. Must contain at least one column."
    )
    ngram_size: int = Field(
        default=1,
        description="The word n-gram window size for shingling (1 = unigrams, 2 = bigrams). Must be greater than 0. Use 1 for maximum recall in blocking; use 2 for slightly tighter candidate sets on longer fields."
    )
    threshold: float = Field(
        default=0.5,
        description="The Jaccard similarity threshold for candidate pairing (0.0 to 1.0)."
    )
    reasoning: str = Field(
        description="Step-by-step reasoning for the configuration."
    )

    @field_validator('blocking_keys')
    @classmethod
    def validate_blocking_keys(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("blocking_keys cannot be empty")
        cleaned = [k.strip() for k in v if k and k.strip()]
        if not cleaned:
            raise ValueError("blocking_keys must contain at least one valid non-empty column name")
        return cleaned

    @field_validator('ngram_size')
    @classmethod
    def validate_ngram_size(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("ngram_size must be strictly positive (> 0)")
        return v

    @field_validator('threshold')
    @classmethod
    def validate_threshold(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError("threshold must be between 0.0 and 1.0 inclusive")
        return v


class QGramIndexConfig(BaseModel):
    """
    The structured response from the LLM defining the Q-Gram inverted index configuration.
    """
    keys: list[str] = Field(
        description="An ordered list of column names from the global schema to concatenate and extract character Q-grams from. Must contain at least one column."
    )
    reasoning: str = Field(
        description="Step-by-step reasoning for the configuration."
    )

    @field_validator('keys')
    @classmethod
    def validate_keys(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("keys cannot be empty")
        cleaned = [k.strip() for k in v if k and k.strip()]
        if not cleaned:
            raise ValueError("keys must contain at least one valid non-empty column name")
        return cleaned


class TFIDFIndexConfig(BaseModel):
    """
    The structured response from the LLM defining the TF-IDF index configuration.
    """
    keys: list[str] = Field(
        description="An ordered list of column names from the global schema to concatenate for TF-IDF indexing. Must contain at least one column."
    )
    reasoning: str = Field(
        description="Step-by-step reasoning for the configuration."
    )

    @field_validator('keys')
    @classmethod
    def validate_keys(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("keys cannot be empty")
        cleaned = [k.strip() for k in v if k and k.strip()]
        if not cleaned:
            raise ValueError("keys must contain at least one valid non-empty column name")
        return cleaned



class MatchResolution(BaseModel):
    """
    The structured response expected from the LLM when resolving uncertain matches.
    """
    pair_id: str = Field(
        description="The unique identifier for the candidate pair being evaluated."
    )
    reasoning: str = Field(
        description="A concise chain-of-thought rationale detailing why the differences in the attributes are acceptable (e.g., formatting/typo) or represent distinct entities."
    )
    is_match: bool = Field(
        description="True if the two rows represent the same real-world entity, False otherwise."
    )

class BatchMatchResolution(BaseModel):
    resolutions: list[MatchResolution] = Field(
        description="The list of resolutions for the provided candidate pairs."
    )

@dataclass
class EntityResolutionResult:
    """
    Structured result of a single ER pipeline execution.
    Contains both the final matches and intermediate data for analysis/evaluation.
    """
    config: ERPipelineConfiguration
    er_config_metadata: ExecutionMetadata
    profile_a: TableProfile
    profile_b: TableProfile
    df_a_clean: pd.DataFrame
    df_b_clean: pd.DataFrame
    er_refinement_metadata: ExecutionMetadata | None = None
    cleaning_report_a: CleaningReport | None = None
    cleaning_report_b: CleaningReport | None = None
    candidate_pairs: pd.MultiIndex | None = None
    matches: pd.DataFrame = field(default_factory=pd.DataFrame)
    uncertain: pd.DataFrame = field(default_factory=pd.DataFrame)
    non_matches: pd.DataFrame = field(default_factory=pd.DataFrame)


__all__ = [
    "BatchMatchResolution",
    "ClassificationMode",
    "CleaningReport",
    "ColumnMatchConfig",
    "ECMColumnConfig",
    "ECMMatchingConfig",
    "ERPipelineConfiguration",
    "EntityResolutionResult",
    "ExecutionMetadata",
    "KMeansColumnConfig",
    "KMeansMatchingConfig",
    "MatchResolution",
    "MinHashLSHIndexConfig",
    "QGramIndexConfig",
    "SimilarityAlgorithm",
    "SortedNeighborhoodIndexConfig",
    "TFIDFIndexConfig",
    "TableProfile",
    "TableResource",
]
