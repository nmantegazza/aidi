"""Evaluator module for entity resolution matching metrics."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import pandas as pd

from entity_resolution.metrics import (
    compute_precision_recall_f1,
    pairs_to_set,
)


class MatchingMetricsEvaluator:
    """Evaluates entity resolution classification against ground truth."""

    def evaluate(
        self,
        classified_pairs: (
            pd.MultiIndex | pd.DataFrame | Iterable[tuple[Any, Any]]
        ),
        ground_truth: (
            set[tuple[str, str]] | pd.MultiIndex | Iterable[tuple[Any, Any]]
        ),
        uncertain_pairs: (
            pd.MultiIndex | pd.DataFrame | Iterable[tuple[Any, Any]] | None
        ) = None,
        total_candidates: int | None = None,
    ) -> dict[str, Any]:
        """Compute precision, recall, F1, confusion matrix, and triage metrics.

        Args:
            classified_pairs: Predicted match pairs.
            ground_truth: Ground truth positive match pairs.
            uncertain_pairs: Optional uncertain match pairs for triage analysis.
            total_candidates: Total candidate pairs evaluated.

        Returns:
            Dictionary containing direct performance metrics, confusion counts,
            and optional triage perspective metrics.
        """
        metrics = compute_precision_recall_f1(
            predicted=classified_pairs,
            ground_truth=ground_truth,
            total=total_candidates,
        )

        potential_recall: float | None = None
        potential_f1: float | None = None
        unrecoverable_loss: float | None = None
        llm_workload_ratio: float | None = None
        uncertain_purity: float | None = None
        uncertain_count: int = 0

        if uncertain_pairs is not None:
            a1 = pairs_to_set(classified_pairs)
            a2 = pairs_to_set(uncertain_pairs)
            gt = pairs_to_set(ground_truth)

            gt_size = len(gt)
            a2_size = len(a2)
            c_size = (
                total_candidates
                if total_candidates is not None
                else (len(a1) + a2_size)
            )

            p_dir = metrics.precision
            if gt_size > 0:
                potential_recall = len((a1 | a2) & gt) / gt_size
                unrecoverable_loss = 1.0 - potential_recall
            else:
                potential_recall = 0.0
                unrecoverable_loss = 0.0

            if (p_dir + potential_recall) > 0:
                potential_f1 = (
                    2.0 * p_dir * potential_recall / (p_dir + potential_recall)
                )
            else:
                potential_f1 = 0.0

            if c_size > 0:
                llm_workload_ratio = a2_size / c_size
            else:
                llm_workload_ratio = 0.0

            if a2_size > 0:
                uncertain_purity = len(a2 & gt) / a2_size
            else:
                uncertain_purity = 0.0

            uncertain_count = a2_size

        return {
            "precision": metrics.precision,
            "recall": metrics.recall,
            "f1": metrics.f1,
            "tp": metrics.tp,
            "fp": metrics.fp,
            "fn": metrics.fn,
            "tn": metrics.tn,
            "potential_recall": potential_recall,
            "potential_f1": potential_f1,
            "unrecoverable_loss": unrecoverable_loss,
            "llm_workload_ratio": llm_workload_ratio,
            "uncertain_purity": uncertain_purity,
            "uncertain_count": uncertain_count,
        }
