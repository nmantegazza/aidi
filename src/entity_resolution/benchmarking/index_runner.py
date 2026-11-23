"""CLI runner for benchmarking entity resolution indexing strategies.

Provides multi-iteration execution, failure resilience, automated metric
aggregation, and in-place retry capabilities for indexing strategies.
"""

from __future__ import annotations

import argparse
import asyncio
import gc
import json
import logging
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rich.markup import escape

from entity_resolution.dataset_loader import (
    discover_and_load,
    save_candidate_set,
)
from entity_resolution.indexing_strategies import (
    BaseIndexingStrategy,
    MinHashLSHStrategy,
    QGramIndexStrategy,
    SortedNeighborhoodStrategy,
    TFIDFIndexStrategy,
)
from entity_resolution.metrics import ensure_multiindex
from entity_resolution.models import TableResource
from shared.benchmarking import (
    BenchmarkReportWriter,
    RunLayoutManager,
)
from shared.cleaning.engine import clean_data
from shared.config import config
from shared.console import console
from shared.profiling.engine import DataProfiler
from shared.schema_models import TableField, TableSchema

from .common.models import (
    RunStatus,
    TokenUsage,
    compute_mean_std,
)
from .common.reporting import (
    export_json,
    format_cost_usd,
    format_markdown_table,
    render_rich_table,
)
from .common.resilience import (
    find_failed_iterations,
    resolve_run_directory,
)
from .config_generator import LLMIndexConfigGenerator
from .index_evaluation import IndexingMetricsEvaluator
from .index_models import (
    IndexDatasetStrategyMetrics,
    IndexIterationMetrics,
    IndexRunSummary,
)

logger = logging.getLogger(__name__)

STRATEGY_REGISTRY: dict[str, type[BaseIndexingStrategy]] = {
    "sn": SortedNeighborhoodStrategy,
    "sorted_neighborhood": SortedNeighborhoodStrategy,
    "lsh": MinHashLSHStrategy,
    "minhash_lsh": MinHashLSHStrategy,
    "qgram": QGramIndexStrategy,
    "qgram_index": QGramIndexStrategy,
    "qgram_inverted_index": QGramIndexStrategy,
    "tfidf": TFIDFIndexStrategy,
    "tfidf_index": TFIDFIndexStrategy,
}


def _resolve_strategy_class(name: str) -> type[BaseIndexingStrategy] | None:
    """Resolves a strategy class from a name or slug.

    Args:
        name: Strategy name, key, or slug.

    Returns:
        Strategy class type or None if unresolved.
    """
    normalized = (
        name.lower()
        .replace(" ", "_")
        .replace("-", "_")
        .removesuffix("_strategy")
    )
    if normalized in STRATEGY_REGISTRY:
        return STRATEGY_REGISTRY[normalized]

    for candidate in [
        SortedNeighborhoodStrategy,
        MinHashLSHStrategy,
        QGramIndexStrategy,
        TFIDFIndexStrategy,
    ]:
        cand_norm = candidate.__name__.lower().removesuffix("strategy")
        if normalized == cand_norm or normalized == candidate.__name__.lower():
            return candidate
    return None


def _strategy_canonical_slug(cls_: type[BaseIndexingStrategy]) -> str:
    """Returns canonical slug for indexing strategy directory naming."""
    mapping = {
        SortedNeighborhoodStrategy: "sorted_neighborhood",
        MinHashLSHStrategy: "minhash_lsh",
        QGramIndexStrategy: "qgram_index",
        TFIDFIndexStrategy: "tfidf_index",
    }
    return mapping.get(cls_, cls_.__name__.lower().removesuffix("strategy"))


def _strategy_display_name(cls_: type[BaseIndexingStrategy]) -> str:
    """Returns clean display name for indexing strategy."""
    mapping = {
        SortedNeighborhoodStrategy: "Sorted Neighborhood",
        MinHashLSHStrategy: "MinHash LSH",
        QGramIndexStrategy: "Q-Gram Index",
        TFIDFIndexStrategy: "TF-IDF Index",
    }
    return mapping.get(cls_, cls_.__name__.removesuffix("Strategy"))


async def _run_single_index_iteration(
    dataset: Any,
    strategy_cls: type[BaseIndexingStrategy],
    model_name: str,
    iteration_index: int,
    config_generator: LLMIndexConfigGenerator,
    evaluator: IndexingMetricsEvaluator,
    force_llm: bool = False,
) -> tuple[IndexIterationMetrics, dict[str, Any]]:
    """Executes a single indexing iteration with exception safety.

    Args:
        dataset: Loaded ER dataset object.
        strategy_cls: Indexing strategy class to instantiate and execute.
        model_name: LLM model name for parameter recommendation.
        iteration_index: Current 1-based iteration counter.
        config_generator: Indexing configuration generator.
        evaluator: Indexing evaluator.
        force_llm: Whether to bypass cache for configuration.

    Returns:
        Tuple of (IndexIterationMetrics, execution trace dict).
    """
    df_a = dataset.table_a
    df_b = dataset.table_b
    ground_truth = dataset.ground_truth

    try:
        clean_df_a, _ = clean_data(df_a)
        clean_df_b, _ = clean_data(df_b)
        profile_a = DataProfiler.profile_dataframe(
            clean_df_a, f"{dataset.name}_a"
        )
        profile_b = DataProfiler.profile_dataframe(
            clean_df_b, f"{dataset.name}_b"
        )

        all_cols = list(
            dict.fromkeys(list(clean_df_a.columns) + list(clean_df_b.columns))
        )
        fields = [TableField(name=col, type="string") for col in all_cols]
        table_resource = TableResource(
            name=dataset.name, schema=TableSchema(fields=fields)
        )

        strategy_instance, llm_metrics = (
            await config_generator.get_configuration(
                dataset_name=dataset.name,
                profile_a=profile_a,
                profile_b=profile_b,
                table_resource=table_resource,
                strategy_cls=strategy_cls,
                force_llm=force_llm,
                model_name=model_name,
            )
        )

        if not strategy_instance:
            raise RuntimeError(
                f"Failed to generate configuration for {strategy_cls.__name__}"
            )

        res = strategy_instance.execute(clean_df_a, clean_df_b)
        gt_index = ensure_multiindex(ground_truth)
        eval_metrics = evaluator.evaluate(
            candidate_pairs=res.candidate_pairs,
            ground_truth=gt_index,
            df_a=clean_df_a,
            df_b=clean_df_b,
        )

        if eval_metrics.get("recall", 0.0) >= 1.0:
            save_candidate_set(dataset, res.candidate_pairs)

        token_usage = TokenUsage()
        if llm_metrics:
            lat = getattr(
                llm_metrics,
                "execution_time_seconds",
                getattr(llm_metrics, "latency_seconds", 0.0),
            )
            token_usage = TokenUsage(
                prompt_tokens=llm_metrics.prompt_tokens,
                completion_tokens=llm_metrics.completion_tokens,
                total_tokens=llm_metrics.total_tokens,
                latency_seconds=lat,
                cost_usd=getattr(llm_metrics, "cost_usd", None),
            )

        sorting_keys = getattr(strategy_instance, "sorting_keys", None)
        window_size = getattr(strategy_instance, "window_size", None)

        metric = IndexIterationMetrics(
            iteration_index=iteration_index,
            status=RunStatus.SUCCESS,
            recall=eval_metrics.get("recall", 0.0),
            precision=eval_metrics.get("precision", 0.0),
            reduction_ratio=eval_metrics.get("reduction_ratio", 0.0),
            num_candidates=eval_metrics.get(
                "num_candidates", len(res.candidate_pairs)
            ),
            max_possible_pairs=eval_metrics.get(
                "max_possible_pairs", len(clean_df_a) * len(clean_df_b)
            ),
            num_true_matches=eval_metrics.get(
                "num_true_matches", len(gt_index)
            ),
            missed_true_matches=eval_metrics.get("missed_true_matches", 0),
            indexing_time_sec=res.indexing_time_sec,
            peak_memory_mb=res.peak_memory_mb,
            peak_cpu_percent=res.peak_cpu_percent,
            sorting_keys=sorting_keys,
            window_size=window_size,
            token_usage=token_usage,
        )
        trace = {
            "iteration": iteration_index,
            "status": RunStatus.SUCCESS.value,
            "recall": metric.recall,
            "precision": metric.precision,
            "reduction_ratio": metric.reduction_ratio,
            "num_candidates": metric.num_candidates,
            "indexing_time_sec": metric.indexing_time_sec,
            "peak_memory_mb": metric.peak_memory_mb,
            "token_usage": token_usage.model_dump(),
        }

        # Release heavyweight objects to reduce memory pressure between iterations
        del res, clean_df_a, clean_df_b, gt_index, eval_metrics
        del strategy_instance, profile_a, profile_b

        return metric, trace

    except Exception as exc:
        logger.exception(
            "Iteration %d failed for dataset '%s' strategy '%s'",
            iteration_index,
            dataset.name,
            strategy_cls.__name__,
        )
        tb_str = traceback.format_exc()
        err_msg = str(exc) or type(exc).__name__
        metric = IndexIterationMetrics(
            iteration_index=iteration_index,
            status=RunStatus.FAILED,
            error_message=err_msg,
            traceback=tb_str,
        )
        trace = {
            "iteration": iteration_index,
            "status": RunStatus.FAILED.value,
            "error": err_msg,
            "traceback": tb_str,
        }
        return metric, trace


def _aggregate_index_metrics(
    dataset_name: str,
    domain: str,
    strategy_name: str,
    model_name: str,
    iterations: list[IndexIterationMetrics],
) -> IndexDatasetStrategyMetrics:
    """Aggregates multiple indexing iteration metrics with mean ± std.

    Args:
        dataset_name: Name of evaluated dataset.
        domain: Domain of dataset.
        strategy_name: Display name of strategy.
        model_name: LLM model identifier used for config.
        iterations: List of iteration metric objects.

    Returns:
        Consolidated IndexDatasetStrategyMetrics instance.
    """
    successful = [
        it for it in iterations if it.status == RunStatus.SUCCESS
    ]
    rec_stats = compute_mean_std([it.recall for it in successful])
    prec_stats = compute_mean_std([it.precision for it in successful])
    rr_stats = compute_mean_std([it.reduction_ratio for it in successful])
    time_stats = compute_mean_std([it.indexing_time_sec for it in successful])
    mem_stats = compute_mean_std([it.peak_memory_mb for it in successful])

    prompt_tok = sum(it.token_usage.prompt_tokens for it in iterations)
    comp_tok = sum(it.token_usage.completion_tokens for it in iterations)
    total_tok = sum(it.token_usage.total_tokens for it in iterations)
    est_cost = sum(it.token_usage.cost_usd or 0.0 for it in iterations)

    return IndexDatasetStrategyMetrics(
        dataset_name=dataset_name,
        domain=domain,
        strategy_name=strategy_name,
        model_name=model_name,
        iterations=iterations,
        mean_recall=rec_stats.mean,
        std_recall=rec_stats.std,
        mean_precision=prec_stats.mean,
        std_precision=prec_stats.std,
        mean_reduction_ratio=rr_stats.mean,
        std_reduction_ratio=rr_stats.std,
        mean_indexing_time=time_stats.mean,
        std_indexing_time=time_stats.std,
        mean_memory_mb=mem_stats.mean,
        std_memory_mb=mem_stats.std,
        prompt_tokens=prompt_tok,
        completion_tokens=comp_tok,
        total_tokens=total_tok,
        estimated_cost_usd=round(est_cost, 6),
    )


def _build_index_dataset_markdown_report(
    dm: IndexDatasetStrategyMetrics,
) -> str:
    """Generates Markdown diagnostic report for one dataset and strategy.

    Args:
        dm: Aggregated dataset strategy metrics container.

    Returns:
        Formatted Markdown text.
    """
    lines = [
        f"# Indexing Benchmark: {dm.dataset_name} — {dm.strategy_name}\n",
        f"- **Domain**: {dm.domain or 'general'}",
        f"- **Strategy**: {dm.strategy_name}",
        f"- **Model**: {dm.model_name}",
        (
            f"- **Successful Iterations**: {dm.successful_iterations_count} / "
            f"{len(dm.iterations)}\n"
        ),
        "## Aggregated Metrics\n",
    ]

    stat_headers = ["Metric", "Mean", "Std Dev"]
    stat_rows = [
        ["Recall", f"{dm.mean_recall:.4f}", f"{dm.std_recall:.4f}"],
        ["Precision", f"{dm.mean_precision:.4f}", f"{dm.std_precision:.4f}"],
        [
            "Reduction Ratio",
            f"{dm.mean_reduction_ratio:.4f}",
            f"{dm.std_reduction_ratio:.4f}",
        ],
        [
            "Indexing Time (s)",
            f"{dm.mean_indexing_time:.4f}",
            f"{dm.std_indexing_time:.4f}",
        ],
        [
            "Peak Memory (MB)",
            f"{dm.mean_memory_mb:.2f}",
            f"{dm.std_memory_mb:.2f}",
        ],
    ]
    lines.append(format_markdown_table(stat_headers, stat_rows))
    lines.append("\n## Telemetry\n")
    lines.append(
        format_markdown_table(
            ["Metric", "Value"],
            [
                ["Prompt Tokens", f"{dm.prompt_tokens:,}"],
                ["Completion Tokens", f"{dm.completion_tokens:,}"],
                ["Total Tokens", f"{dm.total_tokens:,}"],
                ["Estimated Cost (USD)", f"${dm.estimated_cost_usd:.4f}"],
            ],
        )
    )
    lines.append("\n## Iterations\n")

    iter_headers = [
        "Iter",
        "Status",
        "Recall",
        "Precision",
        "Red. Ratio",
        "Candidates",
        "Time (s)",
        "Mem (MB)",
        "Tokens",
        "Cost (USD)",
        "Error",
    ]
    iter_rows = []
    for it in dm.iterations:
        err_snippet = (it.error_message or "")[:40]
        iter_rows.append([
            str(it.iteration_index),
            it.status.value,
            f"{it.recall:.4f}" if it.status == RunStatus.SUCCESS else "-",
            f"{it.precision:.4f}" if it.status == RunStatus.SUCCESS else "-",
            (
                f"{it.reduction_ratio:.4f}"
                if it.status == RunStatus.SUCCESS
                else "-"
            ),
            (
                str(it.num_candidates)
                if it.status == RunStatus.SUCCESS
                else "-"
            ),
            (
                f"{it.indexing_time_sec:.4f}"
                if it.status == RunStatus.SUCCESS
                else "-"
            ),
            (
                f"{it.peak_memory_mb:.2f}"
                if it.status == RunStatus.SUCCESS
                else "-"
            ),
            str(it.token_usage.total_tokens),
            format_cost_usd(it.token_usage.cost_usd),
            err_snippet,
        ])
    lines.append(format_markdown_table(iter_headers, iter_rows))
    lines.append("")
    return "\n".join(lines)


def _build_index_summary_markdown(summary: IndexRunSummary) -> str:
    """Constructs human-readable Markdown summary of entire indexing run.

    Args:
        summary: Top-level indexing benchmark summary container.

    Returns:
        Formatted Markdown text.
    """
    lines = [
        "# ER Indexing Benchmark Summary\n",
        f"- **Run ID**: `{summary.run_id}`",
        f"- **Timestamp**: `{summary.timestamp.isoformat()}`",
        f"- **Datasets**: {', '.join(summary.datasets)}",
        f"- **Strategies**: {', '.join(summary.strategies)}",
        f"- **Models**: {', '.join(summary.models)}",
        f"- **Iterations**: {summary.iterations}",
        (
            f"- **Failed Iterations**: {summary.failed_iterations_count} / "
            f"{summary.total_iterations_count}\n"
        ),
        "## Performance Comparison\n",
    ]

    headers = [
        "Dataset",
        "Strategy",
        "Model",
        "Recall (Mean ± Std)",
        "Precision",
        "Red. Ratio",
        "Time (s)",
        "Peak Mem (MB)",
        "Status",
    ]
    rows = []
    for ds_name in summary.datasets:
        for dm in summary.matrix.get(ds_name, {}).values():
            succ = dm.successful_iterations_count
            tot = len(dm.iterations)
            stat = f"{succ}/{tot} OK" if succ == tot else f"{succ}/{tot} FAILED"
            rows.append([
                ds_name,
                dm.strategy_name,
                dm.model_name,
                f"{dm.mean_recall:.4f} ± {dm.std_recall:.4f}",
                f"{dm.mean_precision:.4f}",
                f"{dm.mean_reduction_ratio:.4f}",
                f"{dm.mean_indexing_time:.4f}",
                f"{dm.mean_memory_mb:.2f}",
                stat,
            ])
    lines.append(format_markdown_table(headers, rows))

    if summary.failed_iterations_count > 0:
        lines.append("\n## Failure Diagnostic Log\n")
        fail_headers = ["Dataset", "Strategy", "Model", "Iter", "Error Snippet"]
        fail_rows = []
        for ds_name in summary.datasets:
            for dm in summary.matrix.get(ds_name, {}).values():
                for it in dm.iterations:
                    if it.status != RunStatus.SUCCESS:
                        fail_rows.append([
                            ds_name,
                            dm.strategy_name,
                            dm.model_name,
                            str(it.iteration_index),
                            (it.error_message or "Unknown failure")[:60],
                        ])
        lines.append(format_markdown_table(fail_headers, fail_rows))

    lines.append("")
    return "\n".join(lines)


def _build_index_summary_csv(
    summary: IndexRunSummary,
) -> list[dict[str, Any]]:
    """Builds tabular rows for indexing summary CSV export.

    Args:
        summary: Top-level indexing benchmark summary container.

    Returns:
        List of row dictionaries.
    """
    rows: list[dict[str, Any]] = []
    for ds_name in summary.datasets:
        for dm in summary.matrix.get(ds_name, {}).values():
            rows.append({
                "dataset": ds_name,
                "domain": dm.domain,
                "strategy": dm.strategy_name,
                "model": dm.model_name,
                "mean_recall": dm.mean_recall,
                "std_recall": dm.std_recall,
                "mean_precision": dm.mean_precision,
                "std_precision": dm.std_precision,
                "mean_reduction_ratio": dm.mean_reduction_ratio,
                "std_reduction_ratio": dm.std_reduction_ratio,
                "mean_indexing_time": dm.mean_indexing_time,
                "std_indexing_time": dm.std_indexing_time,
                "mean_memory_mb": dm.mean_memory_mb,
                "std_memory_mb": dm.std_memory_mb,
                "prompt_tokens": dm.prompt_tokens,
                "completion_tokens": dm.completion_tokens,
                "total_tokens": dm.total_tokens,
                "successful_iterations": dm.successful_iterations_count,
                "failed_iterations": dm.failed_iterations_count,
                "total_iterations": len(dm.iterations),
            })
    return rows


def _save_index_dataset_artifacts(
    strat_dir: Path,
    ds_metrics: IndexDatasetStrategyMetrics,
    traces: list[dict[str, Any]],
    append_traces: bool = False,
) -> None:
    """Exports dataset strategy metrics.json, report.md, and traces.jsonl.

    Args:
        strat_dir: Target output directory for strategy artifacts.
        ds_metrics: Aggregated dataset strategy metrics.
        traces: Execution trace records.
        append_traces: Whether to append to existing traces.jsonl.
    """
    strat_dir.mkdir(parents=True, exist_ok=True)
    export_json(ds_metrics, strat_dir / "metrics.json")
    report_md = _build_index_dataset_markdown_report(ds_metrics)
    (strat_dir / "report.md").write_text(report_md, encoding="utf-8")

    traces_file = strat_dir / "traces.jsonl"
    mode = "a" if append_traces and traces_file.exists() else "w"
    with open(traces_file, mode, encoding="utf-8") as f:
        f.writelines(json.dumps(tr, default=str) + "\n" for tr in traces)


def _merge_index_iteration_result(
    existing_dm: IndexDatasetStrategyMetrics,
    new_metric: IndexIterationMetrics,
) -> IndexDatasetStrategyMetrics:
    """Merges a newly executed iteration into existing dataset metrics.

    Args:
        existing_dm: Existing dataset metrics container.
        new_metric: New iteration metric to update/insert.

    Returns:
        Updated IndexDatasetStrategyMetrics container.
    """
    updated_iterations: list[IndexIterationMetrics] = []
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

    return _aggregate_index_metrics(
        dataset_name=existing_dm.dataset_name,
        domain=existing_dm.domain,
        strategy_name=existing_dm.strategy_name,
        model_name=existing_dm.model_name,
        iterations=updated_iterations,
    )


async def run_indexing_benchmark(
    datasets: list[str] | None = None,
    domain: str = "all",
    strategies: list[str] | None = None,
    force_llm: bool = False,
    models: list[str] | str | None = None,
    model_name: str | None = None,
    iterations: int = 1,
    runs: int | None = None,
    output_dir: Path | str | None = None,
    output: str | None = None,
) -> IndexRunSummary:
    """Orchestrates multi-iteration indexing benchmarks across datasets.

    Args:
        datasets: List of specific dataset names to evaluate, or None for all.
        domain: Domain filter for dataset discovery.
        strategies: List of strategy names/aliases to benchmark.
        force_llm: Whether to bypass local cache for LLM configuration.
        models: LLM model name(s) for parameter recommendation.
        model_name: Backwards-compatible single model argument.
        iterations: Number of benchmark repetitions per configuration.
        runs: Backwards-compatible alias for iterations.
        output_dir: Custom root directory for benchmark runs.
        output: Legacy custom output file/dir path.

    Returns:
        IndexRunSummary containing all execution results.
    """
    num_iterations = runs or iterations or 1
    model_list: list[str] = []
    if isinstance(models, list) and models:
        model_list = models
    elif isinstance(models, str) and models:
        model_list = [models]
    elif model_name:
        model_list = [model_name]
    else:
        model_list = [config.DEFAULT_GOOGLE_MODEL]

    console.print(
        f"[dim]Discovering datasets for indexing benchmark (domain='{domain}')...[/]"
    )
    datasets_to_run = discover_and_load(
        data_dir=str(config.ER_DATASETS_DIR),
        domain=domain,
        dataset_names=datasets,
    )

    if not datasets_to_run:
        console.print(
            "[yellow]⚠ No matching datasets found for indexing benchmark.[/]"
        )
        return IndexRunSummary(
            run_id="empty",
            strategies=[],
            datasets=[],
            models=model_list,
            iterations=num_iterations,
        )

    # Determine strategy classes to evaluate
    if not strategies or "all" in [s.lower() for s in strategies]:
        selected_strategy_classes = [
            SortedNeighborhoodStrategy,
            MinHashLSHStrategy,
            QGramIndexStrategy,
            TFIDFIndexStrategy,
        ]
    else:
        selected_strategy_classes = []
        for strat_name in strategies:
            cls_ = _resolve_strategy_class(strat_name)
            if cls_ and cls_ not in selected_strategy_classes:
                selected_strategy_classes.append(cls_)
            elif not cls_:
                console.print(
                    f"[yellow]⚠ Unknown strategy '{strat_name}'. "
                    f"Available strategies: {list(STRATEGY_REGISTRY.keys())} or 'all'[/]"
                )

    if not selected_strategy_classes:
        console.print(
            "[yellow]⚠ No valid strategies selected for benchmark.[/]"
        )
        return IndexRunSummary(
            run_id="empty",
            strategies=[],
            datasets=[],
            models=model_list,
            iterations=num_iterations,
        )

    # Determine output directory
    base_out = (
        Path(output_dir)
        if output_dir
        else config.ER_INDEXING_BENCHMARK_OUTPUT_DIR
    )
    if output:
        out_p = Path(output)
        run_dir = out_p if out_p.is_absolute() else base_out / out_p
    else:
        run_dir = RunLayoutManager.get_run_dir(base_out)

    run_dir.mkdir(parents=True, exist_ok=True)
    run_id = run_dir.name
    console.print(f"[bold cyan]🚀 Benchmark run directory:[/] {run_dir}")

    config_generator = LLMIndexConfigGenerator()
    evaluator = IndexingMetricsEvaluator()

    matrix: dict[str, dict[str, IndexDatasetStrategyMetrics]] = {}
    strategy_slugs = [
        _strategy_canonical_slug(cls_) for cls_ in selected_strategy_classes
    ]
    dataset_names = [d.name for d in datasets_to_run]
    total_iters = 0
    failed_iters = 0

    for m_name in model_list:
        m_slug = RunLayoutManager.sanitize_slug(m_name)
        console.print(
            f"\n[bold magenta]==============================================[/bold magenta]"
            f"\n[bold magenta]Benchmarking Model: {m_name}[/bold magenta]"
            f"\n[bold magenta]==============================================[/bold magenta]"
        )

        for dataset in datasets_to_run:
            ds_name = dataset.name
            if ds_name not in matrix:
                matrix[ds_name] = {}

            for strategy_cls in selected_strategy_classes:
                strat_display = _strategy_display_name(strategy_cls)
                strat_slug = _strategy_canonical_slug(strategy_cls)
                strat_dir = RunLayoutManager.get_dataset_model_dir(
                    run_dir, ds_name, m_name, strategy=strat_slug
                )
                iterations_list: list[IndexIterationMetrics] = []
                traces_list: list[dict[str, Any]] = []

                console.print(
                    f"\n[bold cyan]▶ [{ds_name}] Strategy '{strat_display}' "
                    f"using model '{m_name}' ({num_iterations} iter)[/]"
                )

                for iter_idx in range(1, num_iterations + 1):
                    console.print(
                        f"  [dim]Executing iteration {iter_idx}/{num_iterations}...[/]"
                    )
                    it_metric, trace_dict = await _run_single_index_iteration(
                        dataset=dataset,
                        strategy_cls=strategy_cls,
                        model_name=m_name,
                        iteration_index=iter_idx,
                        config_generator=config_generator,
                        evaluator=evaluator,
                        force_llm=force_llm,
                    )
                    iterations_list.append(it_metric)
                    traces_list.append(trace_dict)
                    total_iters += 1
                    if it_metric.status != RunStatus.SUCCESS:
                        failed_iters += 1
                        console.print(
                            f"    [bold red]✖ Iteration {iter_idx} failed: "
                            f"{it_metric.error_message}[/]"
                        )
                    else:
                        console.print(
                            f"    [green]✔ Iteration {iter_idx} OK: "
                            f"Recall={it_metric.recall:.2%}, "
                            f"RR={it_metric.reduction_ratio:.2%}, "
                            f"Time={it_metric.indexing_time_sec:.2f}s[/]"
                        )

                ds_metrics = _aggregate_index_metrics(
                    dataset_name=ds_name,
                    domain=dataset.domain
                    if hasattr(dataset, "domain")
                    else "general",
                    strategy_name=strat_display,
                    model_name=m_name,
                    iterations=iterations_list,
                )
                matrix_key = (
                    f"{m_slug}/{strat_slug}"
                    if len(model_list) > 1
                    else strat_slug
                )
                matrix[ds_name][matrix_key] = ds_metrics
                _save_index_dataset_artifacts(
                    strat_dir, ds_metrics, traces_list
                )

                # Progressive summary checkpointing
                summary_ckpt = IndexRunSummary(
                    run_id=run_id,
                    strategies=strategy_slugs,
                    datasets=dataset_names,
                    models=model_list,
                    iterations=num_iterations,
                    matrix=matrix,
                    failed_iterations_count=failed_iters,
                    total_iterations_count=total_iters,
                )
                summary_md_ckpt = _build_index_summary_markdown(summary_ckpt)
                summary_csv_ckpt = _build_index_summary_csv(summary_ckpt)
                BenchmarkReportWriter.checkpoint_summaries(
                    run_dir=run_dir,
                    summary_data=summary_ckpt,
                    summary_rows=summary_csv_ckpt,
                    markdown_content=summary_md_ckpt,
                )

                # Force garbage collection between strategy evaluations to
                # reclaim memory from candidate pair MultiIndexes and DataFrames
                gc.collect()

    summary = IndexRunSummary(
        run_id=run_id,
        strategies=strategy_slugs,
        datasets=dataset_names,
        models=model_list,
        iterations=num_iterations,
        matrix=matrix,
        failed_iterations_count=failed_iters,
        total_iterations_count=total_iters,
    )

    summary_md = _build_index_summary_markdown(summary)
    summary_csv = _build_index_summary_csv(summary)
    BenchmarkReportWriter.checkpoint_summaries(
        run_dir=run_dir,
        summary_data=summary,
        summary_rows=summary_csv,
        markdown_content=summary_md,
    )

    table_cols = [
        "Dataset",
        "Strategy",
        "Model",
        "Recall (Mean ± Std)",
        "Precision",
        "Red. Ratio",
        "Time (s)",
        "Peak Mem (MB)",
        "Status",
    ]
    table_rows = []
    for ds_name in summary.datasets:
        for dm in summary.matrix.get(ds_name, {}).values():
            succ = dm.successful_iterations_count
            tot = len(dm.iterations)
            stat_str = (
                f"[green]{succ}/{tot} OK[/]"
                if succ == tot
                else f"[red]{succ}/{tot} OK[/]"
            )
            table_rows.append([
                ds_name,
                escape(dm.strategy_name),
                escape(dm.model_name),
                f"{dm.mean_recall:.2%} ± {dm.std_recall:.2%}",
                f"{dm.mean_precision:.2%}",
                f"{dm.mean_reduction_ratio:.2%}",
                f"{dm.mean_indexing_time:.4f}",
                f"{dm.mean_memory_mb:.2f}",
                stat_str,
            ])
    render_rich_table("Indexing Benchmark Summary", table_cols, table_rows)

    if summary.failed_iterations_count > 0:
        fail_cols = ["Dataset", "Strategy", "Model", "Iter", "Error Snippet"]
        fail_rows = []
        for ds_name in summary.datasets:
            for dm in summary.matrix.get(ds_name, {}).values():
                for it in dm.iterations:
                    if it.status != RunStatus.SUCCESS:
                        fail_rows.append([
                            ds_name,
                            escape(dm.strategy_name),
                            escape(dm.model_name),
                            str(it.iteration_index),
                            (it.error_message or "Failed")[:50],
                        ])
        render_rich_table(
            "Failed Indexing Iterations",
            fail_cols,
            fail_rows,
            header_style="bold red",
        )
        console.print(
            f"[yellow]💡 To retry failed runs: "
            f"[bold]uv run er-index-benchmark --retry {run_id}[/bold][/yellow]\n"
        )

    console.print(
        f"[green]✔ Indexing benchmark completed! Run directory:[/] {run_dir}\n"
    )
    return summary


async def retry_indexing_benchmark_run(
    run_target: str | Path,
    dataset_filter: list[str] | None = None,
    strategy_filter: list[str] | None = None,
    output_dir: Path | None = None,
    force_llm: bool = False,
) -> IndexRunSummary:
    """Retries only failed iterations for an existing indexing benchmark run.

    Args:
        run_target: Run folder, run ID string, or 'latest'.
        dataset_filter: Optional subset of datasets to retry.
        strategy_filter: Optional subset of strategies to retry.
        output_dir: Base directory if relative run ID is used.
        force_llm: Whether to force configuration regeneration on retry.

    Returns:
        Updated IndexRunSummary.
    """
    base_out = output_dir or config.ER_INDEXING_BENCHMARK_OUTPUT_DIR
    run_dir = resolve_run_directory(
        run_target,
        base_out,
        fallback_dirs=[config.LEGACY_ER_INDEXING_BENCHMARK_OUTPUT_DIR],
    )
    console.print(
        f"[cyan]Resolving indexing run directory for retry:[/] {run_dir}"
    )

    failed_items = find_failed_iterations(
        run_dir,
        dataset_filter=dataset_filter,
        strategy_filter=strategy_filter,
    )

    if not failed_items:
        console.print(
            "[green]No failed iterations found to retry in this run directory![/]"
        )
        summary_path = run_dir / "summary.json"
        if summary_path.exists():
            return IndexRunSummary.model_validate_json(
                summary_path.read_text(encoding="utf-8")
            )
        return IndexRunSummary(
            run_id=run_dir.name,
            strategies=[],
            datasets=[],
        )

    console.print(
        f"[yellow]Found {len(failed_items)} failed iteration(s) to re-execute.[/]\n"
    )

    needed_datasets = sorted({item[0] for item in failed_items})
    loaded_datasets = discover_and_load(
        data_dir=str(config.ER_DATASETS_DIR),
        domain="all",
        dataset_names=needed_datasets,
    )
    dataset_map = {d.name: d for d in loaded_datasets}

    config_generator = LLMIndexConfigGenerator()
    evaluator = IndexingMetricsEvaluator()

    for ds_name, strat_slug, iteration_index, strat_dir in failed_items:
        dataset = dataset_map.get(ds_name)
        if not dataset:
            console.print(
                f"[red]Could not load dataset '{ds_name}' to retry iteration {iteration_index}.[/]"
            )
            continue

        strat_cls = _resolve_strategy_class(strat_slug)
        if not strat_cls:
            console.print(
                f"[red]Could not resolve strategy class for slug '{strat_slug}'.[/]"
            )
            continue

        metrics_file = strat_dir / "metrics.json"
        model_name = config.DEFAULT_GOOGLE_MODEL
        if metrics_file.exists():
            try:
                raw_json = json.loads(metrics_file.read_text(encoding="utf-8"))
                model_name = raw_json.get("model_name", model_name)
            except (json.JSONDecodeError, OSError, ValueError):
                pass

        console.print(
            f"[cyan]▶ Retrying {ds_name} | {strat_slug} | "
            f"Iteration {iteration_index}...[/]"
        )
        new_metric, trace_dict = await _run_single_index_iteration(
            dataset=dataset,
            strategy_cls=strat_cls,
            model_name=model_name,
            iteration_index=iteration_index,
            config_generator=config_generator,
            evaluator=evaluator,
            force_llm=force_llm,
        )

        if metrics_file.exists():
            existing_dm = IndexDatasetStrategyMetrics.model_validate_json(
                metrics_file.read_text(encoding="utf-8")
            )
            updated_dm = _merge_index_iteration_result(
                existing_dm, new_metric
            )
            _save_index_dataset_artifacts(
                strat_dir=strat_dir,
                ds_metrics=updated_dm,
                traces=[trace_dict],
                append_traces=True,
            )

    # Rebuild top-level summaries across nested datasets/
    datasets_dir = run_dir / "datasets"
    matrix: dict[str, dict[str, IndexDatasetStrategyMetrics]] = {}
    total_iters = 0
    failed_iters = 0
    all_strategies: set[str] = set()
    all_datasets: set[str] = set()
    all_models: set[str] = set()

    if datasets_dir.exists():
        for metrics_file in sorted(datasets_dir.glob("**/metrics.json")):
            target_dir = metrics_file.parent
            rel_parts = target_dir.relative_to(datasets_dir).parts
            if len(rel_parts) < 2:
                continue
            d_name = rel_parts[0]
            s_key = "/".join(rel_parts[1:])
            if d_name not in matrix:
                matrix[d_name] = {}
            dm = IndexDatasetStrategyMetrics.model_validate_json(
                metrics_file.read_text(encoding="utf-8")
            )
            matrix[d_name][s_key] = dm
            all_datasets.add(d_name)
            all_strategies.add(rel_parts[-1])
            all_models.add(dm.model_name)
            total_iters += len(dm.iterations)
            failed_iters += dm.failed_iterations_count

    summary = IndexRunSummary(
        run_id=run_dir.name,
        timestamp=datetime.now(timezone.utc),
        strategies=sorted(all_strategies),
        datasets=sorted(all_datasets),
        models=sorted(all_models),
        iterations=max((len(dm.iterations) for d in matrix.values() for dm in d.values()), default=1),
        matrix=matrix,
        failed_iterations_count=failed_iters,
        total_iterations_count=total_iters,
    )

    summary_md = _build_index_summary_markdown(summary)
    summary_csv = _build_index_summary_csv(summary)
    BenchmarkReportWriter.checkpoint_summaries(
        run_dir=run_dir,
        summary_data=summary,
        summary_rows=summary_csv,
        markdown_content=summary_md,
    )

    console.print(
        f"[bold green]✔ In-place retry completed for run:[/] {run_dir}\n"
    )
    return summary


def main():
    """Main CLI entry point for index-benchmark command."""
    parser = argparse.ArgumentParser(
        description="Run ER Indexing Benchmarks"
    )
    parser.add_argument(
        "--datasets",
        nargs="*",
        default=None,
        help="List of specific dataset names to benchmark",
    )
    parser.add_argument(
        "--domain",
        type=str,
        default="all",
        help="Dataset domain filter",
    )
    parser.add_argument(
        "--strategies",
        nargs="*",
        default=["all"],
        help="List of strategies to benchmark (e.g. sn, lsh, qgram, all). Default: all",
    )
    parser.add_argument(
        "--force-llm",
        action="store_true",
        help="Force LLM configuration generation, bypassing cache",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="LLM model name to use for index configuration recommendation",
    )
    parser.add_argument(
        "--models",
        nargs="*",
        default=None,
        help="One or more LLM models to benchmark",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=1,
        help="Number of iterations per configuration (default: 1)",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=None,
        help="Alias for --iterations",
    )
    parser.add_argument(
        "--retry",
        type=str,
        default=None,
        help="Retry failed iterations for an existing run target ('latest', ID, or path)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Directory to write benchmark run artifacts",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Legacy output parameter for custom directory or filename",
    )
    args = parser.parse_args()

    if args.retry:
        asyncio.run(
            retry_indexing_benchmark_run(
                run_target=args.retry,
                dataset_filter=args.datasets,
                strategy_filter=(
                    args.strategies
                    if (
                        args.strategies
                        and "all" not in [s.lower() for s in args.strategies]
                    )
                    else None
                ),
                output_dir=Path(args.output_dir) if args.output_dir else None,
                force_llm=args.force_llm,
            )
        )
    else:
        asyncio.run(
            run_indexing_benchmark(
                datasets=args.datasets,
                domain=args.domain,
                strategies=args.strategies,
                force_llm=args.force_llm,
                models=args.models,
                model_name=args.model or config.DEFAULT_GOOGLE_MODEL,
                iterations=args.runs or args.iterations,
                output_dir=args.output_dir,
                output=args.output,
            )
        )


if __name__ == "__main__":
    main()
