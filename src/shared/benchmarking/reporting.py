"""Unified reporting, serialization, and checkpointing for benchmark suites."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel
from rich.table import Table

from shared.console import console


def render_rich_table(
    title: str,
    columns: list[str],
    rows: list[list[str]],
    header_style: str = "bold magenta",
) -> None:
    """Renders a structured table in the console using Rich.

    Args:
        title: Table title header.
        columns: List of column header names.
        rows: Matrix of string row cell values.
        header_style: Rich style for headers.
    """
    table = Table(title=title, show_header=True, header_style=header_style)
    for col in columns:
        table.add_column(col)
    for row in rows:
        table.add_row(*row)
    console.print(table)


def format_markdown_table(
    headers: list[str],
    rows: list[list[str]],
    alignments: list[str] | None = None,
) -> str:
    """Formats headers and row strings into a clean standard Markdown table.

    Args:
        headers: Column header titles.
        rows: List of row cell lists.
        alignments: Optional alignment list (e.g. ['left', 'center', 'right']).

    Returns:
        Formatted Markdown table string.
    """
    if not headers:
        return ""

    align_map = {
        "left": ":---",
        "center": ":---:",
        "right": "---:",
    }

    if alignments and len(alignments) == len(headers):
        sep = [align_map.get(a.lower(), "---") for a in alignments]
    else:
        sep = ["---" for _ in headers]

    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(sep) + " |",
    ]
    for row in rows:
        padded_row = list(row) + [""] * (len(headers) - len(row))
        lines.append("| " + " | ".join(padded_row[: len(headers)]) + " |")

    return "\n".join(lines)


def save_json(
    data: BaseModel | dict[str, Any],
    output_path: Path,
) -> Path:
    """Atomically serializes benchmark data to an indented JSON file.

    Args:
        data: Pydantic model instance or dictionary to serialize.
        output_path: Destination file path.

    Returns:
        The written Path.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if isinstance(data, BaseModel):
        content = data.model_dump_json(indent=2)
    else:
        content = json.dumps(data, indent=2, default=str)

    # Atomic write via temporary file
    temp_file = output_path.with_suffix(".tmp")
    try:
        temp_file.write_text(content, encoding="utf-8")
        temp_file.replace(output_path)
    finally:
        if temp_file.exists():
            try:
                temp_file.unlink()
            except OSError:
                pass

    return output_path


def save_csv(
    rows: list[dict[str, Any]],
    output_path: Path,
) -> Path:
    """Atomically writes benchmark metrics to a flat CSV file.

    Args:
        rows: List of flat metric dictionaries.
        output_path: Destination file path.

    Returns:
        The written Path.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    temp_file = output_path.with_suffix(".tmp")
    try:
        if not rows:
            temp_file.write_text("", encoding="utf-8")
        else:
            fieldnames = list(rows[0].keys())
            with open(temp_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
        temp_file.replace(output_path)
    finally:
        if temp_file.exists():
            try:
                temp_file.unlink()
            except OSError:
                pass

    return output_path


def save_markdown(
    title: str,
    summary_table_md: str,
    details_md: str,
    output_path: Path,
) -> Path:
    """Atomically writes benchmark report as a formatted Markdown document.

    Args:
        title: Main document title.
        summary_table_md: Markdown table string for summary results.
        details_md: Detailed markdown content and per-dataset breakdown.
        output_path: Destination file path.

    Returns:
        The written Path.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    content = (
        f"# {title}\n\n"
        f"## Summary Results\n\n"
        f"{summary_table_md}\n\n"
        f"## Detailed Analysis\n\n"
        f"{details_md}\n"
    )

    temp_file = output_path.with_suffix(".tmp")
    try:
        temp_file.write_text(content, encoding="utf-8")
        temp_file.replace(output_path)
    finally:
        if temp_file.exists():
            try:
                temp_file.unlink()
            except OSError:
                pass

    return output_path


def checkpoint_summaries(
    run_dir: Path,
    summary_data: BaseModel | dict[str, Any],
    summary_rows: list[dict[str, Any]],
    markdown_content: str,
) -> None:
    """Progressively flushes summary.json, summary.csv, and summary.md.

    Ensures that benchmark progress is safe against intermediate process aborts.

    Args:
        run_dir: Benchmark run directory root.
        summary_data: Model or dictionary containing full summary report.
        summary_rows: List of flat row dicts for CSV representation.
        markdown_content: Formatted markdown string.
    """
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    save_json(summary_data, run_dir / "summary.json")
    save_csv(summary_rows, run_dir / "summary.csv")

    temp_md = run_dir / "summary.md.tmp"
    try:
        temp_md.write_text(markdown_content, encoding="utf-8")
        temp_md.replace(run_dir / "summary.md")
    finally:
        if temp_md.exists():
            try:
                temp_md.unlink()
            except OSError:
                pass


class BenchmarkReportWriter:
    """Facade for tabular formatting, file persistence, and checkpointing."""

    render_rich_table = staticmethod(render_rich_table)
    format_markdown_table = staticmethod(format_markdown_table)
    save_json = staticmethod(save_json)
    save_csv = staticmethod(save_csv)
    save_markdown = staticmethod(save_markdown)
    checkpoint_summaries = staticmethod(checkpoint_summaries)
