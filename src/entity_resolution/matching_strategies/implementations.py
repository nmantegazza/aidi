"""
Concrete implementations of entity resolution matching strategies.
"""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd
from pydantic import BaseModel, Field, ValidationInfo, field_validator

from entity_resolution.classification import (
    DynamicThresholdClassificationEngine,
)
from entity_resolution.matching import (
    classify_matches,
    extract_features_and_score,
)
from entity_resolution.matching_strategies.base import BaseMatchingStrategy
from entity_resolution.models import ClassificationMode, ColumnMatchConfig
from entity_resolution.prompts import MATCHING_CONFIG_SYSTEM_PROMPT
from shared.config import config

logger = logging.getLogger(__name__)


class WeightedScoreMatchingConfig(BaseModel):
    """Configuration schema for weighted score matching strategy."""

    reasoning: str = Field(
        description="Step-by-step reasoning following the mandatory 4-step protocol.",
    )
    matching_columns: dict[str, ColumnMatchConfig] = Field(
        description="Mapping of column names to ColumnMatchConfig.",
    )

    @field_validator("matching_columns")
    @classmethod
    def validate_matching_columns(
        cls, v: dict[str, ColumnMatchConfig], info: ValidationInfo
    ) -> dict[str, ColumnMatchConfig]:
        if not v:
            raise ValueError("matching_columns cannot be empty")
        if info.context and "available_columns" in info.context:
            available = set(info.context["available_columns"])
            valid_cols = set(v.keys()) & available
            if not valid_cols:
                raise ValueError(
                    f"None of the configured matching columns {list(v.keys())} "
                    f"exist in the dataset schema. Available columns: {sorted(available)}"
                )
        return v


class WeightedScoreMatchingStrategy(BaseMatchingStrategy):
    """Matching strategy using column similarity metrics and weighted scores."""

    config_schema = WeightedScoreMatchingConfig
    config_prompt = MATCHING_CONFIG_SYSTEM_PROMPT

    def __init__(self, config: WeightedScoreMatchingConfig) -> None:
        """Initialize strategy with configuration."""
        self.config = config

    @classmethod
    def from_llm_config(cls, config: BaseModel) -> WeightedScoreMatchingStrategy:
        """Construct strategy instance from parsed Pydantic config model."""
        if isinstance(config, WeightedScoreMatchingConfig):
            return cls(config)
        return cls(WeightedScoreMatchingConfig.model_validate(config))

    def _perform_matching(
        self,
        df_a: pd.DataFrame,
        df_b: pd.DataFrame,
        candidate_pairs: pd.MultiIndex,
        classification_mode: ClassificationMode = ClassificationMode.TERNARY,
        **kwargs,
    ) -> tuple[pd.MultiIndex, pd.DataFrame | None]:
        """Computes similarity scores on candidate pairs and returns matches.

        Args:
            df_a: Left input DataFrame.
            df_b: Right input DataFrame.
            candidate_pairs: Candidate pairs MultiIndex.
            classification_mode: Binary or ternary classification mode.
            **kwargs: Additional strategy-specific arguments.

        Returns:
            Tuple of (pd.MultiIndex of positive matched pairs, features_df).
        """
        if candidate_pairs.empty:
            return candidate_pairs, None

        features_df = extract_features_and_score(
            candidate_pairs=candidate_pairs,
            df_a=df_a,
            df_b=df_b,
            matching_columns=self.config.matching_columns,
        )

        if classification_mode == ClassificationMode.BINARY:
            matches = features_df[
                features_df["aggregate_score"] >= config.MATCH_THRESHOLD
            ]
            features_df["prediction"] = "non_match"
            features_df.loc[matches.index, "prediction"] = "match"
            return matches.index, features_df

        matches, non_matches, _ = classify_matches(
            features_df,
            matching_columns=self.config.matching_columns,
        )
        features_df["prediction"] = "uncertain"
        features_df.loc[matches.index, "prediction"] = "match"
        features_df.loc[non_matches.index, "prediction"] = "non_match"

        return matches.index, features_df


class DynamicWeightedMatchingStrategy(BaseMatchingStrategy):
    """Weighted score matching with 1D K-Means dynamic thresholding."""

    config_schema = WeightedScoreMatchingConfig
    config_prompt = MATCHING_CONFIG_SYSTEM_PROMPT

    def __init__(self, config: WeightedScoreMatchingConfig) -> None:
        """Initialize strategy with configuration."""
        self.config = config
        self.last_thresholds: dict[str, Any] = {}
        self.classification_engine = DynamicThresholdClassificationEngine()

    @classmethod
    def from_llm_config(
        cls, config: BaseModel
    ) -> DynamicWeightedMatchingStrategy:
        """Construct strategy instance from parsed Pydantic config model."""
        if isinstance(config, WeightedScoreMatchingConfig):
            return cls(config)
        return cls(WeightedScoreMatchingConfig.model_validate(config))

    def _perform_matching(
        self,
        df_a: pd.DataFrame,
        df_b: pd.DataFrame,
        candidate_pairs: pd.MultiIndex,
        classification_mode: ClassificationMode = ClassificationMode.TERNARY,
        **kwargs,
    ) -> tuple[pd.MultiIndex, pd.DataFrame | None]:
        """Computes similarity scores and dynamically thresholds candidates.

        Args:
            df_a: Left input DataFrame.
            df_b: Right input DataFrame.
            candidate_pairs: Candidate pairs MultiIndex.
            classification_mode: Binary or ternary classification mode.
            **kwargs: Additional strategy-specific arguments.

        Returns:
            Tuple of (pd.MultiIndex of positive matched pairs, features_df).
        """
        if candidate_pairs.empty:
            return candidate_pairs, None

        if classification_mode == ClassificationMode.BINARY:
            if len(candidate_pairs) < 2:
                raise ValueError(
                    "Dynamic weighted matching in binary mode requires at least "
                    "2 candidate pairs."
                )
        else:
            if len(candidate_pairs) < 3:
                raise ValueError(
                    "Dynamic weighted matching in ternary mode requires at least "
                    "3 candidate pairs."
                )

        features_df = extract_features_and_score(
            candidate_pairs=candidate_pairs,
            df_a=df_a,
            df_b=df_b,
            matching_columns=self.config.matching_columns,
        )

        all_scores = features_df["aggregate_score"].fillna(0.0)

        result = self.classification_engine.classify(
            all_scores,
            index=candidate_pairs,
            classification_mode=classification_mode,
        )
        self.last_thresholds = result.thresholds
        features_df["prediction"] = result.predictions
        features_df.attrs["dynamic_thresholds"] = dict(result.thresholds)

        if classification_mode == ClassificationMode.TERNARY:
            matches, non_matches, _ = classify_matches(
                features_df,
                lower_threshold=result.thresholds["lower_threshold"],
                upper_threshold=result.thresholds["upper_threshold"],
                matching_columns=self.config.matching_columns,
            )
            features_df["prediction"] = "uncertain"
            features_df.loc[matches.index, "prediction"] = "match"
            features_df.loc[non_matches.index, "prediction"] = "non_match"
            return matches.index, features_df

        return result.matched_pairs, features_df


