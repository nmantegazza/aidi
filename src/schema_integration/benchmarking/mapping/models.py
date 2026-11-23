"""Data models for schema mapping benchmarking and evaluation (Valentine)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from schema_integration.benchmarking.common.models import (
    TokenPayload,
)
from schema_integration.mapping.models import MappingReport


class ColumnSchemaInfo(BaseModel):
    """Metadata describing a single column in a schema."""

    name: str = Field(..., description="Column name.")
    type: str = Field(..., description="Frictionless or logical data type.")
    constraints: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional constraints on the column.",
    )


class TableSchemaInfo(BaseModel):
    """Metadata describing a table within a dataset."""

    table_name: str = Field(..., description="Name of the table resource.")
    row_count: int = Field(default=0, description="Number of rows/records.")
    column_count: int = Field(default=0, description="Number of columns.")
    columns: list[ColumnSchemaInfo] = Field(
        default_factory=list,
        description="List of column definitions.",
    )


class DatasetSchemaInfo(BaseModel):
    """Comprehensive schema metadata for a benchmark dataset."""

    dataset_name: str = Field(..., description="Dataset name.")
    domain: str = Field(default="Unknown", description="Domain of dataset.")
    scenario: str = Field(
        default="Unknown",
        description="Relational scenario.",
    )
    category: str = Field(
        default="single_table",
        description="Benchmark category: 'single_table' or 'multi_table'.",
    )
    source_table: TableSchemaInfo | None = Field(
        default=None,
        description="Primary source table schema (single-table legacy).",
    )
    target_table: TableSchemaInfo | None = Field(
        default=None,
        description="Primary target table schema (single-table legacy).",
    )
    source_tables: list[TableSchemaInfo] = Field(
        default_factory=list,
        description="All source tables in dataset.",
    )
    target_tables: list[TableSchemaInfo] = Field(
        default_factory=list,
        description="All target tables in dataset.",
    )
    ground_truth_pairs: list[tuple[str, str]] = Field(
        default_factory=list,
        description="List of ground truth (source_col, target_col) pairs.",
    )


class FieldMatchInspection(BaseModel):
    """Detailed alignment and mapping inspection for a single target column."""

    target_column: str = Field(..., description="Target column name.")
    target_type: str | None = Field(
        default=None,
        description="Target column data type.",
    )
    expected_source_columns: list[str] = Field(
        default_factory=list,
        description="Expected ground truth source column(s).",
    )
    predicted_source_columns: list[str] = Field(
        default_factory=list,
        description="Source column(s) predicted by model/baseline.",
    )
    status: str = Field(
        ...,
        description=(
            "Match status: MATCH (TP), MISMATCH (FP), MISSED (FN), or UNMAPPED."
        ),
    )
    transformations: list[dict[str, Any]] = Field(
        default_factory=list,
        description="List of transformations applied to map to this target.",
    )


class MatchMetrics(BaseModel):
    """Container for schema matching precision, recall, and F1 metrics."""

    precision: float = Field(
        ...,
        description="Precision score (TP / (TP + FP)).",
    )
    recall: float = Field(
        ...,
        description="Recall score (TP / (TP + FN)).",
    )
    f1: float = Field(
        ...,
        description="Harmonic mean of precision and recall.",
    )
    true_positives: int = Field(
        ...,
        description="Count of correctly predicted column pairs.",
    )
    false_positives: int = Field(
        ...,
        description="Count of incorrectly predicted column pairs.",
    )
    false_negatives: int = Field(
        ...,
        description="Count of gold standard pairs missed by the model.",
    )
    predicted_pairs_count: int = Field(
        ...,
        description="Total number of predicted column pairs.",
    )
    gold_pairs_count: int = Field(
        ...,
        description="Total number of ground truth column pairs.",
    )
    tp_pairs: list[tuple[str, str]] = Field(
        default_factory=list,
        description="List of correctly predicted (source_col, target_col) pairs.",
    )
    fp_pairs: list[tuple[str, str]] = Field(
        default_factory=list,
        description="List of incorrectly predicted (source_col, target_col) pairs.",
    )
    fn_pairs: list[tuple[str, str]] = Field(
        default_factory=list,
        description="List of missed ground truth (source_col, target_col) pairs.",
    )


class BenchmarkExperimentConfig(BaseModel):
    """Provenance and configuration settings for a benchmark experiment."""

    prompt_template_snapshot: str = Field(
        ...,
        description="Exact prompt template text used for schema mapping.",
    )
    instance_preview_included: bool = Field(
        default=False,
        description="Whether data instance previews were included in prompt.",
    )
    provider: str = Field(..., description="LLM provider name.")
    model_name: str = Field(..., description="LLM model identifier.")
    temperature: float | None = Field(
        default=None,
        description="Sampling temperature.",
    )
    max_retries: int = Field(
        default=2,
        description="Maximum retry attempts configured for the agent.",
    )


class IterationResult(BaseModel):
    """Result of a single model run iteration on a dataset."""

    iteration_index: int = Field(
        ...,
        description="1-based iteration index.",
    )
    category: str = Field(
        default="single_table",
        description="Benchmark category: 'single_table' or 'multi_table'.",
    )
    metrics: MatchMetrics = Field(
        ...,
        description="Evaluation metrics for this iteration.",
    )
    latency_seconds: float = Field(
        ...,
        description="Execution latency in seconds.",
    )
    token_usage: TokenPayload = Field(
        default_factory=TokenPayload,
        description="Token consumption.",
    )
    predicted_pairs: list[tuple[str, str]] = Field(
        default_factory=list,
        description="List of predicted (source_col, target_col) pairs.",
    )
    tp_pairs: list[tuple[str, str]] = Field(
        default_factory=list,
        description="True positive match pairs.",
    )
    fp_pairs: list[tuple[str, str]] = Field(
        default_factory=list,
        description="False positive match pairs.",
    )
    fn_pairs: list[tuple[str, str]] = Field(
        default_factory=list,
        description="False negative match pairs.",
    )
    transformation_counts: dict[str, int] = Field(
        default_factory=dict,
        description="Distribution of predicted transformation types.",
    )
    mapping_report: MappingReport | None = Field(
        default=None,
        description="Complete MappingReport produced by the model.",
    )
    field_inspections: list[FieldMatchInspection] = Field(
        default_factory=list,
        description="Per-target-field alignment and transformation inspections.",
    )
    retry_count: int = Field(
        default=0,
        description="Number of retries triggered during this iteration.",
    )
    retry_log: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Structured log of retry events during this iteration.",
    )
    error_message: str | None = Field(
        default=None,
        description="Optional error message if this iteration encountered an exception.",
    )


class AggregatedMetrics(BaseModel):
    """Aggregated statistics across multiple iterations."""

    precision_mean: float = Field(..., description="Mean precision.")
    precision_std: float = Field(..., description="Standard dev of precision.")
    recall_mean: float = Field(..., description="Mean recall.")
    recall_std: float = Field(..., description="Standard dev of recall.")
    f1_mean: float = Field(..., description="Mean F1-score.")
    f1_std: float = Field(..., description="Standard dev of F1-score.")
    latency_mean_sec: float = Field(..., description="Mean latency in sec.")
    latency_std_sec: float = Field(..., description="Std dev of latency.")
    total_tokens: int = Field(..., description="Total tokens across runs.")
    estimated_cost_usd: float = Field(
        default=0.0,
        description="Estimated cumulative inference cost in USD.",
    )


class DatasetBenchmarkResult(BaseModel):
    """Evaluation result for a specific dataset and model across iterations."""

    dataset_name: str = Field(..., description="Dataset name.")
    domain: str = Field(..., description="Benchmark domain.")
    scenario: str = Field(..., description="Relational scenario.")
    category: str = Field(
        default="single_table",
        description="Benchmark category: 'single_table' or 'multi_table'.",
    )
    schema_info: DatasetSchemaInfo | None = Field(
        default=None,
        description="Dataset schema definition and record counts.",
    )
    model_name: str = Field(..., description="Evaluated LLM model name.")
    iterations: int = Field(..., description="Number of executed iterations.")
    aggregated_metrics: AggregatedMetrics = Field(
        ...,
        description="Aggregated metrics across iterations.",
    )
    iteration_results: list[IterationResult] = Field(
        default_factory=list,
        description="Individual iteration results.",
    )
    total_retries: int = Field(
        default=0,
        description="Total retries triggered across all iterations.",
    )
    experiment_config: BenchmarkExperimentConfig | None = Field(
        default=None,
        description="Experiment configuration and prompt snapshot.",
    )

    @property
    def total_iterations(self) -> int:
        """Total iterations recorded."""
        return len(self.iteration_results)

    @property
    def successful_iterations(self) -> int:
        """Count of successful iterations without errors."""
        return sum(1 for it in self.iteration_results if not it.error_message)

    @property
    def failed_iterations(self) -> int:
        """Count of failed iterations with errors."""
        return sum(1 for it in self.iteration_results if it.error_message)

    @property
    def failed_iteration_indices(self) -> list[int]:
        """1-based indices of failed iterations."""
        return [
            it.iteration_index
            for it in self.iteration_results
            if it.error_message
        ]

    @property
    def status(self) -> str:
        """Formatted status string: SUCCESS, PARTIAL, or FAILED."""
        total = self.total_iterations
        succ = self.successful_iterations
        if total == 0:
            return "NO_RUNS"
        if succ == total:
            return f"SUCCESS ({succ}/{total})"
        if succ == 0:
            return f"FAILED (0/{total})"
        return f"PARTIAL ({succ}/{total})"


class BaselineResult(BaseModel):
    """Evaluation result for a non-LLM or classical baseline algorithm."""

    baseline_name: str = Field(..., description="Baseline algorithm name.")
    dataset_name: str = Field(..., description="Dataset name.")
    domain: str = Field(default="Unknown", description="Benchmark domain.")
    scenario: str = Field(
        default="Unknown",
        description="Relational scenario.",
    )
    category: str = Field(
        default="single_table",
        description="Benchmark category: 'single_table' or 'multi_table'.",
    )
    schema_info: DatasetSchemaInfo | None = Field(
        default=None,
        description="Dataset schema definition and record counts.",
    )
    metrics: MatchMetrics = Field(..., description="Evaluation metrics.")
    latency_seconds: float = Field(
        ...,
        description="Execution latency in seconds.",
    )
    predicted_pairs: list[tuple[str, str]] = Field(
        default_factory=list,
        description="List of predicted (source_col, target_col) pairs.",
    )
    tp_pairs: list[tuple[str, str]] = Field(
        default_factory=list,
        description="True positive match pairs.",
    )
    fp_pairs: list[tuple[str, str]] = Field(
        default_factory=list,
        description="False positive match pairs.",
    )
    fn_pairs: list[tuple[str, str]] = Field(
        default_factory=list,
        description="False negative match pairs.",
    )
    field_inspections: list[FieldMatchInspection] = Field(
        default_factory=list,
        description="Per-target-field alignment inspections.",
    )


class BenchmarkReport(BaseModel):
    """Root model representing a full schema integration benchmark run."""

    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO timestamp of the benchmark run.",
    )
    configuration: dict[str, Any] = Field(
        default_factory=dict,
        description="CLI configuration parameters.",
    )
    experiment_config: BenchmarkExperimentConfig | None = Field(
        default=None,
        description="Global experiment configuration snapshot.",
    )
    dataset_results: list[DatasetBenchmarkResult] = Field(
        default_factory=list,
        description="LLM dataset benchmark results.",
    )
    baseline_results: list[BaselineResult] = Field(
        default_factory=list,
        description="Classical baseline results.",
    )
