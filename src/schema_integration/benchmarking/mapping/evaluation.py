"""Evaluation and metric calculation for schema mapping benchmarks (Valentine)."""

from __future__ import annotations

import statistics
from typing import TYPE_CHECKING

from schema_integration.benchmarking.common.models import TokenUsage
from schema_integration.benchmarking.mapping.models import (
    AggregatedMetrics,
    FieldMatchInspection,
    IterationResult,
    MatchMetrics,
)
from schema_integration.mapping.models import MappingReport
from shared.agents import ExecutionMetadata

if TYPE_CHECKING:
    from schema_integration.benchmarking.mapping.loader import BenchmarkDataset


class MappingEvaluator:
    """Evaluates predicted schema mappings against gold-standard ground truth."""

    @staticmethod
    def extract_predicted_pairs(
        report: MappingReport,
        category: str = "single_table",
    ) -> set[tuple[str, str]]:
        """Extract match pairs from MappingReport.

        For multi-table datasets, extracts fully-qualified (source_table.col, target_table.col) pairs.
        For single-table datasets, extracts flat (source_col, target_col) pairs.

        Args:
            report: MappingReport containing generated MappingRules.
            category: Benchmark category ('single_table' or 'multi_table').

        Returns:
            Set of (source_ref, target_ref) pairs.
        """
        pairs: set[tuple[str, str]] = set()
        for rule in report.rules:
            target_col = rule.target_column
            target_tbl = rule.target_table
            source_tbl = rule.source_table
            for s_col in rule.source_columns:
                if s_col and str(s_col).strip():
                    s_clean = str(s_col).strip()
                    if category == "multi_table" or ("." in s_clean and "." in target_col):
                        s_qual = f"{source_tbl}.{s_clean}" if "." not in s_clean else s_clean
                        t_qual = f"{target_tbl}.{target_col}" if "." not in target_col else target_col
                        pairs.add((s_qual, t_qual))
                    else:
                        pairs.add((s_clean, target_col))
        return pairs

    @staticmethod
    def count_transformations(
        report: MappingReport,
    ) -> dict[str, int]:
        """Tally counts of transformation types used across mapping rules.

        Args:
            report: MappingReport containing mapping rules.

        Returns:
            Dictionary mapping transformation type string to occurrence count.
        """
        counts: dict[str, int] = {}
        for rule in report.rules:
            for t in rule.transformations:
                t_type = getattr(t, "type", type(t).__name__)
                counts[t_type] = counts.get(t_type, 0) + 1
        return counts

    @staticmethod
    def compute_match_metrics(
        predicted_pairs: set[tuple[str, str]],
        ground_truth: set[tuple[str, str]],
    ) -> MatchMetrics:
        """Compute precision, recall, F1, and confusion matrix counts/sets.

        Args:
            predicted_pairs: Set of predicted (source_col, target_col) pairs.
            ground_truth: Set of ground truth (source_col, target_col) pairs.

        Returns:
            MatchMetrics instance with TP/FP/FN sets and counts.
        """
        tp_set = predicted_pairs & ground_truth
        fp_set = predicted_pairs - ground_truth
        fn_set = ground_truth - predicted_pairs

        tp = len(tp_set)
        fp = len(fp_set)
        fn = len(fn_set)

        if tp + fp > 0:
            precision = tp / (tp + fp)
        else:
            precision = 1.0 if not ground_truth else 0.0

        if tp + fn > 0:
            recall = tp / (tp + fn)
        else:
            recall = 1.0

        if precision + recall > 0:
            f1 = 2 * (precision * recall) / (precision + recall)
        else:
            f1 = 0.0

        return MatchMetrics(
            precision=round(precision, 4),
            recall=round(recall, 4),
            f1=round(f1, 4),
            true_positives=tp,
            false_positives=fp,
            false_negatives=fn,
            predicted_pairs_count=len(predicted_pairs),
            gold_pairs_count=len(ground_truth),
            tp_pairs=sorted(tp_set),
            fp_pairs=sorted(fp_set),
            fn_pairs=sorted(fn_set),
        )

    @classmethod
    def build_field_inspections(
        cls,
        dataset: BenchmarkDataset,
        predicted_pairs: set[tuple[str, str]],
        mapping_report: MappingReport | None = None,
    ) -> list[FieldMatchInspection]:
        """Generate field-level alignment inspection for all target columns.

        Args:
            dataset: BenchmarkDataset containing schemas and ground truth.
            predicted_pairs: Set of predicted (source_col, target_col) pairs.
            mapping_report: Optional full LLM MappingReport with transformations.

        Returns:
            List of FieldMatchInspection objects for all target columns.
        """
        inspections: list[FieldMatchInspection] = []
        is_multi = getattr(dataset, "category", "single_table") == "multi_table"

        if is_multi:
            target_fields = [
                (f"{r.name}.{f.name}", f.type)
                for r in dataset.target_package.resources
                for f in r.schema_info.fields
            ]
        else:
            target_fields = [
                (f.name, f.type)
                for r in dataset.target_package.resources
                for f in r.schema_info.fields
            ]

        target_field_map = {name: ftype for name, ftype in target_fields}
        all_target_cols = list(target_field_map.keys())

        # Also capture any ground truth or predicted target columns not in schema
        for _, t in dataset.ground_truth:
            if t not in target_field_map and t not in all_target_cols:
                all_target_cols.append(t)
        for _, t in predicted_pairs:
            if t not in target_field_map and t not in all_target_cols:
                all_target_cols.append(t)

        rules_by_target: dict[str, list[dict]] = {}
        if mapping_report:
            for rule in mapping_report.rules:
                t_key = (
                    f"{rule.target_table}.{rule.target_column}"
                    if is_multi
                    else rule.target_column
                )
                t_list = [t.model_dump() for t in rule.transformations]
                rules_by_target.setdefault(t_key, []).extend(t_list)

        for t_col in all_target_cols:
            t_type = target_field_map.get(t_col, "unknown")
            expected_sources = sorted(
                [s for s, t in dataset.ground_truth if t == t_col]
            )
            predicted_sources = sorted(
                [s for s, t in predicted_pairs if t == t_col]
            )
            transformations = rules_by_target.get(t_col, [])

            if expected_sources and predicted_sources:
                if set(predicted_sources) == set(expected_sources):
                    status = "MATCH (TP)"
                elif set(predicted_sources) & set(expected_sources):
                    status = "PARTIAL MATCH"
                else:
                    status = "MISMATCH (FP)"
            elif expected_sources and not predicted_sources:
                status = "MISSED (FN)"
            elif predicted_sources and not expected_sources:
                status = "EXTRA (FP)"
            else:
                status = "UNMAPPED"

            inspections.append(
                FieldMatchInspection(
                    target_column=t_col,
                    target_type=t_type,
                    expected_source_columns=expected_sources,
                    predicted_source_columns=predicted_sources,
                    status=status,
                    transformations=transformations,
                )
            )

        return inspections

    @classmethod
    def evaluate_mapping_iteration(
        cls,
        report: MappingReport,
        dataset: BenchmarkDataset,
        metadata: ExecutionMetadata | None = None,
        iteration_index: int = 1,
    ) -> IterationResult:
        """Evaluate a single mapping run iteration and compute full metrics.

        Args:
            report: MappingReport produced by the mapping agent.
            dataset: BenchmarkDataset being evaluated.
            metadata: Optional execution metadata with tokens and latency.
            iteration_index: 1-indexed iteration counter.

        Returns:
            IterationResult populated with metrics, schemas, and field inspections.
        """
        category = getattr(dataset, "category", "single_table")
        pred_pairs = cls.extract_predicted_pairs(report, category=category)
        metrics = cls.compute_match_metrics(pred_pairs, dataset.ground_truth)
        transform_counts = cls.count_transformations(report)
        field_inspections = cls.build_field_inspections(
            dataset=dataset,
            predicted_pairs=pred_pairs,
            mapping_report=report,
        )

        latency = metadata.execution_time_seconds if metadata else 0.0
        prompt_tokens = metadata.prompt_tokens if metadata else 0
        comp_tokens = metadata.completion_tokens if metadata else 0
        total_tokens = metadata.total_tokens if metadata else 0
        cost_usd = metadata.cost_usd if metadata else None
        retry_count = metadata.retry_count if metadata else 0
        retry_log = (
            [e.model_dump() for e in metadata.retry_log]
            if metadata and metadata.retry_log
            else []
        )

        return IterationResult(
            iteration_index=iteration_index,
            category=category,
            metrics=metrics,
            latency_seconds=round(latency, 3),
            token_usage=TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=comp_tokens,
                total_tokens=total_tokens,
                latency_seconds=round(latency, 3),
                cost_usd=cost_usd,
            ),
            predicted_pairs=sorted(pred_pairs),
            tp_pairs=metrics.tp_pairs,
            fp_pairs=metrics.fp_pairs,
            fn_pairs=metrics.fn_pairs,
            transformation_counts=transform_counts,
            mapping_report=report,
            field_inspections=field_inspections,
            retry_count=retry_count,
            retry_log=retry_log,
        )

    @staticmethod
    def aggregate_iterations(
        iteration_results: list[IterationResult],
    ) -> AggregatedMetrics:
        """Compute mean and standard deviation across multiple iterations.

        Args:
            iteration_results: List of completed IterationResult instances.

        Returns:
            AggregatedMetrics with mean and standard deviation values.
        """
        valid_results = [
            r for r in iteration_results if r.error_message is None
        ]
        if not valid_results:
            return AggregatedMetrics(
                precision_mean=0.0,
                precision_std=0.0,
                recall_mean=0.0,
                recall_std=0.0,
                f1_mean=0.0,
                f1_std=0.0,
                latency_mean_sec=0.0,
                latency_std_sec=0.0,
                total_tokens=0,
                estimated_cost_usd=0.0,
            )

        precisions = [r.metrics.precision for r in valid_results]
        recalls = [r.metrics.recall for r in valid_results]
        f1s = [r.metrics.f1 for r in valid_results]
        latencies = [r.latency_seconds for r in valid_results]
        total_tokens = sum(
            r.token_usage.total_tokens for r in valid_results
        )
        total_cost = sum(
            r.token_usage.cost_usd or 0.0 for r in valid_results
        )

        n = len(valid_results)
        p_mean = statistics.mean(precisions)
        p_std = statistics.stdev(precisions) if n > 1 else 0.0

        r_mean = statistics.mean(recalls)
        r_std = statistics.stdev(recalls) if n > 1 else 0.0

        f1_mean = statistics.mean(f1s)
        f1_std = statistics.stdev(f1s) if n > 1 else 0.0

        lat_mean = statistics.mean(latencies)
        lat_std = statistics.stdev(latencies) if n > 1 else 0.0

        return AggregatedMetrics(
            precision_mean=round(p_mean, 4),
            precision_std=round(p_std, 4),
            recall_mean=round(r_mean, 4),
            recall_std=round(r_std, 4),
            f1_mean=round(f1_mean, 4),
            f1_std=round(f1_std, 4),
            latency_mean_sec=round(lat_mean, 3),
            latency_std_sec=round(lat_std, 3),
            total_tokens=total_tokens,
            estimated_cost_usd=round(total_cost, 6),
        )
