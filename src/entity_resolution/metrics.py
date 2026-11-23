"""
Pure functions for computing Entity Resolution evaluation metrics,
leveraging the official python recordlinkage evaluation API.
All functions are stateless and have no side effects.
"""

from __future__ import annotations

from typing import Set, Tuple, Union, Any, Iterable, Optional
import numpy as np
import pandas as pd
import recordlinkage

from .evaluation_models import EvaluationMetrics


# Type alias for normalized match pairs
MatchPair = Tuple[Any, Any]
MatchSet = Set[MatchPair]
MatchInput = Union[pd.MultiIndex, pd.DataFrame, Iterable[MatchPair]]


def ensure_multiindex(pairs: MatchInput) -> pd.MultiIndex:
    """
    Normalize input record pairs (MultiIndex, DataFrame, Set, or List of tuples)
    into a pd.MultiIndex required by recordlinkage evaluation functions.

    Args:
        pairs: Input record pairs.

    Returns:
        A pd.MultiIndex object.
    """
    if isinstance(pairs, pd.DataFrame):
        return pairs.index
    elif isinstance(pairs, pd.MultiIndex):
        return pairs
    elif isinstance(pairs, (set, list, tuple)):
        if not pairs:
            return pd.MultiIndex.from_tuples([], names=[0, 1])
        return pd.MultiIndex.from_tuples(list(pairs))
    else:
        raise TypeError(f"Expected pd.MultiIndex, pd.DataFrame, set, or list; got {type(pairs)}")


def pairs_to_set(pairs: MatchInput) -> MatchSet:
    """
    Normalize a match result (MultiIndex, DataFrame, or Iterable) into
    a plain Python set of (idx_a, idx_b) tuples.

    Args:
        pairs: MultiIndex, DataFrame, or collection of tuples.

    Returns:
        A set of 2-tuples representing the match pairs.
    """
    if isinstance(pairs, (set, list, tuple)):
        return set(pairs)
    index = ensure_multiindex(pairs)
    return set(index.tolist())


def compute_precision_recall_f1(
    predicted: MatchInput,
    ground_truth: MatchInput,
    total: Optional[int] = None,
) -> EvaluationMetrics:
    """
    Compute Precision, Recall, F1 score, and Confusion Matrix for a set of predicted
    match pairs against a ground-truth set using recordlinkage's evaluation API.

    Args:
        predicted:    Predicted match pairs (MultiIndex, DataFrame, or Set of tuples).
        ground_truth: Known true match pairs (MultiIndex, DataFrame, or Set of tuples).
        total:        Optional total number of evaluated record pairs (enables TN calculation).

    Returns:
        EvaluationMetrics with precision, recall, f1, tp, fp, fn, tn, support, confusion_matrix.
    """
    pred_index = ensure_multiindex(predicted)
    gt_index = ensure_multiindex(ground_truth)

    # Handle empty sets edge cases
    if len(pred_index) == 0 and len(gt_index) == 0:
        cm_matrix = [[0, 0], [0, total]] if total is not None else None
        return EvaluationMetrics(
            precision=1.0, recall=1.0, f1=1.0,
            tp=0, fp=0, fn=0, tn=total, support=0,
            confusion_matrix=cm_matrix,
        )

    # Compute confusion matrix elements using pandas MultiIndex operations
    # (compatible with Pandas 2.0+ and recordlinkage API)
    tp = len(gt_index.intersection(pred_index))
    fn = len(gt_index.difference(pred_index))
    fp = len(pred_index.difference(gt_index))
    tn = int(total - (tp + fp + fn)) if total is not None else None

    # Construct 2x2 confusion matrix array for recordlinkage evaluation functions
    tn_val = tn if tn is not None else np.nan
    cm_arr = np.array([[tp, fn], [fp, tn_val]])
    cm_list = [[tp, fn], [fp, tn]] if total is not None else None
    support = len(gt_index)

    # Leverage official recordlinkage evaluation functions on confusion matrix
    p = float(recordlinkage.precision(cm_arr)) if (tp + fp) > 0 else 0.0
    r = float(recordlinkage.recall(cm_arr)) if (tp + fn) > 0 else 0.0

    try:
        f1 = float(recordlinkage.fscore(cm_arr)) if (p + r) > 0 else 0.0
    except (ZeroDivisionError, ValueError):
        f1 = 0.0

    return EvaluationMetrics(
        precision=round(p, 6),
        recall=round(r, 6),
        f1=round(f1, 6),
        tp=tp,
        fp=fp,
        fn=fn,
        tn=tn,
        support=support,
        confusion_matrix=cm_list,
    )


def compute_reduction_ratio(
    candidate_pairs: Union[int, MatchInput],
    max_possible_pairs: Union[int, Tuple[pd.DataFrame, pd.DataFrame]],
) -> float:
    """
    Compute the Reduction Ratio (RR) using recordlinkage.reduction_ratio logic.

    Args:
        candidate_pairs: Number of candidate pairs (int) or MultiIndex/DataFrame/Set of candidates.
        max_possible_pairs: Total max possible pairs (int) or tuple of DataFrames.

    Returns:
        Reduction ratio in [0.0, 1.0].
    """
    if isinstance(candidate_pairs, int):
        num_candidates = candidate_pairs
    else:
        num_candidates = len(ensure_multiindex(candidate_pairs))

    if isinstance(max_possible_pairs, (tuple, list)) and len(max_possible_pairs) == 2:
        return round(float(recordlinkage.reduction_ratio(num_candidates, *max_possible_pairs)), 6)

    if max_possible_pairs == 0:
        return 0.0

    rr = 1.0 - (num_candidates / max_possible_pairs)
    return round(float(rr), 6)


def compute_pairs_recall(
    candidate_pairs: MatchInput,
    ground_truth: MatchInput,
) -> Tuple[float, int]:
    """
    Compute Pairs Recall (PR) for candidate pairs generated during indexing
    against ground truth using recordlinkage.recall.

    Args:
        candidate_pairs: Candidate record pairs from indexing stage.
        ground_truth:    Set or MultiIndex of ground-truth true match pairs.

    Returns:
        A tuple of (pairs_recall, missed_true_matches).
    """
    gt_index = ensure_multiindex(ground_truth)
    if len(gt_index) == 0:
        return (1.0, 0)

    cand_index = ensure_multiindex(candidate_pairs)
    tp = len(gt_index.intersection(cand_index))
    fn = len(gt_index.difference(cand_index))

    cm_arr = np.array([[tp, fn], [0, 0]])
    recall = float(recordlinkage.recall(cm_arr)) if len(gt_index) > 0 else 1.0

    return round(recall, 6), fn


