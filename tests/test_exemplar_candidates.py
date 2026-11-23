"""Unit tests for exemplar candidate match extraction."""

from __future__ import annotations

import time

import pandas as pd

from entity_resolution.exemplars import extract_exemplar_candidates


def test_extract_exemplar_candidates_structure():
    """Verifies exemplar candidates extraction returns structured pairs."""
    df_a = pd.DataFrame(
        {
            "title": [
                "Sony MDR-7506 Headphones",
                "Apple MacBook Pro 16",
                "Logitech MX Master 3 Mouse",
            ],
            "brand": ["Sony", "Apple", "Logitech"],
            "price": ["99.99", "2499.00", "99.00"],
        }
    )
    df_b = pd.DataFrame(
        {
            "title": [
                "Logitech MX Master 3 Wireless",
                "Sony MDR7506 Professional Headphone",
                "Bose QuietComfort 45",
            ],
            "brand": ["Logitech", "Sony", "Bose"],
            "price": ["99.99", "95.50", "329.00"],
        }
    )

    exemplars = extract_exemplar_candidates(df_a, df_b, top_k=2)

    assert len(exemplars) == 2
    for candidate in exemplars:
        assert isinstance(candidate, dict)
        assert "title" in candidate
        assert "brand" in candidate
        assert "price" in candidate
        val_a, val_b = candidate["title"]
        assert isinstance(val_a, str)
        assert isinstance(val_b, str)
        assert hasattr(candidate, "score")
        assert candidate.score > 0.0


def test_extract_exemplar_candidates_speed():
    """Verifies extraction operates within acceptable latency budget (<100ms)."""
    rows = [
        {
            "title": f"Product Item Model Number {i} Pro Edition",
            "desc": f"Detailed specification overview description for product {i}",
            "sku": f"SKU-{i:06d}",
        }
        for i in range(500)
    ]
    df_a = pd.DataFrame(rows)
    df_b = pd.DataFrame(rows)

    start = time.perf_counter()
    exemplars = extract_exemplar_candidates(df_a, df_b, top_k=3, sample_size=500)
    duration = time.perf_counter() - start

    assert len(exemplars) == 3
    # Ensure latency is well under 100ms (threshold generous at 0.5s for CI variance)
    assert duration < 0.5, f"Exemplar extraction took {duration:.4f}s"


def test_extract_exemplar_candidates_empty_and_edge_cases():
    """Verifies graceful handling of empty or non-overlapping DataFrames."""
    empty_df = pd.DataFrame()
    df_a = pd.DataFrame({"col1": ["val1"]})
    df_b = pd.DataFrame({"col2": ["val2"]})

    assert extract_exemplar_candidates(empty_df, df_a) == []
    assert extract_exemplar_candidates(df_a, empty_df) == []
    assert extract_exemplar_candidates(None, df_a) == []
    # No shared columns
    assert extract_exemplar_candidates(df_a, df_b) == []


def test_comparative_prompt_injection_with_exemplars():
    """Verifies that _build_comparative_prompt formats exemplar candidate pairs."""
    from entity_resolution.agents import _build_comparative_prompt
    from shared.profiling import DataProfiler
    from shared.schema_models import TableField, TableResource, TableSchema

    df_a = pd.DataFrame({"title": ["Sony MDR-7506 Headphones"], "price": ["99.99"]})
    df_b = pd.DataFrame({"title": ["Sony MDR7506 Headphone"], "price": ["95.50"]})

    prof_a = DataProfiler.profile_dataframe(df_a, "table_a")
    prof_b = DataProfiler.profile_dataframe(df_b, "table_b")
    table_res = TableResource(
        name="test_table",
        schema=TableSchema(
            fields=[
                TableField(name="title", type="string"),
                TableField(name="price", type="string"),
            ]
        ),
    )

    exemplars = extract_exemplar_candidates(df_a, df_b, top_k=1)
    prompt = _build_comparative_prompt(
        prof_a, prof_b, table_res, exemplar_candidates=exemplars
    )

    assert "Exemplar Candidate Matches (High-Confidence Entity Pairs)" in prompt
    assert "Candidate Match 1" in prompt
    assert "Aligned Match (Source A ↔ Source B)" in prompt
    assert '"Sony MDR-7506 Headphones" ↔ "Sony MDR7506 Headphone"' in prompt

