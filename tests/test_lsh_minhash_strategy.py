"""
Unit tests for MinHash LSH Indexing Strategy and configuration models.
"""

from __future__ import annotations

import pandas as pd
import pytest
from pydantic import ValidationError

from entity_resolution.models import MinHashLSHIndexConfig
from entity_resolution.indexing_strategies import (
    MinHashLSHStrategy,
    MinHashLSHIndexAlgorithm,
    StrategyResult,
)


def test_minhash_lsh_config_valid():
    """Verify MinHashLSHIndexConfig instantiates with valid parameters."""
    config = MinHashLSHIndexConfig(
        blocking_keys=["title", "brand"],
        ngram_size=3,
        threshold=0.5,
        reasoning="Test reasoning",
    )
    assert config.blocking_keys == ["title", "brand"]
    assert config.ngram_size == 3
    assert config.threshold == 0.5
    assert config.reasoning == "Test reasoning"


def test_minhash_lsh_config_validators():
    """Verify field validators on MinHashLSHIndexConfig."""
    # Invalid blocking_keys (empty)
    with pytest.raises(ValidationError):
        MinHashLSHIndexConfig(
            blocking_keys=[],
            ngram_size=3,
            threshold=0.5,
            reasoning="test",
        )

    # Invalid blocking_keys (whitespace only)
    with pytest.raises(ValidationError):
        MinHashLSHIndexConfig(
            blocking_keys=["   "],
            ngram_size=3,
            threshold=0.5,
            reasoning="test",
        )

    # Invalid ngram_size (<= 0)
    with pytest.raises(ValidationError):
        MinHashLSHIndexConfig(
            blocking_keys=["title"],
            ngram_size=0,
            threshold=0.5,
            reasoning="test",
        )

    # Invalid threshold (< 0 or > 1)
    with pytest.raises(ValidationError):
        MinHashLSHIndexConfig(
            blocking_keys=["title"],
            ngram_size=3,
            threshold=-0.1,
            reasoning="test",
        )

    with pytest.raises(ValidationError):
        MinHashLSHIndexConfig(
            blocking_keys=["title"],
            ngram_size=3,
            threshold=1.5,
            reasoning="test",
        )


def test_minhash_lsh_strategy_execution():
    """Verify MinHashLSHStrategy produces candidate pairs on similar data."""
    df_a = pd.DataFrame(
        {
            "id": ["a1", "a2", "a3"],
            "title": [
                "Apple iPhone 13 Pro 128GB",
                "Samsung Galaxy S21 Ultra",
                "Sony WH-1000XM4 Wireless Headphones",
            ],
        }
    ).set_index("id")

    df_b = pd.DataFrame(
        {
            "id": ["b1", "b2", "b3"],
            "title": [
                "Apple iPhone 13 Pro 128GB Graphite",  # High similarity to a1
                "Samsung Glaxy S21 Ultra 5G",  # Typo in Galaxy, high similarity to a2
                "Bose QuietComfort 45",  # Unrelated
            ],
        }
    ).set_index("id")

    strategy = MinHashLSHStrategy(
        keys=["title"], ngram_size=1, threshold=0.3, num_perm=128
    )
    result = strategy.execute(df_a, df_b)

    assert isinstance(result, StrategyResult)
    pairs = result.candidate_pairs
    assert ("a1", "b1") in pairs
    assert ("a2", "b2") in pairs
    assert ("a3", "b3") not in pairs
    assert result.indexing_time_sec >= 0.0
    assert result.peak_memory_mb >= 0.0


def test_minhash_lsh_strategy_from_llm_config():
    """Verify factory method from_llm_config creates strategy instance correctly."""
    config = MinHashLSHIndexConfig(
        blocking_keys=["name", "address"],
        ngram_size=4,
        threshold=0.6,
        reasoning="Testing factory method",
    )
    strategy = MinHashLSHStrategy.from_llm_config(config)

    assert isinstance(strategy, MinHashLSHStrategy)
    assert strategy.keys == ["name", "address"]
    assert strategy.ngram_size == 4
    assert strategy.threshold == 0.6
    assert strategy.name == "MinHashLSH(keys=[name,address], ngram=4, t=0.6)"


def test_minhash_lsh_edge_cases():
    """Verify handling of empty DataFrames, missing columns, and null values."""
    df_a = pd.DataFrame(
        {"id": ["a1", "a2"], "col_x": [None, "MacBook Pro 16"]}
    ).set_index("id")
    df_b = pd.DataFrame(
        {"id": ["b1", "b2"], "col_x": ["MacBook Pro 16 M1", None]}
    ).set_index("id")

    # Missing column in keys
    strategy = MinHashLSHStrategy(keys=["non_existent_col"], threshold=0.5)
    result = strategy.execute(df_a, df_b)
    assert len(result.candidate_pairs) == 0

    # Short string and null handling with word unigrams
    strategy_null = MinHashLSHStrategy(keys=["col_x"], ngram_size=1, threshold=0.3)
    result_null = strategy_null.execute(df_a, df_b)
    assert ("a2", "b1") in result_null.candidate_pairs

    # Empty input DataFrames
    empty_df = pd.DataFrame(columns=["col_x"]).set_index(
        pd.Index([], name="id")
    )
    result_empty = strategy_null.execute(empty_df, df_b)
    assert len(result_empty.candidate_pairs) == 0


def test_minhash_lsh_algorithm_direct():
    """Verify recordlinkage indexer algorithm directly."""
    df_a = pd.DataFrame(
        {"id": ["a1"], "title": ["Wireless Bluetooth Headphones"]}
    ).set_index("id")
    df_b = pd.DataFrame(
        {"id": ["b1"], "title": ["Wireless Bluetooth Headphone"]}
    ).set_index("id")

    algorithm = MinHashLSHIndexAlgorithm(
        keys=["title"], ngram_size=1, threshold=0.5, num_perm=128
    )
    pairs = algorithm.index(df_a, df_b)
    assert ("a1", "b1") in pairs

