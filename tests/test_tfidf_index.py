"""
Unit tests for the TF-IDF Index strategy and configuration models.
"""

from __future__ import annotations

import json
import pandas as pd
import pytest
from pydantic import ValidationError

from entity_resolution.models import TFIDFIndexConfig
from entity_resolution.indexing_strategies import (
    TFIDFIndexStrategy,
    StrategyResult,
)
from entity_resolution.benchmarking.config_generator import LLMIndexConfigGenerator


def test_tfidf_index_config_valid():
    """Verify TFIDFIndexConfig validates correct parameters."""
    config = TFIDFIndexConfig(
        keys=["title", "brand"],
        reasoning="Test reasoning for TF-IDF config.",
    )
    assert config.keys == ["title", "brand"]
    assert config.reasoning == "Test reasoning for TF-IDF config."


def test_tfidf_index_config_invalid_keys():
    """Verify TFIDFIndexConfig rejects empty or blank keys."""
    with pytest.raises(ValidationError):
        TFIDFIndexConfig(keys=[], reasoning="Test")

    with pytest.raises(ValidationError):
        TFIDFIndexConfig(keys=["   "], reasoning="Test")


def test_tfidf_index_strategy_name():
    """Verify strategy name formatting."""
    strat = TFIDFIndexStrategy(
        keys=["title", "brand"],
        analyzer="char_wb",
        ngram_range=(3, 3),
        threshold=0.5,
    )
    assert strat.name == (
        "TFIDFIndex(keys=[title,brand], analyzer=char_wb, ngram=(3, 3), t=0.5)"
    )

    custom = TFIDFIndexStrategy(keys="title", name="CustomTFIDF")
    assert custom.name == "CustomTFIDF"


def test_tfidf_index_strategy_indexing_match():
    """Verify TFIDFIndexStrategy identifies candidates exceeding similarity threshold."""
    df_a = pd.DataFrame(
        {"id": ["a1", "a2"], "name": ["iPhone 13 Pro", "Samsung Galaxy S21"]}
    ).set_index("id")
    df_b = pd.DataFrame(
        {"id": ["b1", "b2"], "name": ["Apple iPhone 13", "Google Pixel 6"]}
    ).set_index("id")

    strat = TFIDFIndexStrategy(
        keys=["name"], analyzer="char_wb", ngram_range=(3, 3), threshold=0.3
    )
    res = strat.execute(df_a, df_b)

    assert isinstance(res, StrategyResult)
    # "iPhone 13 Pro" and "Apple iPhone 13" share 3-grams ("iPh", "Pho", "hon", etc.)
    assert ("a1", "b1") in res.candidate_pairs
    # "Samsung Galaxy S21" and "Google Pixel 6" should not exceed 0.3 threshold
    assert ("a2", "b2") not in res.candidate_pairs


def test_tfidf_index_strategy_missing_keys_or_empty():
    """Verify strategy returns empty MultiIndex when keys are missing or DataFrames empty."""
    df_a = pd.DataFrame({"id": ["a1"], "title": ["test"]}).set_index("id")
    df_b = pd.DataFrame({"id": ["b1"], "other": ["test"]}).set_index("id")

    strat = TFIDFIndexStrategy(keys=["title"])
    res = strat.execute(df_a, df_b)
    assert len(res.candidate_pairs) == 0

    df_empty = pd.DataFrame(columns=["title"])
    res_empty = strat.execute(df_empty, df_a)
    assert len(res_empty.candidate_pairs) == 0


def test_tfidf_index_strategy_from_llm_config():
    """Verify instantiation via from_llm_config factory method."""
    config = TFIDFIndexConfig(
        keys=["title", "brand"],
        reasoning="Testing factory method",
    )
    strat = TFIDFIndexStrategy.from_llm_config(config)
    assert isinstance(strat, TFIDFIndexStrategy)
    assert strat.keys == ["title", "brand"]
    assert strat.analyzer == "word"
    assert strat.ngram_range == (1, 2)
    assert strat.threshold == 0.1


@pytest.mark.asyncio
async def test_llm_index_config_generator_tfidf_cache(tmp_path):
    """Verify LLMIndexConfigGenerator handles TFIDFIndexStrategy from cache."""
    cache_file = tmp_path / "cache.json"
    cache_data = {
        "dataset1::TFIDFIndexStrategy::google-cloud:gemini-3.8-flash": {
            "dataset_name": "dataset1",
            "strategy_name": "TFIDFIndexStrategy",
            "model_name": "google-cloud:gemini-3.8-flash",
            "config_data": {
                "keys": ["title"],
                "reasoning": "dummy tfidf reasoning",
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
        strategy_cls=TFIDFIndexStrategy,
        force_llm=False,
        model_name="google-cloud:gemini-3.8-flash",
    )

    assert isinstance(strategy_instance, TFIDFIndexStrategy)
    assert strategy_instance.keys == ["title"]
    assert strategy_instance.analyzer == "word"
    assert strategy_instance.threshold == 0.1
    assert meta is None
