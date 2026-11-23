"""Statistical analysis and stability engines for benchmark evaluations."""

from __future__ import annotations

import itertools
import statistics
from collections.abc import Sequence
from typing import Any

from .models import AggregatedMetricStats


def compute_mean_std(values: Sequence[float]) -> AggregatedMetricStats:
    """Compute descriptive statistics for a sequence of numeric values.

    Args:
        values: Sequence of float values.

    Returns:
        AggregatedMetricStats with mean, sample std, min, max, and raw values.
    """
    if not values:
        return AggregatedMetricStats(
            mean=0.0,
            std=0.0,
            min=0.0,
            max=0.0,
            values=[],
        )

    val_list = [float(v) for v in values]
    mean_val = float(statistics.mean(val_list))
    std_val = float(statistics.stdev(val_list)) if len(val_list) > 1 else 0.0
    min_val = float(min(val_list))
    max_val = float(max(val_list))

    return AggregatedMetricStats(
        mean=round(mean_val, 6),
        std=round(std_val, 6),
        min=round(min_val, 6),
        max=round(max_val, 6),
        values=[round(v, 6) for v in val_list],
    )


class BenchmarkStatsEngine:
    """Mathematical and statistical computation engine for benchmarks."""

    @staticmethod
    def compute_mean_std(values: Sequence[float]) -> AggregatedMetricStats:
        """Computes mean and sample standard deviation for numerical metrics."""
        return compute_mean_std(values)

    @staticmethod
    def compute_consensus_ratio(
        predictions: Sequence[Sequence[Any] | Any],
    ) -> float:
        """Computes consensus ratio across iterations.

        If a sequence of scalar choices per iteration is provided (e.g. strategy
        chosen in iter 1, iter 2, ...), computes the fraction of iterations matching
        the majority choice.
        If a sequence of prediction collections per iteration is provided,
        computes the proportion of decisions where all iterations reached consensus.

        Args:
            predictions: Sequence of prediction lists or scalar decisions.

        Returns:
            Float in [0.0, 1.0] representing consensus agreement.
        """
        if not predictions:
            return 1.0

        if not isinstance(predictions[0], (list, tuple, set)):
            # Scalar sequence across iterations: e.g. ["strat_a", "strat_a", "strat_b"]
            total = len(predictions)
            if total <= 1:
                return 1.0
            counts: dict[Any, int] = {}
            for item in predictions:
                counts[item] = counts.get(item, 0) + 1
            max_count = max(counts.values())
            return round(max_count / total, 6)

        # Sequence of collection per iteration: e.g. [ [p1, p2], [p1, p2, p3] ]
        sets = [set(p) for p in predictions if isinstance(p, (list, tuple, set))]
        if not sets:
            return 1.0
        if len(sets) == 1:
            return 1.0

        all_items = set().union(*sets)
        if not all_items:
            return 1.0

        intersect = set.intersection(*sets)
        return round(len(intersect) / len(all_items), 6)

    @staticmethod
    def compute_jaccard_flakiness(
        prediction_sets: Sequence[set[Any] | list[Any]],
    ) -> dict[str, Any]:
        """Computes Jaccard stability and item-level flakiness across iteration sets.

        Args:
            prediction_sets: Sequence of sets/lists containing predicted items
              (e.g., predicted match pairs or chosen strategies).

        Returns:
            Dictionary containing:
                - 'consistent_items': items appearing in every iteration.
                - 'flaky_items': dict mapping item -> appearance fraction.
                - 'mean_pairwise_jaccard': average Jaccard similarity across pairs.
                - 'stability_ratio': size(intersection) / size(union).
        """
        if not prediction_sets:
            return {
                "consistent_items": [],
                "flaky_items": {},
                "mean_pairwise_jaccard": 1.0,
                "stability_ratio": 1.0,
            }

        sets = [set(s) for s in prediction_sets]
        n_iters = len(sets)
        if n_iters <= 1:
            items = list(sets[0]) if sets else []
            return {
                "consistent_items": items,
                "flaky_items": {},
                "mean_pairwise_jaccard": 1.0,
                "stability_ratio": 1.0,
            }

        union_set = set().union(*sets)
        if not union_set:
            return {
                "consistent_items": [],
                "flaky_items": {},
                "mean_pairwise_jaccard": 1.0,
                "stability_ratio": 1.0,
            }

        intersect_set = set.intersection(*sets)
        consistent_items = sorted(intersect_set, key=lambda x: str(x))

        # Item frequency counts
        flaky_items: dict[str, float] = {}
        for item in union_set:
            if item not in intersect_set:
                cnt = sum(1 for s in sets if item in s)
                flaky_items[str(item)] = round(cnt / n_iters, 4)

        # Pairwise Jaccard calculation
        jaccard_scores: list[float] = []
        for s1, s2 in itertools.combinations(sets, 2):
            u = s1.union(s2)
            if not u:
                jaccard_scores.append(1.0)
            else:
                jaccard_scores.append(len(s1.intersection(s2)) / len(u))

        mean_jaccard = (
            float(statistics.mean(jaccard_scores)) if jaccard_scores else 1.0
        )
        stability_ratio = len(intersect_set) / len(union_set)

        return {
            "consistent_items": consistent_items,
            "flaky_items": flaky_items,
            "mean_pairwise_jaccard": round(mean_jaccard, 6),
            "stability_ratio": round(stability_ratio, 6),
        }
