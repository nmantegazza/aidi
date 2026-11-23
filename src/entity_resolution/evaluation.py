from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from shared.config import config
from shared.console import console
from shared.profiling.engine import DataProfiler

from .evaluation_models import (
    EntityResEvalReport,
    IndexingEvaluation,
    MatchingEvaluation,
)
from .exporter import EntityResolutionExporter
from .metrics import (
    compute_pairs_recall,
    compute_precision_recall_f1,
    compute_reduction_ratio,
    pairs_to_set,
)
from .models import EntityResolutionResult, ERPipelineConfiguration, TableResource

MATCH_THRESHOLD = config.MATCH_THRESHOLD
UNCERTAIN_THRESHOLD = config.UNCERTAIN_THRESHOLD


def print_indexing_eval(eval: IndexingEvaluation):
    matched = eval.num_true_matches - eval.missed_true_matches
    console.print(
        f"   [bold green]📦 Indexing:[/] [white]{eval.num_candidates:,} pairs[/white] | "
        f"[dim]Recall: {eval.pairs_recall:.2%} ({matched}/{eval.num_true_matches}) | RR: {eval.reduction_ratio:.2%}[/dim]"
    )


def print_matching_eval(eval: MatchingEvaluation):
    m = eval.metrics
    console.print(
        f"   [bold green]⚖️  Matching:[/] [white]F1 {m.f1:.2%}[/white] | "
        f"[dim]P: {m.precision:.2%} | R: {m.recall:.2%}[/dim]"
    )


def print_final_report(report: EntityResEvalReport):
    console.print(
        f"\n[bold green]✅ Evaluation Finished[/]\n[bold white]   {report.summary_line}[/]\n"
    )


# ---------------------------------------------------------------------------
# Stage-level evaluators
# ---------------------------------------------------------------------------

def evaluate_indexing(
    candidate_pairs: pd.MultiIndex,
    ground_truth: set[tuple],
    df_a: pd.DataFrame,
    df_b: pd.DataFrame,
    sorting_keys: list[str] | None = None,
    window_size: int | None = None,
    indexing_keys: list[str] | None = None,
    indexing_threshold: float | None = None,
) -> IndexingEvaluation:
    """Evaluate the indexing (blocking) stage."""
    max_possible = len(df_a) * len(df_b)
    rr = compute_reduction_ratio(len(candidate_pairs), max_possible)
    pairs_recall, missed = compute_pairs_recall(candidate_pairs, ground_truth)

    return IndexingEvaluation(
        num_candidates=len(candidate_pairs),
        max_possible_pairs=max_possible,
        reduction_ratio=rr,
        pairs_recall=pairs_recall,
        missed_true_matches=missed,
        num_true_matches=len(ground_truth),
        sorting_keys=sorting_keys,
        window_size=window_size,
        indexing_keys=indexing_keys or sorting_keys,
        indexing_threshold=indexing_threshold,
    )


def evaluate_matching(
    matches_df: pd.DataFrame,
    uncertain_df: pd.DataFrame,
    non_matches_df: pd.DataFrame,
    ground_truth: set[tuple],
) -> MatchingEvaluation:
    """Evaluate the deterministic matching (scoring + threshold classification) stage."""
    total_pairs = len(matches_df) + len(uncertain_df) + len(non_matches_df)
    predicted = pairs_to_set(matches_df)
    metrics = compute_precision_recall_f1(predicted, ground_truth, total=total_pairs)

    return MatchingEvaluation(
        metrics=metrics,
        match_threshold=MATCH_THRESHOLD,
        uncertain_threshold=UNCERTAIN_THRESHOLD,
        num_predicted_matches=len(matches_df),
        num_uncertain=len(uncertain_df),
        num_non_matches=len(non_matches_df),
    )


# ---------------------------------------------------------------------------
# Pipeline Result evaluator
# ---------------------------------------------------------------------------

def _profile_to_meta(profile) -> dict | None:
    if profile is None:
        return None
    return {
        "total_row_count": profile.total_rows,
        "column_count": profile.total_columns,
        "column_metadata": {
            col_name: {
                "null_percentage": col_profile.null_percentage,
                "cardinality": col_profile.cardinality,
                "uniqueness_percentage": col_profile.uniqueness_percentage,
            }
            for col_name, col_profile in profile.column_profiles.items()
        },
        "sample_rows": profile.sample_rows,
    }


def evaluate_entity_resolution_run(
    result: EntityResolutionResult,
    ground_truth: set[tuple],
    table_name: str = "eval_table",
    save_html: bool = False,
    output_dir: Path | None = None,
) -> EntityResEvalReport:
    """
    Evaluate the results of a finished ER pipeline execution.
    
    Args:
        result:           The PipelineResult from execute_er_pipeline.
        ground_truth:     Set of (idx_a, idx_b) pairs that are true matches.
        table_name:       Label for console output.
        save_html:        Whether to export HTML report and classified CSVs.
        output_dir:       Optional explicit directory for exports.
        
    Returns:
        EvaluationReport including indexing and matching metrics.
    """
    # 1. Evaluate Indexing
    keys = getattr(result.config, "indexing_keys", None) or getattr(result.config, "sorting_keys", None)
    thresh = getattr(result.config, "indexing_threshold", None)
    ws = getattr(result.config, "window_size", None)
    idx_eval = evaluate_indexing(
        result.candidate_pairs, ground_truth,
        result.df_a_clean, result.df_b_clean,
        sorting_keys=keys,
        window_size=ws,
        indexing_keys=keys,
        indexing_threshold=thresh,
    )
    print_indexing_eval(idx_eval)

    # 2. Evaluate Matching
    if len(result.candidate_pairs) == 0:
        match_eval = MatchingEvaluation(
            metrics=compute_precision_recall_f1(set(), ground_truth),
            match_threshold=MATCH_THRESHOLD,
            uncertain_threshold=UNCERTAIN_THRESHOLD,
            num_predicted_matches=0,
            num_uncertain=0,
            num_non_matches=0,
        )
    else:
        match_eval = evaluate_matching(
            result.matches, 
            result.uncertain, 
            result.non_matches, 
            ground_truth
        )

    print_matching_eval(match_eval)

    # 3. Final Report
    report = EntityResEvalReport(
        table_name=table_name,
        timestamp=datetime.now(timezone.utc),
        num_rows_a=len(result.df_a_clean),
        num_rows_b=len(result.df_b_clean),
        num_ground_truth_matches=len(ground_truth),
        er_config=result.config,
        er_config_metadata=result.er_config_metadata,
        meta_a=_profile_to_meta(result.profile_a),
        meta_b=_profile_to_meta(result.profile_b),
        cleaning_a=result.cleaning_report_a,
        cleaning_b=result.cleaning_report_b,
        indexing=idx_eval,
        matching=match_eval,
    )

    if save_html or output_dir is not None:
        EntityResolutionExporter.export_evaluation_run(
            result, report, ground_truth=ground_truth, output_dir=output_dir
        )
    print_final_report(report)
    return report


# ---------------------------------------------------------------------------
# High-level convenience functions
# ---------------------------------------------------------------------------

async def evaluate_entity_resolution(
    df_a: pd.DataFrame,
    df_b: pd.DataFrame,
    ground_truth: set[tuple],
    table_name: str = "eval_table",
    override_config: ERPipelineConfiguration | None = None,
    model_name: str = "google-cloud:gemini-3.8-flash",
    save_html: bool = False,
    output_dir: Path | None = None,
) -> EntityResEvalReport:
    """
    Runs the full pipe + evaluation on the provided DataFrames.
    """
    from shared.schema_models import TableField, TableSchema

    from .pipeline import run_entity_resolution

    # 1. Dummy logical schema resolution for execute_er_pipeline config identification
    all_cols = list(dict.fromkeys(list(df_a.columns) + list(df_b.columns)))
    fields = [TableField(name=col, type="string") for col in all_cols]
    table_resource = TableResource(
        name=table_name,
        schema=TableSchema(fields=fields)
    )

    # 2. Profiling (Standardized shared layer)
    profile_a = DataProfiler.profile_dataframe(df_a, f"{table_name}_a")
    profile_b = DataProfiler.profile_dataframe(df_b, f"{table_name}_b")

    # 3. Execute ER Pipeline
    result = await run_entity_resolution(
        df_a, df_b,
        profile_a, profile_b,
        table_resource,
        override_config=override_config,
        model_name=model_name,
    )

    # 4. Evaluate Result
    return evaluate_entity_resolution_run(
        result, ground_truth, 
        table_name=table_name, 
        save_html=save_html,
        output_dir=output_dir,
    )
