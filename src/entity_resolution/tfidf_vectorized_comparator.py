"""Vectorized TF-IDF string comparator for recordlinkage."""

from __future__ import annotations

import gc

import numpy as np
import pandas as pd
from recordlinkage.base import BaseCompareFeature
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import paired_cosine_distances


class VectorizedTFIDF(BaseCompareFeature):
    """Vectorized TF-IDF cosine similarity feature comparator.

    Subclasses recordlinkage.base.BaseCompareFeature to compute TF-IDF
    vectorized cosine similarity between string series natively using
    scikit-learn.
    """

    def __init__(
        self,
        labels_left: str | list[str] | int,
        labels_right: str | list[str] | int,
        args: tuple = (),
        kwargs: dict | None = None,
        label: str | list[str] | int | None = None,
        chunk_size: int = 50000,
    ) -> None:
        """Initialize VectorizedTFIDF comparator.

        Args:
            labels_left: Column label(s) for the left DataFrame.
            labels_right: Column label(s) for the right DataFrame.
            args: Positional arguments for similarity computation.
            kwargs: Keyword arguments for similarity computation.
            label: Identifying label for the returned feature column.
            chunk_size: Maximum batch size for computing paired distances.
        """
        if kwargs is None:
            kwargs = {}
        super().__init__(
            labels_left,
            labels_right,
            args=args,
            kwargs=kwargs,
            label=label,
        )
        self.chunk_size = chunk_size

    def _compute_vectorized(
        self, s1: pd.Series, s2: pd.Series
    ) -> pd.Series:
        """Computes TF-IDF cosine similarity across candidate pair series.

        Args:
            s1: Series containing text from left records.
            s2: Series containing text from right records.

        Returns:
            pd.Series containing float cosine similarity scores.
        """
        mask = s1.isna() | s2.isna()
        s1_filled = s1.fillna("")
        s2_filled = s2.fillna("")

        indices_a, unique_a = pd.factorize(s1_filled)
        indices_b, unique_b = pd.factorize(s2_filled)
        all_unique = np.concatenate([unique_a, unique_b])

        try:
            vectorizer = TfidfVectorizer(analyzer="word", dtype=np.float32)
            vectorizer.fit(all_unique)
            v_a = vectorizer.transform(unique_a)
            v_b = vectorizer.transform(unique_b)

            total_pairs = len(s1)
            scores = np.zeros(total_pairs, dtype=np.float32)
            s1_vals = s1_filled.values
            s2_vals = s2_filled.values

            for start_idx in range(0, total_pairs, self.chunk_size):
                end_idx = min(start_idx + self.chunk_size, total_pairs)
                chunk_indices_a = indices_a[start_idx:end_idx]
                chunk_indices_b = indices_b[start_idx:end_idx]

                cand_a = v_a[chunk_indices_a]
                cand_b = v_b[chunk_indices_b]

                nnz_a = np.asarray(cand_a.getnnz(axis=1)).ravel()
                nnz_b = np.asarray(cand_b.getnnz(axis=1)).ravel()

                both_nonzero = (nnz_a > 0) & (nnz_b > 0)
                both_zero = (nnz_a == 0) & (nnz_b == 0)

                chunk_scores = np.zeros(end_idx - start_idx, dtype=np.float32)

                if np.any(both_nonzero):
                    dist = paired_cosine_distances(
                        cand_a[both_nonzero], cand_b[both_nonzero]
                    )
                    chunk_scores[both_nonzero] = 1.0 - dist

                if np.any(both_zero):
                    chunk_s1_vals = s1_vals[start_idx:end_idx]
                    chunk_s2_vals = s2_vals[start_idx:end_idx]
                    chunk_scores[both_zero] = np.where(
                        chunk_s1_vals[both_zero] == chunk_s2_vals[both_zero],
                        1.0,
                        0.0,
                    )

                scores[start_idx:end_idx] = chunk_scores

            scores = np.clip(scores, 0.0, 1.0)
            del v_a, v_b, vectorizer
            gc.collect()
        except ValueError:
            s1_vals = s1_filled.values
            s2_vals = s2_filled.values
            scores = np.where(s1_vals == s2_vals, 1.0, 0.0)

        scores[mask.values] = np.nan
        return pd.Series(scores, index=s1.index)

