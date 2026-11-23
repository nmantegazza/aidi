"""Pydantic models for data fusion benchmarking metrics, iterations, and results."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from shared.benchmarking import (
    AggregatedMetricStats,
    RunStatus,
    TokenPayload,
    compute_mean_std,
)


class MetricsPayload(BaseModel):
    """Container for precision, recall, and F1 evaluation metrics."""

    precision: float = Field(default=0.0, description="Precision score.")
    recall: float = Field(default=0.0, description="Recall score.")
    f1: float = Field(
        default=0.0, description="Harmonic mean of precision and recall."
    )


class FusionIterationMetrics(BaseModel):
    """Metrics and telemetry for a single data fusion execution iteration."""

    iteration_index: int = Field(
        ..., description="1-indexed iteration number."
    )
    status: RunStatus = Field(
        default=RunStatus.SUCCESS, description="Execution status."
    )
    error_message: str | None = Field(
        default=None, description="Error message if iteration failed."
    )
    traceback: str | None = Field(
        default=None, description="Full traceback string if iteration failed."
    )
    absolute_metrics: MetricsPayload = Field(
        default_factory=MetricsPayload,
        description="Metrics against Absolute Ground Truth.",
    )
    reachable_metrics: MetricsPayload = Field(
        default_factory=MetricsPayload,
        description="Metrics against Reachable Ground Truth.",
    )
    latency_seconds: float = Field(
        default=0.0, description="Total execution latency in seconds."
    )
    profiling_latency_seconds: float = Field(
        default=0.0, description="Profiling latency in seconds."
    )
    policy_synthesis_latency_seconds: float = Field(
        default=0.0, description="LLM policy synthesis latency in seconds."
    )
    execution_latency_seconds: float = Field(
        default=0.0,
        description="Deterministic fusion execution latency in seconds.",
    )
    llm_call_log_path: str | None = Field(
        default=None, description="Path to raw LLM call JSON log."
    )
    token_usage: TokenPayload = Field(
        default_factory=TokenPayload, description="Token consumption."
    )
    audit_log: dict[str, str] = Field(
        default_factory=dict,
        description="Attribute to applied strategy mapping.",
    )


# Alias for backward compatibility if needed
DatasetResult = FusionIterationMetrics


class FusionDatasetAggregatedMetrics(BaseModel):
    """Aggregated multi-iteration metrics for a dataset and model pair."""

    dataset_id: str = Field(..., description="Dataset identifier.")
    model_name: str = Field(..., description="Model or strategy identifier.")
    status: RunStatus = Field(
        default=RunStatus.SUCCESS, description="Aggregated run status."
    )
    iterations: list[FusionIterationMetrics] = Field(
        default_factory=list, description="All individual iteration metrics."
    )

    # Aggregated Absolute metrics
    mean_abs_precision: float = Field(default=0.0)
    std_abs_precision: float = Field(default=0.0)
    mean_abs_recall: float = Field(default=0.0)
    std_abs_recall: float = Field(default=0.0)
    mean_abs_f1: float = Field(default=0.0)
    std_abs_f1: float = Field(default=0.0)

    # Aggregated Reachable metrics
    mean_reach_precision: float = Field(default=0.0)
    std_reach_precision: float = Field(default=0.0)
    mean_reach_recall: float = Field(default=0.0)
    std_reach_recall: float = Field(default=0.0)
    mean_reach_f1: float = Field(default=0.0)
    std_reach_f1: float = Field(default=0.0)

    # Aggregated Latency
    mean_latency_seconds: float = Field(default=0.0)
    std_latency_seconds: float = Field(default=0.0)
    mean_synthesis_latency_seconds: float = Field(default=0.0)
    std_synthesis_latency_seconds: float = Field(default=0.0)

    # Aggregated Tokens
    prompt_tokens: int = Field(default=0)
    completion_tokens: int = Field(default=0)
    cached_tokens: int = Field(default=0)
    reasoning_tokens: int = Field(default=0)
    total_tokens: int = Field(default=0)
    estimated_cost_usd: float = Field(default=0.0)

    # Flakiness and Consensus
    strategy_consensus_ratio: float = Field(
        default=1.0,
        description="Proportion of attribute decisions with multi-iteration consensus.",
    )
    flaky_attributes: dict[str, float] = Field(
        default_factory=dict,
        description="Attributes with varying chosen strategies across iterations.",
    )

    @property
    def successful_iterations_count(self) -> int:
        """Count of successful iterations."""
        return sum(
            1 for it in self.iterations if it.status == RunStatus.SUCCESS
        )

    @property
    def failed_iterations_count(self) -> int:
        """Count of failed iterations."""
        return sum(
            1 for it in self.iterations if it.status != RunStatus.SUCCESS
        )


class BenchmarkRunSummary(BaseModel):
    """Root model for exporting benchmark runs and configuration."""

    run_id: str = Field(..., description="Unique run identifier.")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO timestamp of run.",
    )
    configuration: dict[str, Any] = Field(
        default_factory=dict, description="CLI configuration options."
    )
    models: list[str] = Field(
        default_factory=list, description="Evaluated models and baselines."
    )
    datasets: list[str] = Field(
        default_factory=list, description="Evaluated dataset identifiers."
    )
    iterations: int = Field(
        default=1, description="Number of iterations evaluated."
    )
    # Matrix: dataset_id -> model_name -> metrics
    matrix: dict[str, dict[str, FusionDatasetAggregatedMetrics]] = Field(
        default_factory=dict,
        description="Matrix mapping dataset_id -> model_name -> metrics.",
    )
    failed_iterations_count: int = Field(
        default=0, description="Total count of failed iterations."
    )
    total_iterations_count: int = Field(
        default=0, description="Total count of attempted iterations."
    )


__all__ = [
    "AggregatedMetricStats",
    "BenchmarkRunSummary",
    "DatasetResult",
    "FusionDatasetAggregatedMetrics",
    "FusionIterationMetrics",
    "MetricsPayload",
    "RunStatus",
    "TokenPayload",
    "compute_mean_std",
]
