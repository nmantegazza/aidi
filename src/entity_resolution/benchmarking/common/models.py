"""Shared data models and statistics for Entity Resolution benchmarking.

Provides containers for iteration telemetry, statistical aggregations,
flakiness analysis, and benchmark run summaries.
"""

from datetime import datetime

from pydantic import BaseModel, Field

from shared.benchmarking import (
    AggregatedMetricStats,
    RunStatus,
    TokenPayload,
    TokenUsage,
    compute_mean_std,
)


class ERIterationMetrics(BaseModel):
    """Metrics and telemetry for a single execution iteration."""

    iteration_index: int
    status: RunStatus = RunStatus.SUCCESS
    error_message: str | None = None
    traceback: str | None = None

    # Matching metrics
    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0
    tp: int = 0
    fp: int = 0
    fn: int = 0
    tn: int | None = None
    support: int = 0

    # Indexing / blocking metrics
    candidates: int = 0
    pairs_recall: float = 0.0
    reduction_ratio: float = 0.0

    # Telemetry
    latency_seconds: float = 0.0
    token_usage: TokenUsage = Field(default_factory=TokenUsage)


class ERFlakinessAnalysis(BaseModel):
    """Analysis of deterministic stability across stochastic iterations."""

    consistent_matches: list[tuple[str, str]] = Field(default_factory=list)
    flaky_matches: dict[str, float] = Field(default_factory=dict)
    stability_ratio: float = 1.0


class ERDatasetMetrics(BaseModel):
    """Aggregated multi-iteration metrics for a dataset and model pair."""

    dataset_name: str
    domain: str = "general"
    num_rows_a: int = 0
    num_rows_b: int = 0
    ground_truth_count: int = 0
    iterations: list[ERIterationMetrics] = Field(default_factory=list)

    # Aggregated matching metrics
    mean_precision: float = 0.0
    std_precision: float = 0.0
    mean_recall: float = 0.0
    std_recall: float = 0.0
    mean_f1: float = 0.0
    std_f1: float = 0.0

    # Aggregated indexing metrics
    mean_pairs_recall: float = 0.0
    std_pairs_recall: float = 0.0
    mean_reduction_ratio: float = 0.0
    std_reduction_ratio: float = 0.0

    # Aggregated latency & resources
    mean_latency: float = 0.0
    std_latency: float = 0.0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0

    flakiness_analysis: ERFlakinessAnalysis | None = None

    @property
    def successful_iterations_count(self) -> int:
        """Returns the number of successful iterations."""
        return sum(
            1 for it in self.iterations if it.status == RunStatus.SUCCESS
        )

    @property
    def failed_iterations_count(self) -> int:
        """Returns the number of failed iterations."""
        return sum(
            1 for it in self.iterations if it.status == RunStatus.FAILED
        )


class ERRunSummary(BaseModel):
    """Master container summarizing an entire benchmark run."""

    run_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    models: list[str] = Field(default_factory=list)
    datasets: list[str] = Field(default_factory=list)
    iterations: int = 1
    matrix: dict[str, dict[str, ERDatasetMetrics]] = Field(default_factory=dict)
    failed_iterations_count: int = 0
    total_iterations_count: int = 0


__all__ = [
    "AggregatedMetricStats",
    "ERDatasetMetrics",
    "ERFlakinessAnalysis",
    "ERIterationMetrics",
    "ERRunSummary",
    "RunStatus",
    "TokenPayload",
    "TokenUsage",
    "compute_mean_std",
]

