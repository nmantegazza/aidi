"""
Encapsulated exporter for Entity Resolution standalone runs, evaluation runs, and benchmarks.
Centralizes HTML report rendering, CSV exports, JSON serialization, and directory output layouts.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple
import pandas as pd

from shared.config import config
from shared.console import console
from shared.html_builder import (
    build_html_document,
    render_markdown_to_html,
    render_mermaid_to_html,
)
from .evaluation_models import (
    EntityResEvalReport,
    SamplePair,
    ColumnValueComparison,
    BoundarySamples,
)
from .models import EntityResolutionResult
from .benchmarking.models import EntityResBenchmarkReport, EntityResFailedRunReport


class EntityResolutionExporter:
    """Manages all file exports, CSV side-by-side formatting, and HTML reports for ER."""

    @staticmethod
    def _export_csv(
        df: pd.DataFrame,
        df_a: pd.DataFrame,
        df_b: pd.DataFrame,
        path: Path,
        ground_truth: Optional[Set[Tuple]] = None,
    ) -> None:
        """Helper to export a classified subset with side-by-side columns and optional GT label."""
        if df is None or df.empty:
            pd.DataFrame().to_csv(path, index=False)
            return

        # Sort by aggregate_score descending
        df_sorted = df.sort_values(by="aggregate_score", ascending=False)

        # Reset index to bring left_id and right_id as regular columns
        df_out = df_sorted.reset_index()
        if "left_id" not in df_out.columns and "level_0" in df_out.columns:
            df_out = df_out.rename(
                columns={"level_0": "left_id", "level_1": "right_id"}
            )

        # Add prefix to source columns to make them side-by-side
        df_a_prep = df_a.add_prefix("left_")
        df_b_prep = df_b.add_prefix("right_")

        # Avoid column collisions if df_a or df_b contains an ID column named left_id / right_id
        if "left_id" in df_a_prep.columns:
            df_a_prep = df_a_prep.drop(columns=["left_id"])
        if "right_id" in df_b_prep.columns:
            df_b_prep = df_b_prep.drop(columns=["right_id"])

        # Merge side-by-side
        df_out = df_out.merge(df_a_prep, left_on="left_id", right_index=True, how="left")
        df_out = df_out.merge(df_b_prep, left_on="right_id", right_index=True, how="left")

        if (
            ground_truth is not None
            and "left_id" in df_out.columns
            and "right_id" in df_out.columns
        ):
            gt_set = set(ground_truth)
            is_gt = [
                (row["left_id"], row["right_id"]) in gt_set
                for _, row in df_out[["left_id", "right_id"]].iterrows()
            ]
            df_out.insert(2, "is_true_match", is_gt)

        df_out.to_csv(path, index=False)

    @staticmethod
    def _generate_sample_table(samples: List[Dict[str, Any]]) -> str:
        """Generates an HTML table from a list of record dicts."""
        if not samples:
            return "<p>No samples available.</p>"

        cols = list(samples[0].keys())
        html = "<table><thead><tr>"
        for col in cols:
            html += f"<th>{col}</th>"
        html += "</tr></thead><tbody>"

        for row in samples:
            html += "<tr>"
            for col in cols:
                val = row.get(col, "")
                html += f"<td>{val if val is not None else ''}</td>"
            html += "</tr>"

        html += "</tbody></table>"
        return html

    @staticmethod
    def _render_profiling_table(
        meta_a: Dict[str, Any], meta_b: Dict[str, Any]
    ) -> str:
        """Helper to render profiling comparison to Markdown."""
        data = [
            {
                "Metric": "**Total Rows**",
                "Source A": meta_a["total_row_count"],
                "Source B": meta_b["total_row_count"],
            },
            {
                "Metric": "**Total Columns**",
                "Source A": meta_a["column_count"],
                "Source B": meta_b["column_count"],
            },
        ]

        cols_a = set(meta_a["column_metadata"].keys())
        cols_b = set(meta_b["column_metadata"].keys())
        all_cols = sorted(list(cols_a | cols_b))

        for col in all_cols:
            stats_a = meta_a["column_metadata"].get(col, {})
            stats_b = meta_b["column_metadata"].get(col, {})

            data.append(
                {"Metric": f"**Column: {col}**", "Source A": "", "Source B": ""}
            )
            data.append(
                {
                    "Metric": "  Null %",
                    "Source A": f"{stats_a.get('null_percentage', 'N/A')}%",
                    "Source B": f"{stats_b.get('null_percentage', 'N/A')}%",
                }
            )
            data.append(
                {
                    "Metric": "  Cardinality",
                    "Source A": str(stats_a.get("cardinality", "N/A")),
                    "Source B": str(stats_b.get("cardinality", "N/A")),
                }
            )
            data.append(
                {
                    "Metric": "  Uniqueness %",
                    "Source A": f"{stats_a.get('uniqueness_percentage', 'N/A')}%",
                    "Source B": f"{stats_b.get('uniqueness_percentage', 'N/A')}%",
                }
            )

        return pd.DataFrame(data).to_markdown(index=False)

    @staticmethod
    def _generate_mermaid_schema(table_name: str, meta: Dict[str, Any]) -> str:
        """Generates a Mermaid class diagram code from profiling metadata."""
        safe_name = table_name.replace(" ", "_").replace("-", "_")
        lines = ["classDiagram", f"    class {safe_name} {{"]
        for col in meta.get("column_metadata", {}).keys():
            lines.append(f"        {col}")
        lines.append("    }")
        return "\n".join(lines)

    @staticmethod
    def _generate_boundary_samples_html(samples: BoundarySamples) -> str:
        """Generates HTML section for boundary samples."""
        if not samples:
            return ""

        html = "<h2>🎯 Classifier Boundary & Sample Pairs</h2>\n"
        html += (
            "<p>A detailed view of sample pairs near the classifier decision"
            " boundaries.</p>\n"
        )

        categories = [
            (
                "Matches (Highest Score)",
                samples.matches_highest,
                "Most confident matches",
            ),
            (
                "Matches (Lowest Score)",
                samples.matches_lowest,
                "Borderline matches (closest to threshold)",
            ),
            (
                "Uncertain (Highest Score)",
                samples.uncertain_highest,
                "Uncertain pairs closest to match threshold",
            ),
            (
                "Uncertain (Lowest Score)",
                samples.uncertain_lowest,
                "Uncertain pairs closest to non-match threshold",
            ),
            (
                "Non-Matches (Highest Score)",
                samples.non_matches_highest,
                "Borderline non-matches (closest to threshold)",
            ),
            (
                "Non-Matches (Lowest Score)",
                samples.non_matches_lowest,
                "Most confident non-matches",
            ),
        ]

        for title, pairs, desc in categories:
            html += (
                "<details style='margin-bottom: 15px; border: 1px solid #ddd;"
                " padding: 10px; border-radius: 4px;'>\n"
            )
            html += (
                f"  <summary style='font-weight: bold; cursor: pointer;'>"
                f"{title} ({len(pairs)} pairs) - <span style='font-weight:"
                f" normal; color: #666;'>{desc}</span></summary>\n"
            )

            if not pairs:
                html += (
                    "  <p style='margin-top: 10px; color: #777;'>No pairs"
                    " found in this category.</p>\n"
                )
            else:
                html += "  <div style='margin-top: 10px; overflow-x: auto;'>\n"
                for i, pair in enumerate(pairs):
                    match_badge = ""
                    if pair.is_true_match is not None:
                        if pair.is_true_match:
                            match_badge = (
                                " <span style='background-color: #d4edda;"
                                " color: #155724; padding: 2px 6px;"
                                " border-radius: 3px; font-size: 0.85em;"
                                " font-weight: bold;'>True Match</span>"
                            )
                        else:
                            match_badge = (
                                " <span style='background-color: #f8d7da;"
                                " color: #721c24; padding: 2px 6px;"
                                " border-radius: 3px; font-size: 0.85em;"
                                " font-weight: bold;'>False Match</span>"
                            )

                    html += (
                        "    <div style='background-color: #f9f9f9;"
                        " border-left: 4px solid #007bff; padding: 8px;"
                        " margin-bottom: 10px; border-radius: 0 4px 4px 0;'>\n"
                    )
                    html += (
                        f"      <strong>Pair #{i+1}</strong>: ID A ="
                        f" <code>{pair.id_a}</code> | ID B ="
                        f" <code>{pair.id_b}</code> | <strong>Score</strong> ="
                        f" <code>{pair.aggregate_score:.4f}</code>{match_badge}\n"
                    )
                    html += (
                        "      <table style='width: 100%; border-collapse:"
                        " collapse; margin-top: 5px; font-size: 0.9em;'>\n"
                        "        <thead>\n"
                        "          <tr style='border-bottom: 1px solid"
                        " #eee;'>\n"
                        "            <th style='text-align: left; padding:"
                        " 4px;'>Column</th>\n"
                        "            <th style='text-align: left; padding:"
                        " 4px;'>Source A Value</th>\n"
                        "            <th style='text-align: left; padding:"
                        " 4px;'>Source B Value</th>\n"
                        "            <th style='text-align: right; padding:"
                        " 4px;'>Similarity</th>\n"
                        "          </tr>\n"
                        "        </thead>\n"
                        "        <tbody>\n"
                    )

                    for comp in pair.column_comparisons:
                        sim_str = (
                            f"{comp.similarity_score:.4f}"
                            if comp.similarity_score is not None
                            else "N/A"
                        )
                        val_a_display = (
                            comp.val_a
                            if comp.val_a is not None
                            else '<span style="color:#aaa;">NULL</span>'
                        )
                        val_b_display = (
                            comp.val_b
                            if comp.val_b is not None
                            else '<span style="color:#aaa;">NULL</span>'
                        )
                        html += (
                            "          <tr style='border-bottom: 1px solid"
                            " #f1f1f1;'>\n"
                            "            <td style='padding: 4px; font-weight:"
                            f" bold;'>{comp.column_name}</td>\n"
                            "            <td style='padding: 4px; color:"
                            f" #333;'>{val_a_display}</td>\n"
                            "            <td style='padding: 4px; color:"
                            f" #333;'>{val_b_display}</td>\n"
                            "            <td style='padding: 4px; text-align:"
                            f" right;'>{sim_str}</td>\n"
                            "          </tr>\n"
                        )

                    html += "        </tbody>\n      </table>\n    </div>\n"
                html += "  </div>\n"

            html += "</details>\n"

        return html

    @staticmethod
    def _extract_sample_pairs(
        df: pd.DataFrame,
        df_a: pd.DataFrame,
        df_b: pd.DataFrame,
        matching_columns: dict,
        ground_truth: Set[Tuple],
        n: int,
        highest: bool = True,
    ) -> List[SamplePair]:
        """Helper to extract top-N highest/lowest scoring pairs from a classified DataFrame."""
        if df is None or df.empty:
            return []

        df_sorted = df.sort_values(by="aggregate_score", ascending=not highest)
        sampled_df = df_sorted.head(n)

        sample_list = []
        for (idx_a, idx_b), row in sampled_df.iterrows():
            col_comparisons = []
            for col in matching_columns.keys():
                val_a = (
                    df_a.loc[idx_a, col]
                    if col in df_a.columns and idx_a in df_a.index
                    else None
                )
                val_b = (
                    df_b.loc[idx_b, col]
                    if col in df_b.columns and idx_b in df_b.index
                    else None
                )

                if isinstance(val_a, pd.Series):
                    val_a = val_a.iloc[0] if not val_a.empty else None
                if isinstance(val_b, pd.Series):
                    val_b = val_b.iloc[0] if not val_b.empty else None

                str_a = str(val_a) if pd.notna(val_a) else None
                str_b = str(val_b) if pd.notna(val_b) else None
                sim_score = float(row[col]) if col in row else None

                col_comparisons.append(
                    ColumnValueComparison(
                        column_name=col,
                        val_a=str_a,
                        val_b=str_b,
                        similarity_score=sim_score,
                    )
                )

            pair = (idx_a, idx_b)
            is_true = pair in ground_truth if ground_truth else None

            sample_list.append(
                SamplePair(
                    id_a=str(idx_a),
                    id_b=str(idx_b),
                    aggregate_score=float(row["aggregate_score"]),
                    is_true_match=is_true,
                    column_comparisons=col_comparisons,
                )
            )
        return sample_list

    @staticmethod
    def _extract_boundary_samples(
        result: EntityResolutionResult,
        ground_truth: Set[Tuple],
    ) -> BoundarySamples:
        """Extracts boundary sample pairs from an EntityResolutionResult."""
        matching_cols = result.config.matching_columns if result.config else {}
        return BoundarySamples(
            matches_highest=EntityResolutionExporter._extract_sample_pairs(
                result.matches,
                result.df_a_clean,
                result.df_b_clean,
                matching_cols,
                ground_truth,
                50,
                highest=True,
            ),
            matches_lowest=EntityResolutionExporter._extract_sample_pairs(
                result.matches,
                result.df_a_clean,
                result.df_b_clean,
                matching_cols,
                ground_truth,
                50,
                highest=False,
            ),
            uncertain_highest=EntityResolutionExporter._extract_sample_pairs(
                result.uncertain,
                result.df_a_clean,
                result.df_b_clean,
                matching_cols,
                ground_truth,
                25,
                highest=True,
            ),
            uncertain_lowest=EntityResolutionExporter._extract_sample_pairs(
                result.uncertain,
                result.df_a_clean,
                result.df_b_clean,
                matching_cols,
                ground_truth,
                25,
                highest=False,
            ),
            non_matches_highest=EntityResolutionExporter._extract_sample_pairs(
                result.non_matches,
                result.df_a_clean,
                result.df_b_clean,
                matching_cols,
                ground_truth,
                10,
                highest=True,
            ),
            non_matches_lowest=EntityResolutionExporter._extract_sample_pairs(
                result.non_matches,
                result.df_a_clean,
                result.df_b_clean,
                matching_cols,
                ground_truth,
                10,
                highest=False,
            ),
        )

    @staticmethod
    def generate_html_report_content(
        report: EntityResEvalReport,
        boundary_samples: Optional[BoundarySamples] = None,
    ) -> str:
        """Generates full HTML document content for an evaluation report."""
        # 1. Header
        md_lines = [f"# 📊 ER Task Report: {report.table_name}\n"]
        md_lines.append(
            "**Execution Date:** "
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        )

        # 2. Overall Summary
        m = report.matching.metrics
        summary_data = [
            {
                "Scenario": report.table_name,
                "Rows A": report.num_rows_a,
                "Rows B": report.num_rows_b,
                "GT Matches": report.num_ground_truth_matches,
                "Reduction Ratio": f"{report.indexing.reduction_ratio:.2%}",
                "Pairs Recall": f"{report.indexing.pairs_recall:.2%}",
                "F1 Score": f"{m.f1:.2%}",
            }
        ]
        md_lines.append("## Overall Summary\n")
        md_lines.append(
            "\n" + pd.DataFrame(summary_data).to_markdown(index=False) + "\n"
        )

        # 2b. Data Cleaning Report
        if report.cleaning_a and report.cleaning_b:
            md_lines.append("\n## 🧹 Data Cleaning Report\n")
            cleaning_summary = [
                {
                    "Source": "Source A",
                    "Rows Before": report.cleaning_a.rows_before,
                    "Rows After": report.cleaning_a.rows_after,
                    "Duplicates Removed": report.cleaning_a.duplicates_removed,
                    "Whitespace Nullified": (
                        report.cleaning_a.whitespace_cells_nullified
                    ),
                },
                {
                    "Source": "Source B",
                    "Rows Before": report.cleaning_b.rows_before,
                    "Rows After": report.cleaning_b.rows_after,
                    "Duplicates Removed": report.cleaning_b.duplicates_removed,
                    "Whitespace Nullified": (
                        report.cleaning_b.whitespace_cells_nullified
                    ),
                },
            ]
            md_lines.append(
                pd.DataFrame(cleaning_summary).to_markdown(index=False) + "\n"
            )

            def render_examples(examples):
                if not examples:
                    return "_No transformations recorded._"
                ex_data = [
                    {
                        "Column": e.column,
                        "Operation": e.operation,
                        "Before": f"`{e.before}`",
                        "After": (
                            f"`{e.after}`" if e.after is not None else "_NULL_"
                        ),
                    }
                    for e in examples
                ]
                return pd.DataFrame(ex_data).to_markdown(index=False)

            md_lines.append("\n### Example Transformations: Source A\n")
            md_lines.append(render_examples(report.cleaning_a.examples) + "\n")

            md_lines.append("\n### Example Transformations: Source B\n")
            md_lines.append(render_examples(report.cleaning_b.examples) + "\n")

        md_lines.append("\n---\n")

        # 3. Detailed Input Datasets (Mermaid + Profiling)
        if report.meta_a and report.meta_b:
            mermaid_a = EntityResolutionExporter._generate_mermaid_schema(
                "Source_A", report.meta_a
            )
            mermaid_b = EntityResolutionExporter._generate_mermaid_schema(
                "Source_B", report.meta_b
            )

            html_a = render_mermaid_to_html(mermaid_a)
            html_b = render_mermaid_to_html(mermaid_b)

            profiling_table_html = (
                EntityResolutionExporter._render_profiling_table(
                    report.meta_a, report.meta_b
                )
            )

            dataset_section = f"""
<h2 id="detailed-input-datasets">📁 Detailed Input Datasets</h2>
<div class="side-by-side">
    <div class="flex-col">
        <h3>Source A Schema</h3>
{html_a}
    </div>
    <div class="flex-col">
        <h3>Source B Schema</h3>
{html_b}
    </div>
</div>

<h3>Samples: Source A</h3>
<div style="overflow-x: auto; margin-bottom: 20px;">
{EntityResolutionExporter._generate_sample_table(report.meta_a.get('sample_rows', []))}
</div>

<h3>Samples: Source B</h3>
<div style="overflow-x: auto; margin-bottom: 20px;">
{EntityResolutionExporter._generate_sample_table(report.meta_b.get('sample_rows', []))}
</div>

<h3 id="dataset-profiling-comparison">Dataset Profiling Comparison</h3>
{render_markdown_to_html(profiling_table_html)}
<hr />
"""
            md_lines.append(dataset_section)

        md_lines.append("\n---\n")

        # 4. Pipeline Configuration
        if report.er_config:
            md_lines.append("## ⚙️ Pipeline Configuration")
            model_name_display = "manual"
            if report.er_config_metadata and report.er_config_metadata.model_name:
                model_name_display = report.er_config_metadata.model_name
            config_rows = [
                {"Parameter": "**Model**", "Value": f"`{model_name_display}`"},
                {
                    "Parameter": "**Sorting Keys**",
                    "Value": f"`{', '.join(report.er_config.all_sorting_keys)}`",
                },
                {
                    "Parameter": "**Window Size**",
                    "Value": f"`{report.er_config.window_size}`",
                },
            ]
            md_lines.append(
                pd.DataFrame(config_rows).to_markdown(index=False) + "\n"
            )

            md_lines.append(
                f"\n**Reasoning:**\n> {report.er_config.reasoning}\n"
            )

            match_cols_data = [
                {
                    "Column": k,
                    "Algorithm": v.algorithm.value,
                    "Weight": f"{v.weight:.2f}",
                }
                for k, v in report.er_config.matching_columns.items()
            ]
            md_lines.append("**Matching Columns:**\n")
            md_lines.append(
                pd.DataFrame(match_cols_data).to_markdown(index=False) + "\n"
            )

        md_lines.append("\n---\n")

        # 5. Evaluation Results
        md_lines.append("## 📈 Evaluation Results\n")

        idx_matched = (
            report.indexing.num_true_matches
            - report.indexing.missed_true_matches
        )
        idx_recall_str = (
            f"{report.indexing.pairs_recall:.2%} "
            f"({idx_matched}/{report.indexing.num_true_matches})"
        )

        metric_rows = [
            {
                "Stage": "Indexing",
                "Metric": "Pairs Recall (GT Coverage)",
                "Value": idx_recall_str,
            },
            {
                "Stage": "Indexing",
                "Metric": "Reduction Ratio (Efficiency)",
                "Value": f"{report.indexing.reduction_ratio:.2%}",
            },
            {
                "Stage": "Matching",
                "Metric": "Final Precision",
                "Value": f"{m.precision:.2%}",
            },
            {
                "Stage": "Matching",
                "Metric": "Final Recall",
                "Value": f"{m.recall:.2%}",
            },
            {
                "Stage": "Matching",
                "Metric": "Final F1 Score",
                "Value": f"{m.f1:.2%}",
            },
            {"Stage": "Counts", "Metric": "True Positives (TP)", "Value": str(m.tp)},
            {"Stage": "Counts", "Metric": "False Positives (FP)", "Value": str(m.fp)},
            {"Stage": "Counts", "Metric": "False Negatives (FN)", "Value": str(m.fn)},
        ]
        md_lines.append(
            pd.DataFrame(metric_rows).to_markdown(index=False) + "\n"
        )

        full_md = "\n".join(md_lines)
        body_html = render_markdown_to_html(full_md)

        if boundary_samples:
            body_html += EntityResolutionExporter._generate_boundary_samples_html(
                boundary_samples
            )

        return build_html_document(
            f"ER Report: {report.table_name}", body_html
        )

    @staticmethod
    def export_standalone_run(
        result: EntityResolutionResult,
        output_dir: Optional[Path] = None,
    ) -> Path:
        """Exports classified CSV files for a standalone ER execution (without GT evaluation)."""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        if output_dir is None:
            dataset_name = (
                result.table_resource.name
                if result.table_resource
                else "standalone"
            )
            output_dir = (
                config.OUTPUT_BASE_DIR
                / "entity_resolution"
                / dataset_name
                / f"run_{ts}"
            )
        output_dir.mkdir(parents=True, exist_ok=True)

        EntityResolutionExporter._export_csv(
            result.matches,
            result.df_a_clean,
            result.df_b_clean,
            output_dir / "matches.csv",
        )
        EntityResolutionExporter._export_csv(
            result.uncertain,
            result.df_a_clean,
            result.df_b_clean,
            output_dir / "uncertain.csv",
        )
        EntityResolutionExporter._export_csv(
            result.non_matches,
            result.df_a_clean,
            result.df_b_clean,
            output_dir / "non_matches.csv",
        )
        console.print(
            f"   [dim]📁 Classified CSVs exported to: [bold]{output_dir}[/bold][/dim]"
        )
        return output_dir

    @staticmethod
    def export_evaluation_run(
        result: Optional[EntityResolutionResult],
        report: EntityResEvalReport,
        ground_truth: Optional[Set[Tuple]] = None,
        output_dir: Optional[Path] = None,
    ) -> Path:
        """Exports a single evaluation run (HTML report, JSON report, and classified CSVs)."""
        base_dir = config.OUTPUT_BASE_DIR / "entity_resolution"
        dataset_name = report.table_name or "unknown_dataset"

        model_name = "manual"
        if report.er_config_metadata and report.er_config_metadata.model_name:
            model_name = report.er_config_metadata.model_name.replace(
                ":", "_"
            ).replace("/", "_")

        if output_dir is None:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = base_dir / dataset_name / model_name / f"run_{ts}"
        output_dir.mkdir(parents=True, exist_ok=True)

        # 1. Generate boundary samples if result is available
        boundary_samples = None
        if result is not None:
            boundary_samples = (
                EntityResolutionExporter._extract_boundary_samples(
                    result, ground_truth or set()
                )
            )

        # 2. Write HTML report
        html_content = EntityResolutionExporter.generate_html_report_content(
            report, boundary_samples=boundary_samples
        )
        (output_dir / "report.html").write_text(html_content, encoding="utf-8")

        # 3. Write JSON report
        (output_dir / "report.json").write_text(
            report.model_dump_json(indent=2), encoding="utf-8"
        )

        # 4. Export CSV files if result is provided
        if result is not None:
            EntityResolutionExporter._export_csv(
                result.matches,
                result.df_a_clean,
                result.df_b_clean,
                output_dir / "matches.csv",
                ground_truth=ground_truth,
            )
            EntityResolutionExporter._export_csv(
                result.uncertain,
                result.df_a_clean,
                result.df_b_clean,
                output_dir / "uncertain.csv",
                ground_truth=ground_truth,
            )
            EntityResolutionExporter._export_csv(
                result.non_matches,
                result.df_a_clean,
                result.df_b_clean,
                output_dir / "non_matches.csv",
                ground_truth=ground_truth,
            )

        console.print(
            f"   [dim]📄 HTML report saved: [bold]{output_dir / 'report.html'}[/bold][/dim]"
        )
        console.print(
            f"   [dim]📁 Classified CSVs exported to: [bold]{output_dir}[/bold][/dim]"
        )
        return output_dir

    @staticmethod
    def export_benchmark_run(
        benchmark_report: EntityResBenchmarkReport,
        output_dir: Optional[Path] = None,
    ) -> Path:
        """Exports master benchmark report (JSON, HTML summary, summary.csv) and per-dataset outputs."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if output_dir is None:
            output_dir = config.ER_BENCHMARK_OUTPUT_DIR / f"run_{timestamp}"
        output_dir.mkdir(parents=True, exist_ok=True)

        # 1. Master JSON report
        json_data = benchmark_report.model_dump_json(indent=2)
        (output_dir / "summary.json").write_text(json_data, encoding="utf-8")
        (output_dir / "report.json").write_text(json_data, encoding="utf-8")

        # 2. Master summary CSV
        summary_rows = []
        for ds_name, model_results in benchmark_report.dataset_reports.items():
            for model_name, result in model_results.items():
                mean_f1 = result.mean_metrics.get("f1", 0.0)
                std_f1 = result.std_metrics.get("f1", 0.0)
                successful_runs = sum(
                    1 for r in result.runs if isinstance(r, EntityResEvalReport)
                )
                failed_runs = sum(
                    1
                    for r in result.runs
                    if isinstance(r, EntityResFailedRunReport)
                )
                summary_rows.append({
                    "dataset": ds_name,
                    "model": model_name,
                    "mean_f1": mean_f1,
                    "std_f1": std_f1,
                    "successful_runs": successful_runs,
                    "failed_runs": failed_runs,
                    "total_runs": len(result.runs),
                })
        df_summary = pd.DataFrame(summary_rows)
        df_summary.to_csv(output_dir / "summary.csv", index=False)

        # 3. datasets/ folder with per-dataset outputs
        datasets_dir = output_dir / "datasets"
        datasets_dir.mkdir(parents=True, exist_ok=True)
        for ds_name, model_results in benchmark_report.dataset_reports.items():
            for model_name, result in model_results.items():
                safe_model = model_name.replace(":", "_").replace("/", "_")
                model_dir = datasets_dir / ds_name / safe_model
                model_dir.mkdir(parents=True, exist_ok=True)

                # Save per dataset + model JSON report inside nested folder
                (model_dir / "metrics.json").write_text(
                    result.model_dump_json(indent=2), encoding="utf-8"
                )
                (model_dir / "report.json").write_text(
                    result.model_dump_json(indent=2), encoding="utf-8"
                )

                # Save flat JSON file for backwards compatibility
                (datasets_dir / f"{ds_name}_{safe_model}.json").write_text(
                    result.model_dump_json(indent=2), encoding="utf-8"
                )

                # Save per dataset + model Markdown report
                ds_md_lines = [
                    f"# 🔬 ER Diagnostic: {ds_name} | `{model_name}`\n",
                    f"- **Runs**: {len(result.runs)}",
                    f"- **Mean F1**: {result.mean_metrics.get('f1', 0.0):.4f}",
                    f"- **Std F1**: {result.std_metrics.get('f1', 0.0):.4f}\n",
                ]
                (model_dir / "report.md").write_text(
                    "\n".join(ds_md_lines), encoding="utf-8"
                )

        # 4. Master Markdown summary report
        md_lines = [
            "# 📈 Entity Resolution Benchmark Report\n",
            (
                "**Execution Timestamp:** "
                f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            ),
            (
                f"**Source:** `{benchmark_report.config.dataset_domain}` | "
                f"**Runs:** `{benchmark_report.config.runs}` | "
                f"**Models:** `{', '.join(benchmark_report.config.models)}`\n"
            ),
            "## Benchmark Summary\n",
        ]
        if not df_summary.empty:
            md_lines.append(df_summary.to_markdown(index=False) + "\n")
        else:
            md_lines.append("_No datasets evaluated._\n")

        failed_runs_list = []
        for ds_name, model_results in benchmark_report.dataset_reports.items():
            for model_name, result in model_results.items():
                for r in result.runs:
                    if isinstance(r, EntityResFailedRunReport):
                        failed_runs_list.append(r)

        if failed_runs_list:
            md_lines.append("\n## ⚠️ Failed Runs\n")
            fail_data = [
                {
                    "Dataset": fr.dataset_name,
                    "Model": fr.model_name,
                    "Error": fr.error[:100],
                }
                for fr in failed_runs_list
            ]
            md_lines.append(
                pd.DataFrame(fail_data).to_markdown(index=False) + "\n"
            )

        (output_dir / "summary.md").write_text(
            "\n".join(md_lines), encoding="utf-8"
        )

        console.print(
            f"[green]Benchmark report folder created:[/] {output_dir}"
        )
        console.print("  [dim]├─ summary.json[/dim]")
        console.print("  [dim]├─ summary.csv[/dim]")
        console.print("  [dim]├─ summary.md[/dim]")
        console.print("  [dim]└─ datasets/[/dim]")

        return output_dir
