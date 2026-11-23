"""Classification engines for entity resolution candidate pairs."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans

from entity_resolution.models import ClassificationMode
from shared.config import config

logger = logging.getLogger(__name__)


@dataclass
class ClassificationResult:
    """Represents the output of candidate pair classification.

    Attributes:
        predictions: Series of predicted labels ("match", "uncertain",
            "non_match") indexed by candidate pairs.
        matched_pairs: MultiIndex or Index of pairs classified as "match".
        thresholds: Dictionary of threshold telemetry and cluster statistics.
    """

    predictions: pd.Series
    matched_pairs: pd.MultiIndex | pd.Index
    thresholds: dict[str, Any]


class BaseClassificationEngine(ABC):
    """Abstract base class for entity resolution classification engines."""

    @abstractmethod
    def classify(
        self,
        scores: pd.Series | np.ndarray,
        index: pd.Index | pd.MultiIndex | None = None,
        classification_mode: ClassificationMode = ClassificationMode.TERNARY,
        **kwargs: Any,
    ) -> ClassificationResult:
        """Classifies candidate pairs based on continuous similarity scores.

        Args:
            scores: Array or Series of continuous similarity scores.
            index: Optional Index/MultiIndex aligning with scores.
            classification_mode: Binary or ternary classification mode.
            **kwargs: Additional engine-specific arguments.

        Returns:
            ClassificationResult containing predictions, matches, and metadata.
        """
        raise NotImplementedError


class DynamicThresholdClassificationEngine(BaseClassificationEngine):
    """Dynamically thresholds continuous scores via 1D K-Means clustering."""

    def __init__(
        self,
        safety_floor: float = config.DYNAMIC_THRESHOLD_SAFETY_FLOOR,
        asymmetric_alpha: float = config.DYNAMIC_THRESHOLD_ASYMMETRIC_ALPHA,
        dispersion_boost_beta: (
            float
        ) = config.DYNAMIC_THRESHOLD_DISPERSION_BOOST_BETA,
        prefilter_cutoff: float = config.DYNAMIC_THRESHOLD_PREFILTER_CUTOFF,
        random_state: int = config.SEED,
    ) -> None:
        """Initializes the dynamic thresholding engine.

        Args:
            safety_floor: Minimum acceptable upper centroid value before
                triggering dispersion boost.
            asymmetric_alpha: Weight factor for upper threshold interpolation
                between mid and high centroids in ternary mode.
            dispersion_boost_beta: Multiplier for standard deviation tail boost
                when high centroid is below the safety floor.
            prefilter_cutoff: Cutoff score to filter out low-similarity noise.
            random_state: Seed for deterministic K-Means clustering.
        """
        self.safety_floor = safety_floor
        self.asymmetric_alpha = asymmetric_alpha
        self.dispersion_boost_beta = dispersion_boost_beta
        self.prefilter_cutoff = prefilter_cutoff
        self.random_state = random_state

    def compute_thresholds(
        self,
        scores: np.ndarray,
        classification_mode: ClassificationMode = ClassificationMode.TERNARY,
    ) -> dict[str, Any]:
        """Calculates dynamic decision boundaries via 1D K-Means clustering.

        Args:
            scores: 1D numpy array of continuous scores.
            classification_mode: Binary or ternary classification mode.

        Returns:
            Dictionary containing threshold values, mode, centroids, and stats.

        Raises:
            ValueError: If sample size is insufficient or scores exhibit zero
                or insufficient variance for clustering.
        """
        k = 2 if classification_mode == ClassificationMode.BINARY else 3
        mode_label = (
            classification_mode.value
            if hasattr(classification_mode, "value")
            else str(classification_mode)
        )

        if len(scores) < k:
            raise ValueError(
                f"Dynamic thresholding in {mode_label} mode requires at least "
                f"{k} candidate scores. Received {len(scores)} scores."
            )

        if np.all(scores == scores[0]) or len(np.unique(scores)) < 2:
            raise ValueError(
                "Scores exhibit zero or insufficient variance for dynamic "
                "clustering."
            )

        valid_mask = scores >= self.prefilter_cutoff
        filtered_scores = scores[valid_mask]
        clustering_scores = (
            filtered_scores
            if len(filtered_scores) >= k
            and len(np.unique(filtered_scores)) >= 2
            else scores
        )

        num_unique = len(np.unique(clustering_scores))
        if num_unique < 2:
            clustering_scores = scores
            num_unique = len(np.unique(clustering_scores))
            if num_unique < 2:
                raise ValueError(
                    "Scores exhibit zero or insufficient variance for dynamic "
                    "clustering."
                )

        if classification_mode == ClassificationMode.BINARY:
            km = KMeans(
                n_clusters=2,
                n_init=10,
                random_state=self.random_state,
            ).fit(clustering_scores.reshape(-1, 1))

            sorted_order = np.argsort(km.cluster_centers_.flatten())
            c_low, c_high = km.cluster_centers_.flatten()[sorted_order]
            counts = np.bincount(km.labels_, minlength=2)
            n_low = int(counts[sorted_order[0]])
            n_high = int(counts[sorted_order[1]])

            high_cluster_points = (
                clustering_scores[km.labels_ == sorted_order[1]]
            )
            std_high = (
                float(np.std(high_cluster_points))
                if len(high_cluster_points) > 1
                else 0.05
            )

            alpha = float(self.asymmetric_alpha)
            raw_threshold = float(c_low + alpha * (c_high - c_low))

            if raw_threshold < self.safety_floor:
                logger.warning(
                    "Computed raw binary threshold (%.3f) below safety "
                    "floor (%.3f). Applying dispersion-aware tail boost.",
                    raw_threshold,
                    self.safety_floor,
                )
                threshold = float(min(0.90, raw_threshold + std_high))
                mode = "dispersion_boost"
                return {
                    "mode": mode,
                    "threshold": round(threshold, 4),
                    "raw_threshold": round(raw_threshold, 4),
                    "alpha": alpha,
                    "centroids": [round(float(c), 4) for c in (c_low, c_high)],
                    "std_high": round(std_high, 4),
                    "cluster_sizes": [n_low, n_high],
                }

            mode = "dynamic_skew"
            return {
                "mode": mode,
                "threshold": round(raw_threshold, 4),
                "raw_threshold": round(raw_threshold, 4),
                "alpha": alpha,
                "centroids": [round(float(c), 4) for c in (c_low, c_high)],
                "std_high": round(std_high, 4),
                "cluster_sizes": [n_low, n_high],
            }

        if num_unique >= 3:
            km = KMeans(
                n_clusters=3,
                n_init=10,
                random_state=self.random_state,
            ).fit(clustering_scores.reshape(-1, 1))

            sorted_order = np.argsort(km.cluster_centers_.flatten())
            c_low, c_mid, c_high = km.cluster_centers_.flatten()[sorted_order]
            counts = np.bincount(km.labels_, minlength=3)
            n_low = int(counts[sorted_order[0]])
            n_mid = int(counts[sorted_order[1]])
            n_high = int(counts[sorted_order[2]])

            high_cluster_points = clustering_scores[
                km.labels_ == sorted_order[2]
            ]
        else:
            km = KMeans(
                n_clusters=2,
                n_init=10,
                random_state=self.random_state,
            ).fit(clustering_scores.reshape(-1, 1))

            sorted_order = np.argsort(km.cluster_centers_.flatten())
            c_low, c_high = km.cluster_centers_.flatten()[sorted_order]
            c_mid = (c_low + c_high) / 2.0
            counts = np.bincount(km.labels_, minlength=2)
            n_low = int(counts[sorted_order[0]])
            n_mid = 0
            n_high = int(counts[sorted_order[1]])

            high_cluster_points = clustering_scores[
                km.labels_ == sorted_order[1]
            ]

        std_high = (
            float(np.std(high_cluster_points))
            if len(high_cluster_points) > 1
            else 0.05
        )

        if c_high < self.safety_floor:
            logger.warning(
                "Dynamic weighted match centroid (%.3f) below safety "
                "floor. Applying dispersion-aware tail boost.",
                c_high,
            )
            dynamic_upper = float(
                min(0.95, c_high + self.dispersion_boost_beta * std_high)
            )
            dynamic_lower = float(c_high)
            mode = "dispersion_boost"
            return {
                "mode": mode,
                "beta": float(self.dispersion_boost_beta),
                "std_high": round(std_high, 4),
                "lower_threshold": round(dynamic_lower, 4),
                "upper_threshold": round(dynamic_upper, 4),
                "centroids": [
                    round(float(c), 4) for c in (c_low, c_mid, c_high)
                ],
                "cluster_sizes": [n_low, n_mid, n_high],
            }

        alpha = float(self.asymmetric_alpha)
        dynamic_upper = float(c_mid + alpha * (c_high - c_mid))
        dynamic_lower = float((c_low + c_mid) / 2.0)
        mode = "dynamic_skew"
        return {
            "mode": mode,
            "alpha": alpha,
            "std_high": round(std_high, 4),
            "lower_threshold": round(dynamic_lower, 4),
            "upper_threshold": round(dynamic_upper, 4),
            "centroids": [
                round(float(c), 4) for c in (c_low, c_mid, c_high)
            ],
            "cluster_sizes": [n_low, n_mid, n_high],
        }

    def classify(
        self,
        scores: pd.Series | np.ndarray,
        index: pd.Index | pd.MultiIndex | None = None,
        classification_mode: ClassificationMode = ClassificationMode.TERNARY,
        **kwargs: Any,
    ) -> ClassificationResult:
        """Classifies candidate pairs based on dynamic 1D K-Means thresholds.

        Args:
            scores: Continuous similarity scores.
            index: Optional index matching scores if scores is an ndarray.
            classification_mode: Binary or ternary classification mode.
            **kwargs: Additional parameters (unused).

        Returns:
            ClassificationResult with predictions, matched pairs, and metadata.
        """
        if isinstance(scores, pd.Series):
            if index is None:
                index = scores.index
            raw_scores = scores.to_numpy(dtype=float)
        else:
            raw_scores = np.asarray(scores, dtype=float)
            if index is None:
                index = pd.RangeIndex(len(raw_scores))

        thresholds = self.compute_thresholds(
            raw_scores, classification_mode=classification_mode
        )

        if classification_mode == ClassificationMode.BINARY:
            threshold = thresholds["threshold"]
            predictions = pd.Series("non_match", index=index, dtype=object)
            match_mask = raw_scores >= threshold
            predictions.iloc[match_mask] = "match"
            matched_pairs = index[match_mask]
            return ClassificationResult(
                predictions=predictions,
                matched_pairs=matched_pairs,
                thresholds=thresholds,
            )

        lower = thresholds["lower_threshold"]
        upper = thresholds["upper_threshold"]
        predictions = pd.Series("uncertain", index=index, dtype=object)
        match_mask = raw_scores >= upper
        non_match_mask = raw_scores < lower
        predictions.iloc[match_mask] = "match"
        predictions.iloc[non_match_mask] = "non_match"
        matched_pairs = index[match_mask]

        return ClassificationResult(
            predictions=predictions,
            matched_pairs=matched_pairs,
            thresholds=thresholds,
        )
