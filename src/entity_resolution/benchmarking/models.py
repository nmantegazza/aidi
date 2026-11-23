"""Benchmarking data models for Entity Resolution.

Re-exports unified models from common.models and maintains backwards
compatibility for existing benchmark report structures.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field, model_validator

from entity_resolution.evaluation_models import EntityResEvalReport

from .common.models import (
    AggregatedMetricStats,
    ERDatasetMetrics,
    ERFlakinessAnalysis,
    ERIterationMetrics,
    ERRunSummary,
    RunStatus,
    TokenUsage,
    compute_mean_std,
)


class BenchmarkConfig(BaseModel):
    """Configuration for Entity Resolution benchmark runs."""

    models: list[str] = Field(
        default_factory=lambda: ["google-cloud:gemini-3.8-flash"]
    )
    runs: int = 1
    iterations: int = 1
    datasets: list[str] | None = None
    dataset_domain: str = Field(
        default="all",
        description=(
            "Domain of datasets: 'e-commerce', 'citations', 'restaurants', "
            "'movies', 'synthetic', or 'all'"
        ),
    )
    save_dataset_outputs: bool = Field(
        default=True,
        description="Whether to export per-dataset classified CSVs and reports.",
    )
    no_pair_csvs: bool = Field(
        default=False,
        description="Skip generating large classified pair CSV files.",
    )
    output_dir: Path | None = Field(
        default=None,
        description="Optional custom root directory for benchmark artifacts.",
    )

    @model_validator(mode="before")
    @classmethod
    def sync_runs_and_iterations(cls, data: dict) -> dict:
        """Synchronizes runs and iterations parameters."""
        if isinstance(data, dict):
            if "iterations" in data and "runs" not in data:
                data["runs"] = data["iterations"]
            elif "runs" in data and "iterations" not in data:
                data["iterations"] = data["runs"]
            elif (
                "iterations" in data
                and "runs" in data
                and data["iterations"] != data["runs"]
            ):
                data["runs"] = data["iterations"]
        return data


class EntityResFailedRunReport(BaseModel):
    """Legacy report representing a failed run during benchmarking."""

    timestamp: datetime = Field(default_factory=datetime.now)
    model_name: str
    dataset_name: str
    error: str
    traceback: str | None = None


class DatasetModelResult(BaseModel):
    """Legacy result container aggregating runs for a model on a dataset."""

    mean_metrics: dict[str, float]
    std_metrics: dict[str, float]
    runs: list[EntityResEvalReport | EntityResFailedRunReport]


class EntityResBenchmarkReport(BaseModel):
    """Legacy report representing aggregated benchmark results."""

    timestamp: datetime = Field(default_factory=datetime.now)
    config: BenchmarkConfig
    dataset_reports: dict[str, dict[str, DatasetModelResult]]


__all__ = [
    "AggregatedMetricStats",
    "BenchmarkConfig",
    "DatasetModelResult",
    "ERDatasetMetrics",
    "ERFlakinessAnalysis",
    "ERIterationMetrics",
    "ERRunSummary",
    "EntityResBenchmarkReport",
    "EntityResFailedRunReport",
    "RunStatus",
    "TokenUsage",
    "compute_mean_std",
]
