import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

from rich.table import Table

from schema_integration.alignment.agent import align_schemas
from schema_integration.alignment.models import AlignmentReport
from schema_integration.benchmarking.alignment.evaluation import (
    AlignmentEvaluator,
)
from schema_integration.execution.executor import execute_porting
from schema_integration.mapping.agent import map_schema
from schema_integration.mapping.models import MappingReport
from schema_integration.runner import run_schema_integration
from shared.console import console
from shared.ingestion import DataLoader


def get_output_dir(dataset_name: str, model_name: str, timestamp: str) -> Path:
    out_dir = (
        Path("outputs") / "schema_integration" / dataset_name / model_name / timestamp
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def handle_run(args):
    console.print(
        f"[bold blue]Running Schema Integration for {args.input_dir}[/bold blue]"
    )
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dataset_name = Path(args.input_dir).name
    provider = args.provider
    model = args.model

    loader = DataLoader()
    try:
        source_a, _, source_b, _ = loader.load_integration_input(args.input_dir)
    except Exception as e:
        console.print(f"[bold red]Failed to load inputs: {e}[/bold red]")
        sys.exit(1)

    label_a = source_a.package.name
    label_b = source_b.package.name

    try:
        result = run_schema_integration(source_a, source_b, provider, model)
    except Exception as e:
        console.print(f"[bold red]Schema Integration Failed: {e}[/bold red]")
        sys.exit(1)

    out_dir = get_output_dir(dataset_name, model, timestamp)

    with open(out_dir / "alignment_report.json", "w", encoding="utf-8") as f:
        f.write(result.alignment_report.model_dump_json(indent=2))

    with open(out_dir / "mappings_source_a.json", "w", encoding="utf-8") as f:
        f.write(result.mapping_reports[label_a].model_dump_json(indent=2))

    with open(out_dir / "mappings_source_b.json", "w", encoding="utf-8") as f:
        f.write(result.mapping_reports[label_b].model_dump_json(indent=2))

    warnings_a = [
        {
            "target_table": w.target_table,
            "target_column": w.target_column,
            "source_label": w.source_label,
            "message": w.message,
        }
        for pt in result.execution_results[label_a].tables.values()
        for w in pt.warnings
    ]
    warnings_b = [
        {
            "target_table": w.target_table,
            "target_column": w.target_column,
            "source_label": w.source_label,
            "message": w.message,
        }
        for pt in result.execution_results[label_b].tables.values()
        for w in pt.warnings
    ]
    execution_report = {
        "alignment_metadata": result.alignment_metadata.model_dump(),
        "mapping_metadata": {
            k: v.model_dump() for k, v in result.mapping_metadata.items()
        },
        "execution_results": {
            label_a: {
                "total_rows": result.execution_results[label_a].total_rows,
                "processing_time_ms": result.execution_results[
                    label_a
                ].processing_time_ms,
                "warnings": warnings_a,
            },
            label_b: {
                "total_rows": result.execution_results[label_b].total_rows,
                "processing_time_ms": result.execution_results[
                    label_b
                ].processing_time_ms,
                "warnings": warnings_b,
            },
        },
    }
    with open(out_dir / "execution_report.json", "w", encoding="utf-8") as f:
        json.dump(execution_report, f, indent=2)

    ported_dir = out_dir / "ported_data"
    ported_dir.mkdir(exist_ok=True)

    for table_name, pt in result.execution_results[label_a].tables.items():
        pt.dataframe.to_csv(ported_dir / f"source_a_{table_name}.csv", index=False)
    for table_name, pt in result.execution_results[label_b].tables.items():
        pt.dataframe.to_csv(ported_dir / f"source_b_{table_name}.csv", index=False)

    console.print(
        f"[bold green]Successfully ran schema integration. Outputs saved to {out_dir}[/bold green]"
    )


def handle_align(args):
    console.print(f"[bold blue]Aligning schemas for {args.input_dir}[/bold blue]")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dataset_name = Path(args.input_dir).name
    provider = args.provider
    model = args.model

    loader = DataLoader()
    try:
        source_a, _, source_b, _ = loader.load_integration_input(args.input_dir)
    except Exception as e:
        console.print(f"[bold red]Failed to load inputs: {e}[/bold red]")
        sys.exit(1)

    label_a = source_a.package.name
    label_b = source_b.package.name
    schema_a_str = source_a.package.model_dump_json(indent=2, by_alias=True)
    schema_b_str = source_b.package.model_dump_json(indent=2, by_alias=True)

    try:
        report, meta = asyncio.run(
            align_schemas(
                schema_a_str,
                schema_b_str,
                label_a=label_a,
                label_b=label_b,
                provider=provider,
                model_name=model,
            )
        )
    except Exception as e:
        console.print(f"[bold red]Alignment failed: {e}[/bold red]")
        sys.exit(1)

    out_dir = get_output_dir(dataset_name, model, timestamp)
    with open(out_dir / "alignment_report.json", "w", encoding="utf-8") as f:
        f.write(report.model_dump_json(indent=2))

    # Evaluate reference-free quality card
    eval_metrics = AlignmentEvaluator.evaluate_alignment(
        target_schema=report,
        source_a=source_a.package,
        source_b=source_b.package,
        execution_meta=meta,
    )

    card = Table(
        title=f"Schema Alignment Quality Card — {dataset_name}",
        show_header=True,
        header_style="bold cyan",
    )
    card.add_column("Pillar / Metric", style="bold")
    card.add_column("Score / Status", justify="right")

    card.add_row(
        "Information Preservation (Cov_attr)",
        f"{eval_metrics.completeness:.2%}",
    )
    card.add_row(
        "Structural Integrity (S_int)",
        f"{eval_metrics.structural_integrity:.4f}",
    )
    card.add_row(
        "Cross-Source Fusion Rate (M_fusion)",
        f"{eval_metrics.fusion_rate:.2%}",
    )
    card.add_row(
        "Intra-Table Uniqueness (M_unique)",
        f"{eval_metrics.intra_table_uniqueness:.4f}",
    )
    card.add_row(
        "Flagged Duplicate Clones",
        str(len(eval_metrics.detected_clones)),
    )
    card.add_row(
        "Latency",
        f"{eval_metrics.latency_seconds:.2f}s",
    )
    console.print(card)

    if eval_metrics.unmapped_source_columns:
        console.print(
            f"[yellow]Warning: {len(eval_metrics.unmapped_source_columns)} "
            "source column(s) not retained in target schema.[/yellow]"
        )
    if eval_metrics.broken_fks:
        console.print(
            f"[red]Warning: {len(eval_metrics.broken_fks)} "
            "broken foreign key reference(s) detected.[/red]"
        )

    console.print(
        f"[bold green]Successfully aligned schemas. Outputs saved to {out_dir}[/bold green]"
    )


def handle_map(args):
    console.print(f"[bold blue]Mapping schemas for {args.input_dir}[/bold blue]")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dataset_name = Path(args.input_dir).name
    provider = args.provider
    model = args.model

    loader = DataLoader()
    try:
        source_a, _, source_b, _ = loader.load_integration_input(args.input_dir)
    except Exception as e:
        console.print(f"[bold red]Failed to load inputs: {e}[/bold red]")
        sys.exit(1)

    label_a = source_a.package.name
    label_b = source_b.package.name

    try:
        with open(args.alignment, "r", encoding="utf-8") as f:
            alignment_data = f.read()
            alignment = AlignmentReport.model_validate_json(alignment_data)
    except Exception as e:
        console.print(f"[bold red]Failed to load alignment report: {e}[/bold red]")
        sys.exit(1)

    try:
        # Source A
        report_a, meta_a = asyncio.run(
            map_schema(
                source_schema=source_a.package,
                source_label=label_a,
                alignment_report=alignment,
                provider=provider,
                model_name=model,
            )
        )

        # Source B
        report_b, meta_b = asyncio.run(
            map_schema(
                source_schema=source_b.package,
                source_label=label_b,
                alignment_report=alignment,
                provider=provider,
                model_name=model,
            )
        )
    except Exception as e:
        console.print(f"[bold red]Mapping failed: {e}[/bold red]")
        sys.exit(1)

    out_dir = get_output_dir(dataset_name, model, timestamp)
    with open(out_dir / "mappings_source_a.json", "w", encoding="utf-8") as f:
        f.write(report_a.model_dump_json(indent=2))

    with open(out_dir / "mappings_source_b.json", "w", encoding="utf-8") as f:
        f.write(report_b.model_dump_json(indent=2))

    console.print(
        f"[bold green]Successfully mapped schemas. Outputs saved to {out_dir}[/bold green]"
    )


def handle_execute(args):
    console.print(f"[bold blue]Executing porting for {args.input_dir}[/bold blue]")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dataset_name = Path(args.input_dir).name
    model = args.model

    loader = DataLoader()
    try:
        source_a, _, source_b, _ = loader.load_integration_input(args.input_dir)
    except Exception as e:
        console.print(f"[bold red]Failed to load inputs: {e}[/bold red]")
        sys.exit(1)

    try:
        with open(args.alignment, "r", encoding="utf-8") as f:
            alignment = AlignmentReport.model_validate_json(f.read())
        with open(args.mapping_a, "r", encoding="utf-8") as f:
            mapping_a = MappingReport.model_validate_json(f.read())
        with open(args.mapping_b, "r", encoding="utf-8") as f:
            mapping_b = MappingReport.model_validate_json(f.read())
    except Exception as e:
        console.print(f"[bold red]Failed to load artifacts: {e}[/bold red]")
        sys.exit(1)

    try:
        exec_a = execute_porting(
            mapping_report=mapping_a,
            source_data=source_a,
            target_schema=alignment.target_schema,
        )
        exec_b = execute_porting(
            mapping_report=mapping_b,
            source_data=source_b,
            target_schema=alignment.target_schema,
        )
    except Exception as e:
        console.print(f"[bold red]Execution failed: {e}[/bold red]")
        sys.exit(1)

    out_dir = get_output_dir(dataset_name, model, timestamp)

    warnings_a = [
        {
            "target_table": w.target_table,
            "target_column": w.target_column,
            "source_label": w.source_label,
            "message": w.message,
        }
        for pt in exec_a.tables.values()
        for w in pt.warnings
    ]
    warnings_b = [
        {
            "target_table": w.target_table,
            "target_column": w.target_column,
            "source_label": w.source_label,
            "message": w.message,
        }
        for pt in exec_b.tables.values()
        for w in pt.warnings
    ]
    execution_report = {
        "execution_results": {
            "source_a": {
                "total_rows": exec_a.total_rows,
                "processing_time_ms": exec_a.processing_time_ms,
                "warnings": warnings_a,
            },
            "source_b": {
                "total_rows": exec_b.total_rows,
                "processing_time_ms": exec_b.processing_time_ms,
                "warnings": warnings_b,
            },
        }
    }

    with open(out_dir / "execution_report.json", "w", encoding="utf-8") as f:
        json.dump(execution_report, f, indent=2)

    ported_dir = out_dir / "ported_data"
    ported_dir.mkdir(exist_ok=True)

    for table_name, pt in exec_a.tables.items():
        pt.dataframe.to_csv(ported_dir / f"source_a_{table_name}.csv", index=False)
    for table_name, pt in exec_b.tables.items():
        pt.dataframe.to_csv(ported_dir / f"source_b_{table_name}.csv", index=False)

    console.print(
        f"[bold green]Successfully executed porting. Outputs saved to {out_dir}[/bold green]"
    )


def handle_benchmark_mapping(args):
    from schema_integration.benchmarking.mapping.runner import MappingRunner

    MappingRunner.run_cli(args)


def handle_benchmark_alignment(args):
    from schema_integration.benchmarking.alignment.runner import AlignmentRunner

    retry_run = getattr(args, "retry_run", None)
    models = (
        args.models
        if hasattr(args, "models") and args.models
        else (None if retry_run else ["gemini-3.8-flash"])
    )
    datasets = (
        args.datasets
        if hasattr(args, "datasets")
        else getattr(args, "dataset", None)
    )
    iterations = getattr(args, "iterations", 1)
    data_dir = Path(getattr(args, "data_dir", "data/schema_alignment"))
    output_dir = Path(
        getattr(
            args,
            "output_dir",
            "outputs/schema_integration/benchmarks/alignment",
        )
    )

    if retry_run:
        asyncio.run(
            AlignmentRunner.retry_benchmark_run(
                run_target=retry_run,
                dataset_filter=datasets,
                model_filter=models,
                data_dir=data_dir,
                output_dir=output_dir,
            )
        )
    else:
        asyncio.run(
            AlignmentRunner.run_benchmark(
                models=models,
                dataset_filter=datasets,
                iterations=iterations,
                data_dir=data_dir,
                output_dir=output_dir,
            )
        )


def main():
    parser = argparse.ArgumentParser(description="Schema Integration CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Common arguments parser
    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument(
        "input_dir",
        type=str,
        help="Path to input directory containing dataset A and B",
    )
    common_parser.add_argument(
        "--provider", type=str, default="google-cloud", help="LLM Provider"
    )
    common_parser.add_argument(
        "--model",
        type=str,
        default="gemini-3.8-flash",
        help="LLM Model name",
    )

    # Run
    run_parser = subparsers.add_parser(
        "run", parents=[common_parser], help="Run end-to-end integration pipeline"
    )
    run_parser.set_defaults(func=handle_run)

    # Align
    align_parser = subparsers.add_parser(
        "align", parents=[common_parser], help="Run alignment only"
    )
    align_parser.set_defaults(func=handle_align)

    # Map
    map_parser = subparsers.add_parser(
        "map", parents=[common_parser], help="Run mapping only"
    )
    map_parser.add_argument(
        "--alignment",
        type=str,
        required=True,
        help="Path to alignment_report.json",
    )
    map_parser.set_defaults(func=handle_map)

    # Execute
    execute_parser = subparsers.add_parser(
        "execute", parents=[common_parser], help="Run execution (porting) only"
    )
    execute_parser.add_argument(
        "--alignment",
        type=str,
        required=True,
        help="Path to alignment_report.json",
    )
    execute_parser.add_argument(
        "--mapping-a",
        type=str,
        required=True,
        help="Path to mappings_source_a.json",
    )
    execute_parser.add_argument(
        "--mapping-b",
        type=str,
        required=True,
        help="Path to mappings_source_b.json",
    )
    execute_parser.set_defaults(func=handle_execute)

    # Benchmark (Mapping)
    bench_map_parser = subparsers.add_parser(
        "benchmark-mapping",
        help="Run schema mapping benchmark on Valentine datasets",
    )
    bench_map_parser.add_argument(
        "--models",
        nargs="+",
        default=None,
        help="One or more LLM models to benchmark (e.g. gemini-3.8-flash).",
    )
    bench_map_parser.add_argument(
        "--datasets",
        "--dataset",
        nargs="+",
        dest="datasets",
        default=None,
        help=(
            "One or more dataset names/substrings to benchmark, "
            "or 'all' to run all datasets."
        ),
    )
    bench_map_parser.add_argument(
        "--category",
        choices=["all", "single_table", "multi_table"],
        default="all",
        help="Dataset category to benchmark: 'all', 'single_table', or 'multi_table'.",
    )
    bench_map_parser.add_argument(
        "--iterations",
        type=int,
        default=1,
        help="Number of repetitions per model/dataset.",
    )
    bench_map_parser.add_argument(
        "--baselines",
        action="store_true",
        help="Include classical Valentine baseline matchers.",
    )
    bench_map_parser.add_argument(
        "--data-dir",
        type=str,
        default="data/schema_mapping",
        help="Path to mapping benchmark data directory.",
    )
    bench_map_parser.add_argument(
        "--output-dir",
        type=str,
        default="outputs/schema_integration/benchmarks/mapping",
        help="Path to save mapping benchmark reports.",
    )
    bench_map_parser.add_argument(
        "--retry-run",
        "--resume",
        dest="retry_run",
        default=None,
        help=(
            "Run ID or path to an existing mapping benchmark run to retry "
            "failed iterations in-place."
        ),
    )
    bench_map_parser.set_defaults(func=handle_benchmark_mapping)

    # Alias: 'benchmark' for benchmark-mapping
    bench_parser = subparsers.add_parser(
        "benchmark",
        parents=[bench_map_parser],
        add_help=False,
        help="Alias for benchmark-mapping",
    )
    bench_parser.set_defaults(func=handle_benchmark_mapping)

    # Benchmark (Alignment)
    bench_align_parser = subparsers.add_parser(
        "benchmark-alignment",
        help="Run schema alignment benchmark on SchemaNet datasets",
    )
    bench_align_parser.add_argument(
        "--models",
        nargs="+",
        default=None,
        help="One or more LLM models to benchmark.",
    )
    bench_align_parser.add_argument(
        "--datasets",
        "--dataset",
        nargs="+",
        dest="datasets",
        default=None,
        help=(
            "One or more dataset names/substrings to benchmark, "
            "or 'all' to run all datasets."
        ),
    )
    bench_align_parser.add_argument(
        "--iterations",
        type=int,
        default=1,
        help="Number of repetitions per model/dataset.",
    )
    bench_align_parser.add_argument(
        "--data-dir",
        type=str,
        default="data/schema_alignment",
        help="Path to alignment benchmark data directory.",
    )
    bench_align_parser.add_argument(
        "--output-dir",
        type=str,
        default="outputs/schema_integration/benchmarks/alignment",
        help="Path to save alignment benchmark reports.",
    )
    bench_align_parser.add_argument(
        "--retry-run",
        "--resume",
        dest="retry_run",
        default=None,
        help=(
            "Run ID or path to an existing alignment benchmark run to retry "
            "failed iterations in-place."
        ),
    )
    bench_align_parser.set_defaults(func=handle_benchmark_alignment)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
