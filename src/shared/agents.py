import functools
import inspect
import json
import time
from collections.abc import Callable
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any, Generic, Literal, TypeVar

import httpx
from httpx import AsyncClient
from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from pydantic_ai import Agent, ModelRetry, ModelSettings, RunUsage
from pydantic_ai.exceptions import ModelAPIError
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.models.mistral import MistralModel
from pydantic_ai.models.openai import OpenAIChatModel, OpenAIResponsesModel
from pydantic_ai.providers.deepseek import DeepSeekProvider
from pydantic_ai.providers.google_cloud import GoogleCloudProvider
from pydantic_ai.providers.mistral import MistralProvider
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.retries import (
    AsyncTenacityTransport,
    RetryConfig,
    wait_retry_after,
)
from pydantic_ai.settings import ThinkingLevel
from tenacity import (
    AsyncRetrying,
    Retrying,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from .config import config
from .console import console as r_console
from .llm_cache import LLMCache, compute_cache_key

T = TypeVar("T")
D = TypeVar("D")


class TimingStatus:
    """A Rich renderable that displays a message with a real-time elapsed timer."""

    def __init__(self, message: str):
        self.message = message
        self.start_time = time.perf_counter()

    def __rich__(self) -> str:
        elapsed = time.perf_counter() - self.start_time
        return f"{self.message} [dim]({elapsed:.1f}s elapsed)[/dim]"


class RetryEvent(BaseModel):
    """Structured event capturing a validation or API/network retry."""

    timestamp: str
    attempt: int
    retry_type: Literal["validation", "network", "api"]
    message: str


class ExecutionMetadata(BaseModel):
    """Standardized metadata for LLM execution tracking."""

    model_name: str
    provider: str
    thinking_level: str | None = None
    execution_time_seconds: float
    prompt_tokens: int
    completion_tokens: int
    cached_tokens: int = 0
    total_tokens: int
    reasoning_tokens: int = 0
    accepted_prediction_tokens: int = 0
    rejected_prediction_tokens: int = 0
    prompt_audio_tokens: int = 0
    completion_audio_tokens: int = 0
    cost_usd: float | None = None
    """Best-effort inference cost in USD, or `None` when the run is unpriced.

    Sourced from pydantic-ai's `RunUsage.cost`, which is itself computed by
    `genai-prices` from the model name, provider and request timestamp.
    """
    retry_count: int = 0
    retry_log: list[RetryEvent] = Field(default_factory=list)
    prompt_template: str | None = None
    user_prompt: str | None = None
    raw_response: Any | None = None
    log_file_path: str | None = None

    @property
    def execution_time_ms(self) -> float:
        return self.execution_time_seconds * 1000

    @execution_time_ms.setter
    def execution_time_ms(self, value: float):
        self.execution_time_seconds = value / 1000


def normalize_provider(provider: str | None) -> str | None:
    """Normalizes provider aliases to the canonical names defined in config."""
    if provider is None:
        return None
    p = provider.lower()
    if p in [
        "google",
        "google-gla",
        "google-gai",
        "google-cloud",
        "google-vertex",
        "google-cloud",
        "vertex",
        "vertexai",
        "gemini",
    ]:
        return config.PROVIDER_GOOGLE
    if p in ["openai"]:
        return config.PROVIDER_OPENAI
    if p in ["deepseek"]:
        return config.PROVIDER_DEEPSEEK
    return p


def get_default_http_timeout() -> httpx.Timeout:
    """Returns standard granular timeout configuration for LLM calls."""
    return httpx.Timeout(
        connect=config.LLM_CONNECT_TIMEOUT,
        read=config.LLM_HTTP_TIMEOUT,
        write=60.0,
        pool=30.0,
    )


def is_retryable_llm_exception(exc: Exception) -> bool:
    """Determine whether an LLM call exception is transient and safe to retry.

    Explicitly excludes httpx.ReadTimeout to prevent expensive duplicate token billing
    and wasted execution time when generation exceeds the read timeout limit.
    """
    if isinstance(exc, httpx.ReadTimeout) or isinstance(
        getattr(exc, "__cause__", None), httpx.ReadTimeout
    ):
        return False

    if isinstance(
        exc,
        (
            httpx.ConnectTimeout,
            httpx.ConnectError,
            httpx.PoolTimeout,
            httpx.NetworkError,
            ConnectionError,
            TimeoutError,
        ),
    ):
        return True

    if (
        isinstance(exc, httpx.HTTPStatusError)
        and exc.response.status_code in {429, 500, 502, 503, 504}
    ):
        return True

    if isinstance(exc, ModelAPIError):
        msg = str(exc).lower()
        if "read timeout" in msg or "timed out reading" in msg:
            return False
        if any(
            k in msg
            for k in [
                "connect timeout",
                "rate limit",
                "status code 5",
                "500",
                "502",
                "503",
                "504",
            ]
        ):
            return True

    return False


def create_retrying_http_client(
    max_attempts: int | None = None,
    timeout: httpx.Timeout | None = None,
) -> httpx.AsyncClient:
    """Creates an HTTP client with tenacity retry transport for LLM calls."""
    effective_attempts = (
        max_attempts if max_attempts is not None else config.LLM_MAX_RETRIES
    )
    effective_timeout = timeout or get_default_http_timeout()

    def log_retry(retry_state):
        attempt = retry_state.attempt_number
        exception = retry_state.outcome.exception()
        sleep_time = retry_state.next_action.sleep
        exc_msg = str(exception).strip() or type(exception).__name__
        r_console.print(
            f"  └─ [yellow] Attempt {attempt} failed: {exc_msg}. "
            f"Retrying in {sleep_time:.1f}s...[/yellow]"
        )

    transport = AsyncTenacityTransport(
        config=RetryConfig(
            retry=retry_if_exception(is_retryable_llm_exception),
            wait=wait_retry_after(
                fallback_strategy=wait_exponential(
                    multiplier=2, min=2, max=10
                ),
                max_wait=30,
            ),
            stop=stop_after_attempt(effective_attempts),
            reraise=True,
            before_sleep=log_retry,
        ),
        validate_response=lambda r: r.raise_for_status(),
    )
    return AsyncClient(timeout=effective_timeout, transport=transport)


def _resolve_provider(model_name: str, provider: str | None = None) -> str:
    """Resolve the LLM provider for a given model name.

    If provider is explicitly given, normalizes and returns it.
    Otherwise, looks up model_name in config.SUPPORTED_MODELS for each provider.

    Raises:
        ValueError: If the provider cannot be determined and the model is not found
                    in any provider's supported model list.
    """
    if provider is not None:
        normalized = normalize_provider(provider)
        if normalized:
            return normalized

    actual_model = model_name
    if ":" in model_name:
        prefix, actual_model = model_name.split(":", 1)
        normalized = normalize_provider(prefix)
        if normalized:
            return normalized

    # Search SUPPORTED_MODELS for the model name
    for prov, models in config.SUPPORTED_MODELS.items():
        if actual_model in models or model_name in models:
            return prov

    if ":" in model_name:
        return model_name.split(":", 1)[0]

    raise ValueError(
        f"Cannot resolve provider for model '{model_name}'. "
        f"Supported models: {config.SUPPORTED_MODELS}. "
        f"Please specify a valid provider or add '{model_name}' to "
        f"config.SUPPORTED_MODELS."
    )


def get_pydantic_model_name(
    model_name: str,
    provider: str | None = None,
    http_client: httpx.AsyncClient | None = None,
) -> Any:
    """Initializes the appropriate Pydantic AI model with explicit authentication.

    Provider is resolved via _resolve_provider, which checks config.SUPPORTED_MODELS.
    """
    provider = _resolve_provider(model_name, provider)

    actual_model_name = model_name
    if ":" in model_name:
        actual_model_name = model_name.split(":", 1)[1]

    if provider == config.PROVIDER_GOOGLE:
        return GoogleModel(
            actual_model_name,
            provider=GoogleCloudProvider(
                api_key=config.GEMINI_API_KEY, http_client=http_client
            ),
        )
    elif provider == config.PROVIDER_OPENAI:
        client = AsyncOpenAI(
            api_key=config.OPENAI_API_KEY,
            http_client=http_client,
            max_retries=0,
        )
        return OpenAIResponsesModel(
            actual_model_name, provider=OpenAIProvider(openai_client=client)
        )
    elif provider == config.PROVIDER_DEEPSEEK:
        # DeepSeek API server accepts 'deepseek-v4-flash' or 'deepseek-flash' (not 'deepseek-v4.1-flash').
        # Pydantic AI requires 'deepseek-v4-' prefix to disable forced tool_choice in thinking mode.
        deepseek_model_id = actual_model_name
        if deepseek_model_id in {"deepseek-v4.1-flash", "deepseek-flash"}:
            deepseek_model_id = "deepseek-v4-flash"

        client = AsyncOpenAI(
            base_url=config.DEEPSEEK_BASE_URL,
            api_key=config.DEEPSEEK_API_KEY,
            http_client=http_client,
            max_retries=0,
        )
        return OpenAIChatModel(
            deepseek_model_id, provider=DeepSeekProvider(openai_client=client)
        )
    elif provider == config.PROVIDER_MISTRAL:
        return MistralModel(
            actual_model_name,
            provider=MistralProvider(
                api_key=config.MISTRAL_API_KEY, http_client=http_client
            ),
        )
    else:
        # Fallback to string if unknown provider
        return f"{provider}:{actual_model_name}" if provider else model_name

class LLMAgent(Generic[D, T]):
    """Centralized Agent Interface wrapping pydantic_ai.Agent.

    Handles model resolution, execution timing, and usage tracking.
    """

    def __init__(
        self,
        response_model: type[T],
        system_prompt: str,
        provider: str | None,
        model_name: str,
        name: str | None = None,
        deps_type: type[D] = Any,
        retries: int = 0,
        http_client: httpx.AsyncClient | None = None,
        thinking: ThinkingLevel | None = None,
    ):
        self.name = name or "agent"

        provider_part = _resolve_provider(model_name, provider)
        self.provider = provider_part
        self.model_name = model_name
        default_thinking = (
            getattr(config, "DEFAULT_GOOGLE_THINKING_LEVEL", "low")
            if provider_part == config.PROVIDER_GOOGLE
            else getattr(config, "DEFAULT_THINKING_LEVEL", "medium")
        )
        self.thinking = thinking if thinking is not None else default_thinking

        effective_http_client = http_client or create_retrying_http_client()
        model = get_pydantic_model_name(
            model_name=model_name,
            provider=provider_part,
            http_client=effective_http_client,
        )

        self.system_prompt = system_prompt
        self.response_model = response_model
        self.response_schema = (
            response_model.model_json_schema()
            if hasattr(response_model, "model_json_schema")
            else {}
        )
        self.cache = LLMCache()
        self.agent = Agent(
            model,
            output_type=response_model,
            deps_type=deps_type,
            system_prompt=system_prompt,
            retries=retries,
            model_settings=ModelSettings(thinking=self.thinking),
        )
        self._current_retry_log: list[RetryEvent] = []
        self._validation_retry_count: int = 0

    def output_validator(self, func: Callable) -> Callable:
        """Decorator to add an output validator to the underlying agent."""
        if inspect.iscoroutinefunction(func):

            @functools.wraps(func)
            async def wrapper(*args: Any, **kwargs: Any) -> Any:
                try:
                    return await func(*args, **kwargs)
                except ModelRetry as exc:
                    self._validation_retry_count += 1
                    event = RetryEvent(
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        attempt=self._validation_retry_count,
                        retry_type="validation",
                        message=str(exc),
                    )
                    self._current_retry_log.append(event)
                    raise

        else:

            @functools.wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                try:
                    return func(*args, **kwargs)
                except ModelRetry as exc:
                    self._validation_retry_count += 1
                    event = RetryEvent(
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        attempt=self._validation_retry_count,
                        retry_type="validation",
                        message=str(exc),
                    )
                    self._current_retry_log.append(event)
                    raise

        return self.agent.output_validator(wrapper)

    def _extract_metadata(
        self,
        result: Any,
        execution_time: float,
        retry_log: list[RetryEvent] | None = None,
        user_prompt: str | None = None,
    ) -> ExecutionMetadata:
        usage: RunUsage = result.usage
        details = usage.details or {}
        # `RunUsage.cost` is a Decimal (or None when unpriced); normalise to
        # float so the value round-trips cleanly through JSON/Pydantic.
        cost = getattr(usage, "cost", None)
        retries = (
            retry_log
            if retry_log is not None
            else list(self._current_retry_log)
        )
        raw_resp = None
        if result and hasattr(result, "output"):
            raw_resp = (
                result.output.model_dump()
                if hasattr(result.output, "model_dump")
                else str(result.output)
            )

        return ExecutionMetadata(
            model_name=self.model_name,
            provider=self.provider,
            thinking_level=str(self.thinking) if self.thinking is not None else None,
            execution_time_seconds=execution_time,
            prompt_tokens=usage.input_tokens or 0,
            completion_tokens=usage.output_tokens or 0,
            total_tokens=usage.total_tokens or 0,
            cached_tokens=usage.cache_read_tokens or 0,
            reasoning_tokens=details.get("reasoning_tokens", 0),
            accepted_prediction_tokens=0,
            rejected_prediction_tokens=0,
            prompt_audio_tokens=usage.input_audio_tokens or 0,
            completion_audio_tokens=usage.output_audio_tokens or 0,
            cost_usd=float(cost) if cost is not None else None,
            retry_count=len(retries),
            retry_log=retries,
            prompt_template=self.system_prompt,
            user_prompt=user_prompt,
            raw_response=raw_resp,
        )

    def _log_call(
        self,
        user_prompt: str,
        system_prompt: str,
        deps: Any,
        result: Any | None = None,
        error: str | None = None,
        execution_time: float = 0.0,
        metadata: ExecutionMetadata | None = None,
    ):
        if not config.OUTPUT_BASE_DIR:
            return

        try:
            log_dir = config.OUTPUT_BASE_DIR / "logs" / "llm_calls"
            log_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            safe_name = "".join(x for x in self.name if x.isalnum())
            filename = f"{timestamp}_{safe_name}.json"

            # Prepare data
            has_error = error is not None
            log_data = {
                "timestamp": datetime.now().isoformat(),
                "agent_name": self.name,
                "model_name": self.model_name,
                "provider": self.provider,
                "thinking_level": str(self.thinking) if self.thinking is not None else None,
                "system_prompt": str(system_prompt),
                "user_prompt": str(user_prompt),
                "dependencies": str(deps) if deps else None,
                "execution_time_seconds": execution_time,
                "status": "error" if has_error else "success",
            }

            if metadata:
                log_data["cost_usd"] = metadata.cost_usd
                log_data["retry_count"] = metadata.retry_count
                log_data["retry_log"] = [
                    e.model_dump() for e in metadata.retry_log
                ]

            if has_error:
                log_data["error"] = str(error).strip() or "Error (no message details provided)"

            if result:
                try:
                    usage = result.usage
                    log_data["usage"] = (
                        asdict(usage)
                        if hasattr(usage, "__dataclass_fields__")
                        else str(usage)
                    )
                except Exception:
                    log_data["usage"] = str(result.usage)

                log_data["response"] = (
                    result.output.model_dump()
                    if hasattr(result.output, "model_dump")
                    else str(result.output)
                )

            file_path = log_dir / filename
            with open(file_path, "w") as f:
                json.dump(log_data, f, indent=2, default=str)

            if metadata:
                metadata.log_file_path = str(file_path)

            return str(file_path)

        except Exception as e:
            r_console.print(f"  └─ [red]Failed to log LLM call: {e}[/red]")
            return None

    @staticmethod
    def _print_execution_summary(metadata: ExecutionMetadata) -> None:
        """Render a compact one-line execution summary to the console.

        Args:
            metadata: Execution metadata for the completed run.
        """
        cost_suffix = (
            f" (~${metadata.cost_usd:.4f})"
            if metadata.cost_usd is not None
            else ""
        )
        r_console.print(
            f"  └─ [dim]LLM Summary: {metadata.total_tokens:,} "
            f"tokens in {metadata.execution_time_seconds:.1f}s"
            f"{cost_suffix}[/dim]"
        )

    def run_sync(
        self, user_prompt: str, deps: D | None = None
    ) -> tuple[T, ExecutionMetadata]:
        cache_key = None
        if self.cache.is_active:
            cache_key = compute_cache_key(
                provider=self.provider,
                model_name=self.model_name,
                system_prompt=self.system_prompt,
                user_prompt=user_prompt,
                response_schema=self.response_schema,
                thinking=str(self.thinking) if self.thinking is not None else None,
            )
            cached_result = self.cache.get(cache_key, self.response_model)
            if cached_result is not None:
                output, metadata = cached_result
                r_console.print(
                    f"  └─ [dim]LLM Summary (CACHED): {metadata.total_tokens:,} "
                    f"tokens in 0.0s[/dim]"
                )
                return output, metadata

        status_msg = f"[bold yellow]Querying LLM ({self.model_name})..."
        start_time = time.perf_counter()
        result = None
        error = None
        metadata = None
        self._current_retry_log = []
        self._validation_retry_count = 0

        def log_retry(retry_state):
            attempt = retry_state.attempt_number
            exception = retry_state.outcome.exception()
            sleep_time = retry_state.next_action.sleep
            exc_msg = str(exception).strip() or type(exception).__name__
            event = RetryEvent(
                timestamp=datetime.now(timezone.utc).isoformat(),
                attempt=attempt,
                retry_type=(
                    "api"
                    if isinstance(exception, ModelAPIError)
                    else "network"
                ),
                message=exc_msg,
            )
            self._current_retry_log.append(event)
            r_console.print(
                f"  └─ [yellow] Attempt {attempt} failed: {exc_msg}. "
                f"Retrying in {sleep_time:.1f}s...[/yellow]"
            )

        try:
            for attempt in Retrying(
                retry=retry_if_exception(is_retryable_llm_exception),
                wait=wait_exponential(multiplier=2, min=2, max=10),
                stop=stop_after_attempt(config.LLM_MAX_RETRIES),
                reraise=True,
                before_sleep=log_retry,
            ):
                with attempt:
                    with r_console.status(TimingStatus(status_msg)):
                        model = get_pydantic_model_name(
                            model_name=self.model_name,
                            provider=self.provider,
                            http_client=None,
                        )
                        result = self.agent.run_sync(
                            user_prompt,
                            deps=deps,
                            model=model,
                            model_settings=ModelSettings(thinking=self.thinking),
                        )
            execution_time = time.perf_counter() - start_time
            metadata = self._extract_metadata(
                result, execution_time, user_prompt=user_prompt
            )
            self._log_call(
                user_prompt,
                self.system_prompt,
                deps,
                result,
                error,
                execution_time,
                metadata,
            )
            if self.cache.mode in {"record", "auto"} and cache_key:
                req_ctx = {
                    "model_name": self.model_name,
                    "provider": self.provider,
                    "system_prompt": self.system_prompt,
                    "user_prompt": user_prompt,
                    "thinking": str(self.thinking) if self.thinking is not None else None,
                    "response_schema": self.response_schema,
                }
                self.cache.set(cache_key, result.output, metadata, req_ctx)
            return result.output, metadata
        except Exception as e:
            error = str(e).strip() or type(e).__name__
            execution_time = time.perf_counter() - start_time
            self._log_call(
                user_prompt,
                self.system_prompt,
                deps,
                None,
                error,
                execution_time,
                None,
            )
            raise e
        finally:
            if metadata:
                self._print_execution_summary(metadata)

    async def run(
        self, user_prompt: str, deps: D | None = None
    ) -> tuple[T, ExecutionMetadata]:
        cache_key = None
        if self.cache.is_active:
            cache_key = compute_cache_key(
                provider=self.provider,
                model_name=self.model_name,
                system_prompt=self.system_prompt,
                user_prompt=user_prompt,
                response_schema=self.response_schema,
                thinking=str(self.thinking) if self.thinking is not None else None,
            )
            cached_result = self.cache.get(cache_key, self.response_model)
            if cached_result is not None:
                output, metadata = cached_result
                r_console.print(
                    f"  └─ [dim]LLM Summary (CACHED): {metadata.total_tokens:,} "
                    f"tokens in 0.0s[/dim]"
                )
                return output, metadata

        status_msg = f"[bold yellow]Querying LLM ({self.model_name})..."
        start_time = time.perf_counter()
        result = None
        error = None
        metadata = None
        self._current_retry_log = []
        self._validation_retry_count = 0

        def log_retry(retry_state):
            attempt = retry_state.attempt_number
            exception = retry_state.outcome.exception()
            sleep_time = retry_state.next_action.sleep
            exc_msg = str(exception).strip() or type(exception).__name__
            event = RetryEvent(
                timestamp=datetime.now(timezone.utc).isoformat(),
                attempt=attempt,
                retry_type=(
                    "api"
                    if isinstance(exception, ModelAPIError)
                    else "network"
                ),
                message=exc_msg,
            )
            self._current_retry_log.append(event)
            r_console.print(
                f"  └─ [yellow] Attempt {attempt} failed: {exc_msg}. "
                f"Retrying in {sleep_time:.1f}s...[/yellow]"
            )

        try:
            async for attempt in AsyncRetrying(
                retry=retry_if_exception(is_retryable_llm_exception),
                wait=wait_exponential(multiplier=2, min=2, max=10),
                stop=stop_after_attempt(config.LLM_MAX_RETRIES),
                reraise=True,
                before_sleep=log_retry,
            ):
                with attempt:
                    with r_console.status(TimingStatus(status_msg)):
                        async with httpx.AsyncClient(
                            timeout=get_default_http_timeout()
                        ) as http_client:
                            model = get_pydantic_model_name(
                                model_name=self.model_name,
                                provider=self.provider,
                                http_client=http_client,
                            )
                            result = await self.agent.run(
                                user_prompt,
                                deps=deps,
                                model=model,
                                model_settings=ModelSettings(thinking=self.thinking),
                            )
            execution_time = time.perf_counter() - start_time
            metadata = self._extract_metadata(
                result, execution_time, user_prompt=user_prompt
            )
            self._log_call(
                user_prompt,
                self.system_prompt,
                deps,
                result,
                error,
                execution_time,
                metadata,
            )
            if self.cache.mode in {"record", "auto"} and cache_key:
                req_ctx = {
                    "model_name": self.model_name,
                    "provider": self.provider,
                    "system_prompt": self.system_prompt,
                    "user_prompt": user_prompt,
                    "thinking": str(self.thinking) if self.thinking is not None else None,
                    "response_schema": self.response_schema,
                }
                self.cache.set(cache_key, result.output, metadata, req_ctx)
            return result.output, metadata
        except Exception as e:
            error = str(e).strip() or type(e).__name__
            execution_time = time.perf_counter() - start_time
            self._log_call(
                user_prompt,
                self.system_prompt,
                deps,
                None,
                error,
                execution_time,
                None,
            )
            raise e
        finally:
            if metadata:
                self._print_execution_summary(metadata)
