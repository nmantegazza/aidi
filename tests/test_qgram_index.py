"""
Unit tests for the Q-Gram Inverted Index strategy and configuration models.
"""

from __future__ import annotations

import json
import pandas as pd
import pytest
from pydantic import ValidationError

from entity_resolution.models import QGramIndexConfig
from entity_resolution.indexing_strategies import (
    QGramIndexStrategy,
    StrategyResult,
)
from entity_resolution.benchmarking.config_generator import LLMIndexConfigGenerator


def test_qgram_index_config_valid():
    """Verify QGramIndexConfig validates correct parameters."""
    config = QGramIndexConfig(
        keys=["title", "brand"],
        reasoning="Test reasoning for Q-gram config.",
    )
    assert config.keys == ["title", "brand"]
    assert config.reasoning == "Test reasoning for Q-gram config."


def test_qgram_index_config_invalid_keys():
    """Verify QGramIndexConfig rejects empty or blank keys."""
    with pytest.raises(ValidationError):
        QGramIndexConfig(keys=[], reasoning="Test")

    with pytest.raises(ValidationError):
        QGramIndexConfig(keys=["   "], reasoning="Test")


def test_qgram_index_strategy_name():
    """Verify strategy name formatting."""
    strat = QGramIndexStrategy(keys=["title", "brand"], q=3)
    assert strat.name == "QGramIndex(keys=[title,brand], q=3)"

    auto_strat = QGramIndexStrategy(keys=["title", "brand"])
    assert auto_strat.name == "QGramIndex(keys=[title,brand], q=auto)"

    # Run execution to verify name updates
    df_a = pd.DataFrame({"id": ["a1"], "title": ["abc"], "brand": ["xyz"]}).set_index("id")
    df_b = pd.DataFrame({"id": ["b1"], "title": ["abc"], "brand": ["xyz"]}).set_index("id")
    auto_strat.execute(df_a, df_b)
    assert auto_strat.name == "QGramIndex(keys=[title,brand], q=3(auto))"

    custom = QGramIndexStrategy(keys="title", name="CustomQGram")
    assert custom.name == "CustomQGram"


def test_qgram_compute_q_logic():
    """Verify dynamic q calculation based on dataset scale."""
    strat = QGramIndexStrategy(keys=["title"])
    assert strat._compute_q(100, 100) == 3       # 10k < 100k
    assert strat._compute_q(1000, 1000) == 4     # 1M < 10M
    assert strat._compute_q(10000, 2000) == 5    # 20M >= 10M

    # Explicit q overrides computation
    explicit_strat = QGramIndexStrategy(keys=["title"], q=2)
    assert explicit_strat._compute_q(10000, 2000) == 2


def test_qgram_token_frequency_pruning():
    """Verify high-frequency stop-grams are pruned."""
    # Construct 100 rows where 90 rows share token "common_gram" but only 2 share "unique_gram"
    names_a = ["common_gram unique1"] + ["common_gram noise"] * 49
    names_b = ["common_gram unique1"] + ["common_gram noise"] * 49
    df_a = pd.DataFrame({"id": [f"a{i}" for i in range(50)], "name": names_a}).set_index("id")
    df_b = pd.DataFrame({"id": [f"b{i}" for i in range(50)], "name": names_b}).set_index("id")

    # With max_token_freq=0.05, "common_gram" (>5% frequency) should be pruned
    strat = QGramIndexStrategy(keys=["name"], q=10, max_token_freq=0.05)
    res = strat.execute(df_a, df_b)

    # Only a0 and b0 should link via "unique1" (10-gram: " unique1"), not all 50x50 pairs via "common_gram"
    assert ("a0", "b0") in res.candidate_pairs
    assert len(res.candidate_pairs) == 1


def test_qgram_extract_qgrams_helper():
    """Verify character Q-gram extraction logic."""
    assert QGramIndexStrategy._extract_qgrams("hello", 3) == ["hel", "ell", "llo"]
    assert QGramIndexStrategy._extract_qgrams("hi", 3) == ["hi"]
    assert QGramIndexStrategy._extract_qgrams("", 3) == []


def test_qgram_index_strategy_indexing_match():
    """Verify QGramIndexStrategy identifies candidates with overlapping Q-grams."""
    df_a = pd.DataFrame(
        {"id": ["a1", "a2"], "name": ["iPhone 13 Pro", "Samsung Galaxy S21"]}
    ).set_index("id")
    df_b = pd.DataFrame(
        {"id": ["b1", "b2"], "name": ["Apple iPhone 13", "Google Pixel 6"]}
    ).set_index("id")

    strat = QGramIndexStrategy(keys=["name"], q=3)
    res = strat.execute(df_a, df_b)

    assert isinstance(res, StrategyResult)
    # "iPhone 13 Pro" and "Apple iPhone 13" share Q-grams "iPh", "Pho", "hon", "one", "13", etc.
    assert ("a1", "b1") in res.candidate_pairs
    # "Samsung Galaxy S21" and "Google Pixel 6" share no 3-grams
    assert ("a2", "b2") not in res.candidate_pairs


def test_qgram_index_strategy_deduplication():
    """Verify QGramIndexStrategy drops duplicate candidate pairs."""
    df_a = pd.DataFrame(
        {"id": ["a1"], "title": ["super long overlapping sentence"]}
    ).set_index("id")
    df_b = pd.DataFrame(
        {"id": ["b1"], "title": ["super long overlapping sentence"]}
    ).set_index("id")

    strat = QGramIndexStrategy(keys=["title"], q=3)
    res = strat.execute(df_a, df_b)

    # Even though they share many 3-grams, only 1 candidate pair (a1, b1) should be returned
    assert len(res.candidate_pairs) == 1
    assert ("a1", "b1") in res.candidate_pairs


def test_qgram_index_strategy_missing_keys_or_empty():
    """Verify strategy returns empty MultiIndex when keys are missing or DataFrames are empty."""
    df_a = pd.DataFrame({"id": ["a1"], "title": ["test"]}).set_index("id")
    df_b = pd.DataFrame({"id": ["b1"], "other": ["test"]}).set_index("id")

    strat = QGramIndexStrategy(keys=["title"], q=3)
    res = strat.execute(df_a, df_b)
    assert len(res.candidate_pairs) == 0

    df_empty = pd.DataFrame(columns=["title"])
    res_empty = strat.execute(df_empty, df_a)
    assert len(res_empty.candidate_pairs) == 0


def test_qgram_index_strategy_from_llm_config():
    """Verify instantiation via from_llm_config factory method."""
    config = QGramIndexConfig(
        keys=["title", "brand"],
        reasoning="Testing factory method",
    )
    strat = QGramIndexStrategy.from_llm_config(config)
    assert isinstance(strat, QGramIndexStrategy)
    assert strat.keys == ["title", "brand"]
    assert strat.user_q is None


@pytest.mark.asyncio
async def test_llm_index_config_generator_qgram_cache(tmp_path):
    """Verify LLMIndexConfigGenerator handles QGramIndexStrategy from cache."""
    cache_file = tmp_path / "cache.json"
    cache_data = {
        "dataset1::QGramIndexStrategy::google-cloud:gemini-3.8-flash": {
            "dataset_name": "dataset1",
            "strategy_name": "QGramIndexStrategy",
            "model_name": "google-cloud:gemini-3.8-flash",
            "config_data": {
                "keys": ["title"],
                "reasoning": "dummy qgram reasoning",
            },
            "llm_metrics": None,
        }
    }
    with open(cache_file, "w") as f:
        json.dump(cache_data, f)

    config_gen = LLMIndexConfigGenerator(cache_path=cache_file)
    strategy_instance, meta = await config_gen.get_configuration(
        dataset_name="dataset1",
        profile_a=None,
        profile_b=None,
        table_resource=None,
        strategy_cls=QGramIndexStrategy,
        force_llm=False,
    )

    assert isinstance(strategy_instance, QGramIndexStrategy)
    assert strategy_instance.keys == ["title"]
    assert strategy_instance.user_q is None
    assert meta is None

