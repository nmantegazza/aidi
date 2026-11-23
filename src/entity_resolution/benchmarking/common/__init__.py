"""Shared benchmarking infrastructure for Entity Resolution.

Exports models, reporting formats, and resilience / retry utilities.
"""

from .models import (
    AggregatedMetricStats,
    ERDatasetMetrics,
    ERFlakinessAnalysis,
    ERIterationMetrics,
    ERRunSummary,
    RunStatus,
    TokenUsage,
    compute_mean_std,
)
from .reporting import (
    build_dataset_markdown_report,
    build_run_summary_csv,
    build_run_summary_markdown,
    export_csv,
    export_json,
    format_markdown_table,
    render_rich_table,
)
from .resilience import (
    find_failed_iterations,
    merge_iteration_result,
    resolve_run_directory,
)

__all__ = [
    "AggregatedMetricStats",
    "ERDatasetMetrics",
    "ERFlakinessAnalysis",
    "ERIterationMetrics",
    "ERRunSummary",
    "RunStatus",
    "TokenUsage",
    "build_dataset_markdown_report",
    "build_run_summary_csv",
    "build_run_summary_markdown",
    "compute_mean_std",
    "export_csv",
    "export_json",
    "find_failed_iterations",
    "format_markdown_table",
    "merge_iteration_result",
    "render_rich_table",
    "resolve_run_directory",
]
