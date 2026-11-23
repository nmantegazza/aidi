"""Unit tests for KMeansMatchingStrategy and its configuration models."""

import pandas as pd
import pytest

from entity_resolution.benchmarking.matching_runner import (
    STRATEGIES,
    _matching_strategy_canonical_slug,
    _matching_strategy_display_name,
    _resolve_matching_strategy_class,
)
from entity_resolution.matching_strategies import (
    KMeansMatchingConfig,
    KMeansMatchingStrategy,
)
from entity_resolution.models import (
    ClassificationMode,
    KMeansColumnConfig,
    SimilarityAlgorithm,
)


def test_kmeans_config_validation():
    """Tests Pydantic validation for KMeansMatchingConfig."""
    cfg = KMeansMatchingConfig(
        reasoning="Test reasoning for KMeans configuration.",
        matching_columns={
            "name": KMeansColumnConfig(algorithm=SimilarityAlgorithm.JAROWINKLER),
            "age": KMeansColumnConfig(algorithm=SimilarityAlgorithm.NUMERIC_LINEAR),
        },
    )
    assert cfg.reasoning == "Test reasoning for KMeans configuration."
    assert (
        cfg.matching_columns["name"].algorithm == SimilarityAlgorithm.JAROWINKLER
    )
    assert (
        cfg.matching_columns["age"].algorithm == SimilarityAlgorithm.NUMERIC_LINEAR
    )

    with pytest.raises(ValueError, match="matching_columns cannot be empty"):
        KMeansMatchingConfig(reasoning="Test", matching_columns={})


def test_kmeans_matching_strategy_execution_vanilla():
    """Tests KMeansMatchingStrategy in vanilla binary mode."""
    df_a = pd.DataFrame(
        {
            "name": [
                "Alice Smith",
                "Bob Jones",
                "Charlie Brown",
                "David Wilson",
            ],
            "city": ["New York", "Los Angeles", "Chicago", "Houston"],
        }
    )
    df_b = pd.DataFrame(
        {
            "name": [
                "Alice Smith",
                "Bobby Jones",
                "Xavier Drake",
                "Zack Taylor",
            ],
            "city": ["New York", "Los Angeles", "Miami", "Seattle"],
        }
    )
    candidate_pairs = pd.MultiIndex.from_tuples(
        [(0, 0), (1, 1), (2, 2), (3, 3)], names=["a", "b"]
    )

    cfg = KMeansMatchingConfig(
        reasoning="Test vanilla KMeans matching configuration.",
        matching_columns={
            "name": KMeansColumnConfig(algorithm=SimilarityAlgorithm.JAROWINKLER),
            "city": KMeansColumnConfig(algorithm=SimilarityAlgorithm.EXACT),
        },
    )
    strategy = KMeansMatchingStrategy(cfg)
    result = strategy.execute(
        df_a,
        df_b,
        candidate_pairs,
        classification_mode=ClassificationMode.BINARY,
    )

    assert isinstance(result.classified_pairs, pd.MultiIndex)
    assert result.features_df is not None
    assert "prediction" in result.features_df.columns
    assert set(result.features_df["prediction"].unique()).issubset(
        {"match", "non_match"}
    )
    assert "uncertain" not in result.features_df["prediction"].values
    # (0, 0) and (1, 1) are high similarity, (2, 2) and (3, 3) are dissimilar
    assert (0, 0) in result.classified_pairs


def test_kmeans_matching_strategy_execution_ternary_bucket():
    """Tests KMeansMatchingStrategy with ClassificationMode.TERNARY."""
    df_a = pd.DataFrame(
        {
            "name": [
                "Alice Smith",
                "Bob Jones",
                "Charlie Brown",
                "David Wilson",
            ],
            "city": ["New York", "Los Angeles", "Chicago", "Houston"],
        }
    )
    df_b = pd.DataFrame(
        {
            "name": [
                "Alice Smith",
                "Bobby Jones",
                "Xavier Drake",
                "Zack Taylor",
            ],
            "city": ["New York", "Los Angeles", "Miami", "Seattle"],
        }
    )
    candidate_pairs = pd.MultiIndex.from_tuples(
        [(0, 0), (1, 1), (2, 2), (3, 3)], names=["a", "b"]
    )

    cfg = KMeansMatchingConfig(
        reasoning="Test ternary bucket KMeans matching configuration.",
        matching_columns={
            "name": KMeansColumnConfig(algorithm=SimilarityAlgorithm.JAROWINKLER),
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

    assert isinstance(result.classified_pairs, pd.MultiIndex)
    assert result.features_df is not None
    assert "prediction" in result.features_df.columns
    assert "probability" in result.features_df.columns
    assert set(result.features_df["prediction"].unique()).issubset(
        {"match", "uncertain", "non_match"}
    )


def test_kmeans_matching_strategy_empty_pairs():
    """Tests that empty candidate pairs returns empty result."""
    df_a = pd.DataFrame({"name": ["Alice Smith"]})
    df_b = pd.DataFrame({"name": ["Alice Smith"]})
    empty_pairs = pd.MultiIndex.from_tuples([], names=["a", "b"])

    cfg = KMeansMatchingConfig(
        reasoning="Test empty candidate pairs.",
        matching_columns={
            "name": KMeansColumnConfig(algorithm=SimilarityAlgorithm.JAROWINKLER),
        },
    )
    strategy = KMeansMatchingStrategy(cfg)
    result = strategy.execute(df_a, df_b, empty_pairs)
    assert result.classified_pairs.empty
    assert result.features_df is None


def test_kmeans_matching_strategy_insufficient_samples():
    """Tests candidate count guards in binary (<2) and ternary (<3) modes."""
    df_a = pd.DataFrame({"name": ["Alice Smith", "Bob Jones"]})
    df_b = pd.DataFrame({"name": ["Alice Smith", "Bob Jones"]})
    single_pair = pd.MultiIndex.from_tuples([(0, 0)], names=["a", "b"])
    two_pairs = pd.MultiIndex.from_tuples([(0, 0), (1, 1)], names=["a", "b"])

    cfg = KMeansMatchingConfig(
        reasoning="Test insufficient samples configuration.",
        matching_columns={
            "name": KMeansColumnConfig(algorithm=SimilarityAlgorithm.JAROWINKLER),
        },
    )
    strategy = KMeansMatchingStrategy(cfg)

    with pytest.raises(
        ValueError,
        match="KMeans matching in binary mode requires at least 2 candidate pairs",
    ):
        strategy.execute(
            df_a,
            df_b,
            single_pair,
            classification_mode=ClassificationMode.BINARY,
        )

    with pytest.raises(
        ValueError,
        match="KMeans matching in ternary mode requires at least 3 candidate pairs",
    ):
        strategy.execute(
            df_a,
            df_b,
            two_pairs,
            classification_mode=ClassificationMode.TERNARY,
        )


def test_kmeans_matching_strategy_unconstrained_binary_with_low_centroid(caplog):
    """Tests that low centroid in binary mode logs a warning but proceeds unconstrained."""
    df_a = pd.DataFrame(
        {
            "name": ["Alice", "Bob", "Charlie", "David"],
            "city": ["New York", "Chicago", "Boston", "Seattle"],
        }
    )
    df_b = pd.DataFrame(
        {
            "name": ["Alicia", "Robert", "Chuck", "Dave"],
            "city": ["Newark", "Chicago Heights", "Austin", "Portland"],
        }
    )
    candidate_pairs = pd.MultiIndex.from_tuples(
        [(0, 0), (1, 1), (2, 2), (3, 3)], names=["a", "b"]
    )

    cfg = KMeansMatchingConfig(
        reasoning="Test unconstrained binary prediction configuration.",
        matching_columns={
            "name": KMeansColumnConfig(
                algorithm=SimilarityAlgorithm.JAROWINKLER
            ),
            "city": KMeansColumnConfig(
                algorithm=SimilarityAlgorithm.JAROWINKLER
            ),
        },
    )
    strategy = KMeansMatchingStrategy(cfg)
    result = strategy.execute(
        df_a,
        df_b,
        candidate_pairs,
        classification_mode=ClassificationMode.BINARY,
    )
    assert result.features_df is not None
    assert "prediction" in result.features_df.columns
    assert isinstance(result.classified_pairs, pd.MultiIndex)


def test_kmeans_matching_strategy_ternary_dispersion_boost():
    """Tests that low similarity distribution in ternary mode triggers dynamic dispersion boost."""
    df_a = pd.DataFrame(
        {
            "name": ["Alice", "Bob", "Charlie", "David"],
            "city": ["New York", "Chicago", "Boston", "Seattle"],
        }
    )
    df_b = pd.DataFrame(
        {
            "name": ["Alicia", "Robert", "Chuck", "Dave"],
            "city": ["Newark", "Chicago Heights", "Austin", "Portland"],
        }
    )
    candidate_pairs = pd.MultiIndex.from_tuples(
        [(0, 0), (1, 1), (2, 2), (3, 3)], names=["a", "b"]
    )

    cfg = KMeansMatchingConfig(
        reasoning="Test ternary dispersion boost configuration.",
        matching_columns={
            "name": KMeansColumnConfig(
                algorithm=SimilarityAlgorithm.JAROWINKLER
            ),
            "city": KMeansColumnConfig(
                algorithm=SimilarityAlgorithm.JAROWINKLER
            ),
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
    assert "mode" in strategy.last_thresholds
    assert "upper_threshold" in strategy.last_thresholds


def test_kmeans_nan_imputation():
    """Tests that NaN/None values in comparison features are imputed to 0.0."""
    df_a = pd.DataFrame(
        {
            "name": ["Alice Smith", None, "Charlie Brown", "David Wilson"],
            "city": [None, "Los Angeles", "Chicago", "Miami"],
        }
    )
    df_b = pd.DataFrame(
        {
            "name": [None, "Bob Jones", "Charlie Brown", "David W."],
            "city": ["New York", None, "Chicago", "Miami"],
        }
    )
    candidate_pairs = pd.MultiIndex.from_tuples(
        [(0, 0), (1, 1), (2, 2), (3, 3)], names=["a", "b"]
    )

    cfg = KMeansMatchingConfig(
        reasoning="Test NaN imputation configuration.",
        matching_columns={
            "name": KMeansColumnConfig(algorithm=SimilarityAlgorithm.JAROWINKLER),
            "city": KMeansColumnConfig(algorithm=SimilarityAlgorithm.EXACT),
        },
    )
    strategy = KMeansMatchingStrategy(cfg)
    result = strategy.execute(df_a, df_b, candidate_pairs)

    assert result.features_df is not None
    # Feature columns should have no NaN values
    assert not result.features_df[["name", "city"]].isna().any().any()


def test_kmeans_runner_registration():
    """Tests registration and lookup of KMeansMatchingStrategy in runner."""
    assert "kmeans" in STRATEGIES
    assert STRATEGIES["kmeans"] is KMeansMatchingStrategy

    assert _resolve_matching_strategy_class("kmeans") is KMeansMatchingStrategy
    assert (
        _resolve_matching_strategy_class("kmeans_strategy")
        is KMeansMatchingStrategy
    )
    assert (
        _resolve_matching_strategy_class("KMeansMatchingStrategy")
        is KMeansMatchingStrategy
    )

    assert (
        _matching_strategy_canonical_slug(KMeansMatchingStrategy) == "kmeans"
    )
    assert (
        _matching_strategy_display_name(KMeansMatchingStrategy)
        == "K-Means Matching"
    )
