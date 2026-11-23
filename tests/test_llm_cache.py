"""Unit tests for the LLM record/replay cache."""

from pathlib import Path

import pytest
from pydantic import BaseModel

from shared.agents import ExecutionMetadata
from shared.llm_cache import (
    CacheCorruptedError,
    CacheMissError,
    LLMCache,
    compute_cache_key,
)


class SampleResponse(BaseModel):
    name: str
    score: float


def test_compute_cache_key_determinism():
    """Verify compute_cache_key produces identical hashes for identical inputs."""
    schema = SampleResponse.model_json_schema()
    key1 = compute_cache_key(
        provider="google-cloud",
        model_name="gemini-3.8-flash",
        system_prompt="You are an expert.",
        user_prompt="Analyze table.",
        response_schema=schema,
        thinking="low",
    )
    key2 = compute_cache_key(
        provider="google-cloud",
        model_name="gemini-3.8-flash",
        system_prompt="You are an expert.",
        user_prompt="Analyze table.",
        response_schema=schema,
        thinking="low",
    )
    assert key1 == key2
    assert len(key1) == 64


def test_compute_cache_key_variance():
    """Verify compute_cache_key alters hash on any input variation."""
    schema = SampleResponse.model_json_schema()
    base_key = compute_cache_key(
        provider="google-cloud",
        model_name="gemini-3.8-flash",
        system_prompt="You are an expert.",
        user_prompt="Analyze table.",
        response_schema=schema,
    )

    # Prompt change
    key_prompt = compute_cache_key(
        provider="google-cloud",
        model_name="gemini-3.8-flash",
        system_prompt="You are an expert.",
        user_prompt="Analyze table 2.",
        response_schema=schema,
    )
    assert base_key != key_prompt

    # Model change
    key_model = compute_cache_key(
        provider="openai",
        model_name="gpt-5.6-sol",
        system_prompt="You are an expert.",
        user_prompt="Analyze table.",
        response_schema=schema,
    )
    assert base_key != key_model

    # Schema change
    class DifferentResponse(BaseModel):
        name: str
        extra: int

    key_schema = compute_cache_key(
        provider="google-cloud",
        model_name="gemini-3.8-flash",
        system_prompt="You are an expert.",
        user_prompt="Analyze table.",
        response_schema=DifferentResponse.model_json_schema(),
    )
    assert base_key != key_schema


def test_cache_off_mode(tmp_path: Path):
    """Verify LLMCache does nothing in off mode."""
    cache = LLMCache(mode="off", cache_dir=tmp_path)
    assert not cache.is_active
    assert cache.get("any_key", SampleResponse) is None


def test_cache_set_and_get_roundtrip(tmp_path: Path):
    """Verify roundtrip set and get works accurately."""
    cache = LLMCache(mode="auto", cache_dir=tmp_path)
    assert cache.is_active

    key = "a" * 64
    sample_output = SampleResponse(name="test_item", score=0.95)
    metadata = ExecutionMetadata(
        model_name="gemini-3.8-flash",
        provider="google-cloud",
        execution_time_seconds=2.5,
        prompt_tokens=100,
        completion_tokens=50,
        total_tokens=150,
        cost_usd=0.0001,
    )
    req_ctx = {
        "model_name": "gemini-3.8-flash",
        "provider": "google-cloud",
        "system_prompt": "Sys",
        "user_prompt": "User",
    }

    path = cache.set(key, sample_output, metadata, req_ctx)
    assert path.is_file()

    # Get cached item
    result = cache.get(key, SampleResponse)
    assert result is not None
    out, meta = result
    assert isinstance(out, SampleResponse)
    assert out.name == "test_item"
    assert out.score == 0.95
    assert meta.total_tokens == 150
    assert meta.cached_tokens == 150
    assert meta.execution_time_seconds == 0.0
    assert meta.execution_time_ms == 0.0


def test_cache_replay_mode_hit_and_miss(tmp_path: Path):
    """Verify replay mode returns hits and raises CacheMissError on miss."""
    cache_auto = LLMCache(mode="auto", cache_dir=tmp_path)
    key = "b" * 64
    sample_output = SampleResponse(name="replay_item", score=1.0)
    metadata = ExecutionMetadata(
        model_name="gemini-3.8-flash",
        provider="google-cloud",
        execution_time_seconds=1.0,
        prompt_tokens=10,
        completion_tokens=20,
        total_tokens=30,
    )
    cache_auto.set(key, sample_output, metadata, {})

    # Replay cache
    cache_replay = LLMCache(mode="replay", cache_dir=tmp_path)
    hit_res = cache_replay.get(key, SampleResponse)
    assert hit_res is not None
    out, _ = hit_res
    assert out.name == "replay_item"

    # Missing key raises CacheMissError
    with pytest.raises(CacheMissError) as exc_info:
        cache_replay.get("c" * 64, SampleResponse)
    assert "LLM Cache miss in replay mode" in str(exc_info.value)


def test_cache_corrupted_file(tmp_path: Path):
    """Verify corrupted JSON file raises CacheCorruptedError."""
    cache = LLMCache(mode="auto", cache_dir=tmp_path)
    key = "d" * 64
    corrupted_file = tmp_path / f"{key}.json"
    corrupted_file.write_text("invalid json contents", encoding="utf-8")

    with pytest.raises(CacheCorruptedError):
        cache.get(key, SampleResponse)
