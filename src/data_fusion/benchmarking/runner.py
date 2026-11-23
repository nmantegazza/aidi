"""CLI runner for data fusion benchmarking with multi-iteration isolation and resilience."""

from __future__ import annotations

import argparse
import json
import logging
import shutil
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from data_fusion.benchmarking.evaluation import DataFusionEvaluator
from data_fusion.benchmarking.loader import BenchmarkDataLoader
from data_fusion.benchmarking.models import (
    BenchmarkRunSummary,
    FusionDatasetAggregatedMetrics,
    FusionIterationMetrics,
    MetricsPayload,
    RunStatus,
    TokenPayload,
)
from data_fusion.entrypoint import DataFusionEngine
from data_fusion.models import (
    ColumnPolicy,
    FusionStrategy,
    TableFusionPolicy,
)
from data_fusion.policy_executor import PolicyExecutor
from shared.benchmarking import (
    BenchmarkReportWriter,
    BenchmarkStatsEngine,
    RunLayoutManager,
    RunResilienceHelper,
)
from shared.config import config
from shared.console import console

logger = logging.getLogger(__name__)


def run_baseline(
    baseline_type: str,
    df_a: pd.DataFrame,
    df_b: pd.DataFrame,
    entity_id_col: str,
    attributes: list[str],
) -> tuple[pd.DataFrame, dict[str, str], dict[str, float]]:
    """Executes a forced baseline policy (TRUST_SOURCE_A or TRUST_SOURCE_B).

    Args:
        baseline_type: Either 'trust_a' or 'trust_b'.
        df_a: Source A DataFrame.
        df_b: Source B DataFrame.
        entity_id_col: Column name identifying entities.
        attributes: List of attribute column names.

    Returns:
        Tuple of (Fused DataFrame, audit_log dict, timings dict in seconds).
    """
    trust_score = 1.0 if baseline_type == "trust_a" else 0.0

    col_policies = [
        ColumnPolicy(
            column_name=attr,
            strategy=FusionStrategy.TRUST_SOURCE,
            reasoning=f"Baseline forced policy: {baseline_type}",
        )
        for attr in attributes
    ]

    table_policy = TableFusionPolicy(
        table_name="data",
        column_policies=col_policies,
        reasoning=f"Baseline forced policy: {baseline_type}",
    )

    trust_scores = {attr: trust_score for attr in attributes}
    executor = PolicyExecutor(table_policy, trust_scores)

    df_a_reset = df_a.reset_index(drop=True)
    df_b_reset = df_b.reset_index(drop=True)
    linked_pairs = pd.DataFrame({entity_id_col: df_a_reset[entity_id_col]})

    for attr in attributes:
        linked_pairs[attr + "_a"] = df_a_reset[attr]
        linked_pairs[attr + "_b"] = df_b_reset[attr]

    t_exec_start = time.perf_counter()
    fused_df = executor.execute(linked_pairs)
    exec_latency_sec = time.perf_counter() - t_exec_start
    audit_log = {attr: "trust_source" for attr in attributes}
    timings = {
        "profiling_sec": 0.0,
        "synthesis_sec": 0.0,
        "execution_sec": round(exec_latency_sec, 4),
    }

    return fused_df, audit_log, timings


def run_pipeline_model(
    model_name: str,
    df_a: pd.DataFrame,
    df_b: pd.DataFrame,
    entity_id_col: str,
    attributes: list[str],
) -> tuple[
    pd.DataFrame,
    dict[str, str],
    TokenPayload,
    dict[str, float],
    str | None,
]:
    """Executes the native data fusion pipeline with an LLM model.

    Args:
        model_name: Name of the model (e.g. 'gemini-2.0-flash').
        df_a: Source A DataFrame.
        df_b: Source B DataFrame.
        entity_id_col: Column name identifying entities.
        attributes: Attribute column names.

    Returns:
        Tuple of (Fused DataFrame, audit_log dict, TokenPayload, timings dict in sec, llm_log_path).
    """
    engine = DataFusionEngine(model_name=model_name)

    df_links = pd.DataFrame(
        {"left_id": range(len(df_a)), "right_id": range(len(df_b))}
    )
    tables = {"data": (df_a, df_b, df_links)}

    # Measure Profiling
    t_prof_start = time.perf_counter()
    profile = engine.profiler.profile("Source A", "Source B", tables)
    profiling_latency_sec = time.perf_counter() - t_prof_start

    # Measure Policy Generation
    t_synth_start = time.perf_counter()
    policy, meta_dict = engine.policy_agent.generate_policy(
        profile, return_metadata=True
    )
    policy_synthesis_latency_sec = time.perf_counter() - t_synth_start

    # Measure Deterministic Execution
    t_exec_start = time.perf_counter()
    fused_tables = engine.execute(
        tables=tables, policy=policy, profile=profile, merge_unlinked=False
    )
    execution_latency_sec = time.perf_counter() - t_exec_start
    fused_df = fused_tables["data"]

    # Extract audit log of applied strategies
    audit_log = {}
    if "data" in policy.tables:
        for cp in policy.tables["data"].column_policies:
            audit_log[cp.column_name] = cp.strategy.value
        for fg in policy.tables["data"].fusion_groups:
            for col in fg.columns:
                audit_log[col] = fg.strategy.value

    # Extract real token usage and log file path from metadata
    meta = meta_dict.get("data") if meta_dict else None
    if meta:
        token_usage = TokenPayload(
            prompt_tokens=meta.prompt_tokens,
            completion_tokens=meta.completion_tokens,
            cached_tokens=meta.cached_tokens,
            reasoning_tokens=meta.reasoning_tokens,
            total_tokens=meta.total_tokens,
            latency_seconds=round(
                profiling_latency_sec
                + policy_synthesis_latency_sec
                + execution_latency_sec,
                4,
            ),
            cost_usd=getattr(meta, "cost_usd", None),
        )
        llm_log_path = meta.log_file_path
    else:
        token_usage = TokenPayload(
            latency_seconds=round(
                profiling_latency_sec
                + policy_synthesis_latency_sec
                + execution_latency_sec,
                4,
            )
        )
        llm_log_path = None

    timings = {
        "profiling_sec": round(profiling_latency_sec, 4),
        "synthesis_sec": round(policy_synthesis_latency_sec, 4),
        "execution_sec": round(execution_latency_sec, 4),
    }

    return fused_df, audit_log, token_usage, timings, llm_log_path


def _aggregate_data_fusion_metrics(
    dataset_id: str,
    model_name: str,
    iterations: list[FusionIterationMetrics],
) -> FusionDatasetAggregatedMetrics:
    """Computes statistical aggregations and consensus metrics across iterations."""
    successful = [it for it in iterations if it.status == RunStatus.SUCCESS]
    if not successful:
        return FusionDatasetAggregatedMetrics(
            dataset_id=dataset_id,
            model_name=model_name,
            status=RunStatus.FAILED,
            iterations=iterations,
        )

    # Absolute metrics
    abs_p_stats = BenchmarkStatsEngine.compute_mean_std(
        [it.absolute_metrics.precision for it in successful]
    )
    abs_r_stats = BenchmarkStatsEngine.compute_mean_std(
        [it.absolute_metrics.recall for it in successful]
    )
    abs_f1_stats = BenchmarkStatsEngine.compute_mean_std(
        [it.absolute_metrics.f1 for it in successful]
    )

    # Reachable metrics
    reach_p_stats = BenchmarkStatsEngine.compute_mean_std(
        [it.reachable_metrics.precision for it in successful]
    )
    reach_r_stats = BenchmarkStatsEngine.compute_mean_std(
        [it.reachable_metrics.recall for it in successful]
    )
    reach_f1_stats = BenchmarkStatsEngine.compute_mean_std(
        [it.reachable_metrics.f1 for it in successful]
    )

    # Latency
    lat_stats = BenchmarkStatsEngine.compute_mean_std(
        [it.latency_seconds for it in successful]
    )
    synth_lat_stats = BenchmarkStatsEngine.compute_mean_std(
        [it.policy_synthesis_latency_seconds for it in successful]
    )

    # Strategy consensus and flakiness across audit logs
    all_attributes = set()
    for it in successful:
        all_attributes.update(it.audit_log.keys())

    consensus_scores: list[float] = []
    flaky_attrs: dict[str, float] = {}

    for attr in sorted(all_attributes):
        choices = [
            it.audit_log.get(attr, "unknown")
            for it in successful
            if attr in it.audit_log
        ]
        ratio = BenchmarkStatsEngine.compute_consensus_ratio(choices)
        consensus_scores.append(ratio)
        if ratio < 1.0:
            flaky_attrs[attr] = round(ratio, 4)

    mean_consensus = (
        sum(consensus_scores) / len(consensus_scores)
        if consensus_scores
        else 1.0
    )

    # Status
    if len(successful) == len(iterations):
        status = RunStatus.SUCCESS
    else:
        status = RunStatus.PARTIAL

    return FusionDatasetAggregatedMetrics(
        dataset_id=dataset_id,
        model_name=model_name,
        status=status,
        iterations=iterations,
        mean_abs_precision=abs_p_stats.mean,
        std_abs_precision=abs_p_stats.std,
        mean_abs_recall=abs_r_stats.mean,
        std_abs_recall=abs_r_stats.std,
        mean_abs_f1=abs_f1_stats.mean,
        std_abs_f1=abs_f1_stats.std,
        mean_reach_precision=reach_p_stats.mean,
        std_reach_precision=reach_p_stats.std,
        mean_reach_recall=reach_r_stats.mean,
        std_reach_recall=reach_r_stats.std,
        mean_reach_f1=reach_f1_stats.mean,
        std_reach_f1=reach_f1_stats.std,
        mean_latency_seconds=lat_stats.mean,
        std_latency_seconds=lat_stats.std,
        mean_synthesis_latency_seconds=synth_lat_stats.mean,
        std_synthesis_latency_seconds=synth_lat_stats.std,
        prompt_tokens=sum(it.token_usage.prompt_tokens for it in iterations),
        completion_tokens=sum(
            it.token_usage.completion_tokens for it in iterations
        ),
        cached_tokens=sum(it.token_usage.cached_tokens for it in iterations),
        reasoning_tokens=sum(
            it.token_usage.reasoning_tokens for it in iterations
        ),
        total_tokens=sum(it.token_usage.total_tokens for it in iterations),
        estimated_cost_usd=round(
            sum(it.token_usage.cost_usd or 0.0 for it in iterations), 6
        ),
        strategy_consensus_ratio=round(mean_consensus, 4),
        flaky_attributes=flaky_attrs,
    )


def _build_data_fusion_summary_markdown(summary: BenchmarkRunSummary) -> str:
    """Builds formatted Markdown report summary from BenchmarkRunSummary."""
    lines = [
        "# Data Fusion Benchmarking Report\n",
        f"- **Run ID**: `{summary.run_id}`",
        f"- **Timestamp**: `{summary.timestamp}`",
        f"- **Datasets**: {', '.join(summary.datasets)}",
        f"- **Models / Strategies**: {', '.join(summary.models)}",
        f"- **Iterations**: {summary.iterations}",
        (
            f"- **Failed Iterations**: {summary.failed_iterations_count} / "
            f"{summary.total_iterations_count}\n"
        ),
        "## Macro-Averaged Results\n",
    ]

    macro_headers = [
        "Model / Strategy",
        "Abs Precision",
        "Abs Recall",
        "Abs F1",
        "Reach Precision",
        "Reach Recall",
        "Reach F1",
        "Mean Latency (s)",
        "Total Tokens",
        "Cost (USD)",
        "Consensus",
        "Status",
    ]
    macro_rows = []

    for model in summary.models:
        all_metrics = [
            summary.matrix.get(ds, {}).get(model)
            for ds in summary.datasets
            if model in summary.matrix.get(ds, {})
        ]
        valid_metrics = [m for m in all_metrics if m and m.successful_iterations_count > 0]
        if not valid_metrics:
            continue

        abs_p = sum(m.mean_abs_precision for m in valid_metrics) / len(valid_metrics)
        abs_r = sum(m.mean_abs_recall for m in valid_metrics) / len(valid_metrics)
        abs_f1 = sum(m.mean_abs_f1 for m in valid_metrics) / len(valid_metrics)

        reach_p = sum(m.mean_reach_precision for m in valid_metrics) / len(valid_metrics)
        reach_r = sum(m.mean_reach_recall for m in valid_metrics) / len(valid_metrics)
        reach_f1 = sum(m.mean_reach_f1 for m in valid_metrics) / len(valid_metrics)

        mean_lat = sum(m.mean_latency_seconds for m in valid_metrics) / len(valid_metrics)
        total_tokens = sum(m.total_tokens for m in valid_metrics)
        total_cost = sum(m.estimated_cost_usd for m in valid_metrics)
        mean_cons = sum(m.strategy_consensus_ratio for m in valid_metrics) / len(valid_metrics)

        succ = sum(m.successful_iterations_count for m in valid_metrics)
        tot = sum(len(m.iterations) for m in valid_metrics)
        status_str = f"{succ}/{tot} OK" if succ == tot else f"{succ}/{tot} PARTIAL"

        macro_rows.append([
            model,
            f"{abs_p:.4f}",
            f"{abs_r:.4f}",
            f"{abs_f1:.4f}",
            f"{reach_p:.4f}",
            f"{reach_r:.4f}",
            f"{reach_f1:.4f}",
            f"{mean_lat:.2f}s",
            f"{total_tokens:,}",
            f"${total_cost:.4f}",
            f"{mean_cons:.2%}",
            status_str,
        ])

    lines.append(BenchmarkReportWriter.format_markdown_table(macro_headers, macro_rows))
    lines.append("\n## Per-Dataset Breakdown\n")

    breakdown_headers = [
        "Dataset",
        "Model / Strategy",
        "Abs F1 (Mean ± Std)",
        "Reach F1 (Mean ± Std)",
        "Latency (s)",
        "Tokens (Total/Reasoning)",
        "Cost (USD)",
        "Consensus",
        "Status",
    ]
    breakdown_rows = []

    for ds in summary.datasets:
        for model in summary.models:
            m = summary.matrix.get(ds, {}).get(model)
            if not m:
                continue
            abs_f1_str = (
                f"{m.mean_abs_f1:.4f} ± {m.std_abs_f1:.4f}"
                if summary.iterations > 1
                else f"{m.mean_abs_f1:.4f}"
            )
            reach_f1_str = (
                f"{m.mean_reach_f1:.4f} ± {m.std_reach_f1:.4f}"
                if summary.iterations > 1
                else f"{m.mean_reach_f1:.4f}"
            )
            tok_str = f"{m.total_tokens:,} ({m.reasoning_tokens:,})"
            succ = m.successful_iterations_count
            tot = len(m.iterations)
            stat = f"{succ}/{tot} OK" if succ == tot else f"{succ}/{tot} FAILED"

            breakdown_rows.append([
                ds,
                model,
                abs_f1_str,
                reach_f1_str,
                f"{m.mean_latency_seconds:.2f}s",
                tok_str,
                f"${m.estimated_cost_usd:.4f}",
                f"{m.strategy_consensus_ratio:.2%}",
                stat,
            ])

    lines.append(BenchmarkReportWriter.format_markdown_table(breakdown_headers, breakdown_rows))

    if summary.failed_iterations_count > 0:
        lines.append("\n## Failure Diagnostic Log\n")
        fail_headers = ["Dataset", "Model", "Iteration", "Error Snippet"]
        fail_rows = []
        for ds in summary.datasets:
            for model in summary.models:
                m = summary.matrix.get(ds, {}).get(model)
                if not m:
                    continue
                for it in m.iterations:
                    if it.status != RunStatus.SUCCESS:
                        fail_rows.append([
                            ds,
                            model,
                            str(it.iteration_index),
                            (it.error_message or "Unknown failure")[:60],
                        ])
        lines.append(BenchmarkReportWriter.format_markdown_table(fail_headers, fail_rows))

    lines.append("")
    return "\n".join(lines)


def _build_data_fusion_summary_csv(
    summary: BenchmarkRunSummary,
) -> list[dict[str, Any]]:
    """Builds tabular rows for data fusion summary CSV export."""
    rows: list[dict[str, Any]] = []
    for ds in summary.datasets:
        for model in summary.models:
            m = summary.matrix.get(ds, {}).get(model)
            if not m:
                continue
            rows.append({
                "dataset": ds,
                "model": model,
                "status": m.status.value if hasattr(m.status, "value") else str(m.status),
                "abs_precision_mean": m.mean_abs_precision,
                "abs_precision_std": m.std_abs_precision,
                "abs_recall_mean": m.mean_abs_recall,
                "abs_recall_std": m.std_abs_recall,
                "abs_f1_mean": m.mean_abs_f1,
                "abs_f1_std": m.std_abs_f1,
                "reach_precision_mean": m.mean_reach_precision,
                "reach_precision_std": m.std_reach_precision,
                "reach_recall_mean": m.mean_reach_recall,
                "reach_recall_std": m.std_reach_recall,
                "reach_f1_mean": m.mean_reach_f1,
                "reach_f1_std": m.std_reach_f1,
                "latency_mean_sec": m.mean_latency_seconds,
                "latency_std_sec": m.std_latency_seconds,
                "synthesis_latency_mean_sec": m.mean_synthesis_latency_seconds,
                "prompt_tokens": m.prompt_tokens,
                "completion_tokens": m.completion_tokens,
                "cached_tokens": m.cached_tokens,
                "reasoning_tokens": m.reasoning_tokens,
                "total_tokens": m.total_tokens,
                "estimated_cost_usd": m.estimated_cost_usd,
                "strategy_consensus_ratio": m.strategy_consensus_ratio,
                "successful_iterations": m.successful_iterations_count,
                "failed_iterations": m.failed_iterations_count,
                "total_iterations": len(m.iterations),
            })
    return rows


def _run_single_df_iteration(
    loader: BenchmarkDataLoader,
    evaluator: DataFusionEvaluator,
    dataset_id: str,
    model_name: str,
    iteration_index: int,
    iter_dir: Path,
) -> tuple[FusionIterationMetrics, dict[str, Any]]:
    """Executes a single iteration of Data Fusion and isolates its artifacts."""
    iter_dir.mkdir(parents=True, exist_ok=True)
    trace_record: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dataset_id": dataset_id,
        "model_name": model_name,
        "iteration": iteration_index,
    }

    try:
        df_a, df_b, df_gt, meta = loader.load_dataset(dataset_id)
        entity_id_col = meta["entity_id_column"]
        attributes = meta["attributes"]

        start_time = time.perf_counter()
        token_usage = TokenPayload()
        llm_log_path = None
        timings: dict[str, float] = {}

        if model_name in ("trust_a", "trust_b"):
            fused_df, audit_log, timings = run_baseline(
                model_name, df_a, df_b, entity_id_col, attributes
            )
        else:
            (
                fused_df,
                audit_log,
                token_usage,
                timings,
                llm_log_path,
            ) = run_pipeline_model(
                model_name, df_a, df_b, entity_id_col, attributes
            )

        latency_sec = time.perf_counter() - start_time

        # Save fused.csv
        fused_df.to_csv(iter_dir / "fused.csv", index=False)

        # Evaluate against GT
        abs_m, reach_m = evaluator.evaluate_predictions(
            df_pred=fused_df,
            df_gt=df_gt,
            df_a=df_a,
            df_b=df_b,
            entity_id_col=entity_id_col,
            attributes=attributes,
        )

        # Extract disagreements
        disagreements_df = evaluator.extract_disagreements(
            df_pred=fused_df,
            df_gt=df_gt,
            df_a=df_a,
            df_b=df_b,
            entity_id_col=entity_id_col,
            attributes=attributes,
            audit_log=audit_log,
        )
        if not disagreements_df.empty:
            disagreements_df.to_csv(
                iter_dir / "disagreements.csv", index=False
            )

        # Copy LLM call log if present
        if llm_log_path and Path(llm_log_path).exists():
            target_llm_json = iter_dir / "llm_call.json"
            shutil.copy2(llm_log_path, target_llm_json)
            rel_log = f"iterations/iter_{iteration_index}/llm_call.json"
        else:
            rel_log = None

        iter_metric = FusionIterationMetrics(
            iteration_index=iteration_index,
            status=RunStatus.SUCCESS,
            absolute_metrics=MetricsPayload(
                precision=round(abs_m.precision, 4),
                recall=round(abs_m.recall, 4),
                f1=round(abs_m.f1, 4),
            ),
            reachable_metrics=MetricsPayload(
                precision=round(reach_m.precision, 4),
                recall=round(reach_m.recall, 4),
                f1=round(reach_m.f1, 4),
            ),
            latency_seconds=round(latency_sec, 4),
            profiling_latency_seconds=timings.get("profiling_sec", 0.0),
            policy_synthesis_latency_seconds=timings.get("synthesis_sec", 0.0),
            execution_latency_seconds=timings.get("execution_sec", 0.0),
            llm_call_log_path=rel_log,
            token_usage=token_usage,
            audit_log=audit_log,
        )
        trace_record["status"] = "SUCCESS"
        trace_record["metrics"] = iter_metric.model_dump()
        return iter_metric, trace_record

    except Exception as exc:  # noqa: BLE001
        logger.error(
            "Iteration %d failed for dataset '%s' model '%s': %s",
            iteration_index,
            dataset_id,
            model_name,
            exc,
        )
        err_msg = str(exc).strip() or type(exc).__name__
        trace_record["status"] = "FAILED"
        trace_record["error"] = err_msg
        trace_record["traceback"] = traceback.format_exc()

        failed_metric = FusionIterationMetrics(
            iteration_index=iteration_index,
            status=RunStatus.FAILED,
            error_message=err_msg,
            traceback=traceback.format_exc(),
        )
        return failed_metric, trace_record


def run_data_fusion_benchmark(
    datasets: list[str] | None = None,
    models: list[str] | None = None,
    baselines: list[str] | None = None,
    iterations: int = 1,
    output_dir: Path | str | None = None,
) -> BenchmarkRunSummary:
    """Main execution function for Data Fusion Benchmarking."""
    loader = BenchmarkDataLoader()
    evaluator = DataFusionEvaluator()

    # Discover datasets dynamically and sort for deterministic ordering
    if not datasets or "all" in datasets:
        processed_dir = loader.base_dir
        if processed_dir.exists():
            dataset_ids = sorted([
                d.name
                for d in processed_dir.iterdir()
                if d.is_dir() and (d / "metadata.json").exists()
            ])
        else:
            dataset_ids = ["books", "flights", "stocks", "restaurants"]
    else:
        dataset_ids = sorted(datasets)

    # Build models to run
    models_to_run: list[str] = []
    if baselines:
        if "all" in baselines:
            models_to_run.extend(["trust_a", "trust_b"])
        else:
            models_to_run.extend(baselines)
    if models:
        models_to_run.extend(models)

    if not models_to_run:
        console.print(
            "[yellow]No models or baselines specified. Defaulting to 'trust_a' and 'trust_b'.[/yellow]"
        )
        models_to_run = ["trust_a", "trust_b"]

    base_out = Path(output_dir) if output_dir else config.DF_BENCHMARK_OUTPUT_DIR
    run_dir = RunLayoutManager.get_run_dir(base_out)
    run_dir.mkdir(parents=True, exist_ok=True)
    run_id = run_dir.name
    console.print(f"[bold cyan]🚀 Benchmark run directory:[/] {run_dir}")

    matrix: dict[str, dict[str, FusionDatasetAggregatedMetrics]] = {}
    total_iters = 0
    failed_iters = 0

    for model_name in models_to_run:
        console.print(
            f"\n[bold magenta]==============================================[/bold magenta]"
            f"\n[bold magenta]Benchmarking Model / Strategy: {model_name}[/bold magenta]"
            f"\n[bold magenta]==============================================[/bold magenta]"
        )

        for dataset_id in dataset_ids:
            if dataset_id not in matrix:
                matrix[dataset_id] = {}

            model_ds_dir = RunLayoutManager.get_dataset_model_dir(
                run_dir, dataset_id, model_name
            )
            model_ds_dir.mkdir(parents=True, exist_ok=True)

            iteration_metrics: list[FusionIterationMetrics] = []
            trace_records: list[dict[str, Any]] = []

            console.print(
                f"\n[bold blue]▶ \\[{dataset_id}\\] Evaluating '{model_name}' ({iterations} iter)[/bold blue]"
            )

            for iter_idx in range(1, iterations + 1):
                iter_dir = RunLayoutManager.get_iteration_dir(
                    model_ds_dir, iter_idx
                )
                status_msg = f"Executing [{dataset_id} | {model_name}] iteration {iter_idx}/{iterations}..."
                with console.status(f"[dim]{status_msg}[/dim]", spinner="dots"):
                    it_metric, trace_rec = _run_single_df_iteration(
                        loader=loader,
                        evaluator=evaluator,
                        dataset_id=dataset_id,
                        model_name=model_name,
                        iteration_index=iter_idx,
                        iter_dir=iter_dir,
                    )
                iteration_metrics.append(it_metric)
                trace_records.append(trace_rec)
                total_iters += 1
                if it_metric.status != RunStatus.SUCCESS:
                    failed_iters += 1
                    console.print(
                        f"  [bold red]✖ Iter {iter_idx}/{iterations} FAILED:[/] "
                        f"[red]{it_metric.error_message}[/red]"
                    )
                else:
                    cost_str = (
                        f" │ [cyan]Cost:[/] ${it_metric.token_usage.cost_usd:.4f}"
                        if it_metric.token_usage.cost_usd is not None
                        else ""
                    )
                    tok_str = (
                        f" │ [magenta]Tokens:[/] {it_metric.token_usage.total_tokens:,}"
                        if it_metric.token_usage.total_tokens > 0
                        else ""
                    )
                    lat_str = f"[dim]Time:[/] {it_metric.latency_seconds:.2f}s"
                    if it_metric.policy_synthesis_latency_seconds > 0:
                        lat_str += f" [dim](synth: {it_metric.policy_synthesis_latency_seconds:.1f}s, exec: {it_metric.execution_latency_seconds:.2f}s)[/dim]"
                    console.print(
                        f"  [green]✔ Iter {iter_idx}/{iterations} OK[/green] │ "
                        f"[bold]Abs F1:[/] {it_metric.absolute_metrics.f1:.4f} │ "
                        f"[bold]Reach F1:[/] {it_metric.reachable_metrics.f1:.4f} │ "
                        f"{lat_str}{tok_str}{cost_str}"
                    )

            # Compute multi-iteration statistics & flakiness
            ds_metrics = _aggregate_data_fusion_metrics(
                dataset_id=dataset_id,
                model_name=model_name,
                iterations=iteration_metrics,
            )
            matrix[dataset_id][model_name] = ds_metrics

            # Save metrics.json (REQ-005) & execution_trace.jsonl
            BenchmarkReportWriter.save_json(
                ds_metrics, model_ds_dir / "metrics.json"
            )
            trace_content = "".join(
                json.dumps(t, default=str) + "\n" for t in trace_records
            )
            (model_ds_dir / "execution_trace.jsonl").write_text(
                trace_content, encoding="utf-8"
            )

            # Progressive summary checkpointing (REQ-002)
            summary_ckpt = BenchmarkRunSummary(
                run_id=run_id,
                models=models_to_run,
                datasets=dataset_ids,
                iterations=iterations,
                configuration={
                    "datasets": ",".join(dataset_ids),
                    "models": ",".join(models_to_run),
                    "iterations": str(iterations),
                },
                matrix=matrix,
                failed_iterations_count=failed_iters,
                total_iterations_count=total_iters,
            )
            summary_md_ckpt = _build_data_fusion_summary_markdown(summary_ckpt)
            summary_csv_ckpt = _build_data_fusion_summary_csv(summary_ckpt)
            BenchmarkReportWriter.checkpoint_summaries(
                run_dir=run_dir,
                summary_data=summary_ckpt,
                summary_rows=summary_csv_ckpt,
                markdown_content=summary_md_ckpt,
            )

    summary = BenchmarkRunSummary(
        run_id=run_id,
        models=models_to_run,
        datasets=dataset_ids,
        iterations=iterations,
        configuration={
            "datasets": ",".join(dataset_ids),
            "models": ",".join(models_to_run),
            "iterations": str(iterations),
        },
        matrix=matrix,
        failed_iterations_count=failed_iters,
        total_iterations_count=total_iters,
    )

    summary_md = _build_data_fusion_summary_markdown(summary)
    summary_csv = _build_data_fusion_summary_csv(summary)
    BenchmarkReportWriter.checkpoint_summaries(
        run_dir=run_dir,
        summary_data=summary,
        summary_rows=summary_csv,
        markdown_content=summary_md,
    )

    # Render console table
    table_cols = [
        "Dataset",
        "Model / Strategy",
        "Abs F1 (Mean ± Std)",
        "Reach F1 (Mean ± Std)",
        "Latency (s)",
        "Tokens",
        "Cost (USD)",
        "Consensus",
        "Status",
    ]
    table_rows = []
    for ds in summary.datasets:
        for model in summary.models:
            m = summary.matrix.get(ds, {}).get(model)
            if not m:
                continue
            abs_f1_str = (
                f"{m.mean_abs_f1:.2%} ± {m.std_abs_f1:.2%}"
                if summary.iterations > 1
                else f"{m.mean_abs_f1:.2%}"
            )
            reach_f1_str = (
                f"{m.mean_reach_f1:.2%} ± {m.std_reach_f1:.2%}"
                if summary.iterations > 1
                else f"{m.mean_reach_f1:.2%}"
            )
            succ = m.successful_iterations_count
            tot = len(m.iterations)
            stat_str = (
                f"[green]{succ}/{tot} OK[/green]"
                if succ == tot
                else f"[red]{succ}/{tot} OK[/red]"
            )
            table_rows.append([
                ds,
                model,
                abs_f1_str,
                reach_f1_str,
                f"{m.mean_latency_seconds:.2f}s",
                f"{m.total_tokens:,}",
                f"${m.estimated_cost_usd:.4f}",
                f"{m.strategy_consensus_ratio:.2%}",
                stat_str,
            ])
    BenchmarkReportWriter.render_rich_table(
        "Data Fusion Benchmark Summary", table_cols, table_rows
    )

    console.print(
        f"\n[green]✔ Data Fusion benchmark complete! Reports written to directory:\n{run_dir}[/green]"
    )
    return summary


def retry_data_fusion_benchmark_run(
    run_target: str | Path,
    dataset_filter: list[str] | None = None,
    model_filter: list[str] | None = None,
    output_dir: Path | None = None,
) -> BenchmarkRunSummary:
    """Retries only failed iterations in an existing Data Fusion benchmark run in-place."""
    base_out = output_dir or config.DF_BENCHMARK_OUTPUT_DIR
    run_dir = RunResilienceHelper.resolve_run_dir(run_target, base_out)
    console.print(
        f"[cyan]Resolving Data Fusion run directory for retry:[/] {run_dir}"
    )

    failed_items = RunResilienceHelper.find_failed_iterations(
        run_dir,
        dataset_filter=dataset_filter,
        model_filter=model_filter,
    )

    if not failed_items:
        console.print(
            "[green]No failed iterations found to retry in this run directory![/green]"
        )
        summary_path = run_dir / "summary.json"
        if summary_path.exists():
            return BenchmarkRunSummary.model_validate_json(
                summary_path.read_text(encoding="utf-8")
            )
        return BenchmarkRunSummary(
            run_id=run_dir.name,
            models=[],
            datasets=[],
        )

    console.print(
        f"[yellow]Found {len(failed_items)} failed iteration(s) to re-execute.[/yellow]\n"
    )

    loader = BenchmarkDataLoader()
    evaluator = DataFusionEvaluator()

    for item in failed_items:
        ds_name = item.dataset_name
        m_name = item.model_name
        iter_idx = item.iteration_index
        model_ds_dir = item.target_dir
        iter_dir = RunLayoutManager.get_iteration_dir(model_ds_dir, iter_idx)

        status_msg = f"Retrying [{ds_name} | {m_name}] iteration {iter_idx}..."
        with console.status(f"[dim]{status_msg}[/dim]", spinner="dots"):
            new_metric, trace_rec = _run_single_df_iteration(
                loader=loader,
                evaluator=evaluator,
                dataset_id=ds_name,
                model_name=m_name,
                iteration_index=iter_idx,
                iter_dir=iter_dir,
            )

        if new_metric.status != RunStatus.SUCCESS:
            console.print(
                f"  [bold red]✖ Retry Iter {iter_idx} FAILED ({ds_name} | {m_name}):[/] "
                f"[red]{new_metric.error_message}[/red]"
            )
        else:
            cost_str = (
                f" │ [cyan]Cost:[/] ${new_metric.token_usage.cost_usd:.4f}"
                if new_metric.token_usage.cost_usd is not None
                else ""
            )
            tok_str = (
                f" │ [magenta]Tokens:[/] {new_metric.token_usage.total_tokens:,}"
                if new_metric.token_usage.total_tokens > 0
                else ""
            )
            lat_str = f"[dim]Time:[/] {new_metric.latency_seconds:.2f}s"
            if new_metric.policy_synthesis_latency_seconds > 0:
                lat_str += f" [dim](synth: {new_metric.policy_synthesis_latency_seconds:.1f}s, exec: {new_metric.execution_latency_seconds:.2f}s)[/dim]"
            console.print(
                f"  [green]✔ Retry Iter {iter_idx} OK[/green] ({ds_name} | {m_name}) │ "
                f"[bold]Abs F1:[/] {new_metric.absolute_metrics.f1:.4f} │ "
                f"[bold]Reach F1:[/] {new_metric.reachable_metrics.f1:.4f} │ "
                f"{lat_str}{tok_str}{cost_str}"
            )

        # Merge into existing metrics.json
        metrics_file = model_ds_dir / "metrics.json"
        if metrics_file.exists():
            existing_dm = FusionDatasetAggregatedMetrics.model_validate_json(
                metrics_file.read_text(encoding="utf-8")
            )
            updated_iterations: list[FusionIterationMetrics] = []
            replaced = False
            for it in existing_dm.iterations:
                if it.iteration_index == iter_idx:
                    updated_iterations.append(new_metric)
                    replaced = True
                else:
                    updated_iterations.append(it)
            if not replaced:
                updated_iterations.append(new_metric)
            updated_iterations.sort(key=lambda it: it.iteration_index)

            updated_dm = _aggregate_data_fusion_metrics(
                dataset_id=ds_name,
                model_name=m_name,
                iterations=updated_iterations,
            )
            BenchmarkReportWriter.save_json(updated_dm, metrics_file)

            # Append trace
            trace_line = json.dumps(trace_rec, default=str) + "\n"
            trace_file = model_ds_dir / "execution_trace.jsonl"
            if trace_file.exists():
                trace_file.write_text(
                    trace_file.read_text(encoding="utf-8") + trace_line,
                    encoding="utf-8",
                )
            else:
                trace_file.write_text(trace_line, encoding="utf-8")

    # Rebuild top-level summary across all datasets
    datasets_dir = run_dir / "datasets"
    matrix: dict[str, dict[str, FusionDatasetAggregatedMetrics]] = {}
    all_datasets: set[str] = set()
    all_models: set[str] = set()
    total_iters = 0
    failed_iters = 0

    if datasets_dir.exists():
        for metrics_file in sorted(datasets_dir.glob("**/metrics.json")):
            target_dir = metrics_file.parent
            rel_parts = target_dir.relative_to(datasets_dir).parts
            if len(rel_parts) < 2:
                continue
            d_name = rel_parts[0]
            m_name = rel_parts[1]
            if d_name not in matrix:
                matrix[d_name] = {}
            dm = FusionDatasetAggregatedMetrics.model_validate_json(
                metrics_file.read_text(encoding="utf-8")
            )
            matrix[d_name][m_name] = dm
            all_datasets.add(d_name)
            all_models.add(m_name)
            total_iters += len(dm.iterations)
            failed_iters += dm.failed_iterations_count

    summary = BenchmarkRunSummary(
        run_id=run_dir.name,
        timestamp=datetime.now(timezone.utc).isoformat(),
        models=sorted(all_models),
        datasets=sorted(all_datasets),
        iterations=max(
            (len(dm.iterations) for d in matrix.values() for dm in d.values()),
            default=1,
        ),
        matrix=matrix,
        failed_iterations_count=failed_iters,
        total_iterations_count=total_iters,
    )

    summary_md = _build_data_fusion_summary_markdown(summary)
    summary_csv = _build_data_fusion_summary_csv(summary)
    BenchmarkReportWriter.checkpoint_summaries(
        run_dir=run_dir,
        summary_data=summary,
        summary_rows=summary_csv,
        markdown_content=summary_md,
    )

    console.print(
        f"[bold green]✔ In-place retry completed for Data Fusion run:[/] {run_dir}\n"
    )
    return summary


def main() -> None:
    """Main CLI runner entry point for Data Fusion Benchmarking."""
    parser = argparse.ArgumentParser(
        description="Data Fusion Benchmarking Runner."
    )
    parser.add_argument(
        "--datasets",
        type=str,
        nargs="*",
        default=["all"],
        help="Space-separated list of dataset IDs (or 'all').",
    )
    parser.add_argument(
        "--models",
        type=str,
        nargs="*",
        default=[],
        help="Space-separated list of LLM models to run.",
    )
    parser.add_argument(
        "--baselines",
        type=str,
        nargs="*",
        default=[],
        help="Space-separated list of baselines ('trust_a', 'trust_b', or 'all').",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=1,
        help="Number of run iterations.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Optional target output directory.",
    )
    parser.add_argument(
        "--retry-run",
        "--resume",
        type=str,
        default=None,
        help="Retry failed iterations for an existing run target ('latest', ID, or path).",
    )

    args = parser.parse_args()

    if args.retry_run:
        retry_data_fusion_benchmark_run(
            run_target=args.retry_run,
            dataset_filter=args.datasets if "all" not in args.datasets else None,
            model_filter=args.models if args.models else None,
            output_dir=Path(args.output_dir) if args.output_dir else None,
        )
    else:
        run_data_fusion_benchmark(
            datasets=args.datasets,
            models=args.models,
            baselines=args.baselines,
            iterations=args.iterations,
            output_dir=args.output_dir,
        )


if __name__ == "__main__":
    main()
