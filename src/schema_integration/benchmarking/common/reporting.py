"""Reporting utilities for schema integration benchmarks (Rich, JSON, Markdown, CSV)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel

from shared.benchmarking import BenchmarkReportWriter
from shared.benchmarking.reporting import (
    checkpoint_summaries,
    format_markdown_table,
    render_rich_table,
)
from shared.benchmarking.reporting import (
    save_csv as export_summary_csv,
)
from shared.benchmarking.reporting import (
    save_json as export_json_report,
)
from shared.benchmarking.reporting import (
    save_markdown as export_markdown_report,
)


class BenchmarkReporter:
    """Reporter facade for exporting and displaying benchmark outputs."""

    @staticmethod
    def print_table(
        title: str,
        columns: list[str],
        rows: list[list[str]],
        header_style: str = "bold magenta",
    ) -> None:
        """Display Rich table in console."""
        BenchmarkReportWriter.render_rich_table(
            title, columns, rows, header_style=header_style
        )

    @staticmethod
    def format_table(
        headers: list[str],
        rows: list[list[str]],
        alignments: list[str] | None = None,
    ) -> str:
        """Format a Markdown table."""
        return BenchmarkReportWriter.format_markdown_table(
            headers, rows, alignments
        )

    @staticmethod
    def save_json(
        data: BaseModel | dict[str, Any],
        output_path: Path,
    ) -> Path:
        """Persist JSON report to disk."""
        return BenchmarkReportWriter.save_json(data, output_path)

    @staticmethod
    def save_csv(
        rows: list[dict[str, Any]],
        output_path: Path,
    ) -> Path:
        """Persist CSV report to disk."""
        return BenchmarkReportWriter.save_csv(rows, output_path)

    @staticmethod
    def save_markdown(
        title: str,
        summary_table_md: str,
        details_md: str,
        output_path: Path,
    ) -> Path:
        """Persist Markdown report to disk."""
        return BenchmarkReportWriter.save_markdown(
            title, summary_table_md, details_md, output_path
        )

    @staticmethod
    def checkpoint_summaries(
        run_dir: Path,
        summary_data: BaseModel | dict[str, Any],
        summary_rows: list[dict[str, Any]],
        markdown_content: str,
    ) -> None:
        """Progressively flush summary reports."""
        BenchmarkReportWriter.checkpoint_summaries(
            run_dir, summary_data, summary_rows, markdown_content
        )


__all__ = [
    "BenchmarkReportWriter",
    "BenchmarkReporter",
    "checkpoint_summaries",
    "export_json_report",
    "export_markdown_report",
    "export_summary_csv",
    "format_markdown_table",
    "render_rich_table",
]
