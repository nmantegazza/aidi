"""Resilience, run directory resolution, and failure recovery utilities.

Provides mechanisms to find failed benchmark iterations, re-execute them,
and merge new results into existing artifact directories in-place.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from shared.benchmarking import RunResilienceHelper

from .models import (
    ERDatasetMetrics,
    ERIterationMetrics,
    RunStatus,
    compute_mean_std,
)

logger = logging.getLogger(__name__)


def resolve_run_directory(
    run_target: str | Path,
    base_dir: Path,
    fallback_dirs: list[Path] | None = None,
) -> Path:
    """Resolves a target run directory path from an ID, path, or 'latest' alias.

    Delegates to shared.benchmarking.RunResilienceHelper.resolve_run_dir.
    """
    return RunResilienceHelper.resolve_run_dir(
        run_target=run_target,
        base_dir=base_dir,
        fallback_dirs=fallback_dirs,
    )


def find_failed_iterations(
    run_dir: Path,
    dataset_filter: list[str] | None = None,
    model_filter: list[str] | None = None,
    strategy_filter: list[str] | None = None,
    entity_filter: list[str] | None = None,
) -> list[tuple[str, str, int, Path]]:
    """Scans a run directory to identify all failed execution iterations.

    Args:
        run_dir: Path to the benchmark run root.
        dataset_filter: Optional list of dataset names to restrict search.
        model_filter: Optional list of model slugs/names to restrict search.
        strategy_filter: Optional list of strategy slugs to restrict search.
        entity_filter: Generic filter matching either model or strategy slugs.

    Returns:
        List of tuples: (dataset_name, entity_name, iteration_index, entity_dir)
    """
    datasets_dir = run_dir / "datasets"
    failed_items: list[tuple[str, str, int, Path]] = []

    if not datasets_dir.exists():
        return failed_items

    active_entity_filter = entity_filter or strategy_filter or model_filter

    for metrics_file in sorted(datasets_dir.glob("**/metrics.json")):
        entity_dir = metrics_file.parent
        rel_parts = entity_dir.relative_to(datasets_dir).parts
        if len(rel_parts) < 2:
            continue
        ds_name = rel_parts[0]
        entity_slug = rel_parts[-1]

        if dataset_filter and ds_name not in dataset_filter:
            continue
        if active_entity_filter and entity_slug not in active_entity_filter:
            continue

        try:
            content = metrics_file.read_text(encoding="utf-8")
            data = json.loads(content)
        except (json.JSONDecodeError, OSError, ValueError) as err:
            logger.warning(
                "Failed to parse metrics file %s: %s", metrics_file, err
            )
            continue

        iterations = data.get("iterations", [])
        for it in iterations:
            status = it.get("status")
            if (
                status
                and status != RunStatus.SUCCESS.value
                and status != RunStatus.SUCCESS
            ):
                idx = it.get("iteration_index", 1)
                failed_items.append(
                    (ds_name, entity_slug, idx, entity_dir)
                )

    return failed_items


def merge_iteration_result(
    existing_dm: ERDatasetMetrics,
    new_metric: ERIterationMetrics,
) -> ERDatasetMetrics:
    """Merges a newly executed iteration into an existing dataset metrics container.

    Replaces the previous failed iteration result, recalculates mean ± std
    statistics, and aggregates token usage.

    Args:
        existing_dm: The current dataset metrics container.
        new_metric: The new iteration metric to merge.

    Returns:
        Updated ERDatasetMetrics instance.
    """
    updated_iterations: list[ERIterationMetrics] = []
    replaced = False

    for it in existing_dm.iterations:
        if it.iteration_index == new_metric.iteration_index:
            updated_iterations.append(new_metric)
            replaced = True
        else:
            updated_iterations.append(it)

    if not replaced:
        updated_iterations.append(new_metric)

    updated_iterations.sort(key=lambda it: it.iteration_index)
    existing_dm.iterations = updated_iterations

    # Recompute aggregates across successful iterations
    successful = [
        it for it in updated_iterations if it.status == RunStatus.SUCCESS
    ]

    f1_stats = compute_mean_std([it.f1 for it in successful])
    prec_stats = compute_mean_std([it.precision for it in successful])
    rec_stats = compute_mean_std([it.recall for it in successful])
    pr_stats = compute_mean_std([it.pairs_recall for it in successful])
    rr_stats = compute_mean_std([it.reduction_ratio for it in successful])
    lat_stats = compute_mean_std([it.latency_seconds for it in successful])

    existing_dm.mean_f1 = f1_stats.mean
    existing_dm.std_f1 = f1_stats.std
    existing_dm.mean_precision = prec_stats.mean
    existing_dm.std_precision = prec_stats.std
    existing_dm.mean_recall = rec_stats.mean
    existing_dm.std_recall = rec_stats.std
    existing_dm.mean_pairs_recall = pr_stats.mean
    existing_dm.std_pairs_recall = pr_stats.std
    existing_dm.mean_reduction_ratio = rr_stats.mean
    existing_dm.std_reduction_ratio = rr_stats.std
    existing_dm.mean_latency = lat_stats.mean
    existing_dm.std_latency = lat_stats.std

    existing_dm.prompt_tokens = sum(
        it.token_usage.prompt_tokens for it in updated_iterations
    )
    existing_dm.completion_tokens = sum(
        it.token_usage.completion_tokens for it in updated_iterations
    )
    existing_dm.total_tokens = sum(
        it.token_usage.total_tokens for it in updated_iterations
    )
    existing_dm.estimated_cost_usd = round(
        sum(it.token_usage.cost_usd or 0.0 for it in updated_iterations), 6
    )

    return existing_dm
