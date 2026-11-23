"""Deterministic content-addressable record/replay cache for LLM calls.

Provides persistent caching of structured LLM outputs indexed by cryptographic
hash, enabling offline replay with zero network latency, zero token cost, and
bit-level determinism.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel

from .config import config

T = TypeVar("T")


class CacheMissError(RuntimeError):
    """Raised when an entry is not found in cache while in replay mode."""


class CacheCorruptedError(RuntimeError):
    """Raised when a cached JSON file cannot be read or validated."""


class CacheEntry(BaseModel):
    """Data model representing a stored LLM cache file."""

    version: int = 1
    key_hash: str
    timestamp: str
    request: dict[str, Any]
    response: Any
    usage: dict[str, Any]
    execution_time_seconds: float = 0.0


def compute_cache_key(
    provider: str | None,
    model_name: str,
    system_prompt: str,
    user_prompt: str,
    response_schema: dict[str, Any],
    thinking: str | None = None,
) -> str:
    """Compute deterministic SHA256 hex digest identifying an LLM request.

    Args:
        provider: Provider identifier (e.g., 'google-cloud', 'openai').
        model_name: Model identifier (e.g., 'gemini-3.8-flash').
        system_prompt: System prompt string.
        user_prompt: User prompt string.
        response_schema: JSON Schema dictionary of expected response model.
        thinking: Thinking level configuration string or None.

    Returns:
        64-character SHA256 hexadecimal hash string.
    """
    normalized_data = {
        "provider": (provider or "").strip().lower(),
        "model_name": (model_name or "").strip(),
        "system_prompt": (system_prompt or "").strip(),
        "user_prompt": (user_prompt or "").strip(),
        "thinking": (thinking or "").strip().lower() if thinking else None,
        "response_schema": response_schema,
    }
    encoded = json.dumps(
        normalized_data, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


class LLMCache:
    """Manager for recording and replaying LLM responses."""

    def __init__(
        self,
        mode: str | None = None,
        cache_dir: Path | None = None,
    ) -> None:
        """Initialize LLMCache.

        Args:
            mode: Cache mode ('off', 'record', 'replay', 'auto'). Defaults to
                config.LLM_CACHE_MODE.
            cache_dir: Path to directory for cache entries. Defaults to
                config.LLM_CACHE_DIR.
        """
        raw_mode = mode if mode is not None else config.LLM_CACHE_MODE
        self.mode: str = (raw_mode or "off").strip().lower()
        if self.mode not in {"off", "record", "replay", "auto"}:
            self.mode = "off"

        raw_dir = cache_dir if cache_dir is not None else config.LLM_CACHE_DIR
        self.cache_dir: Path = Path(raw_dir)
        if self.is_active:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    @property
    def is_active(self) -> bool:
        """Return True if cache is active (not 'off')."""
        return self.mode != "off"

    def get_entry_path(self, key: str) -> Path:
        """Return path to cached entry JSON file."""
        return self.cache_dir / f"{key}.json"

    def get(
        self,
        key: str,
        response_model: type[T],
    ) -> tuple[T, Any] | None:
        """Retrieve and deserialize a cached response.

        Args:
            key: SHA256 cache key hash.
            response_model: Expected response model type (Pydantic model or
                type).

        Returns:
            Tuple of (output, ExecutionMetadata) if found, or None if missed
            when not in replay mode.

        Raises:
            CacheMissError: If mode is 'replay' and key is not found.
            CacheCorruptedError: If file is malformed or validation fails.
        """
        if not self.is_active:
            return None

        file_path = self.get_entry_path(key)

        if not file_path.is_file():
            if self.mode == "replay":
                raise CacheMissError(
                    f"LLM Cache miss in replay mode for key '{key}' "
                    f"at path '{file_path}'"
                )
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            entry = CacheEntry.model_validate(data)
        except Exception as exc:
            raise CacheCorruptedError(
                f"Failed to read or parse cache entry at '{file_path}': {exc}"
            ) from exc

        # Import ExecutionMetadata lazily to avoid circular import
        from .agents import ExecutionMetadata

        try:
            # Reconstruct typed response
            raw_response = entry.response
            if isinstance(raw_response, dict) and hasattr(
                response_model, "model_validate"
            ):
                output: T = response_model.model_validate(raw_response)
            elif isinstance(raw_response, str) and hasattr(
                response_model, "model_validate_json"
            ):
                output = response_model.model_validate_json(raw_response)
            else:
                output = raw_response

            usage_dict = entry.usage or {}
            total_tokens = int(usage_dict.get("total_tokens", 0))

            metadata = ExecutionMetadata(
                model_name=str(entry.request.get("model_name", "")),
                provider=str(entry.request.get("provider", "")),
                thinking_level=entry.request.get("thinking"),
                execution_time_seconds=0.0,
                prompt_tokens=int(usage_dict.get("prompt_tokens", 0)),
                completion_tokens=int(usage_dict.get("completion_tokens", 0)),
                cached_tokens=total_tokens,
                total_tokens=total_tokens,
                reasoning_tokens=int(usage_dict.get("reasoning_tokens", 0)),
                cost_usd=usage_dict.get("cost_usd"),
                prompt_template=entry.request.get("system_prompt"),
                user_prompt=entry.request.get("user_prompt"),
                raw_response=raw_response,
                log_file_path=str(file_path),
            )
            return output, metadata
        except Exception as exc:
            raise CacheCorruptedError(
                f"Validation error deserializing cached entry '{file_path}' "
                f"into {response_model}: {exc}"
            ) from exc

    def set(
        self,
        key: str,
        output: Any,
        metadata: Any,
        request_context: dict[str, Any],
    ) -> Path:
        """Atomically persist a completed LLM execution to disk.

        Args:
            key: SHA256 cache key hash.
            output: Validated response object or BaseModel.
            metadata: ExecutionMetadata instance.
            request_context: Request parameter dictionary.

        Returns:
            Path of written JSON cache file.
        """
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        file_path = self.get_entry_path(key)

        serialized_response = (
            output.model_dump() if hasattr(output, "model_dump") else output
        )

        usage_dict = {
            "prompt_tokens": getattr(metadata, "prompt_tokens", 0),
            "completion_tokens": getattr(metadata, "completion_tokens", 0),
            "total_tokens": getattr(metadata, "total_tokens", 0),
            "cached_tokens": getattr(metadata, "cached_tokens", 0),
            "reasoning_tokens": getattr(metadata, "reasoning_tokens", 0),
            "cost_usd": getattr(metadata, "cost_usd", None),
        }

        entry = CacheEntry(
            version=1,
            key_hash=key,
            timestamp=datetime.now(timezone.utc).isoformat(),
            request=request_context,
            response=serialized_response,
            usage=usage_dict,
            execution_time_seconds=getattr(
                metadata, "execution_time_seconds", 0.0
            ),
        )

        data_json = entry.model_dump_json(indent=2)

        # Atomic write: write to temp file in same directory, then rename
        temp_fd, temp_path = tempfile.mkstemp(
            dir=self.cache_dir, prefix=f"{key}_", suffix=".tmp"
        )
        try:
            with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
                f.write(data_json)
            os.replace(temp_path, file_path)
        except Exception:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise

        return file_path
