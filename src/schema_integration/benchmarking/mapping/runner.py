"""Benchmark execution engine and CLI runner for schema mapping."""

from __future__ import annotations

import argparse
import asyncio
import csv
import hashlib
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from schema_integration.alignment.models import AlignmentReport
from schema_integration.benchmarking.common.reporting import (
    BenchmarkReporter,
)
from schema_integration.benchmarking.mapping.baselines import (
    BaselineRunner,
)
from schema_integration.benchmarking.mapping.evaluation import (
    MappingEvaluator,
)
from schema_integration.benchmarking.mapping.loader import (
    BenchmarkDataset,
    SchemaMappingLoader,
)
from schema_integration.benchmarking.mapping.models import (
    BaselineResult,
    BenchmarkExperimentConfig,
    BenchmarkReport,
    DatasetBenchmarkResult,
    IterationResult,
    MatchMetrics,
)
from schema_integration.mapping.agent import MAPPING_SYSTEM_PROMPT, map_schema
from shared.benchmarking import RunLayoutManager, RunResilienceHelper
from shared.console import console

logger = logging.getLogger(__name__)


class MappingRunner:
    """Orchestrates benchmark runs on mapping datasets."""

    @classmethod
    async def run_llm_iteration(
        cls,
        dataset: BenchmarkDataset,
        model_name: str,
        iteration_index: int = 1,
    ) -> tuple[IterationResult, dict[str, Any]]:
        """Execute a single schema mapping iteration using the LLM agent.

        Args:
            dataset: Benchmark dataset to evaluate.
            model_name: Identifier of the LLM model.
            iteration_index: 1-based index of this iteration.

        Returns:
            Tuple of (IterationResult, execution trace dictionary).
        """
        source_json = dataset.source_package.model_dump_json(
            indent=2, by_alias=True
        )
        target_json = dataset.target_package.model_dump_json(
            indent=2, by_alias=True
        )
        user_prompt = (
            f"### SOURCE LABEL: {dataset.source_package.name}\n\n"
            f"### SOURCE SCHEMA\n{source_json}\n\n"
            f"### TARGET SCHEMA\n{target_json}\n\n"
            f"### CONCEPTUAL CONFLICT AUDIT LOG\n[]"
        )

        try:
            dummy_alignment = AlignmentReport(
                target_schema=dataset.target_package,
                conflict_report=[],
            )
            report, meta = await map_schema(
                source_schema=dataset.source_package,
                source_label=dataset.source_package.name,
                alignment_report=dummy_alignment,
                model_name=model_name,
            )

            it_res = MappingEvaluator.evaluate_mapping_iteration(
                report=report,
                dataset=dataset,
                metadata=meta,
                iteration_index=iteration_index,
            )
            trace = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "iteration": iteration_index,
                "dataset": dataset.name,
                "category": dataset.category,
                "model": model_name,
                "user_prompt": user_prompt,
                "precision": it_res.metrics.precision,
                "recall": it_res.metrics.recall,
                "f1": it_res.metrics.f1,
                "latency_seconds": it_res.latency_seconds,
                "total_tokens": it_res.token_usage.total_tokens,
                "cost_usd": it_res.token_usage.cost_usd,
                "retry_count": it_res.retry_count,
                "retry_log": it_res.retry_log,
            }
            return it_res, trace
        except Exception as e:  # noqa: BLE001
            err_msg = str(e).strip() or type(e).__name__
            console.print(
                f"    [bold red]Iteration {iteration_index} failed: {err_msg}[/bold red]"
            )
            err_res = IterationResult(
                iteration_index=iteration_index,
                category=dataset.category,
                metrics=MatchMetrics(
                    precision=0.0,
                    recall=0.0,
                    f1=0.0,
                    true_positives=0,
                    false_positives=0,
                    false_negatives=len(dataset.ground_truth),
                    predicted_pairs_count=0,
                    gold_pairs_count=len(dataset.ground_truth),
                ),
                latency_seconds=0.0,
                error_message=err_msg,
            )
            trace = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "iteration": iteration_index,
                "dataset": dataset.name,
                "category": dataset.category,
                "model": model_name,
                "user_prompt": user_prompt,
                "error_message": err_msg,
            }
            return err_res, trace

    @classmethod
    async def benchmark_dataset_llm(
        cls,
        dataset: BenchmarkDataset,
        model_name: str,
        iterations: int = 1,
    ) -> tuple[DatasetBenchmarkResult, list[dict[str, Any]]]:
        """Run benchmark iterations on a single dataset for a given LLM model.

        Args:
            dataset: Target benchmark dataset.
            model_name: LLM model identifier.
            iterations: Number of evaluation iterations.

        Returns:
            Tuple of (DatasetBenchmarkResult, list of iteration traces).
        """
        iteration_results: list[IterationResult] = []
        iteration_traces: list[dict[str, Any]] = []
        total_retries = 0

        for i in range(1, iterations + 1):
            console.print(
                f"  [cyan]Iteration {i}/{iterations}[/cyan] on "
                f"[bold]{dataset.name}[/bold] ({dataset.category}) "
                f"with model [yellow]{model_name}[/yellow]..."
            )
            it_res, trace = await cls.run_llm_iteration(
                dataset=dataset,
                model_name=model_name,
                iteration_index=i,
            )
            iteration_results.append(it_res)
            iteration_traces.append(trace)
            total_retries += it_res.retry_count
            if not it_res.error_message:
                console.print(
                    f"    [green]Precision: {it_res.metrics.precision:.2f} | "
                    f"Recall: {it_res.metrics.recall:.2f} | "
                    f"F1: {it_res.metrics.f1:.2f} | "
                    f"Latency: {it_res.latency_seconds:.1f}s[/green]"
                )

        agg_metrics = MappingEvaluator.aggregate_iterations(iteration_results)
        schema_info = dataset.to_schema_info()

        exp_config = BenchmarkExperimentConfig(
            prompt_template_snapshot=MAPPING_SYSTEM_PROMPT,
            instance_preview_included=False,
            provider="auto",
            model_name=model_name,
            max_retries=2,
        )

        result = DatasetBenchmarkResult(
            dataset_name=dataset.name,
            domain=dataset.domain,
            scenario=dataset.scenario,
            category=dataset.category,
            schema_info=schema_info,
            model_name=model_name,
            iterations=iterations,
            aggregated_metrics=agg_metrics,
            iteration_results=iteration_results,
            total_retries=total_retries,
            experiment_config=exp_config,
        )
        return result, iteration_traces

    @classmethod
    def benchmark_dataset_baseline(
        cls,
        dataset: BenchmarkDataset,
        baseline_name: str,
    ) -> BaselineResult | None:
        """Run a classical baseline matcher on a single dataset."""
        b_norm = baseline_name.strip().lower()
        schema_info = dataset.to_schema_info()

        if dataset.category == "multi_table":
            if b_norm == "exact":
                pred_pairs, latency = BaselineRunner.run_exact_multi_table(
                    dataset.source_package, dataset.target_package
                )
            else:
                return None
        else:
            if b_norm == "exact":
                pred_pairs, latency = BaselineRunner.run_exact(
                    dataset.source_df, dataset.target_df
                )
            else:
                pred_pairs, latency = BaselineRunner.run_valentine(
                    dataset.source_df, dataset.target_df, algorithm_name=b_norm
                )

        metrics = MappingEvaluator.compute_match_metrics(
            predicted_pairs=pred_pairs,
            ground_truth=dataset.ground_truth,
        )

        field_inspections = MappingEvaluator.build_field_inspections(
            dataset=dataset,
            predicted_pairs=pred_pairs,
        )

        return BaselineResult(
            baseline_name=baseline_name,
            dataset_name=dataset.name,
            domain=dataset.domain,
            scenario=dataset.scenario,
            category=dataset.category,
            schema_info=schema_info,
            metrics=metrics,
            latency_seconds=round(latency, 3),
            predicted_pairs=sorted(pred_pairs),
            tp_pairs=metrics.tp_pairs,
            fp_pairs=metrics.fp_pairs,
            fn_pairs=metrics.fn_pairs,
            field_inspections=field_inspections,
        )

    @classmethod
    def _save_dataset_artifacts(
        cls,
        model_ds_dir: Path,
        dataset: BenchmarkDataset,
        dr: DatasetBenchmarkResult,
        traces: list[dict[str, Any]] | None = None,
        append_traces: bool = False,
    ) -> None:
        """Save per-dataset, per-model artifacts (metrics, traces, reports)."""
        model_ds_dir.mkdir(parents=True, exist_ok=True)

        # Save metrics.json
        (model_ds_dir / "metrics.json").write_text(
            dr.model_dump_json(indent=2),
            encoding="utf-8",
        )

        # Save or append execution traces JSONL
        if traces:
            trace_file = model_ds_dir / "execution_trace.jsonl"
            mode = "a" if append_traces else "w"
            with open(trace_file, mode, encoding="utf-8") as f:
                for tr in traces:
                    f.write(json.dumps(tr) + "\n")

        # Save raw MappingReport from last valid iteration if exists
        valid_its = [
            it for it in dr.iteration_results if not it.error_message
        ]
        if valid_its and valid_its[-1].mapping_report:
            (model_ds_dir / "mapping_report.json").write_text(
                valid_its[-1].mapping_report.model_dump_json(indent=2),
                encoding="utf-8",
            )

        # Save per-iteration artifacts for multi-iteration inspectability
        if len(dr.iteration_results) > 1:
            iterations_dir = model_ds_dir / "iterations"
            iterations_dir.mkdir(parents=True, exist_ok=True)
            for it in dr.iteration_results:
                (iterations_dir / f"iteration_{it.iteration_index}.json").write_text(
                    it.model_dump_json(indent=2),
                    encoding="utf-8",
                )

    @staticmethod
    def _export_summary_csv(report: BenchmarkReport, file_path: Path) -> None:
        """Export flat tabular CSV with all model runs, iterations, and baselines."""
        fieldnames = [
            "dataset",
            "category",
            "domain",
            "scenario",
            "method_or_model",
            "type",
            "iteration",
            "status",
            "precision",
            "recall",
            "f1",
            "tp",
            "fp",
            "fn",
            "latency_seconds",
            "prompt_tokens",
            "completion_tokens",
            "total_tokens",
            "cost_usd",
            "retries",
            "error",
        ]

        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            # Baselines
            for b in report.baseline_results:
                writer.writerow(
                    {
                        "dataset": b.dataset_name,
                        "category": b.category,
                        "domain": b.domain,
                        "scenario": b.scenario,
                        "method_or_model": b.baseline_name,
                        "type": "baseline",
                        "iteration": 1,
                        "status": "SUCCESS",
                        "precision": b.metrics.precision,
                        "recall": b.metrics.recall,
                        "f1": b.metrics.f1,
                        "tp": b.metrics.true_positives,
                        "fp": b.metrics.false_positives,
                        "fn": b.metrics.false_negatives,
                        "latency_seconds": b.latency_seconds,
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                        "total_tokens": 0,
                        "cost_usd": "",
                        "retries": 0,
                        "error": "",
                    }
                )

            # LLM models & iterations
            for dr in report.dataset_results:
                for it in dr.iteration_results:
                    status_val = "FAILED" if it.error_message else "SUCCESS"
                    writer.writerow(
                        {
                            "dataset": dr.dataset_name,
                            "category": dr.category,
                            "domain": dr.domain,
                            "scenario": dr.scenario,
                            "method_or_model": dr.model_name,
                            "type": "llm",
                            "iteration": it.iteration_index,
                            "status": status_val,
                            "precision": it.metrics.precision,
                            "recall": it.metrics.recall,
                            "f1": it.metrics.f1,
                            "tp": it.metrics.true_positives,
                            "fp": it.metrics.false_positives,
                            "fn": it.metrics.false_negatives,
                            "latency_seconds": it.latency_seconds,
                            "prompt_tokens": it.token_usage.prompt_tokens,
                            "completion_tokens": it.token_usage.completion_tokens,
                            "total_tokens": it.token_usage.total_tokens,
                            "cost_usd": it.token_usage.cost_usd if it.token_usage.cost_usd is not None else "",
                            "retries": it.retry_count,
                            "error": it.error_message or "",
                        }
                    )

    @classmethod
    def _compute_macro_metrics(
        cls,
        results: list[Any],
        is_llm: bool = True,
    ) -> dict[str, dict[str, Any]]:
        """Compute macro-averaged precision, recall, F1, latency, and status."""
        grouped: dict[str, list[Any]] = {}
        for r in results:
            method = r.model_name if is_llm else r.baseline_name
            grouped.setdefault(method, []).append(r)

        summary: dict[str, dict[str, Any]] = {}
        for method, items in grouped.items():
            n = len(items)
            if is_llm:
                precisions = [r.aggregated_metrics.precision_mean for r in items]
                recalls = [r.aggregated_metrics.recall_mean for r in items]
                f1s = [r.aggregated_metrics.f1_mean for r in items]
                latencies = [
                    r.aggregated_metrics.latency_mean_sec for r in items
                ]
                tokens = sum(r.aggregated_metrics.total_tokens for r in items)
                cost = sum(r.aggregated_metrics.estimated_cost_usd for r in items)
                retries = sum(r.total_retries for r in items)
                succ_runs = sum(r.successful_iterations for r in items)
                fail_runs = sum(r.failed_iterations for r in items)
                tot = succ_runs + fail_runs
                if tot == 0:
                    status = "NO_RUNS"
                elif fail_runs == 0:
                    status = f"SUCCESS ({succ_runs}/{tot})"
                elif succ_runs == 0:
                    status = f"FAILED (0/{tot})"
                else:
                    status = f"PARTIAL ({succ_runs}/{tot})"
            else:
                precisions = [r.metrics.precision for r in items]
                recalls = [r.metrics.recall for r in items]
                f1s = [r.metrics.f1 for r in items]
                latencies = [r.latency_seconds for r in items]
                tokens = 0
                cost = 0.0
                retries = 0
                succ_runs = n
                fail_runs = 0
                status = f"SUCCESS ({n}/{n})" if n else "NO_RUNS"

            summary[method] = {
                "status": status,
                "precision": sum(precisions) / n if n else 0.0,
                "recall": sum(recalls) / n if n else 0.0,
                "f1": sum(f1s) / n if n else 0.0,
                "latency": sum(latencies) / n if n else 0.0,
                "total_tokens": tokens,
                "estimated_cost_usd": round(cost, 6),
                "retries": retries,
                "successful_runs": succ_runs,
                "failed_runs": fail_runs,
            }
        return summary

    @classmethod
    def _render_macro_table(
        cls,
        title: str,
        llm_results: list[DatasetBenchmarkResult],
        baseline_results: list[BaselineResult],
    ) -> str:
        """Render a markdown macro table for a subset of results."""
        if not llm_results and not baseline_results:
            return ""

        llm_macro = cls._compute_macro_metrics(llm_results, is_llm=True)
        base_macro = cls._compute_macro_metrics(baseline_results, is_llm=False)

        lines = [
            f"### {title}\n",
            "| Method / Model | Type | Status | Precision | Recall | "
            "F1-Score | Latency (s) | Total Tokens | Cost (USD) | Retries |",
            "|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|",
        ]

        for method in sorted(base_macro.keys()):
            m = base_macro[method]
            lines.append(
                f"| `{method}` | `baseline` | `{m['status']}` | "
                f"{m['precision']:.4f} | {m['recall']:.4f} | "
                f"**{m['f1']:.4f}** | {m['latency']:.2f}s | - | - | - |"
            )

        for method in sorted(llm_macro.keys()):
            m = llm_macro[method]
            lines.append(
                f"| `{method}` | `llm` | `{m['status']}` | "
                f"{m['precision']:.4f} | {m['recall']:.4f} | "
                f"**{m['f1']:.4f}** | {m['latency']:.2f}s | "
                f"{m['total_tokens']:,} | ${m['estimated_cost_usd']:.4f} | {m['retries']} |"
            )

        lines.append("")
        return "\n".join(lines)

    @classmethod
    def _generate_markdown_summary(cls, report: BenchmarkReport) -> str:
        """Generate comprehensive Markdown summary report."""
        category_config = report.configuration.get("category", "all")
        lines = [
            "# Schema Mapping Benchmark Report",
            f"\n- **Timestamp**: `{report.timestamp}`",
            f"- **Models Evaluated**: {', '.join(report.configuration.get('models', []))}",
            f"- **Category Scope**: `{category_config}`",
            f"- **Iterations per model**: `{report.configuration.get('iterations', 1)}`",
            f"- **Baselines Included**: `{report.configuration.get('include_baselines', False)}`",
        ]

        exp_config = report.experiment_config
        if exp_config:
            prompt_hash = hashlib.sha256(
                exp_config.prompt_template_snapshot.encode("utf-8")
            ).hexdigest()[:12]
            prompt_len = len(exp_config.prompt_template_snapshot)
            grounding_mode = (
                "Enabled" if exp_config.instance_preview_included else "Disabled"
            )
            lines.extend(
                [
                    "\n## Experiment Configuration & Provenance\n",
                    f"- **System Prompt Snapshot**: `{prompt_len} chars` (SHA256: `{prompt_hash}`)",
                    f"- **Instance Grounding Preview**: `{grounding_mode}`",
                    f"- **Provider / Model**: `{exp_config.provider}` / `{exp_config.model_name}`",
                    f"- **Max Agent Retries**: `{exp_config.max_retries}`",
                ]
            )

        lines.append("\n## Macro-Averaged Results\n")

        # Partition results by category
        st_llm = [r for r in report.dataset_results if r.category == "single_table"]
        st_base = [r for r in report.baseline_results if r.category == "single_table"]
        mt_llm = [r for r in report.dataset_results if r.category == "multi_table"]
        mt_base = [r for r in report.baseline_results if r.category == "multi_table"]

        if st_llm or st_base:
            lines.append(
                cls._render_macro_table(
                    "Single-Table Benchmarks Macro",
                    st_llm,
                    st_base,
                )
            )

        if mt_llm or mt_base:
            lines.append(
                cls._render_macro_table(
                    "Multi-Table Benchmarks Macro",
                    mt_llm,
                    mt_base,
                )
            )

        lines.append(
            cls._render_macro_table(
                "Overall Suite Macro",
                report.dataset_results,
                report.baseline_results,
            )
        )

        lines.extend(
            [
                "## Per-Dataset Evaluation Results\n",
                "| Dataset | Category | Domain | Scenario | Method / Model | "
                "Status | Precision | Recall | F1-Score | TP / FP / FN | "
                "Latency (s) | Tokens | Cost (USD) | Retries |",
                "|---|---|---|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|",
            ]
        )

        for b in report.baseline_results:
            lines.append(
                f"| `{b.dataset_name}` | `{b.category}` | {b.domain} | "
                f"{b.scenario} | `{b.baseline_name}` | `SUCCESS (1/1)` | "
                f"{b.metrics.precision:.4f} | {b.metrics.recall:.4f} | "
                f"**{b.metrics.f1:.4f}** | "
                f"{b.metrics.true_positives} / {b.metrics.false_positives} / "
                f"{b.metrics.false_negatives} | "
                f"{b.latency_seconds:.2f}s | - | - | - |"
            )

        for dr in report.dataset_results:
            p_str = f"{dr.aggregated_metrics.precision_mean:.4f}"
            r_str = f"{dr.aggregated_metrics.recall_mean:.4f}"
            f1_str = f"{dr.aggregated_metrics.f1_mean:.4f}"
            first_it = (
                dr.iteration_results[0] if dr.iteration_results else None
            )
            counts_str = (
                f"{first_it.metrics.true_positives} / "
                f"{first_it.metrics.false_positives} / "
                f"{first_it.metrics.false_negatives}"
                if first_it
                else "- / - / -"
            )
            lines.append(
                f"| `{dr.dataset_name}` | `{dr.category}` | {dr.domain} | "
                f"{dr.scenario} | `{dr.model_name}` | `{dr.status}` | "
                f"{p_str} | {r_str} | **{f1_str}** | {counts_str} | "
                f"{dr.aggregated_metrics.latency_mean_sec:.2f}s | "
                f"{dr.aggregated_metrics.total_tokens:,} | "
                f"${dr.aggregated_metrics.estimated_cost_usd:.4f} | {dr.total_retries} |"
            )

        # Collect Failures & Errors section
        failures: list[dict[str, Any]] = []
        for dr in report.dataset_results:
            for it in dr.iteration_results:
                if it.error_message:
                    failures.append(
                        {
                            "dataset": dr.dataset_name,
                            "category": dr.category,
                            "model": dr.model_name,
                            "iteration": it.iteration_index,
                            "error": it.error_message,
                        }
                    )

        lines.append("\n## Failures & Errors\n")
        if not failures:
            lines.append(
                ":white_check_mark: Zero iteration failures recorded "
                "across all evaluated datasets and models.\n"
            )
        else:
            run_id = report.configuration.get("run_id", "")
            retry_hint = (
                f" Use `--retry-run {run_id}` to re-execute failed "
                "iterations in-place."
                if run_id
                else ""
            )
            lines.append(
                f"> [!WARNING]\n"
                f"> **{len(failures)} iteration failure(s) recorded**."
                f"{retry_hint}\n"
            )
            lines.append(
                "| Dataset | Category | Model | Iteration | Error Message |\n"
                "|---|:---:|:---:|:---:|---|"
            )
            for f in failures:
                lines.append(
                    f"| `{f['dataset']}` | `{f['category']}` | "
                    f"`{f['model']}` | {f['iteration']} | `{f['error']}` |"
                )
            lines.append("")

        lines.append("\n## Detailed Dataset Inspection & Field Diagnostics\n")
        for dr in report.dataset_results:
            lines.append(
                f"### Dataset: `{dr.dataset_name}` "
                f"(Category: `{dr.category}`, Model: `{dr.model_name}`)\n"
            )
            lines.append(f"- **Domain / Scenario**: {dr.domain} / {dr.scenario}")
            if dr.schema_info:
                s_tbls = len(dr.schema_info.source_tables)
                t_tbls = len(dr.schema_info.target_tables)
                s_cols = sum(
                    t.column_count for t in dr.schema_info.source_tables
                )
                t_cols = sum(
                    t.column_count for t in dr.schema_info.target_tables
                )
                lines.append(
                    f"- **Source Tables**: {s_tbls} ({s_cols} columns)"
                )
                lines.append(
                    f"- **Target Tables**: {t_tbls} ({t_cols} columns)"
                )
            first_it = (
                dr.iteration_results[0] if dr.iteration_results else None
            )
            if first_it:
                lines.append(
                    f"- **Ground Truth Pairs**: {first_it.metrics.gold_pairs_count}"
                )
                lines.append(
                    f"- **True Positives**: {first_it.metrics.true_positives}"
                )
                lines.append(
                    f"- **False Positives**: {first_it.metrics.false_positives}"
                )
                lines.append(
                    f"- **False Negatives**: {first_it.metrics.false_negatives}"
                )

                if first_it.field_inspections:
                    lines.append("\n#### Target Field Inspection Summary\n")
                    lines.append(
                        "| Target Column | Status | Expected Source | "
                        "Predicted Source |"
                    )
                    lines.append("|---|:---:|---|---|")
                    for fi in first_it.field_inspections[:30]:
                        exp_str = (
                            ", ".join(fi.expected_source_columns)
                            or "*(none)*"
                        )
                        pred_str = (
                            ", ".join(fi.predicted_source_columns)
                            or "*(none)*"
                        )
                        lines.append(
                            f"| `{fi.target_column}` | `{fi.status}` | "
                            f"{exp_str} | {pred_str} |"
                        )
                    if len(first_it.field_inspections) > 30:
                        lines.append(
                            f"\n*(Showing first 30 of "
                            f"{len(first_it.field_inspections)} target fields)*\n"
                        )
            lines.append("")

        return "\n".join(lines)

    @classmethod
    def _save_run_summaries(
        cls,
        run_out_dir: Path,
        report: BenchmarkReport,
        render_table: bool = True,
    ) -> None:
        """Export summary.json, summary.csv, and summary.md, and optionally print console table."""
        csv_path = run_out_dir / "summary.csv"
        cls._export_summary_csv(report, csv_path)

        md_content = cls._generate_markdown_summary(report)

        # Read the generated CSV rows or re-export
        rows_data = []
        if csv_path.exists():
            with open(csv_path, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows_data = list(reader)

        BenchmarkReporter.checkpoint_summaries(
            run_dir=run_out_dir,
            summary_data=report,
            summary_rows=rows_data,
            markdown_content=md_content,
        )

        if not render_table:
            return

        # Render Rich table
        columns = [
            "Matcher / Model",
            "Category",
            "Status",
            "Dataset",
            "Precision",
            "Recall",
            "F1",
            "Latency (s)",
        ]
        rows: list[list[str]] = []
        iterations = report.configuration.get("iterations", 1)
        for r in report.dataset_results:
            p_str = (
                f"{r.aggregated_metrics.precision_mean:.2f} ± {r.aggregated_metrics.precision_std:.2f}"
                if iterations > 1
                else f"{r.aggregated_metrics.precision_mean:.2f}"
            )
            r_str = (
                f"{r.aggregated_metrics.recall_mean:.2f} ± {r.aggregated_metrics.recall_std:.2f}"
                if iterations > 1
                else f"{r.aggregated_metrics.recall_mean:.2f}"
            )
            f1_str = (
                f"{r.aggregated_metrics.f1_mean:.2f} ± {r.aggregated_metrics.f1_std:.2f}"
                if iterations > 1
                else f"{r.aggregated_metrics.f1_mean:.2f}"
            )
            if r.failed_iterations == 0:
                status_color = f"[green]{r.status}[/green]"
            elif r.successful_iterations == 0:
                status_color = f"[red]{r.status}[/red]"
            else:
                status_color = f"[yellow]{r.status}[/yellow]"

            rows.append(
                [
                    r.model_name,
                    r.category,
                    status_color,
                    r.dataset_name,
                    p_str,
                    r_str,
                    f1_str,
                    f"{r.aggregated_metrics.latency_mean_sec:.1f}s",
                ]
            )

        for b in report.baseline_results:
            rows.append(
                [
                    f"Baseline ({b.baseline_name})",
                    b.category,
                    "[green]SUCCESS (1/1)[/green]",
                    b.dataset_name,
                    f"{b.metrics.precision:.2f}",
                    f"{b.metrics.recall:.2f}",
                    f"{b.metrics.f1:.2f}",
                    f"{b.latency_seconds:.1f}s",
                ]
            )

        BenchmarkReporter.print_table(
            title="Schema Mapping Benchmark Results",
            columns=columns,
            rows=rows,
        )

    @classmethod
    async def run_benchmark(
        cls,
        models: list[str] | None = None,
        dataset_filter: list[str] | str | None = None,
        category: str = "all",
        iterations: int = 1,
        include_baselines: bool = False,
        data_dir: Path = Path("data/schema_mapping"),
        output_dir: Path = Path("outputs/schema_integration/benchmarks/mapping"),
    ) -> BenchmarkReport:
        """Execute schema mapping benchmark suite."""
        suite = SchemaMappingLoader.load_suite(
            data_dir,
            dataset_filter=dataset_filter,
            category_filter=category,
        )
        run_out_dir = RunLayoutManager.get_run_dir(output_dir)
        run_id = run_out_dir.name
        run_out_dir.mkdir(parents=True, exist_ok=True)

        # Save dataset schema in advance
        datasets_dir = run_out_dir / "datasets"
        for ds in suite:
            ds_dir = datasets_dir / ds.name
            ds_dir.mkdir(parents=True, exist_ok=True)
            schema_info = ds.to_schema_info()
            (ds_dir / "dataset_schema.json").write_text(
                schema_info.model_dump_json(indent=2),
                encoding="utf-8",
            )

        effective_models = models or ["gemini-3.8-flash"]
        llm_results: list[DatasetBenchmarkResult] = []
        baseline_results: list[BaselineResult] = []

        for model in effective_models:
            if model and model.lower() not in ["none", "skip"]:
                console.print(
                    "\n[bold magenta]==============================================[/bold magenta]"
                )
                console.print(
                    f"[bold magenta]Benchmarking Model: {model} (Category: {category})[/bold magenta]"
                )
                console.print(
                    "[bold magenta]==============================================[/bold magenta]"
                )
                for ds in suite:
                    res, traces = await cls.benchmark_dataset_llm(
                        dataset=ds,
                        model_name=model,
                        iterations=iterations,
                    )
                    llm_results.append(res)
                    model_dir = RunLayoutManager.get_dataset_model_dir(
                        run_out_dir, ds.name, model
                    )
                    cls._save_dataset_artifacts(
                        model_ds_dir=model_dir,
                        dataset=ds,
                        dr=res,
                        traces=traces,
                        append_traces=False,
                    )

                    # Progressively checkpoint summaries after each dataset-model block
                    exp_config_inter = (
                        llm_results[0].experiment_config
                        if llm_results and llm_results[0].experiment_config
                        else None
                    )
                    intermediate_report = BenchmarkReport(
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        configuration={
                            "run_id": run_id,
                            "models": effective_models,
                            "dataset_filter": dataset_filter,
                            "category": category,
                            "iterations": iterations,
                            "include_baselines": include_baselines,
                            "data_dir": str(data_dir),
                        },
                        experiment_config=exp_config_inter,
                        dataset_results=list(llm_results),
                        baseline_results=list(baseline_results),
                    )
                    cls._save_run_summaries(
                        run_out_dir, intermediate_report, render_table=False
                    )

        if include_baselines:
            console.print(
                "\n[bold blue]==============================================[/bold blue]"
            )
            console.print(
                f"[bold blue]Running Baseline Matchers (Category: {category})[/bold blue]"
            )
            console.print(
                "[bold blue]==============================================[/bold blue]"
            )
            baselines = ["exact", "jaccard", "cupid", "distribution_based", "coma"]
            for b in baselines:
                for ds in suite:
                    try:
                        b_res = cls.benchmark_dataset_baseline(ds, b)
                        if b_res is not None:
                            baseline_results.append(b_res)
                            base_dir = RunLayoutManager.get_dataset_model_dir(
                                run_out_dir, ds.name, b
                            )
                            base_dir.mkdir(parents=True, exist_ok=True)
                            (base_dir / "metrics.json").write_text(
                                b_res.model_dump_json(indent=2),
                                encoding="utf-8",
                            )
                    except Exception as e:  # noqa: BLE001
                        console.print(
                            f"  [yellow]Baseline {b} on {ds.name} skipped/failed: {e}[/yellow]"
                        )

        exp_config = (
            llm_results[0].experiment_config
            if llm_results and llm_results[0].experiment_config
            else None
        )

        report = BenchmarkReport(
            timestamp=datetime.now(timezone.utc).isoformat(),
            configuration={
                "run_id": run_id,
                "models": effective_models,
                "dataset_filter": dataset_filter,
                "category": category,
                "iterations": iterations,
                "include_baselines": include_baselines,
                "data_dir": str(data_dir),
            },
            experiment_config=exp_config,
            dataset_results=llm_results,
            baseline_results=baseline_results,
        )

        cls._save_run_summaries(run_out_dir, report, render_table=True)
        console.print(f"[bold green]✓ Benchmark artifacts saved to {run_out_dir}[/bold green]")
        return report

    @classmethod
    async def retry_benchmark_run(
        cls,
        run_target: str | Path,
        dataset_filter: list[str] | str | None = None,
        model_filter: list[str] | str | None = None,
        category: str = "all",
        data_dir: Path = Path("data/schema_mapping"),
        output_dir: Path = Path("outputs/schema_integration/benchmarks/mapping"),
    ) -> BenchmarkReport:
        """Retry failed iterations in an existing benchmark run in-place.

        Args:
            run_target: Run ID (e.g. 'run_20260908_120000') or directory path.
            dataset_filter: Optional filter for datasets.
            model_filter: Optional filter for models.
            category: Dataset category filter ('all', 'single_table', 'multi_table').
            data_dir: Path to source mapping datasets.
            output_dir: Base directory for mapping benchmark runs.

        Returns:
            Updated BenchmarkReport.
        """
        run_dir = RunResilienceHelper.resolve_run_dir(run_target, output_dir)

        summary_file = run_dir / "summary.json"
        if not summary_file.exists():
            raise FileNotFoundError(
                f"Missing summary.json in benchmark run directory '{run_dir}'."
            )

        with open(summary_file, encoding="utf-8") as f:
            summary_data = json.load(f)

        cfg = summary_data.get("configuration", {})
        run_id = cfg.get("run_id", run_dir.name)
        all_models: list[str] = cfg.get("models", [])
        iterations: int = cfg.get("iterations", 1)
        run_category = cfg.get("category", category)

        if model_filter:
            m_list = (
                [model_filter] if isinstance(model_filter, str) else model_filter
            )
            models = [
                m
                for m in all_models
                if m in m_list or any(f in m for f in m_list)
            ]
        else:
            models = all_models

        suite = SchemaMappingLoader.load_suite(
            data_dir,
            dataset_filter=dataset_filter or cfg.get("dataset_filter"),
            category_filter=run_category,
        )

        datasets_dir = run_dir / "datasets"
        llm_results_by_ds_model: dict[tuple[str, str], DatasetBenchmarkResult] = {}
        tasks_to_retry: list[
            tuple[
                BenchmarkDataset,
                str,
                Path,
                DatasetBenchmarkResult,
                list[IterationResult],
            ]
        ] = []

        for ds in suite:
            for model in all_models:
                safe_model = model.replace(":", "_").replace("/", "_")
                model_ds_dir = datasets_dir / ds.name / safe_model
                metrics_file = model_ds_dir / "metrics.json"
                if not metrics_file.exists():
                    continue
                with open(metrics_file, encoding="utf-8") as f:
                    dr_data = json.load(f)
                dr = DatasetBenchmarkResult.model_validate(dr_data)
                llm_results_by_ds_model[(ds.name, model)] = dr

                if model in models:
                    failed_its = [
                        it for it in dr.iteration_results if it.error_message
                    ]
                    if failed_its:
                        tasks_to_retry.append(
                            (ds, model, model_ds_dir, dr, failed_its)
                        )

        baseline_results: list[BaselineResult] = [
            BaselineResult.model_validate(b)
            for b in summary_data.get("baseline_results", [])
        ]
        exp_config = (
            BenchmarkExperimentConfig.model_validate(
                summary_data["experiment_config"]
            )
            if summary_data.get("experiment_config")
            else None
        )

        if not tasks_to_retry:
            console.print(
                f"\n[bold green]No failed iterations detected in run '{run_id}'. "
                "Nothing to retry.[/bold green]"
            )
            report = BenchmarkReport(
                timestamp=datetime.now(timezone.utc).isoformat(),
                configuration=cfg,
                experiment_config=exp_config,
                dataset_results=list(llm_results_by_ds_model.values()),
                baseline_results=baseline_results,
            )
            cls._save_run_summaries(run_dir, report)
            return report

        total_retries = sum(len(f) for _, _, _, _, f in tasks_to_retry)
        console.print(
            f"\n[bold yellow]Found {total_retries} failed iteration(s) to retry across "
            f"{len(tasks_to_retry)} dataset/model pair(s)...[/bold yellow]\n"
        )

        for ds, model, model_ds_dir, dr, failed_its in tasks_to_retry:
            new_traces: list[dict[str, Any]] = []
            for failed_it in failed_its:
                idx = failed_it.iteration_index
                console.print(
                    f"  [cyan]Retrying failed iteration {idx}/{iterations}[/cyan] on "
                    f"[bold]{ds.name}[/bold] ({ds.category}) "
                    f"with model [yellow]{model}[/yellow]..."
                )
                metric, trace = await cls.run_llm_iteration(
                    dataset=ds,
                    model_name=model,
                    iteration_index=idx,
                )
                trace["retry"] = True
                new_traces.append(trace)

                replaced = False
                for i_pos, it in enumerate(dr.iteration_results):
                    if it.iteration_index == idx:
                        dr.iteration_results[i_pos] = metric
                        replaced = True
                        break
                if not replaced:
                    dr.iteration_results.append(metric)

            dr.iteration_results.sort(key=lambda x: x.iteration_index)
            dr.aggregated_metrics = MappingEvaluator.aggregate_iterations(
                dr.iteration_results
            )
            dr.total_retries = sum(it.retry_count for it in dr.iteration_results)

            cls._save_dataset_artifacts(
                model_ds_dir=model_ds_dir,
                dataset=ds,
                dr=dr,
                traces=new_traces,
                append_traces=True,
            )

        cfg["run_id"] = run_id
        report = BenchmarkReport(
            timestamp=datetime.now(timezone.utc).isoformat(),
            configuration=cfg,
            experiment_config=exp_config,
            dataset_results=list(llm_results_by_ds_model.values()),
            baseline_results=baseline_results,
        )
        cls._save_run_summaries(run_dir, report)
        console.print(
            f"\n[bold green]Successfully retried failed iterations and updated "
            f"run '{run_id}' in-place.[/bold green]"
        )
        return report

    @classmethod
    def run_cli(cls, args: Any) -> None:
        """CLI delegate function for mapping benchmark subcommand."""
        models = (
            args.models
            if hasattr(args, "models") and args.models
            else ["gemini-3.8-flash"]
        )
        datasets = (
            args.datasets
            if hasattr(args, "datasets")
            else getattr(args, "dataset", None)
        )
        category = getattr(args, "category", "all")
        iterations = getattr(args, "iterations", 1)
        baselines = getattr(args, "baselines", False)
        data_dir = Path(getattr(args, "data_dir", "data/schema_mapping"))
        output_dir = Path(
            getattr(
                args,
                "output_dir",
                "outputs/schema_integration/benchmarks/mapping",
            )
        )
        retry_run = getattr(args, "retry_run", None)

        if retry_run:
            asyncio.run(
                cls.retry_benchmark_run(
                    run_target=retry_run,
                    dataset_filter=datasets,
                    model_filter=models,
                    category=category,
                    data_dir=data_dir,
                    output_dir=output_dir,
                )
            )
        else:
            asyncio.run(
                cls.run_benchmark(
                    models=models,
                    dataset_filter=datasets,
                    category=category,
                    iterations=iterations,
                    include_baselines=baselines,
                    data_dir=data_dir,
                    output_dir=output_dir,
                )
            )


# Alias for backwards compatibility
BenchmarkRunner = MappingRunner


def main() -> None:
    """CLI entrypoint for Schema Mapping Benchmarking."""
    parser = argparse.ArgumentParser(
        description="Run Schema Mapping Benchmark across single-table and multi-table datasets."
    )
    parser.add_argument(
        "--models",
        nargs="+",
        default=["gemini-3.8-flash"],
        help="One or more LLM models to benchmark.",
    )
    parser.add_argument(
        "--datasets",
        "--dataset",
        nargs="+",
        dest="datasets",
        default=None,
        help="One or more dataset names/substrings or 'all'.",
    )
    parser.add_argument(
        "--category",
        choices=["all", "single_table", "multi_table"],
        default="all",
        help="Dataset category to benchmark: 'all', 'single_table', or 'multi_table'.",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=1,
        help="Number of repetitions per model/dataset.",
    )
    parser.add_argument(
        "--baselines",
        action="store_true",
        help="Include classical baseline matchers.",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data/schema_mapping"),
        help="Path to mapping benchmark datasets.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/schema_integration/benchmarks/mapping"),
        help="Directory to save benchmark reports.",
    )
    parser.add_argument(
        "--retry-run",
        "--resume",
        dest="retry_run",
        default=None,
        help="Run ID or path to an existing benchmark run to retry failed iterations in-place.",
    )

    args = parser.parse_args()
    try:
        MappingRunner.run_cli(args)
    except Exception as e:  # noqa: BLE001
        console.print(f"[bold red]Benchmark run failed: {e}[/bold red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
