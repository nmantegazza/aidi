"""Core benchmarking data models and enumerations."""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, model_validator


class RunStatus(str, Enum):
    """Execution status for a single benchmark iteration or overall run."""

    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    PARTIAL = "PARTIAL"


class TokenPayload(BaseModel):
    """Telemetry capturing token counts, latency and estimated cost for LLM operations."""

    prompt_tokens: int = Field(
        default=0,
        description="Input prompt tokens consumed.",
    )
    completion_tokens: int = Field(
        default=0,
        description="Generated output tokens consumed.",
    )
    cached_tokens: int = Field(
        default=0,
        description="Cached prompt tokens consumed.",
    )
    reasoning_tokens: int = Field(
        default=0,
        description="Reasoning or thinking tokens consumed.",
    )
    total_tokens: int = Field(
        default=0,
        description="Total tokens consumed across the run.",
    )
    latency_seconds: float = Field(
        default=0.0,
        description="Execution latency in seconds.",
    )
    cost_usd: float | None = Field(
        default=None,
        description=(
            "Best-effort inference cost in USD, or None when the run is "
            "unpriced."
        ),
    )


# Alias for backward compatibility
TokenUsage = TokenPayload


class AggregatedMetricStats(BaseModel):
    """Summary statistics (mean, std, min, max) for a numeric metric."""

    mean: float = Field(default=0.0, description="Sample mean.")
    std: float = Field(
        default=0.0,
        description="Sample standard deviation.",
    )
    min: float = Field(
        default=0.0,
        description="Minimum observed value.",
    )
    max: float = Field(
        default=0.0,
        description="Maximum observed value.",
    )
    values: list[float] = Field(
        default_factory=list,
        description="List of raw values across iterations.",
    )

    @model_validator(mode="before")
    @classmethod
    def _normalize_min_max(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "min_val" in data and "min" not in data:
                data["min"] = data["min_val"]
            if "max_val" in data and "max" not in data:
                data["max"] = data["max_val"]
        return data

    @property
    def min_val(self) -> float:
        """Alias for minimum value."""
        return self.min

    @property
    def max_val(self) -> float:
        """Alias for maximum value."""
        return self.max


class FailedIterationDescriptor(BaseModel):
    """Descriptor capturing context for an iteration that failed to execute."""

    dataset_name: str = Field(..., description="Target dataset identifier.")
    model_name: str = Field(..., description="Target model identifier.")
    iteration_index: int = Field(
        ...,
        description="1-indexed iteration number.",
    )
    target_dir: Path = Field(
        ...,
        description="Target output directory for the iteration.",
    )
    strategy_name: str | None = Field(
        default=None,
        description="Optional strategy identifier if applicable.",
    )
    error_message: str | None = Field(
        default=None,
        description="Optional error message or failure reason.",
    )
