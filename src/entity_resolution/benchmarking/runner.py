"""Overhauled Entity Resolution benchmarking harness.

Provides multi-iteration execution, failure resilience, automated metric
aggregation with flakiness analysis, and targeted in-place retry capabilities.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from entity_resolution.dataset_loader import discover_and_load
from entity_resolution.evaluation import evaluate_entity_resolution_run
from entity_resolution.exporter import EntityResolutionExporter
from entity_resolution.models import TableResource
from entity_resolution.pipeline import run_entity_resolution
from shared.benchmarking import (
    BenchmarkReportWriter,
)
from shared.config import config
from shared.console import console
from shared.profiling.engine import DataProfiler
from shared.schema_models import TableField, TableSchema

from .common.models import (
    ERDatasetMetrics,
    ERFlakinessAnalysis,
    ERIterationMetrics,
    ERRunSummary,
    RunStatus,
    TokenUsage,
    compute_mean_std,
)
from .common.reporting import (
    build_dataset_markdown_report,
    build_run_summary_csv,
    build_run_summary_markdown,
    export_csv,
    export_json,
    render_rich_table,
)
from .common.resilience import (
    find_failed_iterations,
    merge_iteration_result,
    resolve_run_directory,
)
from .models import BenchmarkConfig

logger = logging.getLogger(__name__)


async def _run_single_iteration(
    dataset: Any,
    model_name: str,
    iteration_index: int,
    run_dir: Path,
    save_csvs: bool = True,
) -> tuple[ERIterationMetrics, dict[str, Any], set[tuple[Any, Any]]]:
    """Executes a single benchmark iteration with full exception safety.

    Args:
        dataset: Loaded ER dataset object.
        model_name: Model identifier string.
        iteration_index: Current 1-based iteration counter.
        run_dir: Target benchmark run root directory.
        save_csvs: Whether to export classified pair CSV files.

    Returns:
        Tuple of (ERIterationMetrics, execution trace dict, set of match pair IDs)
    """
    safe_model = model_name.replace(":", "_").replace("/", "_")
    model_ds_dir = run_dir / "datasets" / dataset.name / safe_model
    model_ds_dir.mkdir(parents=True, exist_ok=True)

    df_a = dataset.table_a
    df_b = dataset.table_b
    ground_truth = dataset.ground_truth

    try:
        # 1. Profile inputs and build TableResource
        profile_a = DataProfiler.profile_dataframe(df_a, f"{dataset.name}_a")
        profile_b = DataProfiler.profile_dataframe(df_b, f"{dataset.name}_b")
        all_cols = list(dict.fromkeys(list(df_a.columns) + list(df_b.columns)))
        fields = [TableField(name=col, type="string") for col in all_cols]
        table_resource = TableResource(
            name=dataset.name, schema=TableSchema(fields=fields)
        )

        # 2. Execute ER pipeline
        result = await run_entity_resolution(
            df_a_clean=df_a,
            df_b_clean=df_b,
            profile_a=profile_a,
            profile_b=profile_b,
            table_resource=table_resource,
            model_name=model_name,
        )

        # 3. Domain-restricted filtering for sampled datasets
        if (
            dataset.ground_truth_type.value == "sampled"
            and dataset.candidates is not None
        ):
            domain_idx = dataset.candidates
            if not result.matches.empty:
                result.matches = result.matches.loc[
                    result.matches.index.intersection(domain_idx)
                ]
            if not result.uncertain.empty:
                result.uncertain = result.uncertain.loc[
                    result.uncertain.index.intersection(domain_idx)
                ]
            if not result.non_matches.empty:
                result.non_matches = result.non_matches.loc[
                    result.non_matches.index.intersection(domain_idx)
                ]

        # 4. Evaluate run without generating HTML
        report = evaluate_entity_resolution_run(
            result=result,
            ground_truth=ground_truth,
            table_name=dataset.name,
            save_html=False,
            output_dir=None,
        )

        # 5. Extract token usage and latency
        p_tok = 0
        c_tok = 0
        tot_tok = 0
        lat_sec = 0.0
        cost_usd: float | None = None

        if result.er_config_metadata:
            p_tok += result.er_config_metadata.prompt_tokens
            c_tok += result.er_config_metadata.completion_tokens
            tot_tok += result.er_config_metadata.total_tokens
            lat_sec += result.er_config_metadata.execution_time_seconds
            if result.er_config_metadata.cost_usd is not None:
                cost_usd = (cost_usd or 0.0) + result.er_config_metadata.cost_usd

        if result.er_refinement_metadata:
            p_tok += result.er_refinement_metadata.prompt_tokens
            c_tok += result.er_refinement_metadata.completion_tokens
            tot_tok += result.er_refinement_metadata.total_tokens
            lat_sec += result.er_refinement_metadata.execution_time_seconds
            if result.er_refinement_metadata.cost_usd is not None:
                cost_usd = (
                    cost_usd or 0.0
                ) + result.er_refinement_metadata.cost_usd

        token_usage = TokenUsage(
            prompt_tokens=p_tok,
            completion_tokens=c_tok,
            total_tokens=tot_tok,
            latency_seconds=lat_sec,
            cost_usd=cost_usd,
        )

        match_eval = report.matching.metrics
        idx_eval = report.indexing

        # 6. Extract match pairs for flakiness tracking
        match_pairs: set[tuple[Any, Any]] = set()
        if not result.matches.empty:
            match_pairs = set(result.matches.index.tolist())

        # 7. Optionally save classified CSVs
        if save_csvs:
            EntityResolutionExporter._export_csv(
                result.matches,
                df_a,
                df_b,
                model_ds_dir / "matches.csv",
                ground_truth=ground_truth,
            )
            EntityResolutionExporter._export_csv(
                result.uncertain,
                df_a,
                df_b,
                model_ds_dir / "uncertain.csv",
                ground_truth=ground_truth,
            )
            EntityResolutionExporter._export_csv(
                result.non_matches,
                df_a,
                df_b,
                model_ds_dir / "non_matches.csv",
                ground_truth=ground_truth,
            )

        iteration_metric = ERIterationMetrics(
            iteration_index=iteration_index,
            status=RunStatus.SUCCESS,
            precision=match_eval.precision,
            recall=match_eval.recall,
            f1=match_eval.f1,
            tp=match_eval.tp,
            fp=match_eval.fp,
            fn=match_eval.fn,
            tn=match_eval.tn,
            support=report.num_ground_truth_matches,
            candidates=idx_eval.num_candidates,
            pairs_recall=idx_eval.pairs_recall,
            reduction_ratio=idx_eval.reduction_ratio,
            latency_seconds=lat_sec,
            token_usage=token_usage,
        )

        trace_dict = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "iteration": iteration_index,
            "status": "SUCCESS",
            "f1": match_eval.f1,
            "precision": match_eval.precision,
            "recall": match_eval.recall,
            "latency_seconds": lat_sec,
            "tokens": tot_tok,
        }

        console.print(
            f"[green]✓ Iteration {iteration_index}:[/] F1={match_eval.f1:.4f} | "
            f"P={match_eval.precision:.4f} | R={match_eval.recall:.4f} "
            f"({lat_sec:.2f}s)"
        )
        return iteration_metric, trace_dict, match_pairs

    except Exception as exc:  # noqa: BLE001
        tb_str = traceback.format_exc()
        err_msg = str(exc).strip() or type(exc).__name__
        console.print(
            f"[red]✗ Iteration {iteration_index} Failed:[/] {err_msg}\n"
        )
        iteration_metric = ERIterationMetrics(
            iteration_index=iteration_index,
            status=RunStatus.FAILED,
            error_message=err_msg,
            traceback=tb_str,
            latency_seconds=0.0,
        )
        trace_dict = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "iteration": iteration_index,
            "status": "FAILED",
            "error": err_msg,
            "traceback": tb_str,
        }
        return iteration_metric, trace_dict, set()


def _aggregate_dataset_metrics(
    dataset_name: str,
    domain: str,
    num_rows_a: int,
    num_rows_b: int,
    ground_truth_count: int,
    iterations: list[ERIterationMetrics],
    match_pairs_list: list[set[tuple[Any, Any]]],
) -> ERDatasetMetrics:
    """Aggregates metrics and stochastic flakiness across iterations.

    Args:
        dataset_name: Dataset name.
        domain: Domain label.
        num_rows_a: Row count for table A.
        num_rows_b: Row count for table B.
        ground_truth_count: Total true match pairs.
        iterations: List of iteration metric objects.
        match_pairs_list: List of sets of match pair IDs per successful iteration.

    Returns:
        Aggregated ERDatasetMetrics instance.
    """
    successful = [
        it for it in iterations if it.status == RunStatus.SUCCESS
    ]

    f1_stats = compute_mean_std([it.f1 for it in successful])
    prec_stats = compute_mean_std([it.precision for it in successful])
    rec_stats = compute_mean_std([it.recall for it in successful])
    pr_stats = compute_mean_std([it.pairs_recall for it in successful])
    rr_stats = compute_mean_std([it.reduction_ratio for it in successful])
    lat_stats = compute_mean_std([it.latency_seconds for it in successful])

    prompt_tokens = sum(it.token_usage.prompt_tokens for it in iterations)
    completion_tokens = sum(
        it.token_usage.completion_tokens for it in iterations
    )
    total_tokens = sum(it.token_usage.total_tokens for it in iterations)
    estimated_cost = sum(
        it.token_usage.cost_usd or 0.0 for it in iterations
    )

    flakiness_analysis = None
    if len(successful) > 1 and match_pairs_list:
        all_unique_pairs: set[tuple[Any, Any]] = set().union(
            *match_pairs_list
        )
        total_runs = len(successful)
        consistent_matches: list[tuple[str, str]] = []
        flaky_matches: dict[str, float] = {}

        for pair in all_unique_pairs:
            pair_key = f"({pair[0]}, {pair[1]})"
            appearances = sum(1 for pset in match_pairs_list if pair in pset)
            freq = appearances / total_runs
            if appearances == total_runs:
                consistent_matches.append((str(pair[0]), str(pair[1])))
            else:
                flaky_matches[pair_key] = round(freq, 4)

        stability_ratio = (
            len(consistent_matches) / len(all_unique_pairs)
            if all_unique_pairs
            else 1.0
        )
        flakiness_analysis = ERFlakinessAnalysis(
            consistent_matches=consistent_matches,
            flaky_matches=flaky_matches,
            stability_ratio=round(stability_ratio, 4),
        )

    return ERDatasetMetrics(
        dataset_name=dataset_name,
        domain=domain,
        num_rows_a=num_rows_a,
        num_rows_b=num_rows_b,
        ground_truth_count=ground_truth_count,
        iterations=iterations,
        mean_precision=prec_stats.mean,
        std_precision=prec_stats.std,
        mean_recall=rec_stats.mean,
        std_recall=rec_stats.std,
        mean_f1=f1_stats.mean,
        std_f1=f1_stats.std,
        mean_pairs_recall=pr_stats.mean,
        std_pairs_recall=pr_stats.std,
        mean_reduction_ratio=rr_stats.mean,
        std_reduction_ratio=rr_stats.std,
        mean_latency=lat_stats.mean,
        std_latency=lat_stats.std,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        estimated_cost_usd=round(estimated_cost, 6),
        flakiness_analysis=flakiness_analysis,
    )


def _save_dataset_artifacts(
    model_ds_dir: Path,
    ds_metrics: ERDatasetMetrics,
    traces: list[dict[str, Any]],
    append_traces: bool = False,
) -> None:
    """Writes dataset artifacts (metrics.json, report.md, traces.jsonl).

    Args:
        model_ds_dir: Directory for dataset and model outputs.
        ds_metrics: Aggregated dataset metrics container.
        traces: Execution traces list.
        append_traces: Whether to append to traces.jsonl instead of overwrite.
    """
    model_ds_dir.mkdir(parents=True, exist_ok=True)

    # 1. metrics.json
    export_json(ds_metrics, model_ds_dir / "metrics.json")

    # 2. report.md
    model_name = model_ds_dir.name
    report_md = build_dataset_markdown_report(ds_metrics, model_name=model_name)
    (model_ds_dir / "report.md").write_text(report_md, encoding="utf-8")

    # 3. traces.jsonl
    mode = "a" if append_traces else "w"
    with open(model_ds_dir / "traces.jsonl", mode, encoding="utf-8") as f:
        f.writelines(json.dumps(t) + "\n" for t in traces)


async def run_entity_resolution_benchmark(
    bench_config: BenchmarkConfig,
    output_dir: Path | None = None,
) -> ERRunSummary:
    """Executes multi-iteration ER benchmark across datasets and models.

    Args:
        bench_config: Execution configuration.
        output_dir: Optional root output directory.

    Returns:
        Master ERRunSummary container.
    """
    console.print(
        f"[dim]Discovering datasets for "
        f"domain='{bench_config.dataset_domain}'...[/]"
    )
    datasets_to_run = discover_and_load(
        data_dir=str(config.ER_DATASETS_DIR),
        domain=bench_config.dataset_domain,
        dataset_names=bench_config.datasets,
    )

    if not datasets_to_run:
        console.print(
            "[yellow]⚠ No matching datasets found — nothing to benchmark.[/]"
        )
        return ERRunSummary(
            run_id="run_empty",
            models=bench_config.models,
            datasets=[],
            iterations=bench_config.iterations,
        )

    console.print(
        f"[green]Found {len(datasets_to_run)} dataset(s):[/] "
        f"{', '.join(d.name for d in datasets_to_run)}\n"
    )

    total_evals = (
        len(datasets_to_run)
        * len(bench_config.models)
        * bench_config.iterations
    )
    console.print(
        f"[dim]Starting: {len(datasets_to_run)} dataset(s) × "
        f"{len(bench_config.models)} model(s) × "
        f"{bench_config.iterations} iteration(s) = {total_evals} total[/]\n"
    )

    timestamp = datetime.now(timezone.utc)
    run_id = f"run_{timestamp.strftime('%Y%m%d_%H%M%S')}"
    base_out = (
        output_dir or bench_config.output_dir or config.ER_BENCHMARK_OUTPUT_DIR
    )
    run_dir = base_out / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    matrix: dict[str, dict[str, ERDatasetMetrics]] = {}
    total_iterations_count = 0
    failed_iterations_count = 0

    save_csvs = not bench_config.no_pair_csvs

    for dataset in datasets_to_run:
        ds_name = dataset.name
        matrix[ds_name] = {}

        for model_name in bench_config.models:
            safe_model = model_name.replace(":", "_").replace("/", "_")
            model_ds_dir = run_dir / "datasets" / ds_name / safe_model

            iteration_metrics: list[ERIterationMetrics] = []
            traces: list[dict[str, Any]] = []
            successful_pair_sets: list[set[tuple[Any, Any]]] = []

            for i in range(1, bench_config.iterations + 1):
                total_iterations_count += 1
                console.print(
                    f"\n[cyan]▶ Evaluating dataset '{ds_name}' with model "
                    f"'{model_name}' (Iteration {i}/{bench_config.iterations})...[/]"
                )

                metric, trace, pair_set = await _run_single_iteration(
                    dataset=dataset,
                    model_name=model_name,
                    iteration_index=i,
                    run_dir=run_dir,
                    save_csvs=save_csvs,
                )
                iteration_metrics.append(metric)
                traces.append(trace)

                if metric.status == RunStatus.SUCCESS:
                    successful_pair_sets.append(pair_set)
                else:
                    failed_iterations_count += 1

            # Aggregate dataset metrics
            ds_metrics = _aggregate_dataset_metrics(
                dataset_name=ds_name,
                domain=bench_config.dataset_domain,
                num_rows_a=len(dataset.table_a),
                num_rows_b=len(dataset.table_b),
                ground_truth_count=len(dataset.ground_truth),
                iterations=iteration_metrics,
                match_pairs_list=successful_pair_sets,
            )

            _save_dataset_artifacts(
                model_ds_dir=model_ds_dir,
                ds_metrics=ds_metrics,
                traces=traces,
                append_traces=False,
            )
            matrix[ds_name][model_name] = ds_metrics

            # Progressive summary checkpointing
            summary_ckpt = ERRunSummary(
                run_id=run_id,
                timestamp=timestamp,
                models=bench_config.models,
                datasets=[d.name for d in datasets_to_run],
                iterations=bench_config.iterations,
                matrix=matrix,
                failed_iterations_count=failed_iterations_count,
                total_iterations_count=total_iterations_count,
            )
            summary_md_ckpt = build_run_summary_markdown(summary_ckpt)
            csv_rows_ckpt = build_run_summary_csv(summary_ckpt)
            BenchmarkReportWriter.checkpoint_summaries(
                run_dir=run_dir,
                summary_data=summary_ckpt,
                summary_rows=csv_rows_ckpt,
                markdown_content=summary_md_ckpt,
            )

    # Build master summary container
    summary = ERRunSummary(
        run_id=run_id,
        timestamp=timestamp,
        models=bench_config.models,
        datasets=[d.name for d in datasets_to_run],
        iterations=bench_config.iterations,
        matrix=matrix,
        failed_iterations_count=failed_iterations_count,
        total_iterations_count=total_iterations_count,
    )

    summary_md = build_run_summary_markdown(summary)
    csv_rows = build_run_summary_csv(summary)
    BenchmarkReportWriter.checkpoint_summaries(
        run_dir=run_dir,
        summary_data=summary,
        summary_rows=csv_rows,
        markdown_content=summary_md,
    )

    # Render terminal console tables
    table_cols = [
        "Dataset",
        "Model",
        "F1 (Mean ± Std)",
        "Precision",
        "Recall",
        "Pairs Recall",
        "Red. Ratio",
        "Status",
    ]
    table_rows = []
    for ds_name in summary.datasets:
        for model_name in summary.models:
            dm = summary.matrix[ds_name][model_name]
            succ = dm.successful_iterations_count
            tot = len(dm.iterations)
            stat_str = (
                f"[green]{succ}/{tot} OK[/]"
                if succ == tot
                else f"[red]{succ}/{tot} OK[/]"
            )
            table_rows.append([
                ds_name,
                model_name,
                f"{dm.mean_f1:.4f} ± {dm.std_f1:.4f}",
                f"{dm.mean_precision:.4f}",
                f"{dm.mean_recall:.4f}",
                f"{dm.mean_pairs_recall:.4f}",
                f"{dm.mean_reduction_ratio:.4f}",
                stat_str,
            ])
    render_rich_table("ER Benchmark Summary", table_cols, table_rows)

    if summary.failed_iterations_count > 0:
        fail_cols = ["Dataset", "Model", "Iter", "Error Snippet"]
        fail_rows = []
        for ds_name in summary.datasets:
            for model_name in summary.models:
                dm = summary.matrix[ds_name][model_name]
                for it in dm.iterations:
                    if it.status == RunStatus.FAILED:
                        err_msg = it.error_message or "Failed"
                        if len(err_msg) > 60:
                            err_msg = err_msg[:57] + "..."
                        fail_rows.append([
                            ds_name,
                            model_name,
                            str(it.iteration_index),
                            err_msg,
                        ])
        render_rich_table(
            "Failed Benchmark Runs",
            fail_cols,
            fail_rows,
            header_style="bold red",
        )
        console.print(
            f"[yellow]💡 To retry failed runs: "
            f"[bold]uv run er-benchmark --retry {run_id}[/bold][/yellow]\n"
        )

    console.print(f"[green]Benchmark completed! Run directory:[/] {run_dir}\n")
    return summary


async def retry_benchmark_run(
    run_target: str | Path,
    dataset_filter: list[str] | None = None,
    model_filter: list[str] | None = None,
    output_dir: Path | None = None,
    save_csvs: bool = True,
) -> ERRunSummary:
    """Finds and re-executes only the failed iterations for an existing run.

    Merges new results into metrics.json and updates root summary files in-place.

    Args:
        run_target: Run folder, run ID string, or 'latest'.
        dataset_filter: Optional subset of datasets to retry.
        model_filter: Optional subset of models to retry.
        output_dir: Base directory if relative run ID is used.
        save_csvs: Whether to export classified CSV files on retry.

    Returns:
        Updated ERRunSummary.
    """
    base_out = output_dir or config.ER_BENCHMARK_OUTPUT_DIR
    run_dir = resolve_run_directory(
        run_target,
        base_out,
        fallback_dirs=[config.LEGACY_ER_BENCHMARK_OUTPUT_DIR],
    )
    console.print(f"[cyan]Resolving run directory for retry:[/] {run_dir}")

    failed_items = find_failed_iterations(
        run_dir,
        dataset_filter=dataset_filter,
        model_filter=model_filter,
    )

    if not failed_items:
        console.print(
            "[green]No failed iterations found to retry in this run directory![/]"
        )
        summary_path = run_dir / "summary.json"
        if summary_path.exists():
            return ERRunSummary.model_validate_json(
                summary_path.read_text(encoding="utf-8")
            )
        return ERRunSummary(
            run_id=run_dir.name,
            models=[],
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

    # Execute failed iterations
    for ds_name, model_slug, iteration_index, model_ds_dir in failed_items:
        dataset = dataset_map.get(ds_name)
        if not dataset:
            console.print(
                f"[red]Could not load dataset '{ds_name}' to retry iteration {iteration_index}.[/]"
            )
            continue

        model_name = model_slug.replace("_", ":")

        console.print(
            f"[cyan]▶ Retrying {ds_name} | {model_name} | "
            f"Iteration {iteration_index}...[/]"
        )

        new_metric, trace_dict, _ = await _run_single_iteration(
            dataset=dataset,
            model_name=model_name,
            iteration_index=iteration_index,
            run_dir=run_dir,
            save_csvs=save_csvs,
        )

        metrics_file = model_ds_dir / "metrics.json"
        if metrics_file.exists():
            dm = ERDatasetMetrics.model_validate_json(
                metrics_file.read_text(encoding="utf-8")
            )
            updated_dm = merge_iteration_result(dm, new_metric)
            _save_dataset_artifacts(
                model_ds_dir=model_ds_dir,
                ds_metrics=updated_dm,
                traces=[trace_dict],
                append_traces=True,
            )

    # Reload all dataset metrics to rebuild root summary
    datasets_dir = run_dir / "datasets"
    matrix: dict[str, dict[str, ERDatasetMetrics]] = {}
    total_iters = 0
    failed_iters = 0
    all_models: set[str] = set()
    all_datasets: set[str] = set()

    if datasets_dir.exists():
        for ds_dir in sorted(datasets_dir.iterdir()):
            if not ds_dir.is_dir():
                continue
            d_name = ds_dir.name
            matrix[d_name] = {}
            all_datasets.add(d_name)

            for m_dir in sorted(ds_dir.iterdir()):
                if not m_dir.is_dir():
                    continue
                m_slug = m_dir.name
                metrics_file = m_dir / "metrics.json"
                if not metrics_file.exists():
                    continue

                dm = ERDatasetMetrics.model_validate_json(
                    metrics_file.read_text(encoding="utf-8")
                )
                matrix[d_name][m_slug] = dm
                all_models.add(m_slug)
                total_iters += len(dm.iterations)
                failed_iters += dm.failed_iterations_count

    summary_file = run_dir / "summary.json"
    prev_run_id = run_dir.name
    prev_iterations = 1
    if summary_file.exists():
        try:
            prev_sum = ERRunSummary.model_validate_json(
                summary_file.read_text(encoding="utf-8")
            )
            prev_run_id = prev_sum.run_id
            prev_iterations = prev_sum.iterations
        except (ValueError, json.JSONDecodeError) as err:
            logger.debug("Could not read previous summary: %s", err)

    updated_summary = ERRunSummary(
        run_id=prev_run_id,
        timestamp=datetime.now(timezone.utc),
        models=sorted(all_models),
        datasets=sorted(all_datasets),
        iterations=prev_iterations,
        matrix=matrix,
        failed_iterations_count=failed_iters,
        total_iterations_count=total_iters,
    )

    # Overwrite summary files in-place
    export_json(updated_summary, run_dir / "summary.json")

    summary_md = build_run_summary_markdown(updated_summary)
    (run_dir / "summary.md").write_text(summary_md, encoding="utf-8")

    csv_rows = build_run_summary_csv(updated_summary)
    export_csv(csv_rows, run_dir / "summary.csv")

    console.print(
        f"\n[green]Retry complete for run '{run_dir.name}'! In-place artifacts updated.[/]"
    )
    return updated_summary


def main():
    """Main CLI entry point for er-benchmark."""
    parser = argparse.ArgumentParser(
        description="Run ER Benchmarking Harness with Resilience and Retry"
    )
    parser.add_argument(
        "--models",
        nargs="+",
        default=[config.DEFAULT_GOOGLE_MODEL],
        help="List of model names to evaluate.",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=1,
        help="Number of iterations to execute per dataset (legacy alias).",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=None,
        help="Number of iterations to execute per dataset.",
    )
    parser.add_argument(
        "--datasets",
        nargs="*",
        default=None,
        help="Specific dataset names to evaluate.",
    )
    parser.add_argument(
        "--domain",
        type=str,
        default="all",
        help="Domain of datasets (e-commerce, citations, movies, synthetic, or all).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Base directory for benchmark outputs.",
    )
    parser.add_argument(
        "--no-pair-csvs",
        action="store_true",
        help="Skip generating large classified candidate pair CSV files.",
    )
    parser.add_argument(
        "--retry",
        type=str,
        default=None,
        help="Run ID, path, or 'latest' to rerun failed iterations in-place.",
    )

    args = parser.parse_args()

    if args.retry:
        asyncio.run(
            retry_benchmark_run(
                run_target=args.retry,
                dataset_filter=args.datasets,
                model_filter=args.models,
                output_dir=args.output_dir,
                save_csvs=not args.no_pair_csvs,
            )
        )
        return

    iterations = (
        args.iterations if args.iterations is not None else args.runs
    )
    conf = BenchmarkConfig(
        models=args.models,
        runs=iterations,
        iterations=iterations,
        datasets=args.datasets,
        dataset_domain=args.domain,
        no_pair_csvs=args.no_pair_csvs,
        output_dir=args.output_dir,
    )
    asyncio.run(
        run_entity_resolution_benchmark(conf, output_dir=args.output_dir)
    )


if __name__ == "__main__":
    main()