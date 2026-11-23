"""Data models for schema alignment benchmarking and reference-free evaluation."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from schema_integration.alignment.models import AlignmentReport
from schema_integration.benchmarking.common.models import TokenUsage


class DetectedCloneRecord(BaseModel):
    """Itemized record of a flagged intra-table semantic clone column pair."""

    target_table: str = Field(
        ...,
        description="Target relation containing candidate duplicate columns.",
    )
    column_a: str = Field(
        ...,
        description="First candidate duplicate column name.",
    )
    column_b: str = Field(
        ...,
        description="Second candidate duplicate column name.",
    )
    source_prov_a: list[str] = Field(
        default_factory=list,
        description="Source provenance references for column A.",
    )
    source_prov_b: list[str] = Field(
        default_factory=list,
        description="Source provenance references for column B.",
    )
    data_type: str = Field(
        ...,
        description="Compatible Frictionless data type.",
    )
    similarity_score: float = Field(
        ...,
        description="Dense semantic cosine similarity score.",
    )
    description_a: str | None = Field(
        default=None,
        description="Column A docstring / description.",
    )
    description_b: str | None = Field(
        default=None,
        description="Column B docstring / description.",
    )


class SynonymPair(BaseModel):
    """Normalized cross-source synonym attribute pair."""

    source_a: str = Field(
        ...,
        description="Qualified attribute in Source A (table.column).",
    )
    source_b: str = Field(
        ...,
        description="Qualified attribute in Source B (table.column).",
    )

    @property
    def canonical_key(self) -> tuple[str, str]:
        """Return standardized lowercase tuple."""
        return (self.source_a.strip().lower(), self.source_b.strip().lower())


class AttributeConsensusPair(BaseModel):
    """Pairwise cross-source attribute alignment consensus across iterations."""

    source_col_a: str = Field(
        ...,
        description="Qualified attribute in Source A (table.column).",
    )
    source_col_b: str = Field(
        ...,
        description="Qualified attribute in Source B (table.column).",
    )
    coaligned_runs: int = Field(
        ...,
        description="Number of benchmark iterations where columns were co-aligned.",
    )
    total_runs: int = Field(
        ...,
        description="Total evaluated benchmark iterations.",
    )
    agreement_rate: float = Field(
        ...,
        description="Fraction of iterations where pair was co-aligned [0.0, 1.0].",
    )
    status: str = Field(
        default="STABLE",
        description="Consensus classification: 'STABLE' (1.0), 'VOLATILE' (<1.0), or 'UNALIGNED' (0.0).",
    )
    target_field_names: list[str] = Field(
        default_factory=list,
        description="Distinct unified target field names assigned across iterations.",
    )


class TopologicalDriftStats(BaseModel):
    """Structural and relational partitioning variation across iterations."""

    table_counts: list[int] = Field(
        default_factory=list,
        description="Target table counts per iteration.",
    )
    mean_table_count: float = Field(
        default=0.0,
        description="Mean table count across iterations.",
    )
    std_table_count: float = Field(
        default=0.0,
        description="Standard deviation of table counts across iterations.",
    )
    fk_counts: list[int] = Field(
        default_factory=list,
        description="Declared foreign key counts per iteration.",
    )
    fk_edge_stability: float = Field(
        default=1.0,
        description="Average pairwise Jaccard similarity of FK edge sets across iterations [0, 1].",
    )


class MultiIterationConsistencyReport(BaseModel):
    """Aggregated consistency, consensus, and drift analysis across iterations."""

    consensus_pairs: list[AttributeConsensusPair] = Field(
        default_factory=list,
        description="Cross-source attribute pairs and their co-alignment rates.",
    )
    overall_consensus_ratio: float = Field(
        default=1.0,
        description="Ratio of stable pairs (100% agreement) to total co-aligned pairs [0, 1].",
    )
    stable_pairs_count: int = Field(
        default=0,
        description="Total cross-source pairs aligned in 100% of iterations.",
    )
    volatile_pairs_count: int = Field(
        default=0,
        description="Total cross-source pairs aligned in <100% of iterations.",
    )
    topological_drift: TopologicalDriftStats = Field(
        default_factory=TopologicalDriftStats,
        description="Table partitioning and relational graph edge stability.",
    )
    clone_flakiness: dict[str, Any] = Field(
        default_factory=dict,
        description="Intra-table clone stability statistics.",
    )


class StructuralIntegrityStats(BaseModel):
    """Integrity audit statistics for generated target schema."""

    pk_validity: float = Field(
        ...,
        description="Ratio of tables with valid declared primary keys [0, 1].",
    )
    fk_validity: float = Field(
        ...,
        description=(
            "Ratio of declared foreign keys pointing to valid resources and "
            "columns [0, 1]."
        ),
    )
    source_fk_preservation: float = Field(
        default=1.0,
        description="Ratio of source FK relationships preserved in target [0, 1].",
    )
    score: float = Field(
        ...,
        description="Combined Structural Integrity score (pk_validity * fk_validity * source_fk_preservation).",
    )
    total_tables: int = Field(default=0, description="Total target tables.")
    total_fks: int = Field(default=0, description="Total declared FKs.")
    total_source_fks: int = Field(
        default=0, description="Total source foreign keys in Source A and B."
    )
    preserved_source_fks: int = Field(
        default=0, description="Source foreign keys preserved in target schema."
    )
    broken_fks: list[str] = Field(
        default_factory=list,
        description="Details of broken foreign key references in target schema.",
    )
    unpreserved_source_fks: list[str] = Field(
        default_factory=list,
        description="Details of source foreign keys not preserved in target schema.",
    )


class AlignmentIterationMetrics(BaseModel):
    """Evaluation metrics for a single reference-free schema alignment iteration."""

    iteration_index: int = Field(
        default=1,
        description="1-based iteration index.",
    )
    completeness: float = Field(
        ...,
        description="Information preservation score Cov_attr [0, 1].",
    )
    structural_integrity: float = Field(
        ...,
        description="Structural and referential integrity score S_rel [0, 1].",
    )
    intra_table_uniqueness: float = Field(
        default=1.0,
        description="Intra-table non-redundancy score M_unique [0, 1].",
    )
    unmapped_source_columns: list[str] = Field(
        default_factory=list,
        description="Source columns not referenced in target schema provenance.",
    )
    broken_fks: list[str] = Field(
        default_factory=list,
        description="Itemized list of broken foreign key reference alerts in target.",
    )
    unpreserved_source_fks: list[str] = Field(
        default_factory=list,
        description="Itemized list of source FK relationships missing in target.",
    )
    detected_clones: list[DetectedCloneRecord] = Field(
        default_factory=list,
        description="Itemized list of flagged intra-table semantic clones.",
    )
    structural_stats: StructuralIntegrityStats = Field(
        ...,
        description="Detailed primary, foreign key, and relational preservation stats.",
    )
    latency_seconds: float = Field(
        default=0.0,
        description="Execution latency in seconds.",
    )
    token_usage: TokenUsage = Field(
        default_factory=TokenUsage,
        description="LLM token usage telemetry.",
    )
    alignment_report: AlignmentReport | None = Field(
        default=None,
        description="Complete AlignmentReport generated by the model.",
    )
    error_message: str | None = Field(
        default=None,
        description="Error message if iteration failed.",
    )

    @property
    def prompt_tokens(self) -> int:
        """Prompt tokens consumed in this iteration."""
        return self.token_usage.prompt_tokens

    @property
    def completion_tokens(self) -> int:
        """Completion tokens consumed in this iteration."""
        return self.token_usage.completion_tokens

    @property
    def total_tokens(self) -> int:
        """Total tokens consumed in this iteration."""
        return self.token_usage.total_tokens


class AlignmentDatasetMetrics(BaseModel):
    """Aggregated reference-free metrics for a dataset across iterations."""

    dataset_name: str = Field(..., description="Dataset name.")
    domain: str = Field(default="Unknown", description="Domain of dataset.")
    table_count_a: int = Field(default=0, description="Tables in source A.")
    table_count_b: int = Field(default=0, description="Tables in source B.")
    column_count_a: int = Field(default=0, description="Columns in source A.")
    column_count_b: int = Field(default=0, description="Columns in source B.")
    ground_truth_count: int = Field(
        default=0,
        description="Total gold standard synonym pairs (telemetry).",
    )
    iterations: list[AlignmentIterationMetrics] = Field(
        default_factory=list,
        description="Individual iteration results.",
    )
    mean_completeness: float = Field(..., description="Mean completeness.")
    std_completeness: float = Field(default=0.0, description="Std completeness.")
    mean_structural_integrity: float = Field(
        ...,
        description="Mean structural integrity.",
    )
    std_structural_integrity: float = Field(
        default=0.0,
        description="Std structural integrity.",
    )
    mean_intra_table_uniqueness: float = Field(
        default=1.0,
        description="Mean intra-table uniqueness.",
    )
    std_intra_table_uniqueness: float = Field(
        default=0.0,
        description="Std intra-table uniqueness.",
    )
    mean_latency_sec: float = Field(..., description="Mean latency in sec.")
    std_latency_sec: float = Field(
        default=0.0,
        description="Std latency in sec.",
    )
    prompt_tokens: int = Field(default=0, description="Total prompt tokens.")
    completion_tokens: int = Field(default=0, description="Total completion tokens.")
    total_tokens: int = Field(default=0, description="Total tokens consumed.")
    estimated_cost_usd: float = Field(
        default=0.0,
        description="Estimated cumulative inference cost in USD.",
    )
    flakiness_analysis: dict[str, Any] = Field(
        default_factory=dict,
        description="Consistency analysis across iterations.",
    )
    consistency_analysis: MultiIterationConsistencyReport | None = Field(
        default=None,
        description="Detailed cross-iteration consensus and topological drift metrics.",
    )

    @property
    def total_iterations(self) -> int:
        """Total iterations recorded."""
        return len(self.iterations)

    @property
    def successful_iterations(self) -> int:
        """Count of successful iterations without errors."""
        return sum(1 for it in self.iterations if not it.error_message)

    @property
    def failed_iterations(self) -> int:
        """Count of failed iterations with errors."""
        return sum(1 for it in self.iterations if it.error_message)

    @property
    def failed_iteration_indices(self) -> list[int]:
        """1-based indices of failed iterations."""
        return [it.iteration_index for it in self.iterations if it.error_message]

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


class MacroModelSummary(BaseModel):
    """Macro-averaged performance and efficiency summary for a model."""

    model_name: str = Field(..., description="LLM model identifier.")
    completeness: float = Field(default=0.0, description="Macro completeness.")
    structural_integrity: float = Field(
        default=0.0,
        description="Macro structural integrity.",
    )
    intra_table_uniqueness: float = Field(
        default=0.0,
        description="Macro intra-table uniqueness.",
    )
    mean_latency_sec: float = Field(default=0.0, description="Average latency in sec.")
    prompt_tokens: int = Field(default=0, description="Total prompt tokens.")
    completion_tokens: int = Field(default=0, description="Total completion tokens.")
    total_tokens: int = Field(default=0, description="Total tokens.")
    estimated_cost_usd: float = Field(
        default=0.0,
        description="Estimated cumulative inference cost in USD.",
    )
    successful_runs: int = Field(
        default=0, description="Total successful iterations across datasets."
    )
    failed_runs: int = Field(
        default=0, description="Total failed iterations across datasets."
    )

    @property
    def status(self) -> str:
        """Formatted status string for the model."""
        total = self.successful_runs + self.failed_runs
        if total == 0:
            return "NO_RUNS"
        if self.failed_runs == 0:
            return f"SUCCESS ({self.successful_runs}/{total})"
        if self.successful_runs == 0:
            return f"FAILED (0/{total})"
        return f"PARTIAL ({self.successful_runs}/{total})"


class AlignmentBenchmarkResult(BaseModel):
    """Full benchmark report for schema alignment across a single model."""

    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO timestamp of benchmark run.",
    )
    model_name: str = Field(..., description="Evaluated LLM model name.")
    dataset_results: dict[str, AlignmentDatasetMetrics] = Field(
        default_factory=dict,
        description="Per-dataset aggregated metrics.",
    )
    overall_summary: dict[str, float] = Field(
        default_factory=dict,
        description="Macro-averaged summary scores across all datasets.",
    )


class AlignmentRunSummary(BaseModel):
    """Overarching multi-model schema alignment benchmark summary."""

    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO timestamp of benchmark run.",
    )
    run_id: str = Field(..., description="Unique run identifier folder name.")
    models: list[str] = Field(default_factory=list, description="Evaluated models.")
    iterations: int = Field(default=1, description="Iterations per dataset.")
    macro_summaries: dict[str, MacroModelSummary] = Field(
        default_factory=dict,
        description="Macro summary per model.",
    )
    dataset_results: dict[str, dict[str, AlignmentDatasetMetrics]] = Field(
        default_factory=dict,
        description="Per-dataset, per-model results mapping [dataset][model].",
    )
