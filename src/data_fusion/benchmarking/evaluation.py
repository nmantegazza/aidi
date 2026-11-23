"""Evaluator for single-truth and multi-truth data fusion benchmarking."""


import pandas as pd

from data_fusion.benchmarking.models import MetricsPayload
from data_fusion.benchmarking.normalization import normalize_string


class DataFusionEvaluator:
    """Evaluates data fusion predictions against Absolute and Reachable GT."""

    def evaluate_predictions(
        self,
        df_pred: pd.DataFrame,
        df_gt: pd.DataFrame,
        df_a: pd.DataFrame,
        df_b: pd.DataFrame,
        entity_id_col: str,
        attributes: list[str],
    ) -> tuple[MetricsPayload, MetricsPayload]:
        """Calculates Absolute and Reachable ground truth metrics.

        Args:
            df_pred: Predicted fused DataFrame.
            df_gt: Ground truth DataFrame.
            df_a: Source A DataFrame.
            df_b: Source B DataFrame.
            entity_id_col: Column name identifying entities.
            attributes: Attribute columns to evaluate.

        Returns:
            Tuple of (Absolute MetricsPayload, Reachable MetricsPayload).
        """
        # Set index to entity_id_col for fast lookup
        pred_indexed = df_pred.set_index(entity_id_col)
        gt_indexed = df_gt.set_index(entity_id_col)
        a_indexed = df_a.set_index(entity_id_col)
        b_indexed = df_b.set_index(entity_id_col)

        common_ids = gt_indexed.index.intersection(pred_indexed.index)

        abs_tp, abs_fp, abs_fn = 0, 0, 0
        reach_tp, reach_fp, reach_fn = 0, 0, 0

        for entity_id in common_ids:
            for attr in attributes:
                if attr not in gt_indexed.columns or attr not in pred_indexed.columns:
                    continue

                val_gt = gt_indexed.loc[entity_id, attr]
                val_pred = pred_indexed.loc[entity_id, attr]

                val_a = a_indexed.loc[entity_id, attr] if entity_id in a_indexed.index and attr in a_indexed.columns else ""
                val_b = b_indexed.loc[entity_id, attr] if entity_id in b_indexed.index and attr in b_indexed.columns else ""

                words_gt = normalize_string(val_gt)
                words_pred = normalize_string(val_pred)

                words_a = normalize_string(val_a)
                words_b = normalize_string(val_b)
                words_avail = words_a.union(words_b)
                words_reach = words_gt.intersection(words_avail)

                # Absolute GT metrics
                tp_abs = len(words_pred.intersection(words_gt))
                fp_abs = len(words_pred - words_gt)
                fn_abs = len(words_gt - words_pred)

                abs_tp += tp_abs
                abs_fp += fp_abs
                abs_fn += fn_abs

                # Reachable GT metrics
                tp_reach = len(words_pred.intersection(words_reach))
                fp_reach = len(words_pred - words_reach)
                fn_reach = len(words_reach - words_pred)

                reach_tp += tp_reach
                reach_fp += fp_reach
                reach_fn += fn_reach

        abs_metrics = self._calculate_metrics(abs_tp, abs_fp, abs_fn)
        reach_metrics = self._calculate_metrics(reach_tp, reach_fp, reach_fn)

        return abs_metrics, reach_metrics

    @staticmethod
    def _calculate_metrics(tp: int, fp: int, fn: int) -> MetricsPayload:
        """Calculates Precision, Recall, and F1 from TP, FP, FN counts.

        Args:
            tp: True Positives.
            fp: False Positives.
            fn: False Negatives.

        Returns:
            MetricsPayload object.
        """
        precision = tp / (tp + fp) if (tp + fp) > 0 else (1.0 if fn == 0 else 0.0)
        recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0
        f1 = (
            (2 * precision * recall) / (precision + recall)
            if (precision + recall) > 0
            else 0.0
        )
        return MetricsPayload(
            precision=round(precision, 4),
            recall=round(recall, 4),
            f1=round(f1, 4),
        )

    def extract_disagreements(
        self,
        df_pred: pd.DataFrame,
        df_gt: pd.DataFrame,
        df_a: pd.DataFrame,
        df_b: pd.DataFrame,
        entity_id_col: str,
        attributes: list[str],
        audit_log: dict[str, str] | None = None,
    ) -> pd.DataFrame:
        """Extracts row-level discrepancies where prediction differs from ground truth.

        Args:
            df_pred: Predicted fused DataFrame.
            df_gt: Ground truth DataFrame.
            df_a: Source A DataFrame.
            df_b: Source B DataFrame.
            entity_id_col: Column name identifying entities.
            attributes: Attribute columns to evaluate.
            audit_log: Optional mapping of attribute to chosen strategy.

        Returns:
            DataFrame of discrepancies.
        """
        audit = audit_log or {}
        pred_indexed = df_pred.set_index(entity_id_col)
        gt_indexed = df_gt.set_index(entity_id_col)
        a_indexed = df_a.set_index(entity_id_col)
        b_indexed = df_b.set_index(entity_id_col)

        common_ids = gt_indexed.index.intersection(pred_indexed.index)
        disagreements = []

        for entity_id in common_ids:
            for attr in attributes:
                if attr not in gt_indexed.columns or attr not in pred_indexed.columns:
                    continue

                raw_gt = gt_indexed.loc[entity_id, attr]
                raw_pred = pred_indexed.loc[entity_id, attr]
                val_gt = str(raw_gt) if not pd.isna(raw_gt) else ""
                val_pred = str(raw_pred) if not pd.isna(raw_pred) else ""

                val_a = ""
                if entity_id in a_indexed.index and attr in a_indexed.columns:
                    raw_a = a_indexed.loc[entity_id, attr]
                    val_a = str(raw_a) if not pd.isna(raw_a) else ""

                val_b = ""
                if entity_id in b_indexed.index and attr in b_indexed.columns:
                    raw_b = b_indexed.loc[entity_id, attr]
                    val_b = str(raw_b) if not pd.isna(raw_b) else ""

                words_gt = normalize_string(val_gt)
                words_pred = normalize_string(val_pred)

                if words_pred == words_gt:
                    continue

                words_a = normalize_string(val_a)
                words_b = normalize_string(val_b)
                words_avail = words_a.union(words_b)
                is_reachable = words_gt.issubset(words_avail) if words_gt else False

                disagreements.append({
                    entity_id_col: entity_id,
                    "attribute": attr,
                    "strategy": audit.get(attr, "unknown"),
                    "source_a": val_a,
                    "source_b": val_b,
                    "predicted": val_pred,
                    "ground_truth": val_gt,
                    "is_reachable": is_reachable,
                })

        return pd.DataFrame(disagreements)
