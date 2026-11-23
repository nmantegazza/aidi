"""Unit tests for the unified classification engine."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from entity_resolution.classification import (
    ClassificationResult,
    DynamicThresholdClassificationEngine,
)
from entity_resolution.models import ClassificationMode


def test_binary_mode_dynamic_skew():
    """Tests binary classification in dynamic skew mode."""
    engine = DynamicThresholdClassificationEngine(
        safety_floor=0.60,
        asymmetric_alpha=0.60,
        prefilter_cutoff=0.0,
        random_state=42,
    )
    scores = np.array([0.1, 0.15, 0.2, 0.85, 0.9, 0.95])
    index = pd.Index(["p1", "p2", "p3", "p4", "p5", "p6"])

    result = engine.classify(
        scores, index=index, classification_mode=ClassificationMode.BINARY
    )

    assert isinstance(result, ClassificationResult)
    assert result.thresholds["mode"] == "dynamic_skew"
    assert "threshold" in result.thresholds
    assert result.thresholds["alpha"] == 0.60
    assert len(result.thresholds["centroids"]) == 2
    c_low, c_high = result.thresholds["centroids"]
    assert c_high >= 0.60
    expected_raw = c_low + 0.60 * (c_high - c_low)
    assert result.thresholds["raw_threshold"] == pytest.approx(
        round(expected_raw, 4), abs=1e-4
    )
    assert result.thresholds["threshold"] == pytest.approx(
        round(expected_raw, 4), abs=1e-4
    )
    assert set(result.predictions.unique()).issubset({"match", "non_match"})
    assert "uncertain" not in result.predictions.values
    assert list(result.matched_pairs) == ["p4", "p5", "p6"]


def test_binary_mode_dispersion_boost():
    """Tests binary classification in dispersion boost mode when raw_threshold < safety_floor."""
    engine = DynamicThresholdClassificationEngine(
        safety_floor=0.70,
        asymmetric_alpha=0.60,
        prefilter_cutoff=0.0,
        random_state=42,
    )
    scores = np.array([0.1, 0.12, 0.15, 0.40, 0.45, 0.48])

    result = engine.classify(
        scores, classification_mode=ClassificationMode.BINARY
    )

    assert result.thresholds["mode"] == "dispersion_boost"
    assert result.thresholds["alpha"] == 0.60
    c_low, c_high = result.thresholds["centroids"]
    std_high = result.thresholds["std_high"]
    expected_raw = c_low + 0.60 * (c_high - c_low)
    expected_th = min(0.90, expected_raw + std_high)
    assert result.thresholds["raw_threshold"] == pytest.approx(
        round(expected_raw, 4), abs=1e-4
    )
    assert result.thresholds["threshold"] == pytest.approx(
        round(expected_th, 4), abs=1e-4
    )


def test_binary_mode_dispersion_boost_elevated_centroid_depressed_threshold():
    """Tests dispersion boost triggers when c_high >= safety_floor but raw_threshold < safety_floor."""
    engine = DynamicThresholdClassificationEngine(
        safety_floor=0.60,
        asymmetric_alpha=0.60,
        prefilter_cutoff=0.0,
        random_state=42,
    )
    # c_low ≈ 0.15, c_high ≈ 0.65 (>= 0.60), raw_threshold ≈ 0.15 + 0.60 * (0.65 - 0.15) = 0.45 (< 0.60)
    scores = np.array([0.10, 0.15, 0.20, 0.60, 0.65, 0.70])

    result = engine.classify(
        scores, classification_mode=ClassificationMode.BINARY
    )

    assert result.thresholds["mode"] == "dispersion_boost"
    _c_low, c_high = result.thresholds["centroids"]
    assert c_high >= 0.60
    assert result.thresholds["raw_threshold"] < 0.60
    assert result.thresholds["threshold"] > result.thresholds["raw_threshold"]


def test_binary_mode_dispersion_boost_cap_at_90():
    """Tests that boosted threshold is capped at 0.90."""
    engine = DynamicThresholdClassificationEngine(
        safety_floor=0.99,  # Force dispersion boost
        asymmetric_alpha=0.60,
        prefilter_cutoff=0.0,
        random_state=42,
    )
    scores = np.array([0.70, 0.75, 0.80, 0.85, 0.92, 0.99])

    result = engine.classify(
        scores, classification_mode=ClassificationMode.BINARY
    )

    assert result.thresholds["mode"] == "dispersion_boost"
    assert result.thresholds["threshold"] == 0.90


def test_ternary_mode_dynamic_skew():
    """Tests ternary classification in dynamic skew mode."""
    engine = DynamicThresholdClassificationEngine(
        safety_floor=0.60,
        asymmetric_alpha=0.60,
        prefilter_cutoff=0.0,
        random_state=42,
    )
    scores = pd.Series(
        [0.05, 0.1, 0.15, 0.5, 0.55, 0.6, 0.85, 0.9, 0.95],
        index=[f"pair_{i}" for i in range(9)],
    )

    result = engine.classify(
        scores, classification_mode=ClassificationMode.TERNARY
    )

    assert result.thresholds["mode"] == "dynamic_skew"
    assert result.thresholds["alpha"] == 0.60
    assert len(result.thresholds["centroids"]) == 3
    c_low, c_mid, c_high = result.thresholds["centroids"]
    assert c_high >= 0.60

    expected_upper = c_mid + 0.60 * (c_high - c_mid)
    expected_lower = (c_low + c_mid) / 2.0
    assert result.thresholds["upper_threshold"] == pytest.approx(
        round(expected_upper, 4), abs=1e-4
    )
    assert result.thresholds["lower_threshold"] == pytest.approx(
        round(expected_lower, 4), abs=1e-4
    )

    assert set(result.predictions.unique()) == {"match", "uncertain", "non_match"}
    assert list(result.matched_pairs) == ["pair_6", "pair_7", "pair_8"]


def test_ternary_mode_dispersion_boost():
    """Tests ternary classification in dispersion boost mode when c_high < safety_floor."""
    engine = DynamicThresholdClassificationEngine(
        safety_floor=0.60,
        dispersion_boost_beta=2.50,
        prefilter_cutoff=0.0,
        random_state=42,
    )
    scores = np.array([0.05, 0.08, 0.10, 0.20, 0.22, 0.25, 0.38, 0.40, 0.42])

    result = engine.classify(
        scores, classification_mode=ClassificationMode.TERNARY
    )

    assert result.thresholds["mode"] == "dispersion_boost"
    assert result.thresholds["beta"] == 2.50
    _c_low, _c_mid, c_high = result.thresholds["centroids"]
    assert c_high < 0.60
    std_high = result.thresholds["std_high"]
    expected_upper = min(0.95, c_high + 2.50 * std_high)
    expected_lower = c_high
    assert result.thresholds["upper_threshold"] == pytest.approx(
        round(expected_upper, 4), abs=1e-4
    )
    assert result.thresholds["lower_threshold"] == pytest.approx(
        round(expected_lower, 4), abs=1e-4
    )


def test_prefilter_cutoff():
    """Tests that noise scores below prefilter_cutoff are excluded from clustering."""
    engine = DynamicThresholdClassificationEngine(
        prefilter_cutoff=0.30,
        random_state=42,
    )
    # 5 noise scores < 0.30, and 6 clustered scores >= 0.30
    noise = [0.01, 0.02, 0.03, 0.04, 0.05]
    meaningful = [0.45, 0.50, 0.55, 0.85, 0.90, 0.95]
    scores = np.array(noise + meaningful)

    result = engine.classify(
        scores, classification_mode=ClassificationMode.TERNARY
    )

    # Cluster sizes should sum to len(meaningful) because filtered scores were used
    assert sum(result.thresholds["cluster_sizes"]) == len(meaningful)


def test_prefilter_cutoff_fallback():
    """Tests fallback to raw scores when prefiltered scores count is less than k."""
    engine = DynamicThresholdClassificationEngine(
        prefilter_cutoff=0.80,
        random_state=42,
    )
    # Only 1 score >= 0.80, which is < 3
    scores = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.9])

    result = engine.classify(
        scores, classification_mode=ClassificationMode.TERNARY
    )
    # Uses raw scores fallback
    assert sum(result.thresholds["cluster_sizes"]) == len(scores)


def test_insufficient_samples_raises():
    """Tests that insufficient samples raise ValueError."""
    engine = DynamicThresholdClassificationEngine()

    with pytest.raises(
        ValueError,
        match="Dynamic thresholding in binary mode requires at least 2 candidate scores",
    ):
        engine.compute_thresholds(
            np.array([0.5]), classification_mode=ClassificationMode.BINARY
        )

    with pytest.raises(
        ValueError,
        match="Dynamic thresholding in ternary mode requires at least 3 candidate scores",
    ):
        engine.compute_thresholds(
            np.array([0.5, 0.8]), classification_mode=ClassificationMode.TERNARY
        )


def test_zero_variance_raises():
    """Tests that zero variance scores raise ValueError in binary and ternary modes."""
    engine = DynamicThresholdClassificationEngine()

    with pytest.raises(
        ValueError,
        match="Scores exhibit zero or insufficient variance for dynamic clustering",
    ):
        engine.compute_thresholds(
            np.array([0.0, 0.0, 0.0, 0.0]),
            classification_mode=ClassificationMode.TERNARY,
        )

    with pytest.raises(
        ValueError,
        match="Scores exhibit zero or insufficient variance for dynamic clustering",
    ):
        engine.compute_thresholds(
            np.array([0.7, 0.7, 0.7]),
            classification_mode=ClassificationMode.TERNARY,
        )

    with pytest.raises(
        ValueError,
        match="Scores exhibit zero or insufficient variance for dynamic clustering",
    ):
        engine.compute_thresholds(
            np.array([0.5, 0.5]),
            classification_mode=ClassificationMode.BINARY,
        )
