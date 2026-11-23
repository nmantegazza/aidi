"""CLI script to run entity resolution scoring and classification benchmarks.

Provides multi-iteration execution, failure resilience, automated metric
aggregation with flakiness analysis, and in-place retry capabilities.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import shutil
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
from rich.markup import escape

from entity_resolution.dataset_loader import (
    discover_and_load,
)
from entity_resolution.matching_strategies import (
    DynamicWeightedMatchingStrategy,
    ECMMatchingStrategy,
    KMeansMatchingStrategy,
    WeightedScoreMatchingStrategy,
)
from entity_resolution.matching_strategies.base import BaseMatchingStrategy
from entity_resolution.models import ClassificationMode, TableResource
from shared.benchmarking import (
    BenchmarkReportWriter,
)
from shared.cleaning.engine import clean_data
from shared.config import config
from shared.console import console
from shared.profiling.engine import DataProfiler
from shared.schema_models import TableField, TableSchema

from .common.models import (
    RunStatus,
    TokenUsage,
    compute_mean_std,
)
from .common.reporting import (
    export_csv,
    export_json,
    format_cost_usd,
    format_markdown_table,
    render_rich_table,
)
from .common.resilience import (
    find_failed_iterations,
    resolve_run_directory,
)
from .matching_config_generator import LLMMatchingConfigGenerator
from .matching_evaluation import MatchingMetricsEvaluator
from .matching_models import (
    MatchingDatasetStrategyMetrics,
    MatchingFlakinessAnalysis,
    MatchingIterationMetrics,
    MatchingLLMInteraction,
    MatchingRunSummary,
)

logger = logging.getLogger(__name__)

STRATEGIES: dict[str, type[BaseMatchingStrategy]] = {
    "weighted": WeightedScoreMatchingStrategy,
    "weighted_score": WeightedScoreMatchingStrategy,
    "dynamic_weighted": DynamicWeightedMatchingStrategy,
    "ecm": ECMMatchingStrategy,
    "kmeans": KMeansMatchingStrategy,
}


def _try_read_log_file(log_path: str | Path | None) -> dict[str, Any] | None:
    """Attempts to read and parse an LLM call JSON log file."""
    if not log_path:
        return None
    try:
        p = Path(log_path)
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
    except (json.JSONDecodeError, OSError, TypeError, KeyError) as err:
        logger.debug("Could not read LLM log file %s: %s", log_path, err)
    return None


def _resolve_matching_strategy_class(
    name: str,
) -> type[BaseMatchingStrategy] | None:
    """Resolves matching strategy class from a name, key, or slug.

    Args:
        name: Strategy identifier string.

    Returns:
        Strategy class type or None if unresolved.
    """
    norm = (
        name.lower()
        .replace(" ", "_")
        .replace("-", "_")
        .removesuffix("_strategy")
    )
    if norm in STRATEGIES:
        return STRATEGIES[norm]

    for candidate in [
        WeightedScoreMatchingStrategy,
        DynamicWeightedMatchingStrategy,
        ECMMatchingStrategy,
        KMeansMatchingStrategy,
    ]:
        c_norm = candidate.__name__.lower()
        if norm in (
            c_norm,
            c_norm.removesuffix("strategy"),
            c_norm.removesuffix("matchingstrategy"),
        ):
            return candidate
    return None


def _matching_strategy_canonical_slug(
    cls_: type[BaseMatchingStrategy],
) -> str:
    """Returns canonical slug for matching strategy directory naming."""
    mapping = {
        WeightedScoreMatchingStrategy: "weighted",
        DynamicWeightedMatchingStrategy: "dynamic_weighted",
        ECMMatchingStrategy: "ecm",
        KMeansMatchingStrategy: "kmeans",
    }
    return mapping.get(cls_, cls_.__name__.lower().removesuffix("strategy"))


def _matching_strategy_display_name(
    cls_: type[BaseMatchingStrategy],
) -> str:
    """Returns clean display name for matching strategy."""
    mapping = {
        WeightedScoreMatchingStrategy: "Weighted Score",
        DynamicWeightedMatchingStrategy: "Dynamic Weighted",
        ECMMatchingStrategy: "ECM Matching",
        KMeansMatchingStrategy: "K-Means Matching",
    }
    return mapping.get(cls_, cls_.__name__.removesuffix("Strategy"))


async def _run_single_matching_iteration(
    dataset: Any,
    strategy_cls: type[BaseMatchingStrategy],
    model_name: str,
    iteration_index: int,
    config_generator: LLMMatchingConfigGenerator,
    evaluator: MatchingMetricsEvaluator,
    classification_mode: ClassificationMode = ClassificationMode.TERNARY,
    force_llm: bool = False,
    strat_dir: Path | None = None,
    save_csvs: bool = True,
    max_rows: int | None = None,
) -> tuple[MatchingIterationMetrics, dict[str, Any], set[tuple[Any, Any]]]:
    """Executes a single matching iteration with full exception safety.

    Args:
        dataset: Loaded ER dataset object.
        strategy_cls: Matching strategy class to execute.
        model_name: LLM model name for configuration.
        iteration_index: Current 1-based iteration counter.
        config_generator: Matching configuration generator.
        evaluator: Matching evaluator.
        classification_mode: Binary or ternary classification mode.
        force_llm: Whether to bypass configuration cache.
        strat_dir: Target output directory for iteration artifacts.
        save_csvs: Whether to export bucket prediction CSV files.
        max_rows: Maximum rows to export in bucket CSV files.

    Returns:
        Tuple of (MatchingIterationMetrics, trace dict, predicted matches set).
    """
    df_a = dataset.table_a
    df_b = dataset.table_b
    gt = dataset.ground_truth
    candidate_pairs = dataset.candidates

    try:
        if candidate_pairs is None:
            raise ValueError(
                f"No precomputed candidate pairs found for {dataset.name}"
            )

        clean_df_a, _ = clean_data(df_a)
        clean_df_b, _ = clean_data(df_b)

        valid_a = set(clean_df_a.index)
        valid_b = set(clean_df_b.index)
        mask_keep = (
            candidate_pairs.get_level_values(0).isin(valid_a)
            & candidate_pairs.get_level_values(1).isin(valid_b)
        )
        candidate_pairs = candidate_pairs[mask_keep]

        gt_reconciled = {
            (a, b) for a, b in gt if a in valid_a and b in valid_b
        }

        if candidate_pairs.empty:
            raise ValueError(
                f"No candidate pairs remaining after cleaning for {dataset.name}"
            )

        profile_a = DataProfiler.profile_dataframe(
            clean_df_a, f"{dataset.name}_a"
        )
        profile_b = DataProfiler.profile_dataframe(
            clean_df_b, f"{dataset.name}_b"
        )

        all_cols = list(
            dict.fromkeys(list(clean_df_a.columns) + list(clean_df_b.columns))
        )
        fields = [TableField(name=col, type="string") for col in all_cols]
        table_resource = TableResource(
            name=dataset.name, schema=TableSchema(fields=fields)
        )

        strategy_instance, llm_metrics = (
            await config_generator.get_configuration(
                dataset_name=dataset.name,
                profile_a=profile_a,
                profile_b=profile_b,
                table_resource=table_resource,
                strategy_cls=strategy_cls,
                force_llm=force_llm,
                model_name=model_name,
                df_a=clean_df_a,
                df_b=clean_df_b,
            )
        )

        res = strategy_instance.execute(
            clean_df_a,
            clean_df_b,
            candidate_pairs,
            classification_mode=classification_mode,
            enforce_one_to_one=True,
        )

        uncertain_pairs = None
        if (
            classification_mode == ClassificationMode.TERNARY
            and res.features_df is not None
            and "prediction" in res.features_df.columns
        ):
            uncertain_mask = res.features_df["prediction"] == "uncertain"
            if uncertain_mask.any():
                uncertain_pairs = res.features_df[uncertain_mask].index
            else:
                uncertain_pairs = res.features_df.index[:0]

        metrics = evaluator.evaluate(
            res.classified_pairs,
            gt_reconciled,
            uncertain_pairs=uncertain_pairs,
            total_candidates=len(candidate_pairs),
        )

        cand_count = len(candidate_pairs)
        match_ratio = (
            len(gt_reconciled) / cand_count if cand_count > 0 else 0.0
        )

        # Export detailed bucket CSV reports into iteration subdirectory
        if save_csvs and res.features_df is not None and strat_dir is not None:
            _export_matching_buckets(
                strat_dir=strat_dir,
                clean_df_a=clean_df_a,
                clean_df_b=clean_df_b,
                features_df=res.features_df,
                gt_set=gt_reconciled,
                iteration_index=iteration_index,
                max_rows=max_rows,
            )

        token_usage = TokenUsage()
        if llm_metrics:
            lat = getattr(
                llm_metrics,
                "execution_time_seconds",
                getattr(llm_metrics, "latency_seconds", 0.0),
            )
            token_usage = TokenUsage(
                prompt_tokens=llm_metrics.prompt_tokens,
                completion_tokens=llm_metrics.completion_tokens,
                total_tokens=llm_metrics.total_tokens,
                latency_seconds=lat,
                cost_usd=getattr(llm_metrics, "cost_usd", None),
            )

        llm_interaction: MatchingLLMInteraction | None = None
        if llm_metrics or hasattr(strategy_instance, "config"):
            sys_prompt = (
                (llm_metrics.prompt_template if llm_metrics else None)
                or getattr(strategy_cls, "config_prompt", "")
            )
            u_prompt = (llm_metrics.user_prompt if llm_metrics else None) or ""
            resp = (
                (llm_metrics.raw_response if llm_metrics else None)
                or (
                    strategy_instance.config.model_dump()
                    if hasattr(strategy_instance, "config")
                    else None
                )
            )
            log_path = llm_metrics.log_file_path if llm_metrics else None
            if log_path and (not u_prompt or not sys_prompt or resp is None):
                log_data = _try_read_log_file(log_path)
                if log_data:
                    sys_prompt = sys_prompt or log_data.get(
                        "system_prompt", ""
                    )
                    u_prompt = u_prompt or log_data.get("user_prompt", "")
                    if resp is None:
                        resp = log_data.get("response")

            llm_interaction = MatchingLLMInteraction(
                system_prompt=sys_prompt,
                user_prompt=u_prompt,
                response=resp,
                model_name=getattr(llm_metrics, "model_name", None) or model_name,
                provider=getattr(llm_metrics, "provider", "")
                if llm_metrics
                else "",
                execution_time_seconds=(
                    getattr(llm_metrics, "execution_time_seconds", 0.0)
                    if llm_metrics
                    else 0.0
                ),
                log_file_path=log_path,
            )

        predicted_matches = {
            (str(a), str(b)) for a, b in res.classified_pairs
        }

        metric = MatchingIterationMetrics(
            iteration_index=iteration_index,
            status=RunStatus.SUCCESS,
            precision=metrics["precision"],
            recall=metrics["recall"],
            f1=metrics["f1"],
            tp=metrics["tp"],
            fp=metrics["fp"],
            fn=metrics["fn"],
            tn=metrics.get("tn"),
            candidate_count=cand_count,
            match_ratio=match_ratio,
            potential_recall=metrics.get("potential_recall"),
            potential_f1=metrics.get("potential_f1"),
            unrecoverable_loss=metrics.get("unrecoverable_loss"),
            llm_workload_ratio=metrics.get("llm_workload_ratio"),
            uncertain_purity=metrics.get("uncertain_purity"),
            uncertain_count=metrics.get("uncertain_count", 0),
            execution_time_sec=res.execution_time_sec,
            peak_memory_mb=res.peak_memory_mb,
            peak_cpu_percent=res.peak_cpu_percent,
            token_usage=token_usage,
            llm_interaction=llm_interaction,
        )
        trace = {
            "iteration": iteration_index,
            "status": RunStatus.SUCCESS.value,
            "precision": metric.precision,
            "recall": metric.recall,
            "f1": metric.f1,
            "tp": metric.tp,
            "fp": metric.fp,
            "fn": metric.fn,
            "potential_recall": metric.potential_recall,
            "potential_f1": metric.potential_f1,
            "unrecoverable_loss": metric.unrecoverable_loss,
            "llm_workload_ratio": metric.llm_workload_ratio,
            "uncertain_purity": metric.uncertain_purity,
            "uncertain_count": metric.uncertain_count,
            "execution_time_sec": metric.execution_time_sec,
            "peak_memory_mb": metric.peak_memory_mb,
            "token_usage": token_usage.model_dump(),
            "llm_interaction": (
                llm_interaction.model_dump() if llm_interaction else None
            ),
        }
        if (
            res.features_df is not None
            and "dynamic_thresholds" in res.features_df.attrs
            and res.features_df.attrs["dynamic_thresholds"]
        ):
            trace["dynamic_thresholds"] = (
                res.features_df.attrs["dynamic_thresholds"]
            )
        elif (
            hasattr(strategy_instance, "last_thresholds")
            and strategy_instance.last_thresholds
        ):
            trace["dynamic_thresholds"] = dict(
                strategy_instance.last_thresholds
            )
        return metric, trace, predicted_matches

    except Exception as exc:
        logger.exception(
            "Iteration %d failed for matching dataset '%s' strategy '%s'",
            iteration_index,
            dataset.name,
            strategy_cls.__name__,
        )
        tb_str = traceback.format_exc()
        err_msg = str(exc) or type(exc).__name__
        metric = MatchingIterationMetrics(
            iteration_index=iteration_index,
            status=RunStatus.FAILED,
            error_message=err_msg,
            traceback=tb_str,
        )
        trace = {
            "iteration": iteration_index,
            "status": RunStatus.FAILED.value,
            "error": err_msg,
            "traceback": tb_str,
        }
        return metric, trace, set()


def _export_matching_buckets(
    strat_dir: Path,
    clean_df_a: Any,
    clean_df_b: Any,
    features_df: Any,
    gt_set: set[tuple[Any, Any]],
    iteration_index: int | None = None,
    max_rows: int | None = None,
) -> None:
    """Exports matches, non-matches, and uncertain bucket CSV files."""
    target_dir = (
        strat_dir / f"iteration_{iteration_index}"
        if iteration_index is not None
        else strat_dir
    )
    target_dir.mkdir(parents=True, exist_ok=True)
    details_df = features_df.copy()
    details_df["is_ground_truth_match"] = [
        pair in gt_set for pair in details_df.index
    ]
    left_df = clean_df_a.add_suffix("_a")
    right_df = clean_df_b.add_suffix("_b")

    joined_df = details_df.join(
        left_df, on=details_df.index.names[0]
    ).join(
        right_df, on=details_df.index.names[1]
    )

    left_cols = set(left_df.columns)
    right_cols = set(right_df.columns)
    base_names = {
        col[:-2]
        for col in left_cols.union(right_cols)
        if col.endswith(("_a", "_b"))
    }

    interleaved_source_cols: list[str] = []
    for name in sorted(base_names):
        col_a = f"{name}_a"
        col_b = f"{name}_b"
        if col_a in left_cols:
            interleaved_source_cols.append(col_a)
        if col_b in right_cols:
            interleaved_source_cols.append(col_b)

    feature_cols = list(features_df.columns)
    meta_cols = [
        c
        for c in [
            "prediction",
            "is_ground_truth_match",
            "final_score",
            "probability",
        ]
        if c in joined_df.columns
    ]
    feature_similarity_cols = [
        c for c in feature_cols if c not in meta_cols
    ]

    ordered_cols = (
        meta_cols + interleaved_source_cols + feature_similarity_cols
    )
    joined_df = joined_df[ordered_cols]

    matches_df = joined_df[joined_df["prediction"] == "match"]
    non_matches_df = joined_df[joined_df["prediction"] == "non_match"]
    uncertain_df = joined_df[joined_df["prediction"] == "uncertain"]

    effective_max_rows = (
        max_rows
        if max_rows is not None
        else getattr(config, "MAX_EXPORT_ROWS_PER_CSV", 5000)
    )

    if effective_max_rows is not None and effective_max_rows > 0:
        if len(matches_df) > effective_max_rows:
            matches_df = matches_df.iloc[:effective_max_rows]
        if len(uncertain_df) > effective_max_rows:
            uncertain_df = uncertain_df.iloc[:effective_max_rows]
        if len(non_matches_df) > effective_max_rows:
            # Preserve 100% of False Negatives (actual matches misclassified as non-match)
            fn_df = non_matches_df[non_matches_df["is_ground_truth_match"] == True]
            tn_df = non_matches_df[non_matches_df["is_ground_truth_match"] == False]
            rem_budget = max(0, effective_max_rows - len(fn_df))
            if "final_score" in tn_df.columns:
                sampled_tn = tn_df.sort_values(
                    by="final_score", ascending=False
                ).iloc[:rem_budget]
            elif "probability" in tn_df.columns:
                sampled_tn = tn_df.sort_values(
                    by="probability", ascending=False
                ).iloc[:rem_budget]
            else:
                sampled_tn = tn_df.iloc[:rem_budget]
            non_matches_df = pd.concat([fn_df, sampled_tn]).sort_index()

    matches_df.to_csv(target_dir / "matches.csv")
    non_matches_df.to_csv(target_dir / "non_matches.csv")
    if not uncertain_df.empty:
        uncertain_df.to_csv(target_dir / "uncertain.csv")

    if hasattr(features_df, "attrs") and "dynamic_thresholds" in features_df.attrs:
        (target_dir / "thresholds.json").write_text(
            json.dumps(features_df.attrs["dynamic_thresholds"], indent=2),
            encoding="utf-8",
        )


def _analyze_matching_flakiness(
    predicted_sets: list[set[tuple[Any, Any]]],
) -> MatchingFlakinessAnalysis | None:
    """Computes flakiness analysis across multiple stochastic iterations."""
    if len(predicted_sets) < 2:
        return None

    counts: dict[str, int] = {}
    for p_set in predicted_sets:
        for pair in p_set:
            k = f"{pair[0]}<->{pair[1]}"
            counts[k] = counts.get(k, 0) + 1

    total_iters = len(predicted_sets)
    consistent = sum(1 for c in counts.values() if c == total_iters)
    flaky = sum(1 for c in counts.values() if c < total_iters)
    total_distinct = len(counts)

    flaky_dict = {
        k: c / total_iters for k, c in counts.items() if c < total_iters
    }

    ratio = (
        round(consistent / total_distinct, 4) if total_distinct > 0 else 1.0
    )
    return MatchingFlakinessAnalysis(
        consistent_matches_count=consistent,
        flaky_matches_count=flaky,
        stability_ratio=ratio,
        flaky_pairs=flaky_dict,
    )


def _aggregate_matching_metrics(
    dataset_name: str,
    domain: str,
    strategy_name: str,
    model_name: str,
    iterations: list[MatchingIterationMetrics],
    classification_mode: ClassificationMode = ClassificationMode.TERNARY,
    predicted_sets: list[set[tuple[Any, Any]]] | None = None,
    llm_interaction: MatchingLLMInteraction | None = None,
) -> MatchingDatasetStrategyMetrics:
    """Aggregates multiple matching iterations with mean ± std and flakiness."""
    successful = [
        it for it in iterations if it.status == RunStatus.SUCCESS
    ]
    prec_stats = compute_mean_std([it.precision for it in successful])
    rec_stats = compute_mean_std([it.recall for it in successful])
    f1_stats = compute_mean_std([it.f1 for it in successful])
    time_stats = compute_mean_std([it.execution_time_sec for it in successful])
    mem_stats = compute_mean_std([it.peak_memory_mb for it in successful])

    pot_rec_list = [
        it.potential_recall
        for it in successful
        if it.potential_recall is not None
    ]
    pot_f1_list = [
        it.potential_f1
        for it in successful
        if it.potential_f1 is not None
    ]
    workload_list = [
        it.llm_workload_ratio
        for it in successful
        if it.llm_workload_ratio is not None
    ]
    loss_list = [
        it.unrecoverable_loss
        for it in successful
        if it.unrecoverable_loss is not None
    ]
    purity_list = [
        it.uncertain_purity
        for it in successful
        if it.uncertain_purity is not None
    ]

    pot_rec_stats = compute_mean_std(pot_rec_list) if pot_rec_list else None
    pot_f1_stats = compute_mean_std(pot_f1_list) if pot_f1_list else None
    workload_stats = compute_mean_std(workload_list) if workload_list else None
    loss_stats = compute_mean_std(loss_list) if loss_list else None
    purity_stats = compute_mean_std(purity_list) if purity_list else None

    prompt_tok = sum(it.token_usage.prompt_tokens for it in iterations)
    comp_tok = sum(it.token_usage.completion_tokens for it in iterations)
    total_tok = sum(it.token_usage.total_tokens for it in iterations)
    est_cost = sum(it.token_usage.cost_usd or 0.0 for it in iterations)

    flakiness = (
        _analyze_matching_flakiness(predicted_sets)
        if predicted_sets
        else None
    )

    if llm_interaction is None:
        for it in iterations:
            if it.llm_interaction:
                llm_interaction = it.llm_interaction
                break

    return MatchingDatasetStrategyMetrics(
        dataset_name=dataset_name,
        domain=domain,
        strategy_name=strategy_name,
        model_name=model_name,
        classification_mode=classification_mode,
        iterations=iterations,
        mean_precision=prec_stats.mean,
        std_precision=prec_stats.std,
        mean_recall=rec_stats.mean,
        std_recall=rec_stats.std,
        mean_f1=f1_stats.mean,
        std_f1=f1_stats.std,
        mean_execution_time=time_stats.mean,
        std_execution_time=time_stats.std,
        mean_memory_mb=mem_stats.mean,
        std_memory_mb=mem_stats.std,
        mean_potential_recall=(
            pot_rec_stats.mean if pot_rec_stats else None
        ),
        std_potential_recall=(
            pot_rec_stats.std if pot_rec_stats else None
        ),
        mean_potential_f1=(
            pot_f1_stats.mean if pot_f1_stats else None
        ),
        std_potential_f1=(
            pot_f1_stats.std if pot_f1_stats else None
        ),
        mean_llm_workload_ratio=(
            workload_stats.mean if workload_stats else None
        ),
        mean_unrecoverable_loss=(
            loss_stats.mean if loss_stats else None
        ),
        mean_uncertain_purity=(
            purity_stats.mean if purity_stats else None
        ),
        prompt_tokens=prompt_tok,
        completion_tokens=comp_tok,
        total_tokens=total_tok,
        estimated_cost_usd=round(est_cost, 6),
        flakiness_analysis=flakiness,
        llm_interaction=llm_interaction,
    )


def _build_matching_dataset_markdown_report(
    dm: MatchingDatasetStrategyMetrics,
    traces: list[dict[str, Any]] | None = None,
) -> str:
    """Generates Markdown diagnostic report for one dataset and strategy."""
    lines = [
        f"# Matching Benchmark: {dm.dataset_name} — {dm.strategy_name}\n",
        f"- **Domain**: {dm.domain or 'general'}",
        f"- **Strategy**: {dm.strategy_name}",
        f"- **Model**: {dm.model_name}",
        f"- **Classification Mode**: {dm.classification_mode}",
        (
            f"- **Successful Iterations**: {dm.successful_iterations_count} / "
            f"{len(dm.iterations)}\n"
        ),
        "## Aggregated Metrics\n",
    ]

    stat_headers = ["Metric", "Mean", "Std Dev"]
    stat_rows = [
        ["Precision", f"{dm.mean_precision:.4f}", f"{dm.std_precision:.4f}"],
        ["Recall", f"{dm.mean_recall:.4f}", f"{dm.std_recall:.4f}"],
        ["F1 Score", f"{dm.mean_f1:.4f}", f"{dm.std_f1:.4f}"],
        [
            "Execution Time (s)",
            f"{dm.mean_execution_time:.4f}",
            f"{dm.std_execution_time:.4f}",
        ],
        [
            "Peak Memory (MB)",
            f"{dm.mean_memory_mb:.2f}",
            f"{dm.std_memory_mb:.2f}",
        ],
    ]
    lines.append(format_markdown_table(stat_headers, stat_rows))
    lines.append("\n## Telemetry\n")
    lines.append(
        format_markdown_table(
            ["Metric", "Value"],
            [
                ["Prompt Tokens", f"{dm.prompt_tokens:,}"],
                ["Completion Tokens", f"{dm.completion_tokens:,}"],
                ["Total Tokens", f"{dm.total_tokens:,}"],
                ["Estimated Cost (USD)", f"${dm.estimated_cost_usd:.4f}"],
            ],
        )
    )

    if dm.mean_potential_recall is not None:
        lines.append("\n## Triage Perspective Metrics (Cascaded Tier 1)\n")
        triage_headers = ["Metric", "Mean", "Std Dev"]
        triage_rows = [
            [
                "Potential Recall Ceiling",
                f"{dm.mean_potential_recall:.4f}",
                f"{(dm.std_potential_recall or 0.0):.4f}",
            ],
            [
                "Potential F1 Ceiling",
                f"{(dm.mean_potential_f1 or 0.0):.4f}",
                f"{(dm.std_potential_f1 or 0.0):.4f}",
            ],
            [
                "LLM Workload Ratio",
                f"{((dm.mean_llm_workload_ratio or 0.0) * 100):.1f}%",
                "-",
            ],
            [
                "Unrecoverable Loss",
                f"{(dm.mean_unrecoverable_loss or 0.0):.4f}",
                "-",
            ],
            [
                "Uncertain Purity",
                f"{((dm.mean_uncertain_purity or 0.0) * 100):.1f}%",
                "-",
            ],
        ]
        lines.append(format_markdown_table(triage_headers, triage_rows))

    if dm.flakiness_analysis:
        fa = dm.flakiness_analysis
        lines.append("\n## Deterministic Flakiness Analysis\n")
        flaky_headers = ["Metric", "Value"]
        flaky_rows = [
            ["Stability Ratio", f"{fa.stability_ratio:.2%}"],
            ["Consistent Matches", str(fa.consistent_matches_count)],
            ["Flaky Matches", str(fa.flaky_matches_count)],
        ]
        lines.append(format_markdown_table(flaky_headers, flaky_rows))

    lines.append("\n## Iterations\n")
    iter_headers = [
        "Iter",
        "Status",
        "Precision",
        "Recall",
        "F1",
    ]
    if dm.mean_potential_recall is not None:
        iter_headers.extend(["Pot-R", "Pot-F1", "Workload", "Purity"])
    iter_headers.extend([
        "TP",
        "FP",
        "FN",
        "Time (s)",
        "Mem (MB)",
        "Tokens",
        "Cost (USD)",
        "Error",
    ])
    iter_rows = []
    for it in dm.iterations:
        err_snippet = (it.error_message or "")[:40]
        row = [
            str(it.iteration_index),
            it.status.value,
            f"{it.precision:.4f}" if it.status == RunStatus.SUCCESS else "-",
            f"{it.recall:.4f}" if it.status == RunStatus.SUCCESS else "-",
            f"{it.f1:.4f}" if it.status == RunStatus.SUCCESS else "-",
        ]
        if dm.mean_potential_recall is not None:
            row.extend([
                (
                    f"{it.potential_recall:.4f}"
                    if (
                        it.status == RunStatus.SUCCESS
                        and it.potential_recall is not None
                    )
                    else "-"
                ),
                (
                    f"{it.potential_f1:.4f}"
                    if (
                        it.status == RunStatus.SUCCESS
                        and it.potential_f1 is not None
                    )
                    else "-"
                ),
                (
                    f"{(it.llm_workload_ratio * 100):.1f}%"
                    if (
                        it.status == RunStatus.SUCCESS
                        and it.llm_workload_ratio is not None
                    )
                    else "-"
                ),
                (
                    f"{(it.uncertain_purity * 100):.1f}%"
                    if (
                        it.status == RunStatus.SUCCESS
                        and it.uncertain_purity is not None
                    )
                    else "-"
                ),
            ])
        row.extend([
            str(it.tp) if it.status == RunStatus.SUCCESS else "-",
            str(it.fp) if it.status == RunStatus.SUCCESS else "-",
            str(it.fn) if it.status == RunStatus.SUCCESS else "-",
            (
                f"{it.execution_time_sec:.4f}"
                if it.status == RunStatus.SUCCESS
                else "-"
            ),
            (
                f"{it.peak_memory_mb:.2f}"
                if it.status == RunStatus.SUCCESS
                else "-"
            ),
            str(it.token_usage.total_tokens),
            format_cost_usd(it.token_usage.cost_usd),
            err_snippet,
        ])
        iter_rows.append(row)
    lines.append(format_markdown_table(iter_headers, iter_rows))

    thresh_traces = [
        tr for tr in (traces or []) if "dynamic_thresholds" in tr
    ]
    if thresh_traces:
        lines.append("\n## Dynamic Thresholds\n")
        thresh_headers = [
            "Iter",
            "Mode",
            "Lower Threshold",
            "Upper Threshold",
            "Centroids (Low, Mid, High)",
        ]
        thresh_rows = []
        for tr in thresh_traces:
            dt = tr["dynamic_thresholds"]
            centroids_str = (
                ", ".join(f"{c:.4f}" for c in dt["centroids"])
                if dt.get("centroids")
                else "-"
            )
            thresh_rows.append([
                str(tr.get("iteration", "-")),
                str(dt.get("mode", "-")),
                f"{dt.get('lower_threshold', 0.0):.4f}",
                f"{dt.get('upper_threshold', 0.0):.4f}",
                f"[{centroids_str}]",
            ])
        lines.append(format_markdown_table(thresh_headers, thresh_rows))

    interaction = dm.llm_interaction
    if not interaction and traces:
        for tr in traces:
            if tr.get("llm_interaction"):
                try:
                    interaction = MatchingLLMInteraction.model_validate(
                        tr["llm_interaction"]
                    )
                    break
                except (ValueError, TypeError) as err:
                    logger.debug(
                        "Failed validating llm_interaction trace: %s", err
                    )

    if interaction and (
        interaction.system_prompt
        or interaction.user_prompt
        or interaction.response is not None
    ):
        lines.append("\n## LLM Strategy Configuration & Prompts\n")
        if interaction.model_name:
            lines.append(f"- **Model**: `{interaction.model_name}`")
        if interaction.provider:
            lines.append(f"- **Provider**: `{interaction.provider}`")
        if interaction.execution_time_seconds > 0:
            lines.append(
                f"- **Latency**: `{interaction.execution_time_seconds:.2f}s`"
            )
        if interaction.log_file_path:
            lines.append(f"- **Log File**: `{interaction.log_file_path}`")
        lines.append("")

        lines.append("### LLM Output (Generated Strategy Configuration)\n")
        if interaction.response is not None:
            if isinstance(interaction.response, (dict, list)):
                resp_str = json.dumps(interaction.response, indent=2)
            else:
                resp_str = str(interaction.response)
            lines.append("```json")
            lines.append(resp_str)
            lines.append("```\n")
        else:
            lines.append("_No output recorded._\n")

        lines.append("### LLM Input Prompts\n")
        if interaction.system_prompt:
            lines.append("<details>")
            lines.append(
                "<summary><b>System Prompt</b> (click to expand)</summary>\n"
            )
            lines.append("```text")
            lines.append(interaction.system_prompt.strip())
            lines.append("```")
            lines.append("</details>\n")

        if interaction.user_prompt:
            lines.append("<details>")
            lines.append(
                "<summary><b>User Prompt (Comparative Profile & Exemplars)</b> "
                "(click to expand)</summary>\n"
            )
            lines.append("```markdown")
            lines.append(interaction.user_prompt.strip())
            lines.append("```")
            lines.append("</details>\n")

    lines.append("")
    return "\n".join(lines)


def _build_comparison_summary_markdown(
    datasets: list[str],
    models: list[str],
    strategies: list[type[BaseMatchingStrategy]],
    comparison_map: dict[
        str, dict[str, dict[str, dict[str, MatchingDatasetStrategyMetrics]]]
    ],
) -> str:
    """Generates comparison_summary.md comparing binary and ternary metrics."""
    headers = [
        "Dataset",
        "Model",
        "Strategy",
        "Binary F1",
        "Ternary Direct F1",
        "Potential F1",
        "Potential Recall",
        "LLM Workload (%)",
        "Uncertain Purity (%)",
    ]
    rows = []
    for ds_name in datasets:
        for m_name in models:
            for strat_cls in strategies:
                strat_display = _matching_strategy_display_name(strat_cls)
                strat_slug = _matching_strategy_canonical_slug(strat_cls)
                bin_dm = (
                    comparison_map.get(ds_name, {})
                    .get(m_name, {})
                    .get(strat_slug, {})
                    .get("binary")
                )
                ter_dm = (
                    comparison_map.get(ds_name, {})
                    .get(m_name, {})
                    .get(strat_slug, {})
                    .get("ternary")
                )

                bin_f1 = (
                    f"{bin_dm.mean_f1:.4f} ± {bin_dm.std_f1:.4f}"
                    if bin_dm
                    else "-"
                )
                ter_f1 = (
                    f"{ter_dm.mean_f1:.4f} ± {ter_dm.std_f1:.4f}"
                    if ter_dm
                    else "-"
                )
                pot_f1 = (
                    f"{ter_dm.mean_potential_f1:.4f} ± {ter_dm.std_potential_f1:.4f}"
                    if (ter_dm and ter_dm.mean_potential_f1 is not None)
                    else "-"
                )
                pot_rec = (
                    f"{ter_dm.mean_potential_recall:.4f} ± {ter_dm.std_potential_recall:.4f}"
                    if (ter_dm and ter_dm.mean_potential_recall is not None)
                    else "-"
                )
                workload = (
                    f"{((ter_dm.mean_llm_workload_ratio or 0.0) * 100):.1f}%"
                    if (ter_dm and ter_dm.mean_llm_workload_ratio is not None)
                    else "-"
                )
                purity = (
                    f"{((ter_dm.mean_uncertain_purity or 0.0) * 100):.1f}%"
                    if (ter_dm and ter_dm.mean_uncertain_purity is not None)
                    else "-"
                )

                rows.append([
                    ds_name,
                    m_name,
                    strat_display,
                    bin_f1,
                    ter_f1,
                    pot_f1,
                    pot_rec,
                    workload,
                    purity,
                ])

    lines = [
        "# Dual-Perspective ER Matching Benchmarking Comparison Summary\n",
        (
            "Comparison of Standalone Binary Classification ($k=2$) vs. "
            "Cascaded Ternary Triage ($k=3$ with potential performance "
            "ceilings and LLM workload).\n"
        ),
        format_markdown_table(headers, rows),
        "",
    ]
    return "\n".join(lines)


def _build_matching_summary_markdown(summary: MatchingRunSummary) -> str:
    """Constructs human-readable Markdown summary of entire matching run."""
    lines = [
        "# ER Matching Benchmark Summary\n",
        f"- **Run ID**: `{summary.run_id}`",
        f"- **Timestamp**: `{summary.timestamp.isoformat()}`",
        f"- **Datasets**: {', '.join(summary.datasets)}",
        f"- **Strategies**: {', '.join(summary.strategies)}",
        f"- **Models**: {', '.join(summary.models)}",
        f"- **Iterations**: {summary.iterations}",
        (
            f"- **Failed Iterations**: {summary.failed_iterations_count} / "
            f"{summary.total_iterations_count}\n"
        ),
        "## Performance Comparison\n",
    ]

    has_potential_f1 = any(
        dm.mean_potential_f1 is not None
        for d in summary.matrix.values()
        for m in d.values()
        for dm in m.values()
    )

    headers = [
        "Dataset",
        "Model",
        "Strategy",
        "Mode",
        "F1 (Mean ± Std)",
    ]
    if has_potential_f1:
        headers.append("Potential F1")
    headers.extend([
        "Precision",
        "Recall",
        "Time (s)",
        "Peak Mem (MB)",
        "Status",
    ])
    rows = []
    for ds_name in summary.datasets:
        for m_name in summary.models:
            model_dict = summary.matrix.get(ds_name, {}).get(m_name, {})
            for dm in model_dict.values():
                succ = dm.successful_iterations_count
                tot = len(dm.iterations)
                stat = f"{succ}/{tot} OK" if succ == tot else f"{succ}/{tot} FAILED"
                mode_str = (
                    dm.classification_mode.value
                    if hasattr(dm.classification_mode, "value")
                    else str(dm.classification_mode)
                )
                row = [
                    ds_name,
                    dm.model_name,
                    dm.strategy_name,
                    mode_str,
                    f"{dm.mean_f1:.4f} ± {dm.std_f1:.4f}",
                ]
                if has_potential_f1:
                    pot_f1_str = (
                        f"{dm.mean_potential_f1:.4f} ± {(dm.std_potential_f1 or 0.0):.4f}"
                        if dm.mean_potential_f1 is not None
                        else "-"
                    )
                    row.append(pot_f1_str)
                row.extend([
                    f"{dm.mean_precision:.4f}",
                    f"{dm.mean_recall:.4f}",
                    f"{dm.mean_execution_time:.4f}",
                    f"{dm.mean_memory_mb:.2f}",
                    stat,
                ])
                rows.append(row)
    lines.append(format_markdown_table(headers, rows))

    if summary.failed_iterations_count > 0:
        lines.append("\n## Failure Diagnostic Log\n")
        fail_headers = ["Dataset", "Model", "Strategy", "Iter", "Error Snippet"]
        fail_rows = []
        for ds_name in summary.datasets:
            for m_name in summary.models:
                model_dict = summary.matrix.get(ds_name, {}).get(m_name, {})
                for dm in model_dict.values():
                    for it in dm.iterations:
                        if it.status != RunStatus.SUCCESS:
                            fail_rows.append([
                                ds_name,
                                dm.model_name,
                                dm.strategy_name,
                                str(it.iteration_index),
                                (it.error_message or "Unknown failure")[:60],
                            ])
        lines.append(format_markdown_table(fail_headers, fail_rows))

    lines.append("")
    return "\n".join(lines)


def _build_matching_summary_csv(
    summary: MatchingRunSummary,
) -> list[dict[str, Any]]:
    """Builds tabular rows for matching summary CSV export."""
    rows: list[dict[str, Any]] = []
    for ds_name in summary.datasets:
        for m_name in summary.models:
            model_dict = summary.matrix.get(ds_name, {}).get(m_name, {})
            for dm in model_dict.values():
                stab_ratio = (
                    dm.flakiness_analysis.stability_ratio
                    if dm.flakiness_analysis
                    else 1.0
                )
                mode_str = (
                    dm.classification_mode.value
                    if hasattr(dm.classification_mode, "value")
                    else str(dm.classification_mode)
                )
                rows.append({
                    "dataset": ds_name,
                    "domain": dm.domain,
                    "model": dm.model_name,
                    "strategy": dm.strategy_name,
                    "classification_mode": mode_str,
                    "mean_precision": dm.mean_precision,
                    "std_precision": dm.std_precision,
                    "mean_recall": dm.mean_recall,
                    "std_recall": dm.std_recall,
                    "mean_f1": dm.mean_f1,
                    "std_f1": dm.std_f1,
                    "mean_potential_f1": dm.mean_potential_f1,
                    "std_potential_f1": dm.std_potential_f1,
                    "mean_potential_recall": dm.mean_potential_recall,
                    "std_potential_recall": dm.std_potential_recall,
                    "mean_llm_workload_ratio": dm.mean_llm_workload_ratio,
                    "mean_uncertain_purity": dm.mean_uncertain_purity,
                    "mean_unrecoverable_loss": dm.mean_unrecoverable_loss,
                    "mean_execution_time": dm.mean_execution_time,
                    "std_execution_time": dm.std_execution_time,
                    "mean_memory_mb": dm.mean_memory_mb,
                    "std_memory_mb": dm.std_memory_mb,
                    "stability_ratio": stab_ratio,
                    "prompt_tokens": dm.prompt_tokens,
                    "completion_tokens": dm.completion_tokens,
                    "total_tokens": dm.total_tokens,
                    "estimated_cost_usd": dm.estimated_cost_usd,
                    "successful_iterations": dm.successful_iterations_count,
                    "failed_iterations": dm.failed_iterations_count,
                    "total_iterations": len(dm.iterations),
                })
    return rows


def _save_matching_dataset_artifacts(
    strat_dir: Path,
    ds_metrics: MatchingDatasetStrategyMetrics,
    traces: list[dict[str, Any]],
    append_traces: bool = False,
) -> None:
    """Exports dataset strategy metrics.json, report.md, traces.json, and traces.jsonl."""
    strat_dir.mkdir(parents=True, exist_ok=True)
    export_json(ds_metrics, strat_dir / "metrics.json")
    export_json(traces, strat_dir / "traces.json")
    report_md = _build_matching_dataset_markdown_report(
        ds_metrics, traces=traces
    )
    (strat_dir / "report.md").write_text(report_md, encoding="utf-8")

    if ds_metrics.llm_interaction:
        log_path = ds_metrics.llm_interaction.log_file_path
        if log_path and Path(log_path).exists():
            shutil.copy2(log_path, strat_dir / "llm_call.json")
        else:
            (strat_dir / "llm_call.json").write_text(
                json.dumps(ds_metrics.llm_interaction.model_dump(), indent=2),
                encoding="utf-8",
            )

    traces_file = strat_dir / "traces.jsonl"
    mode = "a" if append_traces and traces_file.exists() else "w"
    with open(traces_file, mode, encoding="utf-8") as f:
        f.writelines(json.dumps(tr, default=str) + "\n" for tr in traces)


def _merge_matching_iteration_result(
    existing_dm: MatchingDatasetStrategyMetrics,
    new_metric: MatchingIterationMetrics,
) -> MatchingDatasetStrategyMetrics:
    """Merges a newly executed iteration into existing dataset metrics."""
    updated_iterations: list[MatchingIterationMetrics] = []
    replaced = False
    for it in existing_dm.iterations:
        if it.iteration_index == new_metric.iteration_index:
            updated_iterations.append(new_metric)
            replaced = True
        else:
            updated_iterations.append(it)
    if not replaced:
        updated_iterations.append(new_metric)
    updated_iterations.sort(key=lambda it: it.iteration_index)

    return _aggregate_matching_metrics(
        dataset_name=existing_dm.dataset_name,
        domain=existing_dm.domain,
        strategy_name=existing_dm.strategy_name,
        model_name=existing_dm.model_name,
        iterations=updated_iterations,
        classification_mode=existing_dm.classification_mode,
        llm_interaction=(
            existing_dm.llm_interaction or new_metric.llm_interaction
        ),
    )


async def run_matching_benchmark(
    data_dir: str | None = None,
    domain: str = "all",
    strategy: str = "all",
    strategies: list[str] | None = None,
    classification_mode: str = "ternary",
    force_llm: bool = False,
    models: list[str] | str | None = None,
    model_name: str | None = None,
    iterations: int = 1,
    runs: int | None = None,
    output_dir: Path | str | None = None,
    output: str | None = None,
    max_csv_rows: int | None = None,
    skip_bucket_csvs: bool = False,
) -> MatchingRunSummary:
    """Orchestrates matching benchmarks across discovered datasets.

    Args:
        data_dir: Path to directory containing datasets.
        domain: Domain filter ('all', 'e-commerce', 'citations', etc.).
        strategy: Single strategy or 'all'.
        strategies: List of strategies to benchmark.
        classification_mode: Classification mode: 'binary', 'ternary', or
          'both'.
        force_llm: Force LLM configuration generation, bypassing cache.
        models: LLM model name(s) to benchmark.
        model_name: Backwards-compatible single model parameter.
        iterations: Number of iterations per configuration.
        runs: Backwards-compatible alias for iterations.
        output_dir: Custom directory path to write benchmark run artifacts.
        output: Legacy optional custom path.
        max_csv_rows: Maximum rows to export in bucket CSV files.
        skip_bucket_csvs: Whether to skip exporting bucket CSV files.

    Returns:
        MatchingRunSummary containing all execution results.
    """
    effective_data_dir = data_dir or str(config.ER_DATASETS_DIR)
    num_iterations = runs or iterations or 1

    norm_mode = classification_mode.lower().strip()
    if norm_mode == ClassificationMode.BOTH.value:
        active_modes = [ClassificationMode.BINARY, ClassificationMode.TERNARY]
    elif norm_mode in (
        ClassificationMode.BINARY.value,
        ClassificationMode.TERNARY.value,
    ):
        active_modes = [ClassificationMode(norm_mode)]
    else:
        raise ValueError(
            f"Invalid classification_mode '{classification_mode}'. "
            "Expected 'binary', 'ternary', or 'both'."
        )

    model_list: list[str] = []
    if isinstance(models, list) and models:
        model_list = models
    elif isinstance(models, str) and models:
        model_list = [models]
    elif model_name:
        model_list = [model_name]
    else:
        model_list = [config.DEFAULT_GOOGLE_MODEL]

    console.print(
        f"[dim]Discovering datasets for matching benchmark "
        f"(data_dir='{effective_data_dir}', domain='{domain}')...[/]"
    )
    discovered = discover_and_load(
        data_dir=effective_data_dir,
        domain=domain,
    )

    if not discovered:
        console.print("[yellow]⚠ No datasets discovered.[/]")
        return MatchingRunSummary(
            run_id="empty",
            strategies=[],
            datasets=[],
            models=model_list,
            iterations=num_iterations,
        )

    # Determine strategies
    strat_inputs: list[str] = []
    if strategies:
        strat_inputs = strategies
    elif strategy:
        strat_inputs = [strategy]
    else:
        strat_inputs = ["all"]

    if not strat_inputs or any(s.lower() == "all" for s in strat_inputs):
        target_strategy_classes = [
            WeightedScoreMatchingStrategy,
            DynamicWeightedMatchingStrategy,
            KMeansMatchingStrategy,
        ]
    else:
        target_strategy_classes = []
        for s_in in strat_inputs:
            cls_ = _resolve_matching_strategy_class(s_in)
            if cls_ and cls_ not in target_strategy_classes:
                target_strategy_classes.append(cls_)
            elif not cls_:
                console.print(
                    f"[yellow]⚠ Unknown matching strategy '{s_in}'.[/]"
                )

    if not target_strategy_classes:
        console.print("[yellow]⚠ No valid matching strategies selected.[/]")
        return MatchingRunSummary(
            run_id="empty",
            strategies=[],
            datasets=[],
            models=model_list,
            iterations=num_iterations,
        )

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    run_id = f"run_{timestamp}"
    base_out = (
        Path(output_dir)
        if output_dir
        else config.ER_MATCHING_BENCHMARK_OUTPUT_DIR
    )
    if output:
        out_p = Path(output)
        run_dir = out_p if out_p.is_absolute() else base_out / out_p
    else:
        run_dir = base_out / run_id

    run_dir.mkdir(parents=True, exist_ok=True)
    console.print(f"[bold cyan]🚀 Benchmark run directory:[/] {run_dir}")

    evaluator = MatchingMetricsEvaluator()
    config_generator = LLMMatchingConfigGenerator()

    matrix: dict[
        str, dict[str, dict[str, MatchingDatasetStrategyMetrics]]
    ] = {}
    comparison_map: dict[
        str, dict[str, dict[str, dict[str, MatchingDatasetStrategyMetrics]]]
    ] = {}
    strategy_slugs = [
        _matching_strategy_canonical_slug(cls_)
        for cls_ in target_strategy_classes
    ]
    dataset_names = [d.name for d in discovered]
    total_iters = 0
    failed_iters = 0

    for dataset in discovered:
        ds_name = dataset.name
        matrix[ds_name] = {}
        comparison_map[ds_name] = {}

        for m_name in model_list:
            model_slug = m_name.replace(":", "_").replace("/", "_")
            matrix[ds_name][m_name] = {}
            comparison_map[ds_name][m_name] = {}

            for strat_cls in target_strategy_classes:
                strat_display = _matching_strategy_display_name(strat_cls)
                strat_slug = _matching_strategy_canonical_slug(strat_cls)
                comparison_map[ds_name][m_name][strat_slug] = {}

                for mode_idx, mode in enumerate(active_modes):
                    strat_dir = (
                        run_dir
                        / "datasets"
                        / ds_name
                        / model_slug
                        / mode.value
                        / strat_slug
                    )
                    iterations_list: list[MatchingIterationMetrics] = []
                    traces_list: list[dict[str, Any]] = []
                    match_sets: list[set[tuple[Any, Any]]] = []

                    console.print(
                        f"\n[bold blue]▶ [{ds_name}] Strategy '{strat_display}' "
                        f"| Model '{m_name}' | Mode '{mode.value}' "
                        f"({num_iterations} iter)[/]"
                    )

                    for iter_idx in range(1, num_iterations + 1):
                        console.print(
                            f"  [dim]Executing iteration {iter_idx}/"
                            f"{num_iterations}...[/]"
                        )
                        # Zero token overhead across modes within the same iteration:
                        # force LLM on mode_idx == 0 for every iteration if force_llm is set
                        effective_force_llm = (
                            force_llm if mode_idx == 0 else False
                        )
                        it_metric, trace_dict, pred_matches = (
                            await _run_single_matching_iteration(
                                dataset=dataset,
                                strategy_cls=strat_cls,
                                model_name=m_name,
                                iteration_index=iter_idx,
                                config_generator=config_generator,
                                evaluator=evaluator,
                                classification_mode=mode,
                                force_llm=effective_force_llm,
                                strat_dir=strat_dir,
                                save_csvs=not skip_bucket_csvs,
                                max_rows=max_csv_rows,
                            )
                        )
                        iterations_list.append(it_metric)
                        traces_list.append(trace_dict)
                        total_iters += 1
                        if it_metric.status != RunStatus.SUCCESS:
                            failed_iters += 1
                            console.print(
                                f"    [bold red]✖ Iteration {iter_idx} failed: "
                                f"{it_metric.error_message}[/]"
                            )
                        else:
                            match_sets.append(pred_matches)
                            console.print(
                                f"    [green]✔ Iteration {iter_idx} OK: "
                                f"P={it_metric.precision:.4f}, "
                                f"R={it_metric.recall:.4f}, "
                                f"F1={it_metric.f1:.4f}, "
                                f"Time={it_metric.execution_time_sec:.2f}s[/]"
                            )

                    ds_metrics = _aggregate_matching_metrics(
                        dataset_name=ds_name,
                        domain=dataset.domain
                        if hasattr(dataset, "domain")
                        else "general",
                        strategy_name=strat_display,
                        model_name=m_name,
                        iterations=iterations_list,
                        classification_mode=mode,
                        predicted_sets=match_sets
                        if len(match_sets) > 1
                        else None,
                    )
                    comparison_map[ds_name][m_name][strat_slug][mode.value] = ds_metrics

                    if len(active_modes) > 1:
                        matrix[ds_name][m_name][f"{strat_slug}_{mode.value}"] = ds_metrics
                    else:
                        matrix[ds_name][m_name][strat_slug] = ds_metrics

                    _save_matching_dataset_artifacts(
                        strat_dir, ds_metrics, traces_list
                    )

                    # Progressive summary checkpointing
                    summary_ckpt = MatchingRunSummary(
                        run_id=run_id,
                        strategies=strategy_slugs,
                        datasets=dataset_names,
                        models=model_list,
                        iterations=num_iterations,
                        matrix=matrix,
                        failed_iterations_count=failed_iters,
                        total_iterations_count=total_iters,
                    )
                    summary_md_ckpt = _build_matching_summary_markdown(summary_ckpt)
                    summary_csv_ckpt = _build_matching_summary_csv(summary_ckpt)
                    BenchmarkReportWriter.checkpoint_summaries(
                        run_dir=run_dir,
                        summary_data=summary_ckpt,
                        summary_rows=summary_csv_ckpt,
                        markdown_content=summary_md_ckpt,
                    )

    summary = MatchingRunSummary(
        run_id=run_id,
        strategies=strategy_slugs,
        datasets=dataset_names,
        models=model_list,
        iterations=num_iterations,
        matrix=matrix,
        failed_iterations_count=failed_iters,
        total_iterations_count=total_iters,
    )

    summary_md = _build_matching_summary_markdown(summary)
    summary_csv = _build_matching_summary_csv(summary)
    BenchmarkReportWriter.checkpoint_summaries(
        run_dir=run_dir,
        summary_data=summary,
        summary_rows=summary_csv,
        markdown_content=summary_md,
    )

    if norm_mode == ClassificationMode.BOTH.value:
        comparison_md = _build_comparison_summary_markdown(
            datasets=dataset_names,
            models=model_list,
            strategies=target_strategy_classes,
            comparison_map=comparison_map,
        )
        (run_dir / "comparison_summary.md").write_text(
            comparison_md, encoding="utf-8"
        )

        comp_cols = [
            "Dataset",
            "Model",
            "Strategy",
            "Binary F1",
            "Ternary Direct F1",
            "Potential F1",
            "Potential Recall",
            "LLM Workload (%)",
            "Uncertain Purity (%)",
        ]
        comp_rows = []
        for d_n in dataset_names:
            for m_n in model_list:
                for s_cls in target_strategy_classes:
                    s_disp = _matching_strategy_display_name(s_cls)
                    s_s = _matching_strategy_canonical_slug(s_cls)
                    b_dm = comparison_map.get(d_n, {}).get(m_n, {}).get(s_s, {}).get("binary")
                    t_dm = comparison_map.get(d_n, {}).get(m_n, {}).get(s_s, {}).get("ternary")
                    b_f1 = (
                        f"{b_dm.mean_f1:.4f} ± {b_dm.std_f1:.4f}"
                        if b_dm
                        else "-"
                    )
                    t_f1 = (
                        f"{t_dm.mean_f1:.4f} ± {t_dm.std_f1:.4f}"
                        if t_dm
                        else "-"
                    )
                    p_f1 = (
                        f"{t_dm.mean_potential_f1:.4f} ± {t_dm.std_potential_f1:.4f}"
                        if (t_dm and t_dm.mean_potential_f1 is not None)
                        else "-"
                    )
                    p_rec = (
                        f"{t_dm.mean_potential_recall:.4f} ± {t_dm.std_potential_recall:.4f}"
                        if (t_dm and t_dm.mean_potential_recall is not None)
                        else "-"
                    )
                    w_load = (
                        f"{((t_dm.mean_llm_workload_ratio or 0.0) * 100):.1f}%"
                        if (t_dm and t_dm.mean_llm_workload_ratio is not None)
                        else "-"
                    )
                    u_pur = (
                        f"{((t_dm.mean_uncertain_purity or 0.0) * 100):.1f}%"
                        if (t_dm and t_dm.mean_uncertain_purity is not None)
                        else "-"
                    )
                    comp_rows.append([
                        d_n,
                        m_n,
                        escape(s_disp),
                        b_f1,
                        t_f1,
                        p_f1,
                        p_rec,
                        w_load,
                        u_pur,
                    ])
        render_rich_table(
            "Dual-Perspective ER Matching Comparison",
            comp_cols,
            comp_rows,
        )

    has_potential_f1 = any(
        dm.mean_potential_f1 is not None
        for d in summary.matrix.values()
        for m in d.values()
        for dm in m.values()
    )

    table_cols = [
        "Dataset",
        "Model",
        "Strategy",
        "Mode",
        "F1 (Mean ± Std)",
    ]
    if has_potential_f1:
        table_cols.append("Potential F1")
    table_cols.extend([
        "Precision",
        "Recall",
        "Time (s)",
        "Peak Mem (MB)",
        "Status",
    ])

    table_rows = []
    for ds_name in summary.datasets:
        for m_name in summary.models:
            model_dict = summary.matrix.get(ds_name, {}).get(m_name, {})
            for dm in model_dict.values():
                succ = dm.successful_iterations_count
                tot = len(dm.iterations)
                stat_str = (
                    f"[green]{succ}/{tot} OK[/]"
                    if succ == tot
                    else f"[red]{succ}/{tot} OK[/]"
                )
                mode_str = (
                    dm.classification_mode.value
                    if hasattr(dm.classification_mode, "value")
                    else str(dm.classification_mode)
                )
                row = [
                    ds_name,
                    dm.model_name,
                    escape(dm.strategy_name),
                    mode_str,
                    f"{dm.mean_f1:.4f} ± {dm.std_f1:.4f}",
                ]
                if has_potential_f1:
                    pot_f1_str = (
                        f"{dm.mean_potential_f1:.4f} ± {(dm.std_potential_f1 or 0.0):.4f}"
                        if dm.mean_potential_f1 is not None
                        else "-"
                    )
                    row.append(pot_f1_str)
                row.extend([
                    f"{dm.mean_precision:.4f}",
                    f"{dm.mean_recall:.4f}",
                    f"{dm.mean_execution_time:.4f}",
                    f"{dm.mean_memory_mb:.2f}",
                    stat_str,
                ])
                table_rows.append(row)
    render_rich_table("Matching Benchmark Summary", table_cols, table_rows)

    if summary.failed_iterations_count > 0:
        fail_cols = ["Dataset", "Model", "Strategy", "Iter", "Error Snippet"]
        fail_rows = []
        for ds_name in summary.datasets:
            for m_name in summary.models:
                model_dict = summary.matrix.get(ds_name, {}).get(m_name, {})
                for dm in model_dict.values():
                    for it in dm.iterations:
                        if it.status != RunStatus.SUCCESS:
                            fail_rows.append([
                                ds_name,
                                dm.model_name,
                                escape(dm.strategy_name),
                                str(it.iteration_index),
                                (it.error_message or "Failed")[:50],
                            ])
        render_rich_table(
            "Failed Matching Iterations",
            fail_cols,
            fail_rows,
            header_style="bold red",
        )
        console.print(
            f"[yellow]💡 To retry failed runs: "
            f"[bold]uv run er-matching-benchmark --retry {run_id}[/bold][/yellow]\n"
        )

    console.print(
        f"[green]✔ Matching benchmark completed! Run directory:[/] {run_dir}\n"
    )
    return summary


async def retry_matching_benchmark_run(
    run_target: str | Path,
    dataset_filter: list[str] | None = None,
    strategy_filter: list[str] | None = None,
    output_dir: Path | None = None,
    classification_mode: str | ClassificationMode | None = None,
    force_llm: bool = False,
    max_csv_rows: int | None = None,
    skip_bucket_csvs: bool = False,
) -> MatchingRunSummary:
    """Retries only failed iterations for an existing matching benchmark run.

    Args:
        run_target: Run folder, run ID string, or 'latest'.
        dataset_filter: Optional subset of datasets to retry.
        strategy_filter: Optional subset of strategies to retry.
        output_dir: Base directory if relative run ID is used.
        classification_mode: Optional explicit classification mode override.
        force_llm: Whether to force configuration regeneration on retry.
        max_csv_rows: Maximum rows to export in bucket CSV files.
        skip_bucket_csvs: Whether to skip exporting bucket CSV files.

    Returns:
        Updated MatchingRunSummary.
    """
    base_out = output_dir or config.ER_MATCHING_BENCHMARK_OUTPUT_DIR
    run_dir = resolve_run_directory(
        run_target,
        base_out,
        fallback_dirs=[config.LEGACY_ER_MATCHING_BENCHMARK_OUTPUT_DIR],
    )
    console.print(
        f"[cyan]Resolving matching run directory for retry:[/] {run_dir}"
    )

    failed_items = find_failed_iterations(
        run_dir,
        dataset_filter=dataset_filter,
        strategy_filter=strategy_filter,
    )

    if not failed_items:
        console.print(
            "[green]No failed iterations found to retry in this run directory![/]"
        )
        summary_path = run_dir / "summary.json"
        if summary_path.exists():
            return MatchingRunSummary.model_validate_json(
                summary_path.read_text(encoding="utf-8")
            )
        return MatchingRunSummary(
            run_id=run_dir.name,
            strategies=[],
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

    evaluator = MatchingMetricsEvaluator()
    config_generator = LLMMatchingConfigGenerator()

    for ds_name, strat_slug, iteration_index, strat_dir in failed_items:
        dataset = dataset_map.get(ds_name)
        if not dataset:
            console.print(
                f"[red]Could not load dataset '{ds_name}' to retry "
                f"iteration {iteration_index}.[/]"
            )
            continue

        strat_cls = _resolve_matching_strategy_class(strat_slug)
        if not strat_cls:
            console.print(
                f"[red]Could not resolve matching strategy for slug "
                f"'{strat_slug}'.[/]"
            )
            continue

        metrics_file = strat_dir / "metrics.json"
        model_name = config.DEFAULT_GOOGLE_MODEL
        target_mode = ClassificationMode.TERNARY
        if classification_mode is not None:
            target_mode = (
                classification_mode
                if isinstance(classification_mode, ClassificationMode)
                else ClassificationMode(classification_mode)
            )
        elif metrics_file.exists():
            try:
                raw_json = json.loads(metrics_file.read_text(encoding="utf-8"))
                model_name = raw_json.get("model_name", model_name)
                if "classification_mode" in raw_json:
                    target_mode = ClassificationMode(
                        raw_json["classification_mode"]
                    )
            except (json.JSONDecodeError, OSError, ValueError):
                pass

        console.print(
            f"[cyan]▶ Retrying {ds_name} | {strat_slug} | "
            f"Mode {target_mode.value} | Iteration {iteration_index}...[/]"
        )
        new_metric, trace_dict, _ = await _run_single_matching_iteration(
            dataset=dataset,
            strategy_cls=strat_cls,
            model_name=model_name,
            iteration_index=iteration_index,
            config_generator=config_generator,
            evaluator=evaluator,
            classification_mode=target_mode,
            force_llm=force_llm,
            strat_dir=strat_dir,
            save_csvs=not skip_bucket_csvs,
            max_rows=max_csv_rows,
        )

        if metrics_file.exists():
            existing_dm = MatchingDatasetStrategyMetrics.model_validate_json(
                metrics_file.read_text(encoding="utf-8")
            )
            updated_dm = _merge_matching_iteration_result(
                existing_dm, new_metric
            )
            _save_matching_dataset_artifacts(
                strat_dir=strat_dir,
                ds_metrics=updated_dm,
                traces=[trace_dict],
                append_traces=True,
            )

    # Rebuild top-level summaries supporting 3-level matrix
    datasets_dir = run_dir / "datasets"
    matrix: dict[
        str, dict[str, dict[str, MatchingDatasetStrategyMetrics]]
    ] = {}
    total_iters = 0
    failed_iters = 0
    all_strategies: set[str] = set()
    all_datasets: set[str] = set()
    all_models: set[str] = set()

    if datasets_dir.exists():
        for metrics_file in sorted(datasets_dir.glob("**/metrics.json")):
            s_dir = metrics_file.parent
            rel_parts = s_dir.relative_to(datasets_dir).parts
            if len(rel_parts) < 2:
                continue
            d_name = rel_parts[0]
            s_slug = rel_parts[-1]
            try:
                dm = MatchingDatasetStrategyMetrics.model_validate_json(
                    metrics_file.read_text(encoding="utf-8")
                )
            except (json.JSONDecodeError, OSError, ValueError) as err:
                logger.warning(
                    "Failed to parse metrics file %s: %s", metrics_file, err
                )
                continue

            m_name = dm.model_name
            if d_name not in matrix:
                matrix[d_name] = {}
            if m_name not in matrix[d_name]:
                matrix[d_name][m_name] = {}

            strat_key = s_slug
            if len(rel_parts) >= 4:
                mode_val = rel_parts[-2]
                strat_key = f"{s_slug}_{mode_val}"
            matrix[d_name][m_name][strat_key] = dm

            all_datasets.add(d_name)
            all_strategies.add(s_slug)
            all_models.add(m_name)
            total_iters += len(dm.iterations)
            failed_iters += dm.failed_iterations_count

    summary = MatchingRunSummary(
        run_id=run_dir.name,
        timestamp=datetime.now(timezone.utc),
        strategies=sorted(all_strategies),
        datasets=sorted(all_datasets),
        models=sorted(all_models),
        iterations=max(
            (
                len(dm.iterations)
                for d in matrix.values()
                for m in d.values()
                for dm in m.values()
            ),
            default=1,
        ),
        matrix=matrix,
        failed_iterations_count=failed_iters,
        total_iterations_count=total_iters,
    )

    export_json(summary, run_dir / "summary.json")
    summary_md = _build_matching_summary_markdown(summary)
    (run_dir / "summary.md").write_text(summary_md, encoding="utf-8")
    summary_csv = _build_matching_summary_csv(summary)
    export_csv(summary_csv, run_dir / "summary.csv")

    console.print(
        f"[bold green]✔ In-place retry completed for run:[/] {run_dir}\n"
    )
    return summary


def main() -> None:
    """CLI entrypoint for matching-benchmark command."""
    parser = argparse.ArgumentParser(
        description="Run entity resolution matching & classification benchmarks."
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default=None,
        help="Path to datasets root directory.",
    )
    parser.add_argument(
        "--domain",
        type=str,
        default="all",
        help="Dataset domain filter.",
    )
    parser.add_argument(
        "--strategy",
        type=str,
        choices=["weighted", "dynamic_weighted", "kmeans", "ecm", "all"],
        default="all",
        help=(
            "Matching strategy to evaluate ('weighted', 'dynamic_weighted', "
            "'kmeans', 'all', or deprecated 'ecm'). Default: all"
        ),
    )
    parser.add_argument(
        "--strategies",
        nargs="*",
        default=None,
        help=(
            "List of matching strategies to evaluate "
            "(e.g. weighted, dynamic_weighted, kmeans)."
        ),
    )
    parser.add_argument(
        "--classification-mode",
        type=str,
        choices=["binary", "ternary", "both"],
        default="ternary",
        help=(
            "Classification mode: 'binary' (standalone matches/non-matches), "
            "'ternary' (matches/non-matches/uncertain cascade), "
            "or 'both' (dual-perspective benchmark)."
        ),
    )
    parser.add_argument(
        "--force-llm",
        action="store_true",
        help="Force LLM configuration generation, bypassing cache.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="LLM model name to use for matching configuration recommendation.",
    )
    parser.add_argument(
        "--models",
        nargs="*",
        default=None,
        help="One or more LLM models to benchmark.",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=1,
        help="Number of iterations per configuration (default: 1)",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=None,
        help="Alias for --iterations",
    )
    parser.add_argument(
        "--retry",
        type=str,
        default=None,
        help="Retry failed iterations for an existing run target ('latest', ID, or path)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Directory path to output benchmark run artifacts.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Legacy custom filename or directory path.",
    )
    parser.add_argument(
        "--max-csv-rows",
        type=int,
        default=None,
        help="Maximum rows to export in matches/non_matches/uncertain CSVs (default: 5000 from config).",
    )
    parser.add_argument(
        "--skip-bucket-csvs",
        action="store_true",
        help="Skip exporting matches/non_matches/uncertain CSV files.",
    )

    args = parser.parse_args()

    if args.retry:
        strat_filter: list[str] | None = None
        if args.strategies and "all" not in [
            s.lower() for s in args.strategies
        ]:
            strat_filter = args.strategies
        elif args.strategy and args.strategy != "all":
            strat_filter = [args.strategy]

        asyncio.run(
            retry_matching_benchmark_run(
                run_target=args.retry,
                strategy_filter=strat_filter,
                output_dir=Path(args.output_dir) if args.output_dir else None,
                classification_mode=args.classification_mode,
                force_llm=args.force_llm,
                max_csv_rows=args.max_csv_rows,
                skip_bucket_csvs=args.skip_bucket_csvs,
            )
        )
    else:
        asyncio.run(
            run_matching_benchmark(
                data_dir=args.data_dir,
                domain=args.domain,
                strategy=args.strategy,
                strategies=args.strategies,
                classification_mode=args.classification_mode,
                force_llm=args.force_llm,
                models=args.models,
                model_name=args.model or config.DEFAULT_GOOGLE_MODEL,
                iterations=args.runs or args.iterations,
                output_dir=args.output_dir,
                output=args.output,
                max_csv_rows=args.max_csv_rows,
                skip_bucket_csvs=args.skip_bucket_csvs,
            )
        )


if __name__ == "__main__":
    main()
