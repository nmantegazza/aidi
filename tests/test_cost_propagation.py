"""Focused tests for cost_usd propagation (agents -> TokenPayload)."""

from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from shared.agents import ExecutionMetadata, LLMAgent
from shared.benchmarking.models import TokenPayload


class DummyResponse:
    result: str


def _make_agent() -> LLMAgent:
    from pydantic import BaseModel

    class R(BaseModel):
        result: str

    return LLMAgent(
        response_model=R,
        system_prompt="sys",
        provider="openai",
        model_name="gpt-4o",
        name="cost-agent",
    )


def _fake_result(cost) -> SimpleNamespace:
    usage = SimpleNamespace(
        input_tokens=100,
        output_tokens=50,
        total_tokens=150,
        cache_read_tokens=10,
        input_audio_tokens=0,
        output_audio_tokens=0,
        details={},
        cost=cost,
    )
    return SimpleNamespace(usage=usage)


def test_extract_metadata_converts_decimal_cost_to_float():
    agent = _make_agent()
    meta = agent._extract_metadata(_fake_result(Decimal("0.4824855")), 1.0)
    assert isinstance(meta.cost_usd, float)
    assert meta.cost_usd == float(Decimal("0.4824855"))


def test_extract_metadata_unpriced_cost_stays_none():
    agent = _make_agent()
    meta = agent._extract_metadata(_fake_result(None), 1.0)
    assert meta.cost_usd is None


def test_log_call_writes_top_level_cost_usd(tmp_path):
    agent = _make_agent()
    meta = ExecutionMetadata(
        model_name="gpt-4o",
        provider="openai",
        execution_time_seconds=1.0,
        prompt_tokens=100,
        completion_tokens=50,
        total_tokens=150,
        cost_usd=0.0123,
    )
    import json

    with patch("shared.agents.config.OUTPUT_BASE_DIR", tmp_path):
        agent._log_call("hi", "sys", None, result=None, metadata=meta)
    files = list((tmp_path / "logs" / "llm_calls").glob("*.json"))
    assert len(files) == 1
    data = json.loads(files[0].read_text())
    assert data["cost_usd"] == 0.0123


def test_token_payload_cost_defaults_none_and_roundtrips():
    assert TokenPayload().cost_usd is None
    tp = TokenPayload(prompt_tokens=10, total_tokens=10, cost_usd=0.001)
    assert tp.cost_usd == 0.001
    # JSON round-trip (metrics.json / summary.json path)
    tp2 = TokenPayload.model_validate_json(tp.model_dump_json())
    assert tp2.cost_usd == 0.001
