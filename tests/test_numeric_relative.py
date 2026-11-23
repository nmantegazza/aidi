"""Unit tests for VectorizedRelativeNumeric comparator and matching integration."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from entity_resolution.matching import (
    VectorizedRelativeNumeric,
    extract_features_and_score,
)
from entity_resolution.models import ColumnMatchConfig, SimilarityAlgorithm


def test_vectorized_relative_numeric_unit_behavior():
    """Verifies formula and edge-case behavior for relative numeric comparisons."""
    comparator = VectorizedRelativeNumeric("col", "col", label="col")

    s1 = pd.Series([10.0, 15.0, 1200.0, 0.0, 0.0, 10.0, np.nan, 25.0])
    s2 = pd.Series([10.0, 25.0, 1210.0, 0.0, 10.0, 0.0, 10.0, np.nan])

    res = comparator._compute_vectorized(s1, s2)

    # 10 vs 10 -> 1.0
    assert pytest.approx(res.iloc[0], abs=1e-4) == 1.0

    # 15 vs 25 -> 1.0 - (10 / 25) = 0.60
    assert pytest.approx(res.iloc[1], abs=1e-4) == 0.60

    # 1200 vs 1210 -> 1.0 - (10 / 1210) ~= 0.9917
    assert pytest.approx(res.iloc[2], abs=1e-4) == 0.9917

    # 0 vs 0 -> 1.0
    assert pytest.approx(res.iloc[3], abs=1e-4) == 1.0

    # 0 vs 10 and 10 vs 0 -> 0.0
    assert pytest.approx(res.iloc[4], abs=1e-4) == 0.0
    assert pytest.approx(res.iloc[5], abs=1e-4) == 0.0

    # Missing value propagation
    assert pd.isna(res.iloc[6])
    assert pd.isna(res.iloc[7])


def test_extract_features_and_score_with_numeric_relative():
    """Verifies end-to-end integration of NUMERIC_RELATIVE in feature scoring."""
    df_a = pd.DataFrame(
        {
            "price": ["$19.99", "100.00", "0.00"],
            "title": ["Product A", "Product B", "Product C"],
        },
        index=[0, 1, 2],
    )
    df_b = pd.DataFrame(
        {
            "price": ["19.99 €", "120.00", "50.00"],
            "title": ["Product A", "Product B", "Product C"],
        },
        index=[10, 11, 12],
    )

    pairs = pd.MultiIndex.from_tuples([(0, 10), (1, 11), (2, 12)])
    matching_columns = {
        "price": ColumnMatchConfig(
            algorithm=SimilarityAlgorithm.NUMERIC_RELATIVE,
            weight=0.5,
        ),
        "title": ColumnMatchConfig(
            algorithm=SimilarityAlgorithm.EXACT,
            weight=0.5,
        ),
    }

    scored = extract_features_and_score(pairs, df_a, df_b, matching_columns)

    assert "price" in scored.columns
    assert "title" in scored.columns
    assert "aggregate_score" in scored.columns

    # Pair (0, 10): 19.99 vs 19.99 -> price=1.0, title=1.0 -> agg=1.0
    assert pytest.approx(scored.loc[(0, 10), "price"], abs=1e-3) == 1.0
    assert pytest.approx(scored.loc[(0, 10), "aggregate_score"], abs=1e-3) == 1.0

    # Pair (1, 11): 100 vs 120 -> 1.0 - (20/120) = 0.8333; title=1.0 -> agg ~= 0.9167
    assert pytest.approx(scored.loc[(1, 11), "price"], abs=1e-3) == 0.8333
    assert pytest.approx(scored.loc[(1, 11), "aggregate_score"], abs=1e-3) == 0.9167

    # Pair (2, 12): 0 vs 50 -> price=0.0, title=1.0 -> agg=0.50
    assert pytest.approx(scored.loc[(2, 12), "price"], abs=1e-3) == 0.0
    assert pytest.approx(scored.loc[(2, 12), "aggregate_score"], abs=1e-3) == 0.50
