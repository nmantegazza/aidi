"""Data models and statistics for ER indexing benchmarking.

Provides containers for iteration telemetry, statistical aggregations,
and suite run summaries for indexing/blocking strategies.
"""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field

from entity_resolution.evaluation_models import IndexingBenchmarkReport

from .common.models import (
    AggregatedMetricStats,
    RunStatus,
    TokenUsage,
    compute_mean_std,
)


class IndexIterationMetrics(BaseModel):
    """Metrics and telemetry for a single indexing iteration."""

    iteration_index: int
    status: RunStatus = RunStatus.SUCCESS
    error_message: str | None = None
    traceback: str | None = None

    recall: float = 0.0
    precision: float = 0.0
    reduction_ratio: float = 0.0
    num_candidates: int = 0
    max_possible_pairs: int = 0
    num_true_matches: int = 0
    missed_true_matches: int = 0

    indexing_time_sec: float = 0.0
    peak_memory_mb: float = 0.0
    peak_cpu_percent: float | None = None

    sorting_keys: list[str] | None = None
    window_size: int | None = None
    token_usage: TokenUsage = Field(default_factory=TokenUsage)


class IndexDatasetStrategyMetrics(BaseModel):
    """Aggregated multi-iteration metrics for one dataset and strategy."""

    dataset_name: str
    domain: str = ""
    strategy_name: str
    model_name: str
    iterations: list[IndexIterationMetrics] = Field(default_factory=list)

    # Aggregated performance stats
    mean_recall: float = 0.0
    std_recall: float = 0.0
    mean_precision: float = 0.0
    std_precision: float = 0.0
    mean_reduction_ratio: float = 0.0
    std_reduction_ratio: float = 0.0
    mean_indexing_time: float = 0.0
    std_indexing_time: float = 0.0
    mean_memory_mb: float = 0.0
    std_memory_mb: float = 0.0

    # Aggregated telemetry
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0

    @property
    def successful_iterations_count(self) -> int:
        """Count of iterations that finished successfully."""
        return sum(
            1 for it in self.iterations if it.status == RunStatus.SUCCESS
        )

    @property
    def failed_iterations_count(self) -> int:
        """Count of iterations that failed."""
        return sum(
            1 for it in self.iterations if it.status != RunStatus.SUCCESS
        )


class IndexRunSummary(BaseModel):
    """Overall summary container for an entire indexing benchmark run."""

    run_id: str
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    strategies: list[str] = Field(default_factory=list)
    datasets: list[str] = Field(default_factory=list)
    models: list[str] = Field(default_factory=list)
    iterations: int = 1
    # Matrix: dataset_name -> strategy_name -> metrics
    matrix: dict[str, dict[str, IndexDatasetStrategyMetrics]] = Field(
        default_factory=dict
    )
    failed_iterations_count: int = 0
    total_iterations_count: int = 0


__all__ = [
    "AggregatedMetricStats",
    "IndexDatasetStrategyMetrics",
    "IndexIterationMetrics",
    "IndexRunSummary",
    "IndexingBenchmarkReport",
    "RunStatus",
    "TokenUsage",
    "compute_mean_std",
]
