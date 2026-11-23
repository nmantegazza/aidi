"""Unit tests for VectorizedTFIDF comparator using word-level tokens."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from entity_resolution.tfidf_vectorized_comparator import VectorizedTFIDF


def test_vectorized_tfidf_word_level_behavior():
    """Verifies that word-level TF-IDF handles word reordering and token overlap."""
    comparator = VectorizedTFIDF("desc", "desc", label="desc")

    s1 = pd.Series(
        [
            "Apple MacBook Pro 16",
            "Sony MDR Professional Headphones",
            "Smith",
            "Completely Different String",
            np.nan,
        ]
    )
    s2 = pd.Series(
        [
            "16 MacBook Pro Apple",
            "Sony MDR Studio Headphones",
            "Smyth",
            "Another Unrelated Text Here",
            "Non-empty text",
        ]
    )

    scores = comparator._compute_vectorized(s1, s2)

    # Word reordering yields identical representation -> ~1.0
    assert pytest.approx(scores.iloc[0], abs=1e-3) == 1.0

    # Overlapping words ("Sony", "MDR", "Headphones") yield high similarity (>0.6)
    assert scores.iloc[1] > 0.60

    # Distinct tokens ("Smith" vs "Smyth") yield 0.0 due to word-level tokenization
    assert pytest.approx(scores.iloc[2], abs=1e-3) == 0.0

    # Completely unrelated texts yield near-zero or low similarity (<0.3)
    assert scores.iloc[3] < 0.30

    # Missing value yields NaN
    assert pd.isna(scores.iloc[4])


def test_vectorized_tfidf_identical_and_empty():
    """Verifies exact identical matches yield 1.0 and empty strings are handled."""
    comparator = VectorizedTFIDF("col", "col", label="col")

    s1 = pd.Series(["Exact Same Text", ""])
    s2 = pd.Series(["Exact Same Text", ""])

    scores = comparator._compute_vectorized(s1, s2)
    assert pytest.approx(scores.iloc[0], abs=1e-3) == 1.0
    assert pytest.approx(scores.iloc[1], abs=1e-3) == 1.0
