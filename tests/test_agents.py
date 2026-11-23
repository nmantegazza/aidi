import json
from unittest.mock import patch

import httpx
import pytest
from pydantic import BaseModel
from pydantic_ai import ModelResponse, TextPart, models
from pydantic_ai.exceptions import UnexpectedModelBehavior
from pydantic_ai.models.function import AgentInfo, FunctionModel
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.models.mistral import MistralModel
from pydantic_ai.models.openai import OpenAIChatModel, OpenAIResponsesModel
from pydantic_ai.models.test import TestModel

# Import the module under test
from shared.agents import (
    ExecutionMetadata,
    LLMAgent,
    create_retrying_http_client,
    get_default_http_timeout,
    get_pydantic_model_name,
    is_retryable_llm_exception,
    normalize_provider,
)
from shared.config import config

# Prevent any accidental real LLM calls during testing
models.ALLOW_MODEL_REQUESTS = False


class DummyResponse(BaseModel):
    """Simple response model for testing."""
    result: str


def test_normalize_provider():
    """Verify that provider aliases are mapped to canonical names."""
    assert normalize_provider("gemini") == "google-cloud"
    assert normalize_provider("google-cloud") == "google-cloud"
    assert normalize_provider("openai") == "openai"
    assert normalize_provider("deepseek") == "deepseek"
    assert normalize_provider("unknown") == "unknown"
    assert normalize_provider(None) is None


def test_get_agent_model_openai():
    """Verify resolving openai models."""
    model = get_pydantic_model_name("openai:gpt-4o")
    assert isinstance(model, OpenAIResponsesModel)
    assert model.model_name == "gpt-4o"


def test_get_agent_model_google():
    """Verify resolving google models."""
    model = get_pydantic_model_name("google:gemini-3.8-flash")
    assert isinstance(model, GoogleModel)
    assert model.model_name == "gemini-3.8-flash"


def test_get_agent_model_deepseek():
    """Verify resolving deepseek models."""
    model = get_pydantic_model_name("deepseek:deepseek-chat")
    assert isinstance(model, OpenAIChatModel)
    assert model.model_name == "deepseek-chat"
    from pydantic_ai.providers.deepseek import DeepSeekProvider
    assert isinstance(model.provider, DeepSeekProvider)


def test_get_agent_model_mistral():
    """Verify resolving mistral models."""
    model = get_pydantic_model_name("mistral-medium-latest")
    assert isinstance(model, MistralModel)
    assert model.model_name == "mistral-medium-latest"


def test_get_agent_model_unknown():
    """Verify fallback for unknown providers."""
    model = get_pydantic_model_name("unknown:model-x")
    assert model == "unknown:model-x"


def test_llm_agent_initialization():
    """Verify initializing LLMAgent sets attributes correctly."""
    agent = LLMAgent(
        response_model=DummyResponse,
        system_prompt="sys prompt",
        provider="openai",
        model_name="gpt-4o",
        name="test-agent",
    )
    assert agent.name == "test-agent"
    assert agent.model_name == "gpt-4o"
    assert agent.provider == "openai"
    assert agent.agent.output_type == DummyResponse


def test_llm_agent_run_sync_success():
    """Verify run_sync success flow with TestModel."""
    agent = LLMAgent(
        response_model=DummyResponse,
        system_prompt="sys prompt",
        provider="openai",
        model_name="gpt-4o",
        name="test-agent",
    )
    
    mock_model = TestModel(
        custom_output_args=DummyResponse(result="hello world")
    )
    
    with agent.agent.override(model=mock_model):
        output, metadata = agent.run_sync("user prompt")
        assert output.result == "hello world"
        assert isinstance(metadata, ExecutionMetadata)
        assert metadata.model_name == "gpt-4o"
        assert metadata.provider == "openai"
        assert metadata.total_tokens >= 0


@pytest.mark.asyncio
async def test_llm_agent_run_async_success():
    """Verify run async success flow with TestModel."""
    agent = LLMAgent(
        response_model=DummyResponse,
        system_prompt="sys prompt",
        provider="openai",
        model_name="gpt-4o",
        name="test-agent",
    )
    
    mock_model = TestModel(
        custom_output_args=DummyResponse(result="hello async")
    )
    
    with agent.agent.override(model=mock_model):
        output, metadata = await agent.run("user prompt")
        assert output.result == "hello async"
        assert isinstance(metadata, ExecutionMetadata)
        assert metadata.model_name == "gpt-4o"


@pytest.mark.asyncio
async def test_llm_agent_run_custom_validator_error():
    """Verify output validator exception bubbles up directly."""
    agent = LLMAgent(
        response_model=DummyResponse,
        system_prompt="sys prompt",
        provider="openai",
        model_name="gpt-4o",
        name="test-agent",
        retries=1,
    )

    @agent.output_validator
    def fail_validation(val: DummyResponse) -> DummyResponse:
        raise ValueError("Invalid result")

    mock_model = TestModel(
        custom_output_args=DummyResponse(result="will fail")
    )

    with (
        agent.agent.override(model=mock_model),
        pytest.raises(ValueError, match="Invalid result"),
    ):
        await agent.run("user prompt")


@pytest.mark.asyncio
async def test_llm_agent_run_schema_validation_exhaust():
    """Verify schema validation failure raises UnexpectedModelBehavior."""
    agent = LLMAgent(
        response_model=DummyResponse,
        system_prompt="sys prompt",
        provider="openai",
        model_name="gpt-4o",
        name="test-agent",
        retries=1,
    )

    # Return invalid JSON text to trigger schema validation error
    def bad_response(messages: list, info: AgentInfo) -> ModelResponse:
        return ModelResponse(parts=[TextPart("not json")])

    mock_model = FunctionModel(bad_response)

    with agent.agent.override(model=mock_model):
        with pytest.raises(UnexpectedModelBehavior) as exc_info:
            await agent.run("user prompt")
        assert "Exceeded maximum output retries" in str(exc_info.value)



@pytest.mark.asyncio
async def test_llm_agent_run_error_handling(tmp_path):
    """Verify that LLMAgent handles direct model errors and logs them."""
    agent = LLMAgent(
        response_model=DummyResponse,
        system_prompt="sys prompt",
        provider="openai",
        model_name="gpt-4o",
        name="error-agent",
    )

    def raise_model_error(messages: list, info: AgentInfo) -> ModelResponse:
        raise RuntimeError("Model crashed")

    mock_model = FunctionModel(raise_model_error)

    # Patch base output directory for logs to a temp directory
    with (
        patch("shared.agents.config.OUTPUT_BASE_DIR", tmp_path),
        agent.agent.override(model=mock_model),
        pytest.raises(RuntimeError, match="Model crashed"),
    ):
        await agent.run("trigger error")

    # Verify call log contains error
    log_dir = tmp_path / "logs" / "llm_calls"
    log_files = list(log_dir.glob("*.json"))
    assert len(log_files) == 1
    log_data = json.loads(log_files[0].read_text())
    assert log_data["status"] == "error"
    assert "Model crashed" in log_data["error"]
    assert log_data["user_prompt"] == "trigger error"


def test_llm_agent_logging_success(tmp_path):
    """Verify that successful calls are logged to output directory."""
    agent = LLMAgent(
        response_model=DummyResponse,
        system_prompt="sys prompt",
        provider="openai",
        model_name="gpt-4o",
        name="success-agent",
    )

    mock_model = TestModel(
        custom_output_args=DummyResponse(result="logged success")
    )

    with (
        patch("shared.agents.config.OUTPUT_BASE_DIR", tmp_path),
        agent.agent.override(model=mock_model),
    ):
        output, _ = agent.run_sync("trigger log")
        assert output.result == "logged success"

        log_dir = tmp_path / "logs" / "llm_calls"
        log_files = list(log_dir.glob("*.json"))
        assert len(log_files) == 1
        with open(log_files[0]) as f:
            log_data = json.load(f)
            assert log_data["status"] == "success"
            assert log_data["agent_name"] == "success-agent"
            assert log_data["model_name"] == "gpt-4o"
            assert log_data["user_prompt"] == "trigger log"
            assert log_data["response"]["result"] == "logged success"


@pytest.mark.asyncio
async def test_create_retrying_http_client():
    """Verify create_retrying_http_client's retry transport on transient errors."""
    client = create_retrying_http_client(max_attempts=3)
    
    class MockTransport:
        def __init__(self):
            self.calls = 0
            
        async def handle_async_request(self, request):
            self.calls += 1
            if self.calls < 3:
                # Raise connection error for the first two attempts
                raise httpx.ConnectError("Connection failed")
            # Succeed on the third attempt
            return httpx.Response(200, request=request)

    # Inject mock transport into tenacity wrapper
    client._transport.wrapped = MockTransport()
    
    # We must patch wait behavior to make the test fast
    from tenacity import wait_none
    client._transport.config['wait'] = wait_none()

    response = await client.get("https://dummy-llm-api.com")
    assert response.status_code == 200
    assert client._transport.wrapped.calls == 3


@pytest.mark.asyncio
async def test_create_retrying_http_client_exhaustion():
    """Verify retry transport propagates exception after max_attempts."""
    client = create_retrying_http_client(max_attempts=3)
    
    class MockTransport:
        def __init__(self):
            self.calls = 0
            
        async def handle_async_request(self, request):
            self.calls += 1
            raise httpx.ConnectError("Transient connection error")

    client._transport.wrapped = MockTransport()
    from tenacity import wait_none
    client._transport.config['wait'] = wait_none()

    with pytest.raises(httpx.ConnectError, match="Transient connection error"):
        await client.get("https://dummy-llm-api.com")
    
    assert client._transport.wrapped.calls == 3


def test_is_retryable_llm_exception_policy():
    """Verify that read timeouts are rejected from retry, while connection errors retry."""
    # Read timeouts should never be retried
    read_timeout = httpx.ReadTimeout("The read operation timed out")
    empty_read_timeout = httpx.ReadTimeout("")
    assert is_retryable_llm_exception(read_timeout) is False
    assert is_retryable_llm_exception(empty_read_timeout) is False

    # Connection and network timeouts should be retried
    assert is_retryable_llm_exception(httpx.ConnectTimeout("connect timed out")) is True
    assert is_retryable_llm_exception(httpx.ConnectError("connection refused")) is True
    assert is_retryable_llm_exception(httpx.PoolTimeout("pool timed out")) is True
    assert is_retryable_llm_exception(ConnectionError("socket error")) is True

    # 429 and 5xx status codes should be retried
    req = httpx.Request("POST", "https://api.openai.com/v1/chat")
    resp_429 = httpx.Response(429, request=req)
    resp_500 = httpx.Response(500, request=req)
    resp_503 = httpx.Response(503, request=req)
    resp_400 = httpx.Response(400, request=req)

    assert is_retryable_llm_exception(httpx.HTTPStatusError("Rate limit", request=req, response=resp_429)) is True
    assert is_retryable_llm_exception(httpx.HTTPStatusError("Server error", request=req, response=resp_500)) is True
    assert is_retryable_llm_exception(httpx.HTTPStatusError("Unavailable", request=req, response=resp_503)) is True
    assert is_retryable_llm_exception(httpx.HTTPStatusError("Bad request", request=req, response=resp_400)) is False


def test_get_default_http_timeout():
    """Verify get_default_http_timeout loads values from config."""
    timeout = get_default_http_timeout()
    assert isinstance(timeout, httpx.Timeout)
    assert timeout.connect == config.LLM_CONNECT_TIMEOUT
    assert timeout.read == config.LLM_HTTP_TIMEOUT
    assert timeout.write == 60.0
    assert timeout.pool == 30.0


@pytest.mark.asyncio
async def test_llm_agent_logging_empty_error_status(tmp_path):
    """Verify that empty exception strings still record status='error' and valid error message."""
    agent = LLMAgent(
        response_model=DummyResponse,
        system_prompt="sys prompt",
        provider="openai",
        model_name="gpt-4o",
        name="timeout-agent",
    )

    def raise_empty_read_timeout(messages: list, info: AgentInfo) -> ModelResponse:
        raise httpx.ReadTimeout("")

    mock_model = FunctionModel(raise_empty_read_timeout)

    with (
        patch("shared.agents.config.OUTPUT_BASE_DIR", tmp_path),
        agent.agent.override(model=mock_model),
        pytest.raises(httpx.ReadTimeout),
    ):
        await agent.run("trigger empty timeout")

    log_dir = tmp_path / "logs" / "llm_calls"
    log_files = list(log_dir.glob("*.json"))
    assert len(log_files) == 1
    log_data = json.loads(log_files[0].read_text())
    assert log_data["status"] == "error"
    assert "error" in log_data
    assert log_data["error"] == "ReadTimeout"


@pytest.mark.asyncio
async def test_create_retrying_http_client_no_retry_on_read_timeout():
    """Verify retry transport does not retry on ReadTimeout."""
    client = create_retrying_http_client(max_attempts=3)

    class MockTransport:
        def __init__(self):
            self.calls = 0

        async def handle_async_request(self, request):
            self.calls += 1
            raise httpx.ReadTimeout("Generation timed out")

    client._transport.wrapped = MockTransport()
    from tenacity import wait_none
    client._transport.config['wait'] = wait_none()

    with pytest.raises(httpx.ReadTimeout):
        await client.get("https://dummy-llm-api.com")

    # Should have stopped after 1 call without retrying
    assert client._transport.wrapped.calls == 1
