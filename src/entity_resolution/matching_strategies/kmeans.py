"""Unsupervised K-Means clustering matching strategy."""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd
import recordlinkage
from pydantic import BaseModel

import shared.patches  # noqa: F401
from entity_resolution.classification import (
    DynamicThresholdClassificationEngine,
)
from entity_resolution.matching import (
    VectorizedRelativeNumeric,
    parse_numeric_series,
)
from entity_resolution.matching_strategies.base import BaseMatchingStrategy
from entity_resolution.models import (
    ClassificationMode,
    KMeansMatchingConfig,
    SimilarityAlgorithm,
)
from entity_resolution.prompts import KMEANS_MATCHING_CONFIG_SYSTEM_PROMPT
from entity_resolution.tfidf_vectorized_comparator import VectorizedTFIDF
from shared.config import config

logger = logging.getLogger(__name__)


class KMeansMatchingStrategy(BaseMatchingStrategy):
    """Matching strategy using unsupervised recordlinkage KMeansClassifier."""

    config_schema = KMeansMatchingConfig
    config_prompt = KMEANS_MATCHING_CONFIG_SYSTEM_PROMPT

    def __init__(self, config: KMeansMatchingConfig) -> None:
        """Initialize strategy with configuration.

        Args:
            config: Validated KMeansMatchingConfig object.
        """
        self.config = config
        self.last_thresholds: dict[str, Any] = {}
        self.classification_engine = DynamicThresholdClassificationEngine()

    @classmethod
    def from_llm_config(cls, config: BaseModel) -> KMeansMatchingStrategy:
        """Construct strategy instance from parsed Pydantic config model.

        Args:
            config: Pydantic model containing KMeans matching configuration.

        Returns:
            Instantiated KMeansMatchingStrategy.
        """
        if isinstance(config, KMeansMatchingConfig):
            return cls(config)
        return cls(KMeansMatchingConfig.model_validate(config))

    def _perform_matching(
        self,
        df_a: pd.DataFrame,
        df_b: pd.DataFrame,
        candidate_pairs: pd.MultiIndex,
        classification_mode: ClassificationMode = ClassificationMode.TERNARY,
        enforce_safety_floor: bool = True,
        **kwargs,
    ) -> tuple[pd.MultiIndex, pd.DataFrame | None]:
        """Computes continuous features and clusters candidates via K-Means.

        Args:
            df_a: Left input DataFrame.
            df_b: Right input DataFrame.
            candidate_pairs: Candidate pairs MultiIndex to evaluate.
            classification_mode: Binary or ternary classification mode.
            enforce_safety_floor: Whether to enforce centroid safety floor
                to prevent precision collapse on sparse blocks.
            **kwargs: Additional runtime options.

        Returns:
            Tuple of (pd.MultiIndex of positive matched pairs, features_df).

        Raises:
            ValueError: If candidate pairs count is less than 2 (binary) or 3
                (ternary), or if none of the configured matching columns exist
                in both tables.
        """
        if candidate_pairs.empty:
            return candidate_pairs, None

        if classification_mode == ClassificationMode.BINARY:
            if len(candidate_pairs) < 2:
                raise ValueError(
                    "KMeans matching in binary mode requires at least 2 "
                    f"candidate pairs. Received {len(candidate_pairs)} pairs."
                )
        else:
            if len(candidate_pairs) < 3:
                raise ValueError(
                    "KMeans matching in ternary mode requires at least 3 "
                    f"candidate pairs. Received {len(candidate_pairs)} pairs."
                )

        valid_cols = [
            c
            for c in self.config.matching_columns
            if c in df_a.columns and c in df_b.columns
        ]
        if not valid_cols:
            shared = sorted(set(df_a.columns) & set(df_b.columns))
            raise ValueError(
                f"None of the configured matching columns "
                f"{list(self.config.matching_columns.keys())} exist in both "
                f"input tables. Available shared columns: {shared}"
            )

        compare = recordlinkage.Compare()
        df_a_comp = df_a.copy()
        df_b_comp = df_b.copy()

        for col_name, col_cfg in self.config.matching_columns.items():
            if col_name not in df_a.columns or col_name not in df_b.columns:
                continue

            algo = col_cfg.algorithm
            if algo in (
                SimilarityAlgorithm.JAROWINKLER,
                SimilarityAlgorithm.COSINE,
                SimilarityAlgorithm.DAMERAU_LEVENSHTEIN,
            ):
                df_a_comp[col_name] = (
                    df_a_comp[col_name]
                    .astype(str)
                    .where(df_a_comp[col_name].notnull(), np.nan)
                )
                df_b_comp[col_name] = (
                    df_b_comp[col_name]
                    .astype(str)
                    .where(df_b_comp[col_name].notnull(), np.nan)
                )
                if algo == SimilarityAlgorithm.COSINE:
                    compare.add(
                        VectorizedTFIDF(col_name, col_name, label=col_name)
                    )
                else:
                    compare.string(
                        col_name,
                        col_name,
                        method=algo.value,
                        label=col_name,
                    )
            elif algo == SimilarityAlgorithm.EXACT:
                compare.exact(col_name, col_name, label=col_name)
            elif algo == SimilarityAlgorithm.NUMERIC_LINEAR:
                df_a_comp[col_name] = parse_numeric_series(df_a_comp[col_name])
                df_b_comp[col_name] = parse_numeric_series(df_b_comp[col_name])
                compare.numeric(
                    col_name,
                    col_name,
                    method="linear",
                    offset=0,
                    scale=10,
                    label=col_name,
                )
            elif algo == SimilarityAlgorithm.NUMERIC_RELATIVE:
                df_a_comp[col_name] = parse_numeric_series(df_a_comp[col_name])
                df_b_comp[col_name] = parse_numeric_series(df_b_comp[col_name])
                compare.add(
                    VectorizedRelativeNumeric(
                        col_name, col_name, label=col_name
                    )
                )
            elif algo == SimilarityAlgorithm.DATE:
                df_a_comp[col_name] = pd.to_datetime(
                    df_a_comp[col_name], errors="coerce"
                ).astype("datetime64[ns]")
                df_b_comp[col_name] = pd.to_datetime(
                    df_b_comp[col_name], errors="coerce"
                ).astype("datetime64[ns]")
                compare.date(col_name, col_name, label=col_name)

        raw_features = compare.compute(candidate_pairs, df_a_comp, df_b_comp)
        raw_features = raw_features.fillna(0.0)

        km = recordlinkage.KMeansClassifier(random_state=config.SEED)
        km.fit(raw_features)

        c1 = km.match_cluster_center
        c0 = km.nonmatch_cluster_center

        if classification_mode == ClassificationMode.BINARY:
            self.last_thresholds = {}
            if float(np.mean(c1)) < config.KMEANS_CENTROID_SAFETY_FLOOR:
                logger.warning(
                    "K-Means match centroid mean %.3f below safety floor %.3f. "
                    "Proceeding with unconstrained K-Means prediction.",
                    float(np.mean(c1)),
                    config.KMEANS_CENTROID_SAFETY_FLOOR,
                )
            matches = km.predict(raw_features)
            raw_features["prediction"] = "non_match"
            if not matches.empty:
                raw_features.loc[matches, "prediction"] = "match"
            return matches, raw_features

        feature_matrix = raw_features.values
        d0 = np.linalg.norm(feature_matrix - c0, axis=1)
        d1 = np.linalg.norm(feature_matrix - c1, axis=1)
        denom = d0 + d1
        scores = np.divide(
            d0, denom, out=np.full_like(d0, 0.5), where=denom > 0
        )

        result = self.classification_engine.classify(
            scores,
            index=candidate_pairs,
            classification_mode=ClassificationMode.TERNARY,
        )
        raw_features["prediction"] = result.predictions
        raw_features["probability"] = scores
        self.last_thresholds = result.thresholds
        raw_features.attrs["dynamic_thresholds"] = dict(result.thresholds)

        return result.matched_pairs, raw_features
