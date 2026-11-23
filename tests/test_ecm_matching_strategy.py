"""
Unit tests for ECMMatchingStrategy and its configuration models.
"""

import pandas as pd
import pytest

from entity_resolution.matching_strategies.ecm import (
    ECMMatchingStrategy,
)
from entity_resolution.models import (
    ClassificationMode,
    ECMColumnConfig,
    ECMMatchingConfig,
    SimilarityAlgorithm,
)


def test_ecm_config_validation():
    """Tests Pydantic validation for ECMMatchingConfig."""
    cfg = ECMMatchingConfig(
        reasoning="Test reasoning for ECM configuration.",
        matching_columns={
            "name": ECMColumnConfig(algorithm=SimilarityAlgorithm.JAROWINKLER),
            "age": ECMColumnConfig(algorithm=SimilarityAlgorithm.NUMERIC_LINEAR),
        },
    )
    assert cfg.reasoning == "Test reasoning for ECM configuration."
    assert cfg.matching_columns["name"].algorithm == SimilarityAlgorithm.JAROWINKLER
    assert cfg.matching_columns["age"].algorithm == SimilarityAlgorithm.NUMERIC_LINEAR

    with pytest.raises(ValueError, match="matching_columns cannot be empty"):
        ECMMatchingConfig(reasoning="Test", matching_columns={})


def test_ecm_matching_strategy_execution_vanilla():
    """Tests ECMMatchingStrategy in vanilla mode (binary classification)."""
    df_a = pd.DataFrame({
        "name": ["Alice Smith", "Bob Jones", "Charlie Brown"],
        "city": ["New York", "Los Angeles", "Chicago"],
    })
    df_b = pd.DataFrame({
        "name": ["Alice Smith", "Bobby Jones", "Charles Brown"],
        "city": ["New York", "Los Angeles", "Chicago"],
    })
    candidate_pairs = pd.MultiIndex.from_tuples([(0, 0), (1, 1), (2, 2)])

    cfg = ECMMatchingConfig(
        reasoning="Test vanilla ECM matching configuration.",
        matching_columns={
            "name": ECMColumnConfig(algorithm=SimilarityAlgorithm.JAROWINKLER),
            "city": ECMColumnConfig(algorithm=SimilarityAlgorithm.EXACT),
        },
    )
    strategy = ECMMatchingStrategy(cfg)
    result = strategy.execute(
        df_a,
        df_b,
        candidate_pairs,
        classification_mode=ClassificationMode.BINARY,
    )

    assert isinstance(result.classified_pairs, pd.MultiIndex)
    assert result.features_df is not None
    assert "prediction" in result.features_df.columns
    assert set(result.features_df["prediction"].unique()).issubset({"match", "non_match"})


def test_ecm_matching_strategy_execution_uncertain_bucket():
    """Tests ECMMatchingStrategy with ClassificationMode.TERNARY."""
    df_a = pd.DataFrame({
        "name": ["Alice Smith", "Bob Jones", "Charlie Brown"],
        "city": ["New York", "Los Angeles", "Chicago"],
    })
    df_b = pd.DataFrame({
        "name": ["Alice Smith", "Bob Jones", "Xavier Drake"],
        "city": ["New York", "San Francisco", "Miami"],
    })
    candidate_pairs = pd.MultiIndex.from_tuples([(0, 0), (1, 1), (2, 2)])

    cfg = ECMMatchingConfig(
        reasoning="Test uncertain bucket ECM matching configuration.",
        matching_columns={
            "name": ECMColumnConfig(algorithm=SimilarityAlgorithm.JAROWINKLER),
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

    assert isinstance(result.classified_pairs, pd.MultiIndex)
    assert result.features_df is not None
    assert "prediction" in result.features_df.columns
    assert set(result.features_df["prediction"].unique()).issubset({"match", "uncertain", "non_match"})


def test_ecm_matching_strategy_empty_pairs():
    """Tests ECMMatchingStrategy with empty candidate pairs."""
    df_a = pd.DataFrame({"name": ["Alice"]})
    df_b = pd.DataFrame({"name": ["Bob"]})
    empty_pairs = pd.MultiIndex.from_tuples([], names=[None, None])

    cfg = ECMMatchingConfig(
        reasoning="Test empty candidate pairs configuration.",
        matching_columns={
            "name": ECMColumnConfig(algorithm=SimilarityAlgorithm.JAROWINKLER),
        },
    )
    strategy = ECMMatchingStrategy(cfg)
    result = strategy.execute(df_a, df_b, empty_pairs)

    assert result.classified_pairs.empty
    assert result.features_df is None


def test_kmeans_binarizer():
    """Tests KMeansBinarizer functionality and safety floor fallback."""
    from entity_resolution.matching_strategies.ecm import KMeansBinarizer

    binarizer = KMeansBinarizer(safety_floor=0.70, fallback_threshold=0.85)

    # Test distinct clusters: low cluster around 0.1, high cluster around 0.9
    df_raw = pd.DataFrame({
        "score": [0.1, 0.12, 0.15, 0.88, 0.92, 0.95]
    })
    df_bin = binarizer.binarize(df_raw)
    assert list(df_bin["score"]) == [0, 0, 0, 1, 1, 1]

    # Test safety floor trigger: upper cluster center < 0.70
    df_low = pd.DataFrame({
        "score": [0.1, 0.2, 0.3, 0.4, 0.5]
    })
    df_bin_low = binarizer.binarize(df_low)
    assert list(df_bin_low["score"]) == [0, 0, 0, 0, 0]

