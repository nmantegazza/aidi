"""Benchmark runner for SchemaNet multi-table reference-free schema alignment."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from schema_integration.alignment.agent import align_schemas
from schema_integration.benchmarking.alignment.evaluation import (
    AlignmentEvaluator,
)
from schema_integration.benchmarking.alignment.loader import (
    SchemaAlignmentDataset,
    SchemaAlignmentLoader,
)
from schema_integration.benchmarking.alignment.models import (
    AlignmentDatasetMetrics,
    AlignmentIterationMetrics,
    AlignmentRunSummary,
    MacroModelSummary,
)
from schema_integration.benchmarking.common.models import compute_mean_std
from schema_integration.benchmarking.common.reporting import (
    BenchmarkReporter,
)
from schema_integration.benchmarking.common.visualizer import (
    generate_schema_er_mermaid,
)
from shared.benchmarking import RunLayoutManager, RunResilienceHelper
from shared.console import console


class AlignmentRunner:
    """Orchestrates benchmark runs on SchemaNet multi-table datasets."""

    @classmethod
    async def _run_single_iteration(
        cls,
        dataset: SchemaAlignmentDataset,
        model_name: str,
        iteration_index: int,
        schema_a_str: str,
        schema_b_str: str,
    ) -> tuple[AlignmentIterationMetrics, dict[str, Any]]:
        """Run a single benchmark iteration and evaluate its metrics.

        Returns:
            Tuple of (AlignmentIterationMetrics, iteration trace dict).
        """
        user_prompt = (
            f"### SCHEMA {dataset.source_a.name}\n{schema_a_str}\n\n"
            f"### SCHEMA {dataset.source_b.name}\n{schema_b_str}"
        )
        try:
            report, meta = await align_schemas(
                schema_a_str,
                schema_b_str,
                label_a=dataset.source_a.name,
                label_b=dataset.source_b.name,
                model_name=model_name,
            )
            metrics = AlignmentEvaluator.evaluate_alignment(
                target_schema=report,
                source_a=dataset.source_a,
                source_b=dataset.source_b,
                execution_meta=meta,
                iteration_index=iteration_index,
            )
            trace = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "iteration": iteration_index,
                "dataset": dataset.name,
                "model": model_name,
                "system_prompt": meta.prompt_template,
                "user_prompt": user_prompt,
                "latency_seconds": meta.execution_time_seconds,
                "prompt_tokens": meta.prompt_tokens,
                "completion_tokens": meta.completion_tokens,
                "total_tokens": meta.total_tokens,
                "cost_usd": meta.cost_usd,
                "retry_count": meta.retry_count,
                "retry_log": [r.model_dump() for r in meta.retry_log],
                "target_schema": report.target_schema.model_dump(by_alias=True),
                "conflict_report": [
                    c.model_dump() for c in report.conflict_report
                ],
                "metrics": {
                    "completeness": metrics.completeness,
                    "structural_integrity": metrics.structural_integrity,
                    "intra_table_uniqueness": metrics.intra_table_uniqueness,
                    "detected_clones_count": len(metrics.detected_clones),
                },
            }
            console.print(
                f"    [green]Completeness: {metrics.completeness:.2f} | "
                f"Integrity: {metrics.structural_integrity:.2f} | "
                f"Uniqueness: {metrics.intra_table_uniqueness:.2f} | "
                f"Latency: {metrics.latency_seconds:.1f}s[/green]"
            )
            return metrics, trace
        except Exception as e:  # noqa: BLE001
            err_msg = str(e).strip() or type(e).__name__
            console.print(
                f"    [bold red]Iteration {iteration_index} failed: {err_msg}[/bold red]"
            )
            err_metric = AlignmentIterationMetrics(
                iteration_index=iteration_index,
                completeness=0.0,
                structural_integrity=0.0,
                intra_table_uniqueness=0.0,
                structural_stats=AlignmentEvaluator.compute_structural_integrity(
                    dataset.source_a
                ),
                error_message=err_msg,
            )
            trace = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "iteration": iteration_index,
                "dataset": dataset.name,
                "model": model_name,
                "user_prompt": user_prompt,
                "error_message": err_msg,
            }
            return err_metric, trace

    @classmethod
    def _aggregate_dataset_metrics(
        cls,
        dataset: SchemaAlignmentDataset,
        iteration_results: list[AlignmentIterationMetrics],
    ) -> AlignmentDatasetMetrics:
        """Compute aggregated statistics across iteration results for a dataset."""
        valid_results = [r for r in iteration_results if not r.error_message]
        comp_stats = compute_mean_std([r.completeness for r in valid_results])
        int_stats = compute_mean_std(
            [r.structural_integrity for r in valid_results]
        )
        unique_stats = compute_mean_std(
            [r.intra_table_uniqueness for r in valid_results]
        )
        lat_stats = compute_mean_std([r.latency_seconds for r in valid_results])

        prompt_tokens = sum(
            r.token_usage.prompt_tokens for r in valid_results
        )
        completion_tokens = sum(
            r.token_usage.completion_tokens for r in valid_results
        )
        total_tokens = sum(
            r.token_usage.total_tokens for r in valid_results
        )
        total_cost = sum(
            r.token_usage.cost_usd or 0.0 for r in valid_results
        )

        flakiness = (
            AlignmentEvaluator.compute_flakiness(valid_results)
            if len(iteration_results) > 1
            else {}
        )
        consistency_report = (
            AlignmentEvaluator.compute_multi_iteration_consistency(
                valid_results, dataset.source_a, dataset.source_b
            )
            if len(iteration_results) > 1
            else None
        )

        cols_a = sum(
            len(r.schema_info.fields) for r in dataset.source_a.resources
        )
        cols_b = sum(
            len(r.schema_info.fields) for r in dataset.source_b.resources
        )

        return AlignmentDatasetMetrics(
            dataset_name=dataset.name,
            domain=dataset.domain,
            table_count_a=len(dataset.source_a.resources),
            table_count_b=len(dataset.source_b.resources),
            column_count_a=cols_a,
            column_count_b=cols_b,
            ground_truth_count=len(dataset.ground_truth),
            iterations=iteration_results,
            mean_completeness=comp_stats.mean,
            std_completeness=comp_stats.std,
            mean_structural_integrity=int_stats.mean,
            std_structural_integrity=int_stats.std,
            mean_intra_table_uniqueness=unique_stats.mean,
            std_intra_table_uniqueness=unique_stats.std,
            mean_latency_sec=lat_stats.mean,
            std_latency_sec=lat_stats.std,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            estimated_cost_usd=round(total_cost, 6),
            flakiness_analysis=flakiness,
            consistency_analysis=consistency_report,
        )

    @classmethod
    async def run_dataset_iterations(
        cls,
        dataset: SchemaAlignmentDataset,
        model_name: str,
        iterations: int = 1,
    ) -> tuple[AlignmentDatasetMetrics, list[dict[str, Any]]]:
        """Run multiple benchmark iterations for a specific dataset and model.

        Args:
            dataset: SchemaAlignmentDataset instance.
            model_name: LLM model identifier.
            iterations: Number of evaluation iterations.

        Returns:
            Tuple of (AlignmentDatasetMetrics with aggregated statistics, list of iteration traces).
        """
        iteration_results: list[AlignmentIterationMetrics] = []
        iteration_traces: list[dict[str, Any]] = []
        schema_a_str = dataset.source_a.model_dump_json(indent=2, by_alias=True)
        schema_b_str = dataset.source_b.model_dump_json(indent=2, by_alias=True)

        for i in range(1, iterations + 1):
            console.print(
                f"  [cyan]Iteration {i}/{iterations}[/cyan] on "
                f"[bold]{dataset.name}[/bold] with model [yellow]{model_name}[/yellow]..."
            )
            metric, trace = await cls._run_single_iteration(
                dataset=dataset,
                model_name=model_name,
                iteration_index=i,
                schema_a_str=schema_a_str,
                schema_b_str=schema_b_str,
            )
            iteration_results.append(metric)
            iteration_traces.append(trace)

        dataset_metrics = cls._aggregate_dataset_metrics(dataset, iteration_results)
        return dataset_metrics, iteration_traces

    @classmethod
    def _build_dataset_markdown_report(
        cls,
        dataset: SchemaAlignmentDataset,
        model_name: str,
        dm: AlignmentDatasetMetrics,
    ) -> str:
        """Generate full diagnostic markdown report with ER diagrams for Source A, Source B, and Target."""
        valid_iterations = [it for it in dm.iterations if not it.error_message]
        last_it = valid_iterations[-1] if valid_iterations else None

        lines: list[str] = [
            f"# Schema Alignment Diagnostic Report — {dataset.name}",
            "",
            f"- **Model**: `{model_name}`",
            f"- **Domain**: {dataset.domain}",
            f"- **Status**: `{dm.status}`",
            f"- **Iterations**: `{len(dm.iterations)}`",
            f"- **Source A**: `{dataset.source_a.name}` ({dm.table_count_a} tables, {dm.column_count_a} cols)",
            f"- **Source B**: `{dataset.source_b.name}` ({dm.table_count_b} tables, {dm.column_count_b} cols)",
            "",
        ]

        if dm.failed_iterations > 0:
            lines.extend(
                [
                    "> [!WARNING]",
                    f"> **{dm.failed_iterations}/{dm.total_iterations} iterations failed** "
                    f"(Iterations: {', '.join(str(i) for i in dm.failed_iteration_indices)}). "
                    "Metrics and consensus below are calculated exclusively on valid runs.",
                    "",
                ]
            )

        lines.extend(
            [
                "## Schema Architectures (ER Diagrams)",
                "",
                f"### Source A Schema (`{dataset.source_a.name}`)",
            "",
            "```mermaid",
            generate_schema_er_mermaid(dataset.source_a),
            "```",
            "",
            f"### Source B Schema (`{dataset.source_b.name}`)",
            "",
            "```mermaid",
            generate_schema_er_mermaid(dataset.source_b),
            "```",
            "",
        ])

        if last_it and last_it.alignment_report:
            if len(dm.iterations) > 1:
                lines.append("### Generated Unified Target Schemas per Iteration")
                lines.append("")
                lines.append(
                    "> [!NOTE]\n"
                    "> Use the toggles below to view the target schema ER diagram generated in each "
                    "iteration. The representative run is expanded by default."
                )
                lines.append("")
                for it in dm.iterations:
                    if not it.alignment_report or not it.alignment_report.target_schema:
                        continue
                    is_rep = it.iteration_index == last_it.iteration_index
                    open_attr = " open" if is_rep else ""
                    rep_tag = " [Representative / Final Run]" if is_rep else ""
                    table_count = len(
                        it.alignment_report.target_schema.resources
                    )
                    summary_text = (
                        f"Iteration {it.iteration_index} Target Schema "
                        f"({table_count} tables, S_rel: {it.structural_integrity:.4f}){rep_tag}"
                    )
                    lines.append(f"<details{open_attr}>")
                    lines.append(f"<summary><b>{summary_text}</b></summary>")
                    lines.append("")
                    lines.append("```mermaid")
                    lines.append(
                        generate_schema_er_mermaid(
                            it.alignment_report.target_schema
                        )
                    )
                    lines.append("```")
                    lines.append("</details>")
                    lines.append("")
            else:
                lines.append("### Generated Unified Target Schema")
                lines.append("")
                lines.append("```mermaid")
                lines.append(
                    generate_schema_er_mermaid(
                        last_it.alignment_report.target_schema
                    )
                )
                lines.append("```")
                lines.append("")

        lines.extend(
            [
                "## Performance & Efficiency Summary",
                "",
            ]
        )

        summary_headers = [
            "Completeness (Cov_attr)",
            "Structural Integrity (S_rel)",
            "Intra-Table Uniqueness (M_unique)",
            "Latency (s)",
            "Total Tokens",
            "Estimated Cost (USD)",
        ]
        summary_rows = [
            [
                f"{dm.mean_completeness:.4f}",
                f"{dm.mean_structural_integrity:.4f}",
                f"{dm.mean_intra_table_uniqueness:.4f}",
                f"{dm.mean_latency_sec:.2f}s",
                f"{dm.total_tokens:,}",
                f"${dm.estimated_cost_usd:.4f}",
            ]
        ]
        lines.append(BenchmarkReporter.format_table(summary_headers, summary_rows))
        lines.append("")

        # Target Schema Granular Breakdown
        if last_it and last_it.alignment_report:
            lines.append("## Target Schema Detailed Specifications")
            lines.append("")
            for t_res in last_it.alignment_report.target_schema.resources:
                t_schema = t_res.schema_info
                pk_set = {
                    str(c).strip().lower()
                    for c in t_schema.primary_key_columns
                }
                fk_map: dict[str, str] = {}
                for fk in t_schema.foreignKeys:
                    fk_fields = (
                        [fk.fields]
                        if isinstance(fk.fields, str)
                        else fk.fields
                    )
                    ref_fields = (
                        [fk.reference.fields]
                        if isinstance(fk.reference.fields, str)
                        else fk.reference.fields
                    )
                    for lf, rf in zip(fk_fields, ref_fields):
                        fk_map[str(lf).strip().lower()] = (
                            f"{fk.reference.resource}.{rf}"
                        )

                lines.append(f"### Target Table: `{t_res.name}`")
                lines.append("")

                col_headers = [
                    "Column Name",
                    "Type",
                    "Key",
                    "Source Provenance",
                    "Description",
                ]
                col_rows: list[list[str]] = []
                for fld in t_schema.fields:
                    fld_low = fld.name.strip().lower()
                    is_pk = fld_low in pk_set
                    is_fk = fld_low in fk_map

                    key_str = "-"
                    if is_pk and is_fk:
                        key_str = "PK, FK"
                    elif is_pk:
                        key_str = "PK"
                    elif is_fk:
                        key_str = f"FK -> `{fk_map[fld_low]}`"

                    prov_str = (
                        ", ".join(f"`{p}`" for p in fld.source_provenance)
                        if fld.source_provenance
                        else "-"
                    )
                    desc_str = fld.description or "-"
                    col_rows.append(
                        [
                            f"`{fld.name}`",
                            fld.type,
                            key_str,
                            prov_str,
                            desc_str,
                        ]
                    )

                lines.append(
                    BenchmarkReporter.format_table(col_headers, col_rows)
                )
                lines.append("")

        lines.append("## 3-Pillar Reference-Free Diagnostic Inspection")
        lines.append("")

        # Pillar 1: Information Preservation
        lines.append("### Pillar 1: Information Preservation (Completeness)")
        lines.append("")
        if last_it:
            lines.append(f"- **Attribute Completeness ($Cov_{{\\text{{attr}}}}$)**: `{last_it.completeness:.2%}`")
            lines.append("")
            if last_it.unmapped_source_columns:
                lines.append("#### Dropped / Unmapped Source Attributes")
                for col in last_it.unmapped_source_columns:
                    lines.append(f"- :x: `{col}`")
                lines.append("")
            else:
                lines.append(
                    ":white_check_mark: 100% of source schema attributes were preserved in target schema provenance."
                )
                lines.append("")

        # Pillar 2: Structural Integrity
        lines.append("### Pillar 2: Structural & Referential Constraints")
        lines.append("")
        if last_it:
            int_stats = last_it.structural_stats
            lines.append(
                f"- **Primary Key Validity**: `{int_stats.pk_validity:.2%}`"
            )
            lines.append(
                f"- **Foreign Key Validity**: `{int_stats.fk_validity:.2%}` "
                f"({int_stats.total_fks} declared FKs)"
            )
            lines.append(
                f"- **Source FK Preservation**: `{int_stats.source_fk_preservation:.2%}` "
                f"({int_stats.preserved_source_fks}/{int_stats.total_source_fks} source relationships preserved)"
            )
            lines.append(
                f"- **Combined Structural Score ($S_{{\\text{{rel}}}}$)**: `{int_stats.score:.4f}`"
            )
            lines.append(f"- **Total Target Tables**: `{int_stats.total_tables}`")
            lines.append("")

            if int_stats.broken_fks:
                lines.append("#### Broken Target Foreign Key Alerts")
                for err in int_stats.broken_fks:
                    lines.append(f"- :warning: **Broken FK**: {err}")
                lines.append("")

            if int_stats.unpreserved_source_fks:
                lines.append("#### Unpreserved Source Foreign Keys")
                for err in int_stats.unpreserved_source_fks:
                    lines.append(f"- :warning: {err}")
                lines.append("")

            if not int_stats.broken_fks and not int_stats.unpreserved_source_fks:
                lines.append(
                    ":white_check_mark: All target foreign keys are valid and all source relational links are preserved."
                )
                lines.append("")

        # Pillar 3: Intrinsic Minimality & Non-Redundancy
        lines.append("### Pillar 3: Intrinsic Minimality & Non-Redundancy")
        lines.append("")
        if last_it:
            lines.append(
                f"- **Intra-Table Uniqueness ($M_{{\\text{{unique}}}}$)**: `{last_it.intra_table_uniqueness:.4f}`"
            )
            lines.append("")

            if last_it.detected_clones:
                lines.append("#### Flagged Intra-Table Candidate Clones")
                clone_headers = [
                    "Target Table",
                    "Column A",
                    "Column B",
                    "Data Type",
                    "Cosine Sim",
                    "Source Prov A",
                    "Source Prov B",
                ]
                clone_rows: list[list[str]] = []
                for rec in last_it.detected_clones:
                    clone_rows.append(
                        [
                            f"`{rec.target_table}`",
                            f"`{rec.column_a}`",
                            f"`{rec.column_b}`",
                            rec.data_type,
                            f"{rec.similarity_score:.4f}",
                            ", ".join(rec.source_prov_a) or "-",
                            ", ".join(rec.source_prov_b) or "-",
                        ]
                    )
                lines.append(BenchmarkReporter.format_table(clone_headers, clone_rows))
                lines.append("")
            else:
                lines.append(
                    ":white_check_mark: Zero semantic duplicate columns detected across target relations."
                )
                lines.append("")

        # Multi-iteration stability section
        if len(dm.iterations) > 1:
            lines.append("## Multi-Iteration Stability Analysis")
            lines.append("")
            it_headers = [
                "Iteration",
                "Completeness",
                "Integrity",
                "Uniqueness",
                "Clones Flagged",
                "Latency (s)",
                "Prompt Tokens",
                "Completion Tokens",
                "Total Tokens",
                "Estimated Cost (USD)",
            ]
            it_rows: list[list[str]] = []
            for it in dm.iterations:
                it_rows.append(
                    [
                        str(it.iteration_index),
                        f"{it.completeness:.4f}",
                        f"{it.structural_integrity:.4f}",
                        f"{it.intra_table_uniqueness:.4f}",
                        str(len(it.detected_clones)),
                        f"{it.latency_seconds:.2f}s",
                        f"{it.prompt_tokens:,}",
                        f"{it.completion_tokens:,}",
                        f"{it.total_tokens:,}",
                        (
                            f"${it.token_usage.cost_usd:.4f}"
                            if it.token_usage.cost_usd is not None
                            else "-"
                        ),
                    ]
                )
            lines.append(BenchmarkReporter.format_table(it_headers, it_rows))
            lines.append("")

            if dm.consistency_analysis:
                ca = dm.consistency_analysis
                lines.append("### Cross-Iteration Attribute Mapping Consensus")
                lines.append("")
                total_coaligned = (
                    ca.stable_pairs_count + ca.volatile_pairs_count
                )
                lines.append(
                    f"- **Total Co-Aligned Attribute Pairs**: `{total_coaligned}`"
                )
                lines.append(
                    f"- **Invariant / Stable Alignments (100% Agreement)**: "
                    f"`{ca.stable_pairs_count}`"
                )
                lines.append(
                    f"- **Volatile / Flaky Alignments (<100% Agreement)**: "
                    f"`{ca.volatile_pairs_count}`"
                )
                lines.append(
                    f"- **Overall Consensus Ratio**: "
                    f"`{ca.overall_consensus_ratio:.2%}`"
                )
                lines.append("")

                td = ca.topological_drift
                lines.append("### Topological & Relational Drift")
                lines.append("")
                min_t = min(td.table_counts) if td.table_counts else 0
                max_t = max(td.table_counts) if td.table_counts else 0
                lines.append(
                    f"- **Mean Table Count**: `{td.mean_table_count:.2f} ± "
                    f"{td.std_table_count:.2f}` (Range: {min_t} – {max_t})"
                )
                lines.append(
                    f"- **Relational Graph Edge Stability (Mean Pairwise Jaccard)**: "
                    f"`{td.fk_edge_stability:.4f}`"
                )
                lines.append("")

                volatile_pairs = [
                    p for p in ca.consensus_pairs if p.status == "VOLATILE"
                ]
                if volatile_pairs:
                    lines.append(
                        "#### Volatile Cross-Source Alignments (Flakiness Breakdown)"
                    )
                    lines.append("")
                    vol_headers = [
                        "Source A Attribute",
                        "Source B Attribute",
                        "Agreement Rate",
                        "Runs",
                        "Assigned Target Field(s)",
                    ]
                    vol_rows: list[list[str]] = []
                    for p in volatile_pairs:
                        vol_rows.append(
                            [
                                f"`{p.source_col_a}`",
                                f"`{p.source_col_b}`",
                                f"{p.agreement_rate:.1%}",
                                f"{p.coaligned_runs}/{p.total_runs}",
                                ", ".join(f"`{t}`" for t in p.target_field_names)
                                or "-",
                            ]
                        )
                    lines.append(
                        BenchmarkReporter.format_table(vol_headers, vol_rows)
                    )
                    lines.append("")
                else:
                    lines.append(
                        ":white_check_mark: Zero volatile attribute alignments; "
                        "100% agreement across all runs."
                    )
                    lines.append("")

                stable_pairs = [
                    p for p in ca.consensus_pairs if p.status == "STABLE"
                ]
                if stable_pairs:
                    lines.append(
                        f"#### Confirmed Invariant Alignments ({len(stable_pairs)} pairs)"
                    )
                    lines.append("")
                    st_headers = [
                        "Source A Attribute",
                        "Source B Attribute",
                        "Unified Target Field",
                    ]
                    st_rows: list[list[str]] = []
                    for p in stable_pairs:
                        st_rows.append(
                            [
                                f"`{p.source_col_a}`",
                                f"`{p.source_col_b}`",
                                ", ".join(f"`{t}`" for t in p.target_field_names)
                                or "-",
                            ]
                        )
                    lines.append(
                        BenchmarkReporter.format_table(st_headers, st_rows)
                    )
                    lines.append("")

                if ca.clone_flakiness:
                    lines.append("### Intra-Table Clone Stability")
                    lines.append("")
                    tot_clones = ca.clone_flakiness.get(
                        "total_distinct_clones", 0
                    )
                    st_clones = ca.clone_flakiness.get("stable_clones_count", 0)
                    stab_ratio = ca.clone_flakiness.get(
                        "stability_ratio", 1.0
                    )
                    lines.append(
                        f"- **Candidate Clones Stability Ratio**: "
                        f"`{stab_ratio:.2%}` ({st_clones}/{tot_clones} stable)"
                    )
                    lines.append("")

        lines.append("## Diagnostic & Observability Telemetry")
        lines.append("")
        lines.append(
            "- **Candidate Clones CSV**: [`detected_clones.csv`](./detected_clones.csv)"
        )
        if dm.consistency_analysis:
            lines.append(
                "- **Mapping Consensus CSV**: [`mapping_consensus.csv`](./mapping_consensus.csv)"
            )
        lines.append(
            "- **LLM Execution Trace**: [`execution_trace.jsonl`](./execution_trace.jsonl)"
        )
        if len(dm.iterations) > 1:
            lines.append(
                "- **Per-Iteration Artifacts**: [`iterations/`](./iterations/)"
            )
        lines.append("")

        return "\n".join(lines)

    @classmethod
    def _save_dataset_artifacts(
        cls,
        model_ds_dir: Path,
        dataset: SchemaAlignmentDataset,
        model: str,
        ds_metric: AlignmentDatasetMetrics,
        ds_traces: list[dict[str, Any]] | None = None,
        append_traces: bool = False,
    ) -> None:
        """Save per-dataset, per-model artifacts (metrics, traces, reports, clones, consensus)."""
        model_ds_dir.mkdir(parents=True, exist_ok=True)

        # Save metrics.json
        BenchmarkReporter.save_json(
            ds_metric, model_ds_dir / "metrics.json"
        )

        # Save or append execution traces JSONL
        if ds_traces:
            trace_file = model_ds_dir / "execution_trace.jsonl"
            mode = "a" if append_traces else "w"
            with open(trace_file, mode, encoding="utf-8") as f:
                for tr in ds_traces:
                    f.write(json.dumps(tr) + "\n")

        # Save raw AlignmentReport from last valid iteration if exists
        valid_its = [
            it for it in ds_metric.iterations if not it.error_message
        ]
        if valid_its and valid_its[-1].alignment_report:
            BenchmarkReporter.save_json(
                valid_its[-1].alignment_report,
                model_ds_dir / "alignment_report.json",
            )

        # Save per-iteration artifacts for multi-iteration inspectability
        if len(ds_metric.iterations) > 1:
            iterations_dir = model_ds_dir / "iterations"
            for it in ds_metric.iterations:
                if it.error_message:
                    continue
                it_dir = iterations_dir / f"iter_{it.iteration_index}"
                it_dir.mkdir(parents=True, exist_ok=True)
                if it.alignment_report:
                    BenchmarkReporter.save_json(
                        it.alignment_report,
                        it_dir / "alignment_report.json",
                    )
                if it.detected_clones:
                    it_clone_rows: list[dict[str, Any]] = [
                        {
                            "target_table": rec.target_table,
                            "column_a": rec.column_a,
                            "column_b": rec.column_b,
                            "data_type": rec.data_type,
                            "similarity_score": rec.similarity_score,
                            "source_prov_a": "; ".join(rec.source_prov_a),
                            "source_prov_b": "; ".join(rec.source_prov_b),
                            "description_a": rec.description_a or "",
                            "description_b": rec.description_b or "",
                        }
                        for rec in it.detected_clones
                    ]
                    BenchmarkReporter.save_csv(
                        it_clone_rows, it_dir / "detected_clones.csv"
                    )

        # Save detected clones CSV
        valid_last = valid_its[-1] if valid_its else None
        clone_rows: list[dict[str, Any]] = [
            {
                "target_table": rec.target_table,
                "column_a": rec.column_a,
                "column_b": rec.column_b,
                "data_type": rec.data_type,
                "similarity_score": rec.similarity_score,
                "source_prov_a": "; ".join(rec.source_prov_a),
                "source_prov_b": "; ".join(rec.source_prov_b),
                "description_a": rec.description_a or "",
                "description_b": rec.description_b or "",
            }
            for rec in (valid_last.detected_clones if valid_last else [])
        ]
        BenchmarkReporter.save_csv(
            clone_rows, model_ds_dir / "detected_clones.csv"
        )

        # Save mapping consensus CSV if multi-iteration analysis exists
        if ds_metric.consistency_analysis:
            consensus_rows: list[dict[str, Any]] = [
                {
                    "source_col_a": p.source_col_a,
                    "source_col_b": p.source_col_b,
                    "coaligned_runs": p.coaligned_runs,
                    "total_runs": p.total_runs,
                    "agreement_rate": p.agreement_rate,
                    "status": p.status,
                    "target_field_names": "; ".join(
                        p.target_field_names
                    ),
                }
                for p in ds_metric.consistency_analysis.consensus_pairs
            ]
            BenchmarkReporter.save_csv(
                consensus_rows,
                model_ds_dir / "mapping_consensus.csv",
            )

        # Generate and save dataset Markdown report
        ds_md = cls._build_dataset_markdown_report(
            dataset=dataset,
            model_name=model,
            dm=ds_metric,
        )
        BenchmarkReporter.save_markdown(
            title=f"Schema Alignment Diagnostic Report — {dataset.name}",
            summary_table_md="",
            details_md=ds_md,
            output_path=model_ds_dir / "alignment_report.md",
        )

    @classmethod
    def _build_and_save_run_summaries(
        cls,
        run_dir: Path,
        run_id: str,
        models: list[str],
        suite: list[SchemaAlignmentDataset],
        dataset_results_matrix: dict[str, dict[str, AlignmentDatasetMetrics]],
        iterations: int,
        is_intermediate: bool = False,
    ) -> AlignmentRunSummary:
        """Compute macro-summaries and write summary.json, summary.csv, and summary.md."""
        macro_summaries: dict[str, MacroModelSummary] = {}
        csv_rows: list[dict[str, Any]] = []

        for model in models:
            model_dataset_metrics = {
                ds.name: dataset_results_matrix[ds.name][model]
                for ds in suite
                if ds.name in dataset_results_matrix
                and model in dataset_results_matrix[ds.name]
            }

            for ds in suite:
                dm = model_dataset_metrics.get(ds.name)
                if not dm:
                    continue
                valid_its = [it for it in dm.iterations if not it.error_message]
                valid_last = valid_its[-1] if valid_its else None
                csv_rows.append(
                    {
                        "dataset": ds.name,
                        "domain": ds.domain,
                        "model": model,
                        "status": dm.status,
                        "success_count": dm.successful_iterations,
                        "failure_count": dm.failed_iterations,
                        "failed_iterations": (
                            "; ".join(str(i) for i in dm.failed_iteration_indices)
                            or "none"
                        ),
                        "completeness": dm.mean_completeness,
                        "structural_integrity": dm.mean_structural_integrity,
                        "intra_table_uniqueness": dm.mean_intra_table_uniqueness,
                        "clones_detected": (
                            len(valid_last.detected_clones) if valid_last else 0
                        ),
                        "latency_sec": dm.mean_latency_sec,
                        "prompt_tokens": dm.prompt_tokens,
                        "completion_tokens": dm.completion_tokens,
                        "total_tokens": dm.total_tokens,
                    }
                )

            all_comp = [m.mean_completeness for m in model_dataset_metrics.values()]
            all_int = [
                m.mean_structural_integrity
                for m in model_dataset_metrics.values()
            ]
            all_unique = [
                m.mean_intra_table_uniqueness
                for m in model_dataset_metrics.values()
            ]
            all_lat = [
                m.mean_latency_sec for m in model_dataset_metrics.values()
            ]
            total_prompt = sum(
                m.prompt_tokens for m in model_dataset_metrics.values()
            )
            total_comp_tokens = sum(
                m.completion_tokens for m in model_dataset_metrics.values()
            )
            total_tok = sum(
                m.total_tokens for m in model_dataset_metrics.values()
            )
            total_cost = sum(
                m.estimated_cost_usd
                for m in model_dataset_metrics.values()
            )
            successful_runs = sum(
                m.successful_iterations for m in model_dataset_metrics.values()
            )
            failed_runs = sum(
                m.failed_iterations for m in model_dataset_metrics.values()
            )

            macro = MacroModelSummary(
                model_name=model,
                completeness=(
                    round(sum(all_comp) / len(all_comp), 4) if all_comp else 0.0
                ),
                structural_integrity=(
                    round(sum(all_int) / len(all_int), 4) if all_int else 0.0
                ),
                intra_table_uniqueness=(
                    round(sum(all_unique) / len(all_unique), 4)
                    if all_unique
                    else 0.0
                ),
                mean_latency_sec=(
                    round(sum(all_lat) / len(all_lat), 3) if all_lat else 0.0
                ),
                prompt_tokens=total_prompt,
                completion_tokens=total_comp_tokens,
                total_tokens=total_tok,
                estimated_cost_usd=round(total_cost, 6),
                successful_runs=successful_runs,
                failed_runs=failed_runs,
            )
            macro_summaries[model] = macro

        # Render Rich console table if final
        if not is_intermediate:
            cli_headers = [
                "Model",
                "Status",
                "Completeness (Cov_attr)",
                "Structural Integrity (S_rel)",
                "Intra-Table Uniqueness (M_unique)",
                "Latency (s)",
                "Total Tokens",
                "Estimated Cost (USD)",
            ]
            cli_rows: list[list[str]] = []
            for mod, mac in macro_summaries.items():
                if mac.failed_runs == 0:
                    status_color = f"[green]{mac.status}[/green]"
                elif mac.successful_runs == 0:
                    status_color = f"[red]{mac.status}[/red]"
                else:
                    status_color = f"[yellow]{mac.status}[/yellow]"

                cli_rows.append(
                    [
                        mod,
                        status_color,
                        f"{mac.completeness:.4f}",
                        f"{mac.structural_integrity:.4f}",
                        f"{mac.intra_table_uniqueness:.4f}",
                        f"{mac.mean_latency_sec:.2f}s",
                        f"{mac.total_tokens:,}",
                        f"${mac.estimated_cost_usd:.4f}",
                    ]
                )
            BenchmarkReporter.print_table(
                "Schema Integration Alignment Benchmark — Macro Summary",
                cli_headers,
                cli_rows,
            )

        # Build Markdown summary
        summary_md_lines = [
            "# Schema Integration Alignment Benchmark Report",
            "",
            f"**Run ID**: `{run_id}`  ",
            f"**Generated**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}  ",
            f"**Iterations per Dataset**: {iterations}  ",
            f"**Evaluated Models**: {', '.join(f'`{m}`' for m in models)}  ",
            f"**Evaluated Datasets**: {len(suite)} datasets  ",
            "",
            "## Macro-Averaged Model Performance",
            "",
        ]

        macro_table_headers = [
            "Model",
            "Status",
            "Completeness (Cov_attr)",
            "Structural Integrity (S_rel)",
            "Intra-Table Uniqueness (M_unique)",
            "Mean Latency",
            "Total Tokens",
        ]
        macro_table_rows = [
            [
                f"`{mac.model_name}`",
                f"`{mac.status}`",
                f"{mac.completeness:.4f}",
                f"{mac.structural_integrity:.4f}",
                f"{mac.intra_table_uniqueness:.4f}",
                f"{mac.mean_latency_sec:.2f}s",
                f"{mac.total_tokens:,}",
            ]
            for mac in macro_summaries.values()
        ]
        summary_md_lines.append(
            BenchmarkReporter.format_table(
                macro_table_headers,
                macro_table_rows,
                alignments=[
                    "left",
                    "center",
                    "center",
                    "center",
                    "center",
                    "center",
                    "right",
                ],
            )
        )
        summary_md_lines.append("")

        # Per-Dataset Breakdown Matrix
        summary_md_lines.append("## Per-Dataset Evaluation Results")
        summary_md_lines.append("")
        per_ds_headers = [
            "Dataset",
            "Domain",
            "Model",
            "Status",
            "Completeness",
            "Structural (I)",
            "Uniqueness",
            "Latency (s)",
            "Tokens",
        ]
        per_ds_rows: list[list[str]] = []
        for ds in suite:
            for mod in models:
                dm = dataset_results_matrix.get(ds.name, {}).get(mod)
                if not dm:
                    continue
                c_str = (
                    f"{dm.mean_completeness:.2f} ± {dm.std_completeness:.2f}"
                    if iterations > 1
                    else f"{dm.mean_completeness:.2f}"
                )
                int_str = (
                    f"{dm.mean_structural_integrity:.2f} ± {dm.std_structural_integrity:.2f}"
                    if iterations > 1
                    else f"{dm.mean_structural_integrity:.2f}"
                )
                u_str = (
                    f"{dm.mean_intra_table_uniqueness:.2f} ± {dm.std_intra_table_uniqueness:.2f}"
                    if iterations > 1
                    else f"{dm.mean_intra_table_uniqueness:.2f}"
                )
                per_ds_rows.append(
                    [
                        f"`{ds.name}`",
                        ds.domain,
                        f"`{mod}`",
                        f"`{dm.status}`",
                        c_str,
                        int_str,
                        u_str,
                        f"{dm.mean_latency_sec:.2f}s",
                        f"{dm.total_tokens:,}",
                    ]
                )
        summary_md_lines.append(
            BenchmarkReporter.format_table(per_ds_headers, per_ds_rows)
        )
        summary_md_lines.append("")

        # Collect Failures & Errors section
        failures: list[dict[str, Any]] = []
        for ds in suite:
            for mod in models:
                dm = dataset_results_matrix.get(ds.name, {}).get(mod)
                if not dm:
                    continue
                for it in dm.iterations:
                    if it.error_message:
                        failures.append(
                            {
                                "dataset": ds.name,
                                "model": mod,
                                "iteration": it.iteration_index,
                                "error": it.error_message,
                            }
                        )

        summary_md_lines.append("## Failures & Errors")
        summary_md_lines.append("")
        if not failures:
            summary_md_lines.append(
                ":white_check_mark: Zero iteration failures recorded across all evaluated datasets and models."
            )
        else:
            summary_md_lines.append(
                f"> [!WARNING]\n"
                f"> **{len(failures)} iteration failure(s) recorded**. "
                f"Use `--retry-run {run_id}` to re-execute failed iterations in-place.\n"
            )
            fail_headers = ["Dataset", "Model", "Iteration", "Error Message"]
            fail_rows = [
                [
                    f"`{f['dataset']}`",
                    f"`{f['model']}`",
                    str(f["iteration"]),
                    f"`{f['error']}`",
                ]
                for f in failures
            ]
            summary_md_lines.append(
                BenchmarkReporter.format_table(fail_headers, fail_rows)
            )
        summary_md_lines.append("")

        # Save root files via progressive checkpointing
        run_summary = AlignmentRunSummary(
            run_id=run_id,
            models=models,
            iterations=iterations,
            macro_summaries=macro_summaries,
            dataset_results=dataset_results_matrix,
        )
        md_full_content = (
            "# Schema Integration Alignment Benchmark Report\n\n"
            + "\n".join(summary_md_lines[2:])
        )
        BenchmarkReporter.checkpoint_summaries(
            run_dir=run_dir,
            summary_data=run_summary,
            summary_rows=csv_rows,
            markdown_content=md_full_content,
        )

        if not is_intermediate:
            console.print(f"\n[bold green]Saved benchmark run to {run_dir}[/bold green]")
        return run_summary

    @classmethod
    async def run_benchmark(
        cls,
        models: list[str] | None = None,
        dataset_filter: list[str] | str | None = None,
        iterations: int = 1,
        data_dir: Path = Path("data/schema_alignment"),
        output_dir: Path = Path("outputs/schema_integration/benchmarks/alignment"),
    ) -> AlignmentRunSummary:
        """Execute alignment benchmark suite for given models and datasets.

        Args:
            models: List of LLM model identifiers. Defaults to ['gemini-3.8-flash'].
            dataset_filter: Optional filter for dataset names.
            iterations: Number of runs per dataset.
            data_dir: Base directory for alignment datasets.
            output_dir: Destination directory for reports.

        Returns:
            AlignmentRunSummary container with all benchmark metrics.
        """
        effective_models = models or ["gemini-3.8-flash"]
        suite = SchemaAlignmentLoader.load_suite(data_dir, dataset_filter)
        run_dir = RunLayoutManager.get_run_dir(output_dir)
        run_id = run_dir.name
        run_dir.mkdir(parents=True, exist_ok=True)

        for ds in suite:
            ds_folder = run_dir / "datasets" / ds.name
            ds_folder.mkdir(parents=True, exist_ok=True)
            schema_payload = {
                "dataset_name": ds.name,
                "domain": ds.domain,
                "source_a": ds.source_a.model_dump(by_alias=True),
                "source_b": ds.source_b.model_dump(by_alias=True),
            }
            BenchmarkReporter.save_json(
                schema_payload, ds_folder / "dataset_schema.json"
            )

        dataset_results_matrix: dict[
            str, dict[str, AlignmentDatasetMetrics]
        ] = {}

        for model in effective_models:
            console.print(
                "\n[bold magenta]==============================================[/bold magenta]"
            )
            console.print(
                f"[bold magenta]Benchmarking Model: {model}[/bold magenta]"
            )
            console.print(
                "[bold magenta]==============================================[/bold magenta]"
            )

            for ds in suite:
                ds_metric, ds_traces = await cls.run_dataset_iterations(
                    dataset=ds,
                    model_name=model,
                    iterations=iterations,
                )
                if ds.name not in dataset_results_matrix:
                    dataset_results_matrix[ds.name] = {}
                dataset_results_matrix[ds.name][model] = ds_metric

                model_ds_dir = RunLayoutManager.get_dataset_model_dir(
                    run_dir, ds.name, model
                )
                cls._save_dataset_artifacts(
                    model_ds_dir=model_ds_dir,
                    dataset=ds,
                    model=model,
                    ds_metric=ds_metric,
                    ds_traces=ds_traces,
                    append_traces=False,
                )

                # Progressively checkpoint summaries after each dataset-model block
                cls._build_and_save_run_summaries(
                    run_dir=run_dir,
                    run_id=run_id,
                    models=effective_models,
                    suite=suite,
                    dataset_results_matrix=dataset_results_matrix,
                    iterations=iterations,
                    is_intermediate=True,
                )

        return cls._build_and_save_run_summaries(
            run_dir=run_dir,
            run_id=run_id,
            models=effective_models,
            suite=suite,
            dataset_results_matrix=dataset_results_matrix,
            iterations=iterations,
            is_intermediate=False,
        )

    @classmethod
    async def retry_benchmark_run(
        cls,
        run_target: str | Path,
        dataset_filter: list[str] | str | None = None,
        model_filter: list[str] | str | None = None,
        data_dir: Path = Path("data/schema_alignment"),
        output_dir: Path = Path("outputs/schema_integration/benchmarks/alignment"),
    ) -> AlignmentRunSummary:
        """Retry failed iterations in an existing benchmark run in-place.

        Args:
            run_target: Run ID (e.g. 'run_20260908_120000') or directory path.
            dataset_filter: Optional filter for datasets.
            model_filter: Optional filter for models.
            data_dir: Path to source alignment datasets.
            output_dir: Base directory for alignment benchmark runs.

        Returns:
            Updated AlignmentRunSummary.
        """
        run_dir = RunResilienceHelper.resolve_run_dir(run_target, output_dir)

        summary_file = run_dir / "summary.json"
        if not summary_file.exists():
            raise FileNotFoundError(
                f"Missing summary.json in benchmark run directory '{run_dir}'."
            )

        with open(summary_file, encoding="utf-8") as f:
            summary_data = json.load(f)

        run_id = summary_data.get("run_id", run_dir.name)
        all_models: list[str] = summary_data.get("models", [])
        iterations: int = summary_data.get("iterations", 1)

        if model_filter:
            m_list = [model_filter] if isinstance(model_filter, str) else model_filter
            models = [
                m
                for m in all_models
                if m in m_list or any(f in m for f in m_list)
            ]
        else:
            models = all_models

        suite = SchemaAlignmentLoader.load_suite(data_dir, dataset_filter)

        dataset_results_matrix: dict[str, dict[str, AlignmentDatasetMetrics]] = {}
        for ds in suite:
            dataset_results_matrix[ds.name] = {}
            for model in all_models:
                model_slug = model.replace("/", "_").replace(":", "_")
                model_ds_dir = run_dir / "datasets" / ds.name / model_slug
                metrics_file = model_ds_dir / "metrics.json"
                if metrics_file.exists():
                    with open(metrics_file, encoding="utf-8") as f:
                        dm_data = json.load(f)
                    dm = AlignmentDatasetMetrics.model_validate(dm_data)
                    dataset_results_matrix[ds.name][model] = dm

        tasks_to_retry: list[
            tuple[
                SchemaAlignmentDataset,
                str,
                Path,
                AlignmentDatasetMetrics,
                list[AlignmentIterationMetrics],
            ]
        ] = []

        for ds in suite:
            for model in models:
                dm = dataset_results_matrix.get(ds.name, {}).get(model)
                if not dm:
                    continue
                failed_its = [it for it in dm.iterations if it.error_message]
                if failed_its:
                    model_slug = model.replace("/", "_").replace(":", "_")
                    model_ds_dir = run_dir / "datasets" / ds.name / model_slug
                    tasks_to_retry.append(
                        (ds, model, model_ds_dir, dm, failed_its)
                    )

        if not tasks_to_retry:
            console.print(
                f"\n[bold green]No failed iterations detected in run '{run_id}'. Nothing to retry.[/bold green]"
            )
            return cls._build_and_save_run_summaries(
                run_dir=run_dir,
                run_id=run_id,
                models=all_models,
                suite=suite,
                dataset_results_matrix=dataset_results_matrix,
                iterations=iterations,
            )

        total_retries = sum(len(f) for _, _, _, _, f in tasks_to_retry)
        console.print(
            f"\n[bold yellow]Found {total_retries} failed iteration(s) to retry across "
            f"{len(tasks_to_retry)} dataset/model pair(s)...[/bold yellow]\n"
        )

        for ds, model, model_ds_dir, dm, failed_its in tasks_to_retry:
            schema_a_str = ds.source_a.model_dump_json(indent=2, by_alias=True)
            schema_b_str = ds.source_b.model_dump_json(indent=2, by_alias=True)
            new_traces: list[dict[str, Any]] = []

            for failed_it in failed_its:
                idx = failed_it.iteration_index
                console.print(
                    f"  [cyan]Retrying failed iteration {idx}/{iterations}[/cyan] on "
                    f"[bold]{ds.name}[/bold] with model [yellow]{model}[/yellow]..."
                )
                metric, trace = await cls._run_single_iteration(
                    dataset=ds,
                    model_name=model,
                    iteration_index=idx,
                    schema_a_str=schema_a_str,
                    schema_b_str=schema_b_str,
                )
                trace["retry"] = True
                new_traces.append(trace)

                replaced = False
                for i_pos, it in enumerate(dm.iterations):
                    if it.iteration_index == idx:
                        dm.iterations[i_pos] = metric
                        replaced = True
                        break
                if not replaced:
                    dm.iterations.append(metric)

            updated_dm = cls._aggregate_dataset_metrics(ds, dm.iterations)
            dataset_results_matrix[ds.name][model] = updated_dm

            cls._save_dataset_artifacts(
                model_ds_dir=model_ds_dir,
                dataset=ds,
                model=model,
                ds_metric=updated_dm,
                ds_traces=new_traces,
                append_traces=True,
            )

        run_summary = cls._build_and_save_run_summaries(
            run_dir=run_dir,
            run_id=run_id,
            models=all_models,
            suite=suite,
            dataset_results_matrix=dataset_results_matrix,
            iterations=iterations,
        )
        console.print(
            f"\n[bold green]Successfully retried failed iterations and updated run '{run_id}' in-place.[/bold green]"
        )
        return run_summary


def main() -> None:
    """CLI entrypoint for Schema Alignment Benchmarking."""
    parser = argparse.ArgumentParser(
        description="Run SchemaNet Schema Alignment Benchmark."
    )
    parser.add_argument(
        "--models",
        nargs="+",
        default=None,
        help="One or more LLM models to benchmark (defaults to gemini-3.8-flash).",
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
        "--iterations",
        type=int,
        default=1,
        help="Number of repetitions per model/dataset.",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data/schema_alignment"),
        help="Path to alignment benchmark datasets.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/schema_integration/benchmarks/alignment"),
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
        if args.retry_run:
            asyncio.run(
                AlignmentRunner.retry_benchmark_run(
                    run_target=args.retry_run,
                    dataset_filter=args.datasets,
                    model_filter=args.models,
                    data_dir=args.data_dir,
                    output_dir=args.output_dir,
                )
            )
        else:
            asyncio.run(
                AlignmentRunner.run_benchmark(
                    models=args.models,
                    dataset_filter=args.datasets,
                    iterations=args.iterations,
                    data_dir=args.data_dir,
                    output_dir=args.output_dir,
                )
            )
    except Exception as e:  # noqa: BLE001
        console.print(f"[bold red]Benchmark run failed: {e}[/bold red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
