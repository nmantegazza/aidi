"""Integration tests for dynamic thresholding standardization across matching strategies."""

from __future__ import annotations

import pandas as pd

from entity_resolution.matching_strategies.ecm import ECMMatchingStrategy
from entity_resolution.matching_strategies.implementations import (
    DynamicWeightedMatchingStrategy,
    WeightedScoreMatchingConfig,
)
from entity_resolution.matching_strategies.kmeans import KMeansMatchingStrategy
from entity_resolution.models import (
    ClassificationMode,
    ColumnMatchConfig,
    ECMColumnConfig,
    ECMMatchingConfig,
    KMeansColumnConfig,
    KMeansMatchingConfig,
    SimilarityAlgorithm,
)


def _sample_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.MultiIndex]:
    """Generates sample test DataFrames and candidate pairs."""
    df_a = pd.DataFrame(
        {
            "name": [
                "Alice Smith",
                "Bob Jones",
                "Charlie Brown",
                "David Wilson",
                "Eva Green",
            ],
            "city": [
                "New York",
                "Los Angeles",
                "Chicago",
                "Houston",
                "Miami",
            ],
        }
    )
    df_b = pd.DataFrame(
        {
            "name": [
                "Alice Smith",
                "Bobby Jones",
                "Charlie Brown",
                "Xavier Drake",
                "Zack Taylor",
            ],
            "city": [
                "New York",
                "San Francisco",
                "Chicago",
                "Seattle",
                "Dallas",
            ],
        }
    )
    candidate_pairs = pd.MultiIndex.from_tuples(
        [(0, 0), (1, 1), (2, 2), (3, 3), (4, 4)], names=["a", "b"]
    )
    return df_a, df_b, candidate_pairs


def test_dynamic_weighted_standardized_telemetry():
    """Tests DynamicWeightedMatchingStrategy produces standardized telemetry."""
    df_a, df_b, candidate_pairs = _sample_data()
    cfg = WeightedScoreMatchingConfig(
        reasoning="Test dynamic weighted standardization.",
        matching_columns={
            "name": ColumnMatchConfig(
                algorithm=SimilarityAlgorithm.JAROWINKLER, weight=1.0
            ),
            "city": ColumnMatchConfig(
                algorithm=SimilarityAlgorithm.EXACT, weight=0.8
            ),
        },
    )
    strategy = DynamicWeightedMatchingStrategy(cfg)
    result = strategy.execute(
        df_a,
        df_b,
        candidate_pairs,
        classification_mode=ClassificationMode.TERNARY,
    )

    assert result.features_df is not None
    assert "prediction" in result.features_df.columns
    assert set(result.features_df["prediction"].unique()).issubset(
        {"match", "uncertain", "non_match"}
    )
    assert "dynamic_thresholds" in result.features_df.attrs
    dt = result.features_df.attrs["dynamic_thresholds"]
    assert dt["mode"] in ("dynamic_skew", "dispersion_boost")
    assert "upper_threshold" in dt
    assert "lower_threshold" in dt
    assert "centroids" in dt
    assert len(dt["centroids"]) == 3
    assert strategy.last_thresholds == dt


def test_kmeans_ternary_dynamic_thresholding():
    """Tests KMeansMatchingStrategy ternary mode delegates to dynamic thresholding."""
    df_a, df_b, candidate_pairs = _sample_data()
    cfg = KMeansMatchingConfig(
        reasoning="Test KMeans ternary dynamic thresholding.",
        matching_columns={
            "name": KMeansColumnConfig(
                algorithm=SimilarityAlgorithm.JAROWINKLER
            ),
            "city": KMeansColumnConfig(algorithm=SimilarityAlgorithm.EXACT),
        },
    )
    strategy = KMeansMatchingStrategy(cfg)
    result = strategy.execute(
        df_a,
        df_b,
        candidate_pairs,
        classification_mode=ClassificationMode.TERNARY,
    )

    assert result.features_df is not None
    assert "prediction" in result.features_df.columns
    assert "probability" in result.features_df.columns
    assert set(result.features_df["prediction"].unique()).issubset(
        {"match", "uncertain", "non_match"}
    )
    assert "dynamic_thresholds" in result.features_df.attrs
    dt = result.features_df.attrs["dynamic_thresholds"]
    assert dt["mode"] in ("dynamic_skew", "dispersion_boost")
    assert "upper_threshold" in dt
    assert "lower_threshold" in dt
    assert len(dt["centroids"]) == 3
    assert strategy.last_thresholds == dt


def test_ecm_ternary_dynamic_thresholding():
    """Tests ECMMatchingStrategy ternary mode delegates to dynamic thresholding."""
    df_a, df_b, candidate_pairs = _sample_data()
    cfg = ECMMatchingConfig(
        reasoning="Test ECM ternary dynamic thresholding.",
        matching_columns={
            "name": ECMColumnConfig(
                algorithm=SimilarityAlgorithm.JAROWINKLER
            ),
            "city": ECMColumnConfig(algorithm=SimilarityAlgorithm.EXACT),
        },
    )
    strategy = ECMMatchingStrategy(cfg)
    result = strategy.execute(
        df_a,
        df_b,
        candidate_pairs,
        classification_mode=ClassificationMode.TERNARY,
    )

    assert result.features_df is not None
    assert "prediction" in result.features_df.columns
    assert "probability" in result.features_df.columns
    assert set(result.features_df["prediction"].unique()).issubset(
        {"match", "uncertain", "non_match"}
    )
    assert "dynamic_thresholds" in result.features_df.attrs
    dt = result.features_df.attrs["dynamic_thresholds"]
    assert dt["mode"] in ("dynamic_skew", "dispersion_boost")
    assert "upper_threshold" in dt
    assert "lower_threshold" in dt
    assert len(dt["centroids"]) == 3
    assert strategy.last_thresholds == dt


def test_native_binary_mode_kmeans_and_ecm():
    """Tests native binary classification is preserved for KMeans and ECM."""
    df_a, df_b, candidate_pairs = _sample_data()

    # KMeans binary
    km_cfg = KMeansMatchingConfig(
        reasoning="Test KMeans binary native.",
        matching_columns={
            "name": KMeansColumnConfig(
                algorithm=SimilarityAlgorithm.JAROWINKLER
            ),
            "city": KMeansColumnConfig(algorithm=SimilarityAlgorithm.EXACT),
        },
    )
    km_strat = KMeansMatchingStrategy(km_cfg)
    km_res = km_strat.execute(
        df_a,
        df_b,
        candidate_pairs,
        classification_mode=ClassificationMode.BINARY,
    )
    assert km_res.features_df is not None
    assert "uncertain" not in km_res.features_df["prediction"].values
    assert km_strat.last_thresholds == {}
    assert "dynamic_thresholds" not in km_res.features_df.attrs

    # ECM binary
    ecm_cfg = ECMMatchingConfig(
        reasoning="Test ECM binary native.",
        matching_columns={
            "name": ECMColumnConfig(
                algorithm=SimilarityAlgorithm.JAROWINKLER
            ),
            "city": ECMColumnConfig(algorithm=SimilarityAlgorithm.EXACT),
        },
    )
    ecm_strat = ECMMatchingStrategy(ecm_cfg)
    ecm_res = ecm_strat.execute(
        df_a,
        df_b,
        candidate_pairs,
        classification_mode=ClassificationMode.BINARY,
    )
    assert ecm_res.features_df is not None
    assert "uncertain" not in ecm_res.features_df["prediction"].values
    assert ecm_strat.last_thresholds == {}
    assert "dynamic_thresholds" not in ecm_res.features_df.attrs
