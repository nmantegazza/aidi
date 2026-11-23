"""Integration tests verifying end-to-end replay cache execution for GUI workflows."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pydantic import BaseModel

from shared.agents import LLMAgent
from shared.llm_cache import CacheMissError, LLMCache


class DummyAlignmentResult(BaseModel):
    mapping_name: str
    confidence: float


class DummyERResult(BaseModel):
    strategy: str
    threshold: float


class DummyFusionResult(BaseModel):
    fusion_rule: str


def test_gui_simulated_pipeline_record_and_replay(tmp_path: Path, monkeypatch):
    """Verify that multiple simulated GUI pipeline phases can record then replay offline.

    Simulates:
    1. Schema Alignment phase
    2. Entity Resolution Config phase
    3. Data Fusion Policy phase
    """
    cache_dir = tmp_path / "gui_cache"

    # --- Step 1: Record Mode ---
    # Setup agents in record mode
    align_agent_rec = LLMAgent(
        response_model=DummyAlignmentResult,
        system_prompt="Schema Alignment Agent System Prompt",
        provider="google-cloud",
        model_name="gemini-3.8-flash",
        name="alignment_agent",
    )
    align_agent_rec.cache = LLMCache(mode="record", cache_dir=cache_dir)

    er_agent_rec = LLMAgent(
        response_model=DummyERResult,
        system_prompt="ER Agent System Prompt",
        provider="google-cloud",
        model_name="gemini-3.8-flash",
        name="er_agent",
    )
    er_agent_rec.cache = LLMCache(mode="record", cache_dir=cache_dir)

    fusion_agent_rec = LLMAgent(
        response_model=DummyFusionResult,
        system_prompt="Fusion Agent System Prompt",
        provider="google-cloud",
        model_name="gemini-3.8-flash",
        name="fusion_agent",
    )
    fusion_agent_rec.cache = LLMCache(mode="record", cache_dir=cache_dir)

    # Mock live provider calls for recording pass
    align_mock = MagicMock()
    align_mock.output = DummyAlignmentResult(mapping_name="source_a_to_target", confidence=0.98)
    align_mock.usage.input_tokens = 120
    align_mock.usage.output_tokens = 40
    align_mock.usage.total_tokens = 160
    align_mock.usage.cache_read_tokens = 0
    align_mock.usage.cost = 0.0005
    align_mock.usage.details = {}
    monkeypatch.setattr(align_agent_rec.agent, "run_sync", MagicMock(return_value=align_mock))

    er_mock = MagicMock()
    er_mock.output = DummyERResult(strategy="qgram_levenshtein", threshold=0.85)
    er_mock.usage.input_tokens = 250
    er_mock.usage.output_tokens = 60
    er_mock.usage.total_tokens = 310
    er_mock.usage.cache_read_tokens = 0
    er_mock.usage.cost = 0.001
    er_mock.usage.details = {}
    monkeypatch.setattr(er_agent_rec.agent, "run_sync", MagicMock(return_value=er_mock))

    fusion_mock = MagicMock()
    fusion_mock.output = DummyFusionResult(fusion_rule="prefer_trusted_source")
    fusion_mock.usage.input_tokens = 180
    fusion_mock.usage.output_tokens = 50
    fusion_mock.usage.total_tokens = 230
    fusion_mock.usage.cache_read_tokens = 0
    fusion_mock.usage.cost = 0.0008
    fusion_mock.usage.details = {}
    monkeypatch.setattr(fusion_agent_rec.agent, "run_sync", MagicMock(return_value=fusion_mock))

    # Execute simulated recording pipeline
    res_align_1, _ = align_agent_rec.run_sync("Align tables A and B")
    res_er_1, _ = er_agent_rec.run_sync("Generate ER config for tables A and B")
    res_fusion_1, _ = fusion_agent_rec.run_sync("Formulate fusion policy")

    assert res_align_1.mapping_name == "source_a_to_target"
    assert res_er_1.strategy == "qgram_levenshtein"
    assert res_fusion_1.fusion_rule == "prefer_trusted_source"

    # Exactly 3 discrete cache entries should exist
    cache_files = list(cache_dir.glob("*.json"))
    assert len(cache_files) == 3

    # --- Step 2: Replay Mode ---
    # Setup agents in strict replay mode pointing to same cache_dir
    align_agent_rep = LLMAgent(
        response_model=DummyAlignmentResult,
        system_prompt="Schema Alignment Agent System Prompt",
        provider="google-cloud",
        model_name="gemini-3.8-flash",
        name="alignment_agent",
    )
    align_agent_rep.cache = LLMCache(mode="replay", cache_dir=cache_dir)

    er_agent_rep = LLMAgent(
        response_model=DummyERResult,
        system_prompt="ER Agent System Prompt",
        provider="google-cloud",
        model_name="gemini-3.8-flash",
        name="er_agent",
    )
    er_agent_rep.cache = LLMCache(mode="replay", cache_dir=cache_dir)

    fusion_agent_rep = LLMAgent(
        response_model=DummyFusionResult,
        system_prompt="Fusion Agent System Prompt",
        provider="google-cloud",
        model_name="gemini-3.8-flash",
        name="fusion_agent",
    )
    fusion_agent_rep.cache = LLMCache(mode="replay", cache_dir=cache_dir)

    # Disallow ANY underlying live calls in replay mode
    def fail_call(*args, **kwargs):
        raise AssertionError("Network/live agent was invoked during replay mode!")

    monkeypatch.setattr(align_agent_rep.agent, "run_sync", fail_call)
    monkeypatch.setattr(er_agent_rep.agent, "run_sync", fail_call)
    monkeypatch.setattr(fusion_agent_rep.agent, "run_sync", fail_call)

    # Execute simulated replay pipeline
    res_align_2, meta_align_2 = align_agent_rep.run_sync("Align tables A and B")
    res_er_2, meta_er_2 = er_agent_rep.run_sync("Generate ER config for tables A and B")
    res_fusion_2, meta_fusion_2 = fusion_agent_rep.run_sync("Formulate fusion policy")

    assert res_align_2 == res_align_1
    assert res_er_2 == res_er_1
    assert res_fusion_2 == res_fusion_1

    # Verify zero latency and cached tokens recorded
    assert meta_align_2.cached_tokens == 160
    assert meta_align_2.execution_time_seconds == 0.0
    assert meta_er_2.cached_tokens == 310
    assert meta_fusion_2.cached_tokens == 230

    # Unseen step raises CacheMissError in replay mode
    with pytest.raises(CacheMissError):
        align_agent_rep.run_sync("Novel unseen prompt")
