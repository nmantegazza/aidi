"""Reporting utilities for Entity Resolution benchmarking.

Generates Markdown reports, Rich console tables, structured JSON,
and tabular CSV summaries.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
from pydantic import BaseModel
from rich.table import Table

from shared.console import console

from .models import (
    ERDatasetMetrics,
    ERRunSummary,
    RunStatus,
)


def format_cost_usd(cost_usd: float | None) -> str:
    """Formats an optional USD cost for Markdown table cells.

    Args:
        cost_usd: Estimated cost in USD, or None when the run is unpriced.

    Returns:
        Formatted currency string, or a dash when no cost was determined.
    """
    return f"${cost_usd:.4f}" if cost_usd is not None else "-"


def render_rich_table(
    title: str,
    columns: list[str],
    rows: list[list[str]],
    header_style: str = "bold magenta",
) -> Table:
    """Renders and prints a Rich console table.

    Args:
        title: Table title.
        columns: List of column header names.
        rows: List of row value lists.
        header_style: Rich style for headers.

    Returns:
        The generated Rich Table instance.
    """
    table = Table(title=title, show_header=True, header_style=header_style)
    for col in columns:
        table.add_column(col)
    for row in rows:
        table.add_row(*row)
    console.print()
    console.print(table)
    console.print()
    return table


def format_markdown_table(
    headers: list[str],
    rows: list[list[str]],
    alignments: list[str] | None = None,
) -> str:
    """Formats a GitHub-flavored Markdown table.

    Args:
        headers: Column header names.
        rows: Rows with string cell contents.
        alignments: Optional alignments per column ('left', 'center', 'right').

    Returns:
        Markdown table string.
    """
    if not headers:
        return ""

    num_cols = len(headers)
    sep_list = []
    for i in range(num_cols):
        align = (
            alignments[i].lower()
            if alignments and i < len(alignments)
            else "left"
        )
        if align == "right":
            sep_list.append("---:")
        elif align == "center":
            sep_list.append(":---:")
        else:
            sep_list.append(":---")

    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(sep_list) + " |",
    ]
    for row in rows:
        padded_row = [row[i] if i < len(row) else "" for i in range(num_cols)]
        sanitized = [cell.replace("|", "\\|") for cell in padded_row]
        lines.append("| " + " | ".join(sanitized) + " |")

    return "\n".join(lines)


def export_json(data: BaseModel | dict[str, Any], path: Path) -> Path:
    """Exports a Pydantic model or dictionary to a formatted JSON file.

    Args:
        data: Pydantic model or dict.
        path: Target file path.

    Returns:
        The destination Path.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, BaseModel):
        content = data.model_dump_json(indent=2)
    else:
        content = json.dumps(data, indent=2, default=str)
    path.write_text(content, encoding="utf-8")
    return path


def export_csv(rows: list[dict[str, Any]], path: Path) -> Path:
    """Exports a list of row dictionaries to a CSV file.

    Args:
        rows: List of dicts representing tabular rows.
        path: Target file path.

    Returns:
        The destination Path.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows)
    df.to_csv(path, index=False)
    return path


def build_dataset_markdown_report(
    dm: ERDatasetMetrics,
    model_name: str,
    sample_pairs: dict[str, Any] | None = None,
) -> str:
    """Constructs a diagnostic Markdown report for a dataset and model.

    Args:
        dm: Dataset metrics container.
        model_name: Model identifier string.
        sample_pairs: Optional classified sample pairs.

    Returns:
        Markdown report string.
    """
    total_it_line = (
        f"- **Total Iterations**: {len(dm.iterations)} "
        f"({dm.successful_iterations_count} Succeeded, "
        f"{dm.failed_iterations_count} Failed)\n"
    )
    lines = [
        f"# 🔬 ER Diagnostic Report: {dm.dataset_name} | `{model_name}`\n",
        f"- **Domain**: {dm.domain}",
        f"- **Rows A**: {dm.num_rows_a:,}",
        f"- **Rows B**: {dm.num_rows_b:,}",
        f"- **Ground Truth Matches**: {dm.ground_truth_count:,}",
        total_it_line,
        "## 📊 Statistical Performance Summary\n",
    ]

    succ_iters = [
        it for it in dm.iterations if it.status == RunStatus.SUCCESS
    ]
    min_f1 = min((it.f1 for it in succ_iters), default=0.0)
    max_f1 = max((it.f1 for it in succ_iters), default=0.0)
    min_p = min((it.precision for it in succ_iters), default=0.0)
    max_p = max((it.precision for it in succ_iters), default=0.0)
    min_r = min((it.recall for it in succ_iters), default=0.0)
    max_r = max((it.recall for it in succ_iters), default=0.0)
    min_pr = min((it.pairs_recall for it in succ_iters), default=0.0)
    max_pr = max((it.pairs_recall for it in succ_iters), default=0.0)
    min_rr = min((it.reduction_ratio for it in succ_iters), default=0.0)
    max_rr = max((it.reduction_ratio for it in succ_iters), default=0.0)
    min_lat = min((it.latency_seconds for it in succ_iters), default=0.0)
    max_lat = max((it.latency_seconds for it in succ_iters), default=0.0)

    stats_headers = ["Metric", "Mean ± Std", "Min", "Max"]
    stats_rows = [
        [
            "F1 Score",
            f"{dm.mean_f1:.4f} ± {dm.std_f1:.4f}",
            f"{min_f1:.4f}",
            f"{max_f1:.4f}",
        ],
        [
            "Precision",
            f"{dm.mean_precision:.4f} ± {dm.std_precision:.4f}",
            f"{min_p:.4f}",
            f"{max_p:.4f}",
        ],
        [
            "Recall",
            f"{dm.mean_recall:.4f} ± {dm.std_recall:.4f}",
            f"{min_r:.4f}",
            f"{max_r:.4f}",
        ],
        [
            "Pairs Recall (Indexing)",
            f"{dm.mean_pairs_recall:.4f} ± {dm.std_pairs_recall:.4f}",
            f"{min_pr:.4f}",
            f"{max_pr:.4f}",
        ],
        [
            "Reduction Ratio (Indexing)",
            f"{dm.mean_reduction_ratio:.4f} ± {dm.std_reduction_ratio:.4f}",
            f"{min_rr:.4f}",
            f"{max_rr:.4f}",
        ],
        [
            "Latency (s)",
            f"{dm.mean_latency:.2f}s ± {dm.std_latency:.2f}s",
            f"{min_lat:.2f}s",
            f"{max_lat:.2f}s",
        ],
    ]
    lines.append(
        format_markdown_table(
            stats_headers,
            stats_rows,
            ["left", "right", "right", "right"],
        )
    )
    lines.append("\n## 🔁 Iteration Breakdown\n")

    it_headers = [
        "Iter",
        "Status",
        "Precision",
        "Recall",
        "F1",
        "Candidates",
        "Pairs Recall",
        "Red. Ratio",
        "Latency",
        "Tokens",
        "Cost (USD)",
    ]
    it_rows = []
    for it in dm.iterations:
        if it.status == RunStatus.SUCCESS:
            it_rows.append([
                str(it.iteration_index),
                "✅ SUCCESS",
                f"{it.precision:.4f}",
                f"{it.recall:.4f}",
                f"{it.f1:.4f}",
                f"{it.candidates:,}",
                f"{it.pairs_recall:.4f}",
                f"{it.reduction_ratio:.4f}",
                f"{it.latency_seconds:.2f}s",
                f"{it.token_usage.total_tokens:,}",
                format_cost_usd(it.token_usage.cost_usd),
            ])
        else:
            err = it.error_message or "Unknown failure"
            if len(err) > 30:
                err = err[:27] + "..."
            it_rows.append([
                str(it.iteration_index),
                f"❌ FAILED ({err})",
                "-",
                "-",
                "-",
                "-",
                "-",
                "-",
                f"{it.latency_seconds:.2f}s",
                "-",
                "-",
            ])

    lines.append(
        format_markdown_table(
            it_headers,
            it_rows,
            [
                "right",
                "left",
                "right",
                "right",
                "right",
                "right",
                "right",
                "right",
                "right",
                "right",
                "right",
            ],
        )
    )

    if dm.flakiness_analysis:
        fa = dm.flakiness_analysis
        lines.append("\n## 🎲 Flakiness & Stability Analysis\n")
        lines.append(
            f"- **Stability Ratio**: {fa.stability_ratio:.2%}\n"
            f"- **Consistent Matches Across All Runs**: "
            f"{len(fa.consistent_matches):,}\n"
            f"- **Flaky Matches (Stochastic Variation)**: "
            f"{len(fa.flaky_matches):,}\n"
        )
        if fa.flaky_matches:
            flaky_headers = ["Pair (Left ID, Right ID)", "Occurrence Frequency"]
            flaky_rows = [
                [pair_key, f"{freq:.2%}"]
                for pair_key, freq in sorted(
                    fa.flaky_matches.items(), key=lambda x: x[1]
                )[:20]
            ]
            lines.append(format_markdown_table(flaky_headers, flaky_rows))

    failed_iters = [
        it for it in dm.iterations if it.status == RunStatus.FAILED
    ]
    if failed_iters:
        lines.append("\n## ⚠️ Failure Forensics\n")
        for fi in failed_iters:
            lines.append(f"### Iteration {fi.iteration_index} Error")
            lines.append(f"**Message**: `{fi.error_message}`\n")
            if fi.traceback:
                lines.append(f"```text\n{fi.traceback}\n```\n")

    return "\n".join(lines)


def build_run_summary_markdown(summary: ERRunSummary) -> str:
    """Builds the root summary Markdown report across all datasets and models.

    Args:
        summary: Master run summary container.

    Returns:
        Master Markdown report text.
    """
    ts_str = summary.timestamp.strftime("%Y-%m-%d %H:%M:%S")
    tot_iter_line = (
        f"- **Total Iterations**: {summary.total_iterations_count} "
        f"({summary.failed_iterations_count} failed)\n"
    )
    lines = [
        "# 📊 Entity Resolution Benchmark Summary Report\n",
        f"- **Run ID**: `{summary.run_id}`",
        f"- **Timestamp**: {ts_str}",
        f"- **Iterations Per Setting**: {summary.iterations}",
        f"- **Models Evaluated**: {', '.join(summary.models)}",
        f"- **Datasets**: {', '.join(summary.datasets)}",
        tot_iter_line,
        "## 🏆 Model Comparative Macro Performance\n",
    ]

    macro_headers = [
        "Model",
        "Mean F1",
        "Mean Precision",
        "Mean Recall",
        "Mean Pairs Recall",
        "Mean Red. Ratio",
        "Avg Latency",
        "Total Tokens",
        "Cost (USD)",
        "Success Rate",
    ]
    macro_rows = []
    for model_name in summary.models:
        all_dms = [
            summary.matrix[ds][model_name]
            for ds in summary.datasets
            if ds in summary.matrix and model_name in summary.matrix[ds]
        ]
        if not all_dms:
            continue

        succ_iters = sum(dm.successful_iterations_count for dm in all_dms)
        tot_iters = sum(len(dm.iterations) for dm in all_dms)
        success_rate = (succ_iters / tot_iters) if tot_iters > 0 else 0.0

        f1_list = [
            dm.mean_f1 for dm in all_dms if dm.successful_iterations_count > 0
        ]
        prec_list = [
            dm.mean_precision
            for dm in all_dms
            if dm.successful_iterations_count > 0
        ]
        rec_list = [
            dm.mean_recall
            for dm in all_dms
            if dm.successful_iterations_count > 0
        ]
        pr_list = [
            dm.mean_pairs_recall
            for dm in all_dms
            if dm.successful_iterations_count > 0
        ]
        rr_list = [
            dm.mean_reduction_ratio
            for dm in all_dms
            if dm.successful_iterations_count > 0
        ]
        lat_list = [
            dm.mean_latency
            for dm in all_dms
            if dm.successful_iterations_count > 0
        ]
        tokens_sum = sum(dm.total_tokens for dm in all_dms)
        cost_sum = sum(dm.estimated_cost_usd for dm in all_dms)

        avg_f1 = sum(f1_list) / len(f1_list) if f1_list else 0.0
        avg_prec = sum(prec_list) / len(prec_list) if prec_list else 0.0
        avg_rec = sum(rec_list) / len(rec_list) if rec_list else 0.0
        avg_pr = sum(pr_list) / len(pr_list) if pr_list else 0.0
        avg_rr = sum(rr_list) / len(rr_list) if rr_list else 0.0
        avg_lat = sum(lat_list) / len(lat_list) if lat_list else 0.0

        macro_rows.append([
            f"`{model_name}`",
            f"{avg_f1:.4f}",
            f"{avg_prec:.4f}",
            f"{avg_rec:.4f}",
            f"{avg_pr:.4f}",
            f"{avg_rr:.4f}",
            f"{avg_lat:.2f}s",
            f"{tokens_sum:,}",
            format_cost_usd(cost_sum),
            f"{success_rate:.1%}",
        ])

    lines.append(
        format_markdown_table(
            macro_headers,
            macro_rows,
            [
                "left",
                "right",
                "right",
                "right",
                "right",
                "right",
                "right",
                "right",
                "right",
                "right",
            ],
        )
    )

    lines.append("\n## 📋 Per-Dataset Scorecard\n")
    sc_headers = [
        "Dataset",
        "Model",
        "F1 (Mean ± Std)",
        "Precision",
        "Recall",
        "Pairs Recall",
        "Red. Ratio",
        "Latency",
        "Success Rate",
    ]
    sc_rows = []
    for ds_name in summary.datasets:
        for model_name in summary.models:
            dm = summary.matrix.get(ds_name, {}).get(model_name)
            if not dm:
                continue
            succ = dm.successful_iterations_count
            tot = len(dm.iterations)
            rate_str = f"{succ}/{tot}"
            f1_str = f"{dm.mean_f1:.4f} ± {dm.std_f1:.4f}"
            sc_rows.append([
                dm.dataset_name,
                f"`{model_name}`",
                f1_str,
                f"{dm.mean_precision:.4f}",
                f"{dm.mean_recall:.4f}",
                f"{dm.mean_pairs_recall:.4f}",
                f"{dm.mean_reduction_ratio:.4f}",
                f"{dm.mean_latency:.2f}s",
                rate_str,
            ])

    lines.append(
        format_markdown_table(
            sc_headers,
            sc_rows,
            [
                "left",
                "left",
                "right",
                "right",
                "right",
                "right",
                "right",
                "right",
                "right",
            ],
        )
    )

    if summary.failed_iterations_count > 0:
        lines.append("\n## ⚠️ Failed Runs & Remediation\n")
        fail_headers = ["Dataset", "Model", "Iter", "Error Snippet"]
        fail_rows = []
        for ds_name in summary.datasets:
            for model_name in summary.models:
                dm = summary.matrix.get(ds_name, {}).get(model_name)
                if not dm:
                    continue
                for it in dm.iterations:
                    if it.status == RunStatus.FAILED:
                        err_msg = it.error_message or "Failed"
                        if len(err_msg) > 60:
                            err_msg = err_msg[:57] + "..."
                        fail_rows.append([
                            ds_name,
                            f"`{model_name}`",
                            str(it.iteration_index),
                            err_msg,
                        ])

        lines.append(format_markdown_table(fail_headers, fail_rows))
        lines.append(
            "\n### Re-execute Failed Iterations\n"
            "You can seamlessly resume and re-execute only the failed "
            f"iterations with:\n\n"
            f"```bash\nuv run er-benchmark --retry {summary.run_id}\n```\n"
        )

    return "\n".join(lines)


def build_run_summary_csv(summary: ERRunSummary) -> list[dict[str, Any]]:
    """Transforms a run summary into a list of flattened row dictionaries for CSV.

    Args:
        summary: Master run summary container.

    Returns:
        List of dictionaries with column key-values.
    """
    rows: list[dict[str, Any]] = []
    for ds_name in summary.datasets:
        for model_name in summary.models:
            dm = summary.matrix.get(ds_name, {}).get(model_name)
            if not dm:
                continue
            rows.append({
                "dataset": dm.dataset_name,
                "domain": dm.domain,
                "model": model_name,
                "mean_f1": dm.mean_f1,
                "std_f1": dm.std_f1,
                "mean_precision": dm.mean_precision,
                "std_precision": dm.std_precision,
                "mean_recall": dm.mean_recall,
                "std_recall": dm.std_recall,
                "mean_pairs_recall": dm.mean_pairs_recall,
                "std_pairs_recall": dm.std_pairs_recall,
                "mean_reduction_ratio": dm.mean_reduction_ratio,
                "std_reduction_ratio": dm.std_reduction_ratio,
                "mean_latency": dm.mean_latency,
                "std_latency": dm.std_latency,
                "prompt_tokens": dm.prompt_tokens,
                "completion_tokens": dm.completion_tokens,
                "total_tokens": dm.total_tokens,
                "estimated_cost_usd": dm.estimated_cost_usd,
                "successful_iterations": dm.successful_iterations_count,
                "failed_iterations": dm.failed_iterations_count,
                "total_iterations": len(dm.iterations),
            })
    return rows
