"""Tests verifying LLMAgent integration with LLMCache."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pydantic import BaseModel

from shared.agents import LLMAgent
from shared.llm_cache import CacheMissError, LLMCache


class DummyResponse(BaseModel):
    message: str


def test_llmagent_cache_off(tmp_path: Path, monkeypatch):
    """Verify LLMAgent does not use cache when mode is off."""
    agent = LLMAgent(
        response_model=DummyResponse,
        system_prompt="Test sys",
        provider="google-cloud",
        model_name="gemini-3.8-flash",
    )
    agent.cache = LLMCache(mode="off", cache_dir=tmp_path)

    # Mock the underlying pydantic_ai Agent.run_sync
    mock_run_result = MagicMock()
    mock_run_result.output = DummyResponse(message="live_response")
    mock_run_result.usage.input_tokens = 10
    mock_run_result.usage.output_tokens = 5
    mock_run_result.usage.total_tokens = 15
    mock_run_result.usage.cache_read_tokens = 0
    mock_run_result.usage.cost = 0.001
    mock_run_result.usage.details = {}
    mock_run_sync = MagicMock(return_value=mock_run_result)
    monkeypatch.setattr(agent.agent, "run_sync", mock_run_sync)

    out, _meta = agent.run_sync("Hello")
    assert out.message == "live_response"
    assert mock_run_sync.call_count == 1
    # Ensure no files written in cache
    assert list(tmp_path.glob("*.json")) == []


def test_llmagent_record_and_replay_sync(tmp_path: Path, monkeypatch):
    """Verify LLMAgent record saves to cache and replay serves without network."""
    # 1. Record mode
    agent_record = LLMAgent(
        response_model=DummyResponse,
        system_prompt="Test sys",
        provider="google-cloud",
        model_name="gemini-3.8-flash",
    )
    agent_record.cache = LLMCache(mode="record", cache_dir=tmp_path)

    mock_run_result = MagicMock()
    mock_run_result.output = DummyResponse(message="recorded_response")
    mock_run_result.usage.input_tokens = 20
    mock_run_result.usage.output_tokens = 10
    mock_run_result.usage.total_tokens = 30
    mock_run_result.usage.cache_read_tokens = 0
    mock_run_result.usage.cost = 0.002
    mock_run_result.usage.details = {}
    mock_run_sync = MagicMock(return_value=mock_run_result)
    monkeypatch.setattr(agent_record.agent, "run_sync", mock_run_sync)

    out, _meta = agent_record.run_sync("Record prompt")
    assert out.message == "recorded_response"
    assert mock_run_sync.call_count == 1
    cache_files = list(tmp_path.glob("*.json"))
    assert len(cache_files) == 1

    # 2. Replay mode with matching prompt
    agent_replay = LLMAgent(
        response_model=DummyResponse,
        system_prompt="Test sys",
        provider="google-cloud",
        model_name="gemini-3.8-flash",
    )
    agent_replay.cache = LLMCache(mode="replay", cache_dir=tmp_path)

    # Replace run_sync on agent_replay to verify it is NEVER called
    replay_run_mock = MagicMock(side_effect=RuntimeError("Should not call live agent!"))
    monkeypatch.setattr(agent_replay.agent, "run_sync", replay_run_mock)

    out_replay, meta_replay = agent_replay.run_sync("Record prompt")
    assert out_replay.message == "recorded_response"
    assert replay_run_mock.call_count == 0
    assert meta_replay.total_tokens == 30
    assert meta_replay.cached_tokens == 30

    # 3. Replay mode with missing prompt raises CacheMissError
    with pytest.raises(CacheMissError):
        agent_replay.run_sync("Uncached novel prompt")


@pytest.mark.asyncio
async def test_llmagent_record_and_replay_async(tmp_path: Path, monkeypatch):
    """Verify LLMAgent async run saves to cache and replays without network."""
    # 1. Record mode
    agent_record = LLMAgent(
        response_model=DummyResponse,
        system_prompt="Async sys",
        provider="openai",
        model_name="gpt-5.6-sol",
    )
    agent_record.cache = LLMCache(mode="record", cache_dir=tmp_path)

    mock_run_result = MagicMock()
    mock_run_result.output = DummyResponse(message="async_recorded")
    mock_run_result.usage.input_tokens = 15
    mock_run_result.usage.output_tokens = 5
    mock_run_result.usage.total_tokens = 20
    mock_run_result.usage.cache_read_tokens = 0
    mock_run_result.usage.cost = 0.0015
    mock_run_result.usage.details = {}

    async def mock_async_run(*args, **kwargs):
        return mock_run_result

    monkeypatch.setattr(agent_record.agent, "run", mock_async_run)

    out, _meta = await agent_record.run("Async prompt")
    assert out.message == "async_recorded"
    assert len(list(tmp_path.glob("*.json"))) == 1

    # 2. Replay mode
    agent_replay = LLMAgent(
        response_model=DummyResponse,
        system_prompt="Async sys",
        provider="openai",
        model_name="gpt-5.6-sol",
    )
    agent_replay.cache = LLMCache(mode="replay", cache_dir=tmp_path)

    async def fail_async_run(*args, **kwargs):
        raise RuntimeError("Network should not be touched in replay!")

    monkeypatch.setattr(agent_replay.agent, "run", fail_async_run)

    out_replay, meta_replay = await agent_replay.run("Async prompt")
    assert out_replay.message == "async_recorded"
    assert meta_replay.cached_tokens == 20

    # 3. Miss raises CacheMissError
    with pytest.raises(CacheMissError):
        await agent_replay.run("Novel async prompt")
