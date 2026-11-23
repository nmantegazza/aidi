"""
[DEPRECATED] ECM probabilistic matching strategy using 1D K-Means binarization.

DEPRECATION NOTICE:
    The ECM (Expectation-Conditional Maximization / Fellegi-Sunter) matching strategy
    is deprecated. The classical ECM algorithm strictly expects discrete binary
    agreement vectors (gamma in {0, 1}^D). In modern entity resolution pipelines with
    heterogeneous and continuous similarity comparators (Jaro-Winkler, Levenshtein,
    Cosine TF-IDF, Numeric Relative distances), binarizing continuous scores via
    static thresholds or 1D K-Means introduces artificial noise, loss of comparison
    granularity, and brittle failure modes without a reliable way to preserve continuous
    signals. Prefer DynamicWeightedMatchingStrategy or continuous KMeansMatchingStrategy.
"""

from __future__ import annotations

import logging
import warnings
from typing import Any

import numpy as np
import pandas as pd
import recordlinkage
from pydantic import BaseModel
from sklearn.cluster import KMeans

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
    ECMMatchingConfig,
    SimilarityAlgorithm,
)
from entity_resolution.prompts import ECM_MATCHING_CONFIG_SYSTEM_PROMPT
from entity_resolution.tfidf_vectorized_comparator import VectorizedTFIDF
from shared.config import config

logger = logging.getLogger(__name__)


class KMeansBinarizer:
    """[DEPRECATED] 1D K-Means feature binarizer with safety floor threshold fallback."""

    def __init__(
        self,
        safety_floor: float = config.ECM_KMEANS_SAFETY_FLOOR,
        fallback_threshold: float = config.ECM_FALLBACK_THRESHOLD,
        random_state: int = config.SEED,
    ) -> None:
        """Initialize KMeansBinarizer with threshold configurations.

        Args:
            safety_floor: Minimum acceptable upper centroid value.
            fallback_threshold: Threshold used if upper centroid is below
                safety floor or if data has insufficient unique values.
            random_state: Random seed for KMeans initialization.
        """
        self.safety_floor = safety_floor
        self.fallback_threshold = fallback_threshold
        self.random_state = random_state

    def binarize(self, raw_features: pd.DataFrame) -> pd.DataFrame:
        """Binarizes raw continuous feature scores using 1D K-Means.

        Args:
            raw_features: DataFrame containing continuous similarity scores.

        Returns:
            DataFrame containing binary integer feature indicators (0 or 1).
        """
        binarized_features = raw_features.copy()

        for col in raw_features.columns:
            col_scores = raw_features[col].values
            non_zero_scores = col_scores[col_scores > 0.0]

            if (
                len(non_zero_scores) >= 2
                and len(np.unique(non_zero_scores)) >= 2
            ):
                kmeans = KMeans(
                    n_clusters=2,
                    n_init=10,
                    random_state=self.random_state,
                )
                kmeans.fit(non_zero_scores.reshape(-1, 1))
                centers = np.sort(kmeans.cluster_centers_.flatten())
                threshold = float((centers[0] + centers[1]) / 2.0)

                if centers[1] < self.safety_floor:
                    logger.debug(
                        "K-Means upper centroid %.3f below safety floor %.3f "
                        "for column '%s'. Overriding threshold to %.3f",
                        centers[1],
                        self.safety_floor,
                        col,
                        self.fallback_threshold,
                    )
                    threshold = self.fallback_threshold
            else:
                threshold = self.fallback_threshold

            binarized_features[col] = (
                raw_features[col] >= threshold
            ).astype(int)

        return binarized_features


class ECMMatchingStrategy(BaseMatchingStrategy):
    """[DEPRECATED] Matching strategy using 1D K-Means binarization and ECM classification.

    Deprecated due to ECM's fundamental limitation requiring binary comparison vectors,
    which necessitates lossy binarization of continuous feature comparators.
    """

    config_schema = ECMMatchingConfig
    config_prompt = ECM_MATCHING_CONFIG_SYSTEM_PROMPT

    def __init__(self, config: ECMMatchingConfig) -> None:
        """Initialize strategy with configuration."""
        warnings.warn(
            "ECMMatchingStrategy is deprecated due to discrete binary feature vector "
            "limitations. Use DynamicWeightedMatchingStrategy or KMeansMatchingStrategy.",
            DeprecationWarning,
            stacklevel=2,
        )
        self.config = config
        self.last_thresholds: dict[str, Any] = {}
        self.classification_engine = DynamicThresholdClassificationEngine()

    @classmethod
    def from_llm_config(cls, config: BaseModel) -> ECMMatchingStrategy:
        """Construct strategy instance from parsed Pydantic config model."""
        if isinstance(config, ECMMatchingConfig):
            return cls(config)
        return cls(ECMMatchingConfig.model_validate(config))

    def _perform_matching(
        self,
        df_a: pd.DataFrame,
        df_b: pd.DataFrame,
        candidate_pairs: pd.MultiIndex,
        classification_mode: ClassificationMode = ClassificationMode.TERNARY,
        **kwargs,
    ) -> tuple[pd.MultiIndex, pd.DataFrame | None]:
        """Computes features, binarizes via K-Means, and classifies via ECM.

        Args:
            df_a: Left input DataFrame.
            df_b: Right input DataFrame.
            candidate_pairs: Candidate pairs MultiIndex.
            classification_mode: Binary or ternary classification mode.
            **kwargs: Additional optional runtime options.

        Returns:
            Tuple of (pd.MultiIndex of positive matched pairs, features_df).
        """
        if candidate_pairs.empty:
            return candidate_pairs, None

        valid_cols = [
            c for c in self.config.matching_columns
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

        binarizer = KMeansBinarizer(
            safety_floor=config.ECM_KMEANS_SAFETY_FLOOR,
            fallback_threshold=config.ECM_FALLBACK_THRESHOLD,
            random_state=config.SEED,
        )
        binarized_features = binarizer.binarize(raw_features)

        ecm = recordlinkage.ECMClassifier()
        ecm.fit(binarized_features)

        if classification_mode == ClassificationMode.BINARY:
            self.last_thresholds = {}
            matches = ecm.predict(binarized_features)
            raw_features["prediction"] = "non_match"
            raw_features.loc[matches, "prediction"] = "match"
            return matches, raw_features

        probs = ecm.prob(binarized_features)
        result = self.classification_engine.classify(
            probs,
            index=candidate_pairs,
            classification_mode=ClassificationMode.TERNARY,
        )
        raw_features["prediction"] = result.predictions
        raw_features["probability"] = probs
        self.last_thresholds = result.thresholds
        raw_features.attrs["dynamic_thresholds"] = dict(result.thresholds)

        return result.matched_pairs, raw_features
