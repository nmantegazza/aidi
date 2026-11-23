"""Zero-configuration exemplar candidate match extraction for ER profiling."""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

from shared.config import config

logger = logging.getLogger(__name__)


class ExemplarPair(dict[str, tuple[str, str]]):
    """Mapping of column names to (val_a, val_b) with an overall score."""

    def __init__(
        self,
        mapping: dict[str, tuple[str, str]],
        score: float = 0.0,
    ) -> None:
        """Initialize exemplar pair with column mapping and score.

        Args:
            mapping: Dictionary mapping column names to value tuples.
            score: Holistic cosine similarity score between records.
        """
        super().__init__(mapping)
        self.score: float = score


def _row_to_text(row: pd.Series, cols: list[str]) -> str:
    """Concatenates non-null values of selected columns into text."""
    tokens = []
    for col in cols:
        val = row.get(col)
        if pd.notna(val):
            val_str = str(val).strip()
            if val_str:
                tokens.append(val_str)
    return " ".join(tokens)


def extract_exemplar_candidates(
    df_a: pd.DataFrame,
    df_b: pd.DataFrame,
    top_k: int = 3,
    sample_size: int = 2000,
) -> list[dict[str, tuple[str, str]]]:
    """Extracts top exemplar candidate pairs across tables via holistic overlap.

    Operates directly on cleaned DataFrames prior to indexing or LLM matching.
    Subsamples rows, computes character 3-gram TF-IDF cosine similarities,
    and returns aligned field pairs for the top-scoring candidate matches.

    Args:
        df_a: Cleaned DataFrame for source A.
        df_b: Cleaned DataFrame for source B.
        top_k: Number of exemplar candidate pairs to return.
        sample_size: Maximum rows to sample from each DataFrame.

    Returns:
        List of dicts mapping column names to (val_a, val_b) tuples.
    """
    if df_a is None or df_b is None or df_a.empty or df_b.empty:
        return []

    shared_cols = [c for c in df_a.columns if c in df_b.columns]
    if not shared_cols:
        return []

    # Subsample DataFrames deterministically
    n_a = min(sample_size, len(df_a))
    n_b = min(sample_size, len(df_b))

    sample_a = (
        df_a.sample(n=n_a, random_state=config.SEED)
        if len(df_a) > n_a
        else df_a
    )
    sample_b = (
        df_b.sample(n=n_b, random_state=config.SEED)
        if len(df_b) > n_b
        else df_b
    )

    corpus_a = [
        _row_to_text(sample_a.iloc[i], shared_cols) for i in range(len(sample_a))
    ]
    corpus_b = [
        _row_to_text(sample_b.iloc[i], shared_cols) for i in range(len(sample_b))
    ]

    try:
        vectorizer = TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=(3, 3),
            min_df=1,
            dtype=np.float32,
        )
        vectorizer.fit(corpus_a + corpus_b)
        v_a = vectorizer.transform(corpus_a)
        v_b = vectorizer.transform(corpus_b)
    except (ValueError, AttributeError) as err:
        logger.debug("TF-IDF vectorization failed for exemplar extraction: %s", err)
        return []

    sim_matrix = v_a.dot(v_b.T).tocoo()
    if sim_matrix.nnz == 0:
        return []

    sort_indices = np.argsort(-sim_matrix.data)

    seen_a: set[int] = set()
    seen_b: set[int] = set()
    selected: list[tuple[int, int, float]] = []

    for idx in sort_indices:
        r_a = int(sim_matrix.row[idx])
        r_b = int(sim_matrix.col[idx])
        score = float(sim_matrix.data[idx])
        if score <= 0.0:
            continue
        if r_a not in seen_a and r_b not in seen_b:
            seen_a.add(r_a)
            seen_b.add(r_b)
            selected.append((r_a, r_b, score))
            if len(selected) >= top_k:
                break

    if len(selected) < top_k:
        existing = {(r_a, r_b) for r_a, r_b, _ in selected}
        for idx in sort_indices:
            r_a = int(sim_matrix.row[idx])
            r_b = int(sim_matrix.col[idx])
            score = float(sim_matrix.data[idx])
            if score <= 0.0:
                continue
            if (r_a, r_b) not in existing:
                existing.add((r_a, r_b))
                selected.append((r_a, r_b, score))
                if len(selected) >= top_k:
                    break

    exemplars: list[dict[str, tuple[str, str]]] = []
    for r_a, r_b, score in selected:
        row_a = sample_a.iloc[r_a]
        row_b = sample_b.iloc[r_b]
        col_pairs: dict[str, tuple[str, str]] = {}
        for col in shared_cols:
            val_a = "" if pd.isna(row_a[col]) else str(row_a[col])
            val_b = "" if pd.isna(row_b[col]) else str(row_b[col])
            col_pairs[col] = (val_a, val_b)
        exemplars.append(ExemplarPair(col_pairs, score=round(score, 4)))

    return exemplars
