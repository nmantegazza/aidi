"""Unit tests for DynamicWeightedMatchingStrategy."""

import logging

import pandas as pd
import pytest

from entity_resolution.benchmarking.matching_runner import (
    STRATEGIES,
    _matching_strategy_canonical_slug,
    _matching_strategy_display_name,
    _resolve_matching_strategy_class,
)
from entity_resolution.matching_strategies import (
    DynamicWeightedMatchingStrategy,
    WeightedScoreMatchingConfig,
)
from entity_resolution.models import (
    ClassificationMode,
    ColumnMatchConfig,
    SimilarityAlgorithm,
)


def _sample_dfs() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Helper to create sample DataFrames for matching."""
    df_a = pd.DataFrame(
        {
            "name": [
                "Alice Smith",
                "Bob Jones",
                "Charlie Brown",
                "David Wilson",
                "Eva Green",
            ],
            "city": ["New York", "Los Angeles", "Chicago", "Houston", "Miami"],
        }
    )
    df_b = pd.DataFrame(
        {
            "name": [
                "Alice Smith",
                "Bobby Jones",
                "Charlie X",
                "Xavier Drake",
                "Zack Taylor",
            ],
            "city": [
                "New York",
                "Los Angeles",
                "Chicago",
                "Seattle",
                "Boston",
            ],
        }
    )
    return df_a, df_b


def _sample_config() -> WeightedScoreMatchingConfig:
    """Helper to create sample WeightedScoreMatchingConfig."""
    return WeightedScoreMatchingConfig(
        reasoning="Test 4-step reasoning for sample matching configuration.",
        matching_columns={
            "name": ColumnMatchConfig(
                algorithm=SimilarityAlgorithm.JAROWINKLER, weight=0.6
            ),
            "city": ColumnMatchConfig(
                algorithm=SimilarityAlgorithm.EXACT, weight=0.4
            ),
        },
    )


def test_dynamic_weighted_matching_strategy_initialization():
    """Tests DynamicWeightedMatchingStrategy instantiation and factory."""
    cfg = _sample_config()
    strategy = DynamicWeightedMatchingStrategy(cfg)
    assert strategy.config == cfg
    assert strategy.name == "DynamicWeightedMatchingStrategy"

    factory_inst = DynamicWeightedMatchingStrategy.from_llm_config(cfg)
    assert isinstance(factory_inst, DynamicWeightedMatchingStrategy)
    assert factory_inst.config == cfg

    dict_cfg = cfg.model_dump()
    from_dict_inst = DynamicWeightedMatchingStrategy.from_llm_config(dict_cfg)
    assert isinstance(from_dict_inst, DynamicWeightedMatchingStrategy)


def test_dynamic_weighted_matching_strategy_empty_pairs():
    """Tests DynamicWeightedMatchingStrategy with empty candidate pairs."""
    df_a, df_b = _sample_dfs()
    candidate_pairs = pd.MultiIndex.from_tuples([], names=["a", "b"])
    cfg = _sample_config()
    strategy = DynamicWeightedMatchingStrategy(cfg)
    result = strategy.execute(df_a, df_b, candidate_pairs)

    assert len(result.classified_pairs) == 0
    assert result.features_df is None


def test_dynamic_weighted_matching_strategy_binary_mode():
    """Tests 1D K-Means (k=2) binary clustering with dynamic skew threshold."""
    df_a, df_b = _sample_dfs()
    # 2 pairs: (0, 0) exact match (score 1.0), (3, 3) mismatch (score 0.0)
    candidate_pairs = pd.MultiIndex.from_tuples(
        [(0, 0), (3, 3)], names=["a", "b"]
    )
    cfg = _sample_config()
    strategy = DynamicWeightedMatchingStrategy(cfg)
    result = strategy.execute(
        df_a,
        df_b,
        candidate_pairs,
        classification_mode=ClassificationMode.BINARY,
    )

    assert result.features_df is not None
    assert len(result.features_df) == 2
    assert (0, 0) in result.classified_pairs
    assert (3, 3) not in result.classified_pairs
    assert result.features_df.loc[(0, 0), "prediction"] == "match"
    assert result.features_df.loc[(3, 3), "prediction"] == "non_match"
    assert "uncertain" not in result.features_df["prediction"].values
    assert strategy.last_thresholds["mode"] == "dynamic_skew"
    assert "threshold" in strategy.last_thresholds
    assert len(strategy.last_thresholds["centroids"]) == 2


def test_dynamic_weighted_matching_strategy_binary_dispersion_boost(caplog):
    """Tests binary mode dispersion tail boost when high centroid < 0.60."""
    df_a = pd.DataFrame(
        {
            "name": ["Alpha Noise One", "Beta Noise Two"],
            "city": ["City A", "City B"],
        }
    )
    df_b = pd.DataFrame(
        {
            "name": ["Gamma Noise Three", "Delta Noise Four"],
            "city": ["City C", "City D"],
        }
    )
    candidate_pairs = pd.MultiIndex.from_tuples(
        [(0, 0), (1, 1)], names=["a", "b"]
    )
    cfg = _sample_config()
    strategy = DynamicWeightedMatchingStrategy(cfg)

    with caplog.at_level(logging.WARNING):
        result = strategy.execute(
            df_a,
            df_b,
            candidate_pairs,
            classification_mode=ClassificationMode.BINARY,
        )

    assert strategy.last_thresholds["mode"] == "dispersion_boost"
    assert "threshold" in strategy.last_thresholds
    assert len(strategy.last_thresholds["centroids"]) == 2
    assert "uncertain" not in result.features_df["prediction"].values


def test_dynamic_weighted_matching_strategy_insufficient_samples():
    """Tests candidate count guards in binary (<2) and ternary (<3) modes."""
    df_a, df_b = _sample_dfs()
    single_pair = pd.MultiIndex.from_tuples([(0, 0)], names=["a", "b"])
    two_pairs = pd.MultiIndex.from_tuples([(0, 0), (1, 1)], names=["a", "b"])
    cfg = _sample_config()
    strategy = DynamicWeightedMatchingStrategy(cfg)

    with pytest.raises(
        ValueError,
        match="Dynamic weighted matching in binary mode requires at least 2 candidate pairs",
    ):
        strategy.execute(
            df_a,
            df_b,
            single_pair,
            classification_mode=ClassificationMode.BINARY,
        )

    with pytest.raises(
        ValueError,
        match="Dynamic weighted matching in ternary mode requires at least 3 candidate pairs",
    ):
        strategy.execute(
            df_a,
            df_b,
            two_pairs,
            classification_mode=ClassificationMode.TERNARY,
        )


def test_dynamic_weighted_matching_strategy_dynamic_kmeans():
    """Tests dynamic 1D K-Means thresholding with >= 3 candidate pairs."""
    df_a, df_b = _sample_dfs()
    # 5 pairs spanning high, moderate, and low similarity:
    # (0, 0): score 1.0 (match)
    # (1, 1): "Bob Jones" vs "Bobby Jones" + city match (moderate/high)
    # (2, 2): "Charlie Brown" vs "Charlie X" + city match (moderate)
    # (3, 3): "David Wilson" vs "Xavier Drake" (low)
    # (4, 4): "Eva Green" vs "Zack Taylor" (low)
    candidate_pairs = pd.MultiIndex.from_tuples(
        [(0, 0), (1, 1), (2, 2), (3, 3), (4, 4)], names=["a", "b"]
    )
    cfg = _sample_config()
    strategy = DynamicWeightedMatchingStrategy(cfg)
    result = strategy.execute(df_a, df_b, candidate_pairs)

    assert result.features_df is not None
    assert "prediction" in result.features_df.columns
    predictions = set(result.features_df["prediction"].unique())
    assert predictions.issubset({"match", "non_match", "uncertain"})

    # Exact match (0, 0) must be classified as match
    assert (0, 0) in result.classified_pairs
    assert result.features_df.loc[(0, 0), "prediction"] == "match"

    # Distant pairs (3, 3) and (4, 4) must be non_match
    assert (3, 3) not in result.classified_pairs
    assert result.features_df.loc[(3, 3), "prediction"] == "non_match"
    assert (4, 4) not in result.classified_pairs
    assert result.features_df.loc[(4, 4), "prediction"] == "non_match"

    assert strategy.last_thresholds["mode"] == "dynamic_skew"
    assert "lower_threshold" in strategy.last_thresholds
    assert "upper_threshold" in strategy.last_thresholds
    assert "alpha" in strategy.last_thresholds
    assert strategy.last_thresholds["alpha"] == 0.60
    assert "std_high" in strategy.last_thresholds
    assert "cluster_sizes" in strategy.last_thresholds
    assert len(strategy.last_thresholds["centroids"]) == 3
    assert len(strategy.last_thresholds["cluster_sizes"]) == 3

    c_low, c_mid, c_high = strategy.last_thresholds["centroids"]
    expected_upper = c_mid + 0.60 * (c_high - c_mid)
    expected_lower = (c_low + c_mid) / 2.0
    assert strategy.last_thresholds["upper_threshold"] == pytest.approx(
        expected_upper, abs=1e-3
    )
    assert strategy.last_thresholds["lower_threshold"] == pytest.approx(
        expected_lower, abs=1e-3
    )
    assert (
        result.features_df.attrs["dynamic_thresholds"]
        == strategy.last_thresholds
    )


def test_dynamic_weighted_matching_strategy_safety_floor(caplog):
    """Tests dispersion-aware tail boost when highest centroid < 0.60."""
    df_a = pd.DataFrame(
        {
            "name": [
                "Sony Wireless Headphones Black",
                "Apple iPhone 12 Case Silicone",
                "Samsung Galaxy S20 Screen Protector",
                "Nike Air Zoom Pegasus 38 Shoes",
                "Random Alpha String One",
            ],
            "city": [
                "New York City",
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
                "Sony Headphones Audio Cable Adapter",
                "Apple Leather Case for Phone",
                "Samsung Protective Film Clear",
                "Adidas Running Shoes Mens",
                "Completely Different Beta Two",
            ],
            "city": [
                "New York Metro",
                "San Francisco",
                "Seattle",
                "Dallas",
                "Boston",
            ],
        }
    )
    candidate_pairs = pd.MultiIndex.from_tuples(
        [(0, 0), (1, 1), (2, 2), (3, 3), (4, 4)], names=["a", "b"]
    )
    cfg = _sample_config()
    strategy = DynamicWeightedMatchingStrategy(cfg)

    with caplog.at_level(logging.WARNING):
        result = strategy.execute(df_a, df_b, candidate_pairs)

    assert any(
        "Dynamic weighted match centroid" in rec.message
        and "below safety floor" in rec.message
        for rec in caplog.records
    )
    assert strategy.last_thresholds["mode"] == "dispersion_boost"
    assert "beta" in strategy.last_thresholds
    assert strategy.last_thresholds["beta"] == 2.50
    assert "std_high" in strategy.last_thresholds
    assert "cluster_sizes" in strategy.last_thresholds

    _c_low, _c_mid, c_high = strategy.last_thresholds["centroids"]
    std_high = strategy.last_thresholds["std_high"]
    assert c_high < 0.60
    expected_upper = min(0.95, c_high + 2.50 * std_high)
    expected_lower = c_high
    assert strategy.last_thresholds["upper_threshold"] == pytest.approx(
        expected_upper, abs=1e-3
    )
    assert strategy.last_thresholds["lower_threshold"] == pytest.approx(
        expected_lower, abs=1e-3
    )
    assert (
        result.features_df.attrs["dynamic_thresholds"]
        == strategy.last_thresholds
    )


def test_dynamic_weighted_prefilter_integration():
    """Tests gentle pre-filtering of candidate pairs with score < 0.20."""
    df_a = pd.DataFrame(
        {
            "name": [
                "Alice Smith",
                "Bob Jones",
                "Charlie Brown",
                "AAAA",
                "BBBB",
            ],
            "city": [
                "New York",
                "Los Angeles",
                "Chicago",
                "XXXX",
                "YYYY",
            ],
        }
    )
    df_b = pd.DataFrame(
        {
            "name": [
                "Alice Smith",
                "Bobby Jones",
                "Charlie B.",
                "ZZZZ",
                "WWWW",
            ],
            "city": [
                "New York",
                "Los Angeles",
                "Chicago",
                "1111",
                "2222",
            ],
        }
    )
    # 3 moderate/high pairs (score >= 0.90) and 2 complete mismatch pairs (score 0.0 < 0.20)
    candidate_pairs = pd.MultiIndex.from_tuples(
        [(0, 0), (1, 1), (2, 2), (3, 3), (4, 4)], names=["a", "b"]
    )
    cfg = _sample_config()
    strategy = DynamicWeightedMatchingStrategy(cfg)
    result = strategy.execute(df_a, df_b, candidate_pairs)

    assert result.features_df is not None
    assert len(result.features_df) == 5
    # The 2 pairs with score < 0.20 were filtered out before K-Means clustering.
    # Therefore, the sum of cluster sizes equals 3 (the informative pairs only).
    cluster_sizes = strategy.last_thresholds["cluster_sizes"]
    assert sum(cluster_sizes) == 3
    # All 5 rows have predictions assigned
    assert set(result.features_df["prediction"].unique()).issubset(
        {"match", "non_match", "uncertain"}
    )
    assert result.features_df.loc[(3, 3), "prediction"] == "non_match"
    assert result.features_df.loc[(4, 4), "prediction"] == "non_match"


def test_dynamic_weighted_runner_resolution():
    """Tests runner resolution, canonical slug, and display name."""
    assert (
        _resolve_matching_strategy_class("dynamic_weighted")
        is DynamicWeightedMatchingStrategy
    )
    assert (
        _resolve_matching_strategy_class("dynamic_weighted_strategy")
        is DynamicWeightedMatchingStrategy
    )
    assert (
        _resolve_matching_strategy_class("DynamicWeightedMatchingStrategy")
        is DynamicWeightedMatchingStrategy
    )
    assert STRATEGIES["dynamic_weighted"] is DynamicWeightedMatchingStrategy
    assert (
        _matching_strategy_canonical_slug(DynamicWeightedMatchingStrategy)
        == "dynamic_weighted"
    )
    assert (
        _matching_strategy_display_name(DynamicWeightedMatchingStrategy)
        == "Dynamic Weighted"
    )


def test_dynamic_thresholds_in_matching_report():
    """Verifies that dynamic thresholds are rendered in benchmark report.md."""
    from entity_resolution.benchmarking.matching_models import (
        MatchingDatasetStrategyMetrics,
    )
    from entity_resolution.benchmarking.matching_runner import (
        _build_matching_dataset_markdown_report,
    )

    dm = MatchingDatasetStrategyMetrics(
        dataset_name="test_ds",
        strategy_name="Dynamic Weighted",
        model_name="mock_model",
    )
    traces = [
        {
            "iteration": 1,
            "dynamic_thresholds": {
                "mode": "dynamic",
                "lower_threshold": 0.4500,
                "upper_threshold": 0.7800,
                "centroids": [0.12, 0.50, 0.90],
            },
        }
    ]
    report = _build_matching_dataset_markdown_report(dm, traces=traces)
    assert "## Dynamic Thresholds" in report
    assert "0.4500" in report
    assert "0.7800" in report
    assert "dynamic" in report
    assert "[0.1200, 0.5000, 0.9000]" in report

