"""Data models and statistics for ER matching benchmarking.

Provides containers for iteration telemetry, statistical aggregations,
flakiness analysis, and suite run summaries for matching strategies.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from entity_resolution.models import ClassificationMode
from shared.agents import ExecutionMetadata

from .common.models import (
    AggregatedMetricStats,
    RunStatus,
    TokenUsage,
    compute_mean_std,
)


class MatchingBenchmarkReport(BaseModel):
    """Legacy report container for individual matching strategy benchmark runs."""

    dataset_name: str
    strategy_name: str
    precision: float
    recall: float
    f1_score: float
    tp: int
    fp: int
    fn: int
    tn: int | None = None
    candidate_count: int
    match_ratio: float
    ground_truth_type: str
    execution_time_sec: float
    peak_memory_mb: float
    peak_cpu_percent: float | None = None
    llm_metrics: ExecutionMetadata | None = None


class MatchingLLMInteraction(BaseModel):
    """Container for LLM prompts and responses in matching configuration."""

    system_prompt: str = ""
    user_prompt: str = ""
    response: Any = None
    model_name: str = ""
    provider: str = ""
    execution_time_seconds: float = 0.0
    log_file_path: str | None = None


class MatchingIterationMetrics(BaseModel):
    """Metrics and telemetry for a single matching iteration."""

    iteration_index: int
    status: RunStatus = RunStatus.SUCCESS
    error_message: str | None = None
    traceback: str | None = None

    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0
    tp: int = 0
    fp: int = 0
    fn: int = 0
    tn: int | None = None
    candidate_count: int = 0
    match_ratio: float = 0.0

    # Triage perspective metrics (Ternary mode)
    potential_recall: float | None = None
    potential_f1: float | None = None
    unrecoverable_loss: float | None = None
    llm_workload_ratio: float | None = None
    uncertain_purity: float | None = None
    uncertain_count: int = 0

    execution_time_sec: float = 0.0
    peak_memory_mb: float = 0.0
    peak_cpu_percent: float | None = None
    token_usage: TokenUsage = Field(default_factory=TokenUsage)
    llm_interaction: MatchingLLMInteraction | None = None


class MatchingFlakinessAnalysis(BaseModel):
    """Analysis of deterministic stability across stochastic iterations."""

    consistent_matches_count: int = 0
    flaky_matches_count: int = 0
    stability_ratio: float = 1.0
    flaky_pairs: dict[str, float] = Field(default_factory=dict)


class MatchingDatasetStrategyMetrics(BaseModel):
    """Aggregated multi-iteration metrics for one dataset and strategy."""

    dataset_name: str
    domain: str = ""
    strategy_name: str
    model_name: str
    classification_mode: ClassificationMode = ClassificationMode.TERNARY
    iterations: list[MatchingIterationMetrics] = Field(default_factory=list)

    # Aggregated performance stats
    mean_precision: float = 0.0
    std_precision: float = 0.0
    mean_recall: float = 0.0
    std_recall: float = 0.0
    mean_f1: float = 0.0
    std_f1: float = 0.0
    mean_execution_time: float = 0.0
    std_execution_time: float = 0.0
    mean_memory_mb: float = 0.0
    std_memory_mb: float = 0.0

    # Aggregated triage stats (Ternary mode)
    mean_potential_recall: float | None = None
    std_potential_recall: float | None = None
    mean_potential_f1: float | None = None
    std_potential_f1: float | None = None
    mean_llm_workload_ratio: float | None = None
    mean_unrecoverable_loss: float | None = None
    mean_uncertain_purity: float | None = None

    # Aggregated telemetry
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0

    flakiness_analysis: MatchingFlakinessAnalysis | None = None
    llm_interaction: MatchingLLMInteraction | None = None

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


class MatchingRunSummary(BaseModel):
    """Overall summary container for an entire matching benchmark run."""

    run_id: str
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    strategies: list[str] = Field(default_factory=list)
    datasets: list[str] = Field(default_factory=list)
    models: list[str] = Field(default_factory=list)
    iterations: int = 1
    matrix: dict[
        str, dict[str, dict[str, MatchingDatasetStrategyMetrics]]
    ] = Field(default_factory=dict)
    failed_iterations_count: int = 0
    total_iterations_count: int = 0


__all__ = [
    "AggregatedMetricStats",
    "ClassificationMode",
    "MatchingBenchmarkReport",
    "MatchingDatasetStrategyMetrics",
    "MatchingFlakinessAnalysis",
    "MatchingIterationMetrics",
    "MatchingLLMInteraction",
    "MatchingRunSummary",
    "RunStatus",
    "TokenUsage",
    "compute_mean_std",
]
