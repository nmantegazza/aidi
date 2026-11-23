"""
Tests for the entity_resolution module.
Covers: core unit tests (cleaning, profiling, indexing, matching),
        evaluation metrics, synthetic generator, and evaluation pipeline integration.
"""

import os
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from entity_resolution.evaluation import (
    evaluate_entity_resolution,
    evaluate_indexing,
    evaluate_matching,
)
from entity_resolution.evaluation_models import (
    EntityResEvalReport,
    MatchingEvaluation,
)
from entity_resolution.indexing import IndexingError, perform_indexing
from entity_resolution.matching import (
    classify_matches,
    extract_features_and_score,
    parse_numeric_series,
)
from entity_resolution.metrics import (
    compute_pairs_recall,
    compute_precision_recall_f1,
    compute_reduction_ratio,
    pairs_to_set,
)
from entity_resolution.models import (
    ColumnMatchConfig,
    ERPipelineConfiguration,
    SimilarityAlgorithm,
)
from entity_resolution.synthetic_generator import (
    SYNTHETIC_SCHEMAS,
    SyntheticConfig,
    generate_synthetic_pair,
    get_default_table_schema,
    get_schema_spec,
)

# ── Module imports ────────────────────────────────────────────────────────────
from shared.cleaning.engine import clean_data
from shared.profiling.engine import DataProfiler
from shared.schema_models import TableField, TableResource, TableSchema

# ── Shared fixtures ───────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def mock_env_vars():
    """Ensure no real API keys are needed during tests."""
    with patch.dict(os.environ, {"GOOGLE_API_KEY": "dummy_key_for_tests"}):
        yield


@pytest.fixture
def simple_resource() -> TableResource:
    return TableResource(
        name="test_table",
        schema=TableSchema(fields=[
            TableField(name="name", type="string", description="Full name"),
            TableField(name="city", type="string", description="City"),
        ])
    )


@pytest.fixture
def simple_dfs():
    df_a = pd.DataFrame({
        "name": ["John Doe",    "Jane Smith",   "Bob Corp"],
        "city": ["new york",    "los angeles",  "chicago"],
    })
    df_b = pd.DataFrame({
        "name": ["Jon Doe",     "Jane Smith",   "Bob Inc"],
        "city": ["new york",    "l.a.",         "chicago"],
    })
    return df_a, df_b


@pytest.fixture
def default_er_config() -> ERPipelineConfiguration:
    return ERPipelineConfiguration(
        indexing_keys=["name"],
        indexing_threshold=0.10,
        matching_columns={
            "name": ColumnMatchConfig(algorithm=SimilarityAlgorithm.JAROWINKLER, weight=1.0),
            "city": ColumnMatchConfig(algorithm=SimilarityAlgorithm.JAROWINKLER, weight=1.0),
        },
        reasoning="Test config"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 1. PROFILING TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestProfiling:
    def test_extract_column_metadata_basic(self, simple_dfs):
        df_a, _ = simple_dfs
        profile = DataProfiler.profile_dataframe(df_a, "test")
        
        metadata = profile.column_profiles
        assert "name" in metadata
        assert metadata["name"].cardinality == 3
        assert metadata["name"].null_percentage == 0.0
        assert metadata["name"].uniqueness_percentage == 100.0

    def test_extract_column_metadata_with_nulls(self):
        df = pd.DataFrame({"x": [1, None, 3, None]})
        profile = DataProfiler.profile_dataframe(df, "test")
        meta = profile.column_profiles["x"]
        assert meta.null_percentage == 50.0
        assert meta.cardinality == 2

    def test_profile_dataset_shape(self, simple_dfs):
        df_a, _ = simple_dfs
        profile = DataProfiler.profile_dataframe(df_a, "test")
        assert profile.total_rows == 3
        assert profile.total_columns == 2
        assert len(profile.column_profiles) == 2
        assert profile.column_profiles["name"].avg_length is not None


# ═══════════════════════════════════════════════════════════════════════════════
# 2. CLEANING TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestCleaning:
    def test_string_columns_lowercased(self, simple_resource):
        df = pd.DataFrame({"name": [" John DOE  ", "JANE smith"], "city": ["NYC", "L.A."]})
        cleaned, report = clean_data(df)
        assert cleaned.iloc[0]["name"] == "john doe"
        assert cleaned.iloc[1]["name"] == "jane smith"
        assert report.rows_before == 2

    def test_numeric_columns_preserved(self):
        resource = TableResource(name="test", schema=TableSchema(fields=[TableField(name="price", type="number")]))
        df = pd.DataFrame({"price": [10.5, 20.0, None]})
        df["price"] = df["price"].astype(float)
        cleaned, _ = clean_data(df)
        # Note: shared engine might promote to numeric if not already
        assert cleaned.iloc[0]["price"] == 10.5
        assert pd.isna(cleaned.iloc[2]["price"])

    def test_datetime_columns_preserved(self):
        resource = TableResource(name="test", schema=TableSchema(fields=[TableField(name="date", type="datetime")]))
        df = pd.DataFrame({"date": pd.to_datetime(["2023-01-01", "2023-12-31"])})
        cleaned, _ = clean_data(df)
        assert pd.api.types.is_datetime64_any_dtype(cleaned["date"])

    def test_accent_stripping(self):
        resource = TableResource(name="test", schema=TableSchema(fields=[TableField(name="name", type="string")]))
        df = pd.DataFrame({"name": ["José", "Niño"]})
        cleaned, report = clean_data(df)
        # Shared engine uses _native_clean_text which strips accents and punctuation
        assert cleaned.iloc[0]["name"] == "jose"
        assert cleaned.iloc[1]["name"] == "nino"
        # Verify example was captured
        assert any(e.operation == "text_normalization" and e.before == "José" for e in report.examples)

    def test_unicode_normalization(self):
        resource = TableResource(name="test", schema=TableSchema(fields=[TableField(name="name", type="string")]))
        # 'e' + combining acute accent (decomposed)
        decomposed = "e" + "\u0301" 
        df = pd.DataFrame({"name": [decomposed]})
        cleaned, _ = clean_data(df)
        # Should be normalized then cleaned
        assert cleaned.iloc[0]["name"] == "e"

    def test_duplicate_rows_removed(self):
        resource = TableResource(name="test", schema=TableSchema(fields=[TableField(name="name", type="string")]))
        df = pd.DataFrame({"name": ["Alice", "Alice", "Bob"]})
        cleaned, report = clean_data(df)
        assert len(cleaned) == 2
        assert report.duplicates_removed == 1
        assert list(cleaned["name"]) == ["alice", "bob"]

    def test_whitespace_only_to_nan(self):
        resource = TableResource(name="test", schema=TableSchema(fields=[
            TableField(name="name", type="string"), 
            TableField(name="city", type="string")
        ]))
        df = pd.DataFrame({"name": ["Alice", "  "], "city": ["NYC", "   "]})
        cleaned, report = clean_data(df)
        assert pd.isna(cleaned.iloc[1]["name"])
        assert pd.isna(cleaned.iloc[1]["city"])
        assert report.whitespace_cells_nullified == 2
        assert any(e.operation == "whitespace_to_nan" for e in report.examples)

    def test_missing_column_in_schema_ignored(self, simple_resource):
        df = pd.DataFrame({"name": ["Alice"], "extra_col": ["foo"]})
        cleaned, _ = clean_data(df)
        assert "extra_col" in cleaned.columns


# ═══════════════════════════════════════════════════════════════════════════════
# 3. INDEXING TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestIndexing:
    def test_sorted_neighborhood_returns_multiindex(self, simple_dfs):
        df_a, df_b = simple_dfs
        candidates = perform_indexing(df_a, df_b, sorting_keys="city", window_size=3)
        assert isinstance(candidates, pd.MultiIndex)

    def test_invalid_keys_raise_error(self, simple_dfs):
        df_a, df_b = simple_dfs
        # Passing an empty key no longer returns empty, it raises IndexingError.
        with pytest.raises(IndexingError, match="none of the provided keys"):
            perform_indexing(df_a, df_b, sorting_keys="", window_size=3)

    def test_window_size_limits_candidates(self, simple_dfs):
        df_a, df_b = simple_dfs
        # Smaller window → fewer candidates
        c1 = perform_indexing(df_a, df_b, sorting_keys="name", window_size=3)
        c2 = perform_indexing(df_a, df_b, sorting_keys="name", window_size=9)
        assert len(c1) <= len(c2)

    def test_multi_key_returns_union(self, simple_dfs):
        """Multi-key indexing should produce at least as many candidates as single-key."""
        df_a, df_b = simple_dfs
        single = perform_indexing(df_a, df_b, sorting_keys="name", window_size=3)
        multi = perform_indexing(df_a, df_b, sorting_keys=["name", "city"], window_size=3)
        single_set = set(single.tolist())
        multi_set = set(multi.tolist())
        # Union is a superset of any individual pass
        assert single_set.issubset(multi_set)
        assert len(multi) >= len(single)

    def test_multi_key_list_input(self, simple_dfs):
        """Accepts both a single string and a list of strings."""
        df_a, df_b = simple_dfs
        c_str = perform_indexing(df_a, df_b, sorting_keys="name", window_size=5)
        c_list = perform_indexing(df_a, df_b, sorting_keys=["name"], window_size=5)
        assert set(c_str.tolist()) == set(c_list.tolist())

    def test_indexing_config_model(self):
        """ERPipelineConfiguration correctly validates indexing_keys and threshold."""
        config = ERPipelineConfiguration(
            indexing_keys=["name", "email"],
            indexing_threshold=0.15,
            matching_columns={
                "name": ColumnMatchConfig(algorithm=SimilarityAlgorithm.JAROWINKLER, weight=1.0), 
                "email": ColumnMatchConfig(algorithm=SimilarityAlgorithm.DAMERAU_LEVENSHTEIN, weight=1.0)
            },
            reasoning="test"
        )
        assert config.indexing_keys == ["name", "email"]
        assert config.indexing_threshold == 0.15

    def test_indexing_config_validation_errors(self):
        """ERPipelineConfiguration rejects empty keys and out-of-range thresholds."""
        with pytest.raises(ValueError):
            ERPipelineConfiguration(
                indexing_keys=[],
                indexing_threshold=0.10,
                matching_columns={"name": ColumnMatchConfig(algorithm=SimilarityAlgorithm.JAROWINKLER, weight=1.0)},
                reasoning="test"
            )
        with pytest.raises(ValueError):
            ERPipelineConfiguration(
                indexing_keys=["name"],
                indexing_threshold=1.5,
                matching_columns={"name": ColumnMatchConfig(algorithm=SimilarityAlgorithm.JAROWINKLER, weight=1.0)},
                reasoning="test"
            )

    def test_indexing_pairs_cap_safety(self, simple_dfs):
        """Verifies that indexing pass is skipped if it exceeds cap limit."""
        df_a, df_b = simple_dfs
        from shared.config import config
        # Set the cap to a very small number (e.g. 2 pairs)
        with patch.object(config, "MAX_CANDIDATE_PAIRS_PER_PASS", 2):
            # perform_indexing with window=5 on name produces > 2 pairs.
            # It should be skipped and raise IndexingError.
            with pytest.raises(IndexingError, match="produced 0 pairs"):
                perform_indexing(
                    df_a, df_b, sorting_keys="name", window_size=5
                )

    def test_indexing_low_cardinality_warning(self, caplog):
        """Verifies low-cardinality triggers warning on large datasets."""
        import logging
        # Create larger dataframes with low cardinality sorting keys
        df_a = pd.DataFrame({"key": ["A"] * 600})
        df_b = pd.DataFrame({"key": ["A"] * 600})
        
        with caplog.at_level(logging.WARNING):
            # This should generate pairs, but trigger cardinality warning
            perform_indexing(df_a, df_b, sorting_keys="key", window_size=3)
            
        warnings = [rec.message for rec in caplog.records]
        assert any("low cardinality in df_a" in w for w in warnings)
        assert any("low cardinality in df_b" in w for w in warnings)


# ═══════════════════════════════════════════════════════════════════════════════
# 4. MATCHING TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestMatching:
    def test_features_have_aggregate_score(self, simple_dfs, default_er_config):
        df_a, df_b = simple_dfs
        candidates = perform_indexing(df_a, df_b, sorting_keys="name", window_size=3)
        features = extract_features_and_score(candidates, df_a, df_b, default_er_config.matching_columns)
        assert "aggregate_score" in features.columns
        assert (features["aggregate_score"] >= 0).all()
        assert (features["aggregate_score"] <= 1).all()

    def test_classify_matches_partition(self, simple_dfs, default_er_config):
        df_a, df_b = simple_dfs
        candidates = perform_indexing(df_a, df_b, sorting_keys="name", window_size=3)
        features = extract_features_and_score(candidates, df_a, df_b, default_er_config.matching_columns)
        matches, non_matches, uncertain = classify_matches(features, lower_threshold=0.6, upper_threshold=0.85)
        total = len(matches) + len(non_matches) + len(uncertain)
        assert total == len(features)

    def test_classify_matches_exact_match(self):
        """Pair with score=1.0 must always be a match at default thresholds."""
        idx = pd.MultiIndex.from_tuples([(0, 0)])
        df = pd.DataFrame({"col_a": [1.0], "aggregate_score": [1.0]}, index=idx)
        matches, non_matches, uncertain = classify_matches(df)
        assert len(matches) == 1
        assert len(non_matches) == 0

    def test_classify_requires_aggregate_score(self):
        df = pd.DataFrame({"col": [0.5]})
        with pytest.raises(ValueError):
            classify_matches(df)

    def test_identical_records_score_high(self):
        df_a = pd.DataFrame({"name": ["alice"]})
        df_b = pd.DataFrame({"name": ["alice"]})
        candidates = perform_indexing(df_a, df_b, sorting_keys="name", window_size=3)
        features = extract_features_and_score(
            candidates, df_a, df_b, {"name": ColumnMatchConfig(algorithm=SimilarityAlgorithm.JAROWINKLER, weight=1.0)}
        )
        assert features["aggregate_score"].iloc[0] >= 0.99

    def test_very_different_records_score_low(self):
        df_a = pd.DataFrame({"name": ["alice"]})
        df_b = pd.DataFrame({"name": ["zzzzzzz"]})
        candidates = perform_indexing(df_a, df_b, sorting_keys="name", window_size=3)
        features = extract_features_and_score(
            candidates, df_a, df_b, {"name": ColumnMatchConfig(algorithm=SimilarityAlgorithm.JAROWINKLER, weight=1.0)}
        )
        assert features["aggregate_score"].iloc[0] < 0.5

    def test_weighted_aggregate_score_dominance(self):
        """A high-weight column should dominate the aggregate score."""
        df_a = pd.DataFrame({"id": ["A1"], "name": ["Alice"], "city": ["New York"]})
        df_b = pd.DataFrame({"id": ["B1"], "name": ["Alice"], "city": ["Los Angeles"]})  # Name match, City mismatch
        idx = pd.MultiIndex.from_tuples([(0, 0)])
        
        # Scenario 1: Name weight 0.9, City weight 0.1
        config_name_heavy = {
            "name": ColumnMatchConfig(algorithm=SimilarityAlgorithm.JAROWINKLER, weight=0.9),
            "city": ColumnMatchConfig(algorithm=SimilarityAlgorithm.JAROWINKLER, weight=0.1)
        }
        res_heavy = extract_features_and_score(idx, df_a, df_b, config_name_heavy)
        score_heavy = res_heavy["aggregate_score"].iloc[0]
        
        # Scenario 2: Name weight 0.1, City weight 0.9
        config_city_heavy = {
            "name": ColumnMatchConfig(algorithm=SimilarityAlgorithm.JAROWINKLER, weight=0.1),
            "city": ColumnMatchConfig(algorithm=SimilarityAlgorithm.JAROWINKLER, weight=0.9)
        }
        res_light = extract_features_and_score(idx, df_a, df_b, config_city_heavy)
        score_light = res_light["aggregate_score"].iloc[0]
        
        # Since names match and cities don't, score_heavy should be much higher than score_light
        assert score_heavy > 0.8
        assert score_light < 0.4

    def test_weighted_mean_equivalence(self, simple_dfs):
        """Equal weights should produce the same result as the arithmetic mean."""
        df_a, df_b = simple_dfs
        idx = pd.MultiIndex.from_tuples([(0, 0), (1, 1)])
        
        config = {
            "name": ColumnMatchConfig(algorithm=SimilarityAlgorithm.JAROWINKLER, weight=1.0),
            "city": ColumnMatchConfig(algorithm=SimilarityAlgorithm.JAROWINKLER, weight=1.0)
        }
        features = extract_features_and_score(idx, df_a, df_b, config)
        
        # Manual mean calculation for the first pair
        f1_name = features.iloc[0]["name"]
        f1_city = features.iloc[0]["city"]
        expected_mean = (f1_name + f1_city) / 2
        
        assert abs(features.iloc[0]["aggregate_score"] - expected_mean) < 1e-6

    def test_weight_with_missing_values(self):
        """Weights of missing values should be excluded from the denominator."""
        df_a = pd.DataFrame({"name": ["Alice"], "city": [None]})
        df_b = pd.DataFrame({"name": ["Alice"], "city": ["NYC"]})
        idx = pd.MultiIndex.from_tuples([(0, 0)])
        
        config = {
            "name": ColumnMatchConfig(algorithm=SimilarityAlgorithm.JAROWINKLER, weight=0.8),
            "city": ColumnMatchConfig(algorithm=SimilarityAlgorithm.JAROWINKLER, weight=0.2)
        }
        # City is missing in df_a, so score for city is NaN. 
        # Aggregate should be purely based on 'name' since its weight is the only one in the denominator.
        features = extract_features_and_score(idx, df_a, df_b, config)
        
        # Feature score for name should be 1.0 (exact match)
        # Aggregate score should be (1.0 * 0.8) / 0.8 = 1.0
        assert abs(features.iloc[0]["aggregate_score"] - 1.0) < 1e-6


# ═══════════════════════════════════════════════════════════════════════════════
# 5. METRICS TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestMetrics:
    def test_perfect_match(self):
        predicted = {(0, 0), (1, 1), (2, 2)}
        gt        = {(0, 0), (1, 1), (2, 2)}
        m = compute_precision_recall_f1(predicted, gt)
        assert m.precision == 1.0
        assert m.recall    == 1.0
        assert m.f1        == 1.0
        assert m.tp == 3
        assert m.fp == 0
        assert m.fn == 0

    def test_no_overlap(self):
        predicted = {(0, 0)}
        gt        = {(1, 1)}
        m = compute_precision_recall_f1(predicted, gt)
        assert m.precision == 0.0
        assert m.recall    == 0.0
        assert m.f1        == 0.0
        assert m.tp == 0
        assert m.fp == 1
        assert m.fn == 1

    def test_partial_overlap(self):
        # predicted = {(0,0), (1,1)}, gt = {(0,0), (2,2)}
        # TP=1, FP=1, FN=1 → P=0.5, R=0.5, F1=0.5
        predicted = {(0, 0), (1, 1)}
        gt        = {(0, 0), (2, 2)}
        m = compute_precision_recall_f1(predicted, gt)
        assert m.tp == 1
        assert m.fp == 1
        assert m.fn == 1
        assert abs(m.precision - 0.5) < 1e-6
        assert abs(m.recall    - 0.5) < 1e-6
        assert abs(m.f1        - 0.5) < 1e-6

    def test_empty_predicted_nonempty_gt(self):
        m = compute_precision_recall_f1(set(), {(0, 0)})
        assert m.precision == 0.0
        assert m.recall    == 0.0
        assert m.fn        == 1

    def test_both_empty(self):
        m = compute_precision_recall_f1(set(), set())
        assert m.precision == 1.0
        assert m.recall    == 1.0
        assert m.f1        == 1.0

    def test_reduction_ratio(self):
        assert compute_reduction_ratio(100, 1000) == pytest.approx(0.9)
        assert compute_reduction_ratio(1000, 1000) == pytest.approx(0.0)
        assert compute_reduction_ratio(0, 1000) == pytest.approx(1.0)

    def test_reduction_ratio_zero_max(self):
        assert compute_reduction_ratio(0, 0) == 0.0

    def test_confusion_matrix_and_tn(self):
        predicted = {(0, 0), (0, 1)}
        ground_truth = {(0, 0), (1, 1)}
        total = 100
        m = compute_precision_recall_f1(predicted, ground_truth, total=total)
        assert m.tp == 1
        assert m.fp == 1
        assert m.fn == 1
        assert m.tn == 97
        assert m.confusion_matrix == [[1, 1], [1, 97]]

    def test_pairs_to_set_from_dataframe(self, simple_dfs, default_er_config):
        df_a, df_b = simple_dfs
        candidates = perform_indexing(df_a, df_b, sorting_keys="name", window_size=3)
        features = extract_features_and_score(candidates, df_a, df_b, default_er_config.matching_columns)
        matches, _, _ = classify_matches(features)
        result = pairs_to_set(matches)
        assert isinstance(result, set)
        for pair in result:
            assert len(pair) == 2

    def test_pairs_to_set_from_multiindex(self, simple_dfs):
        df_a, df_b = simple_dfs
        candidates = perform_indexing(df_a, df_b, sorting_keys="name", window_size=3)
        result = pairs_to_set(candidates)
        assert isinstance(result, set)

    def test_compute_pairs_recall_all_found(self):
        idx = pd.MultiIndex.from_tuples([(0, 0), (1, 1), (2, 2)])
        gt  = {(0, 0), (1, 1)}
        recall, missed = compute_pairs_recall(idx, gt)
        assert recall == 1.0
        assert missed == 0

    def test_compute_pairs_recall_partial(self):
        idx = pd.MultiIndex.from_tuples([(0, 0)])
        gt  = {(0, 0), (1, 1)}
        recall, missed = compute_pairs_recall(idx, gt)
        assert recall == 0.5
        assert missed == 1

    def test_compute_pairs_recall_empty_gt(self):
        idx = pd.MultiIndex.from_tuples([(0, 0)])
        recall, missed = compute_pairs_recall(idx, set())
        assert recall == 1.0
        assert missed == 0


# ═══════════════════════════════════════════════════════════════════════════════
# 6. SYNTHETIC GENERATOR TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestSyntheticGenerator:
    def test_basic_generation(self):
        cfg = SyntheticConfig(schema_name="persons", num_entities=100, overlap_ratio=0.5, seed=42)
        df_a, df_b, gt = generate_synthetic_pair(cfg)
        assert isinstance(df_a, pd.DataFrame)
        assert isinstance(df_b, pd.DataFrame)
        assert isinstance(gt, set)

    def test_ground_truth_size_matches_overlap(self):
        cfg = SyntheticConfig(schema_name="persons", num_entities=200, overlap_ratio=0.5, seed=42)
        _, _, gt = generate_synthetic_pair(cfg)
        expected = round(200 * 0.5)
        # Allow a small tolerance for rounding
        assert abs(len(gt) - expected) <= 2

    def test_reproducibility(self):
        cfg = SyntheticConfig(schema_name="persons", num_entities=100, overlap_ratio=0.4, seed=99)
        df_a1, df_b1, gt1 = generate_synthetic_pair(cfg)
        df_a2, df_b2, gt2 = generate_synthetic_pair(cfg)
        pd.testing.assert_frame_equal(df_a1, df_a2)
        pd.testing.assert_frame_equal(df_b1, df_b2)
        assert gt1 == gt2

    def test_no_noise_level_produces_less_diff(self):
        """
        Verify that 'none' noise produces identical shared-entity values in both sources,
        while 'high' noise introduces differences. Comparison uses ground-truth pair indices
        (not row positions) because source DataFrames are independently shuffled.
        """
        cfg_none = SyntheticConfig(schema_name="persons", num_entities=100, overlap_ratio=1.0, noise_level="none", null_injection_rate=0.0, seed=7)
        cfg_high = SyntheticConfig(schema_name="persons", num_entities=100, overlap_ratio=1.0, noise_level="high", null_injection_rate=0.0, seed=7)

        df_a_none, df_b_none, gt_none = generate_synthetic_pair(cfg_none)
        df_a_high, df_b_high, gt_high = generate_synthetic_pair(cfg_high)

        # With no noise: for every ground-truth match pair, the 'name' fields should be identical
        for a_idx, b_idx in gt_none:
            assert df_a_none.loc[a_idx, "name"] == df_b_none.loc[b_idx, "name"]

        # With high noise: at least some pairs should differ
        diffs_high = sum(
            df_a_high.loc[a_idx, "name"] != df_b_high.loc[b_idx, "name"]
            for a_idx, b_idx in gt_high
        )
        assert diffs_high > 0, "Expected high noise to introduce at least some name differences"

    def test_null_injection_rate(self):
        cfg = SyntheticConfig(schema_name="persons", num_entities=500, overlap_ratio=0.5, null_injection_rate=0.3, seed=10)
        df_a, df_b, _ = generate_synthetic_pair(cfg)
        # Check that some nulls were injected
        null_fraction_a = df_a.isnull().sum().sum() / (df_a.shape[0] * df_a.shape[1])
        assert null_fraction_a > 0.0

    def test_large_scale_generation(self):
        """Verify the generator handles 5000 entities without error."""
        cfg = SyntheticConfig(schema_name="persons", num_entities=5000, overlap_ratio=0.3, noise_level="medium", seed=42)
        df_a, df_b, gt = generate_synthetic_pair(cfg)
        assert len(df_a) >= 1000
        assert len(df_b) >= 1000
        assert len(gt) >= 100

    def test_ground_truth_indices_are_valid(self):
        cfg = SyntheticConfig(schema_name="persons", num_entities=100, overlap_ratio=0.5, seed=42)
        df_a, df_b, gt = generate_synthetic_pair(cfg)
        for a_idx, b_idx in gt:
            assert a_idx in df_a.index, f"idx_a={a_idx} not in df_a"
            assert b_idx in df_b.index, f"idx_b={b_idx} not in df_b"

    def test_default_schema_matches_generator_columns(self):
        schema = get_default_table_schema("persons")
        schema_cols = {f.name for f in schema.fields}
        cfg = SyntheticConfig(schema_name="persons", num_entities=50, seed=42)
        df_a, _, _ = generate_synthetic_pair(cfg)
        assert schema_cols == set(df_a.columns)

    @pytest.mark.parametrize("schema_name,expected_col", [
        ("persons",   "email"),
        ("companies", "company_name"),
        ("products",  "product_name"),
    ])
    def test_all_named_schemas_generate_correctly(self, schema_name, expected_col):
        """Each named schema should produce the correct columns and valid ground truth."""
        cfg = SyntheticConfig(schema_name=schema_name, num_entities=80, overlap_ratio=0.5, seed=42)
        df_a, df_b, gt = generate_synthetic_pair(cfg)
        assert expected_col in df_a.columns
        assert expected_col in df_b.columns
        assert len(gt) > 0
        for a_idx, b_idx in gt:
            assert a_idx in df_a.index
            assert b_idx in df_b.index

    def test_schema_columns_match_spec(self):
        """Columns produced by generate_synthetic_pair must match the schema spec."""
        for schema_name, spec in SYNTHETIC_SCHEMAS.items():
            expected_cols = set(spec.column_names())
            cfg = SyntheticConfig(schema_name=schema_name, num_entities=30, seed=0)
            df_a, _, _ = generate_synthetic_pair(cfg)
            assert set(df_a.columns) == expected_cols, f"Schema '{schema_name}' column mismatch"

    def test_invalid_schema_name_raises(self):
        with pytest.raises(ValueError, match="Unknown schema name"):
            get_schema_spec("nonexistent_schema")


# ═══════════════════════════════════════════════════════════════════════════════
# 7. EVALUATION INTEGRATION TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestEvaluationIntegration:
    """
    Integration tests for the evaluation pipeline.
    All tests use override_config to avoid any LLM calls.
    """

    @pytest.fixture(params=SYNTHETIC_SCHEMAS.keys())
    def synthetic_setup(self, request):
        schema_name = request.param
        cfg = SyntheticConfig(schema_name=schema_name, num_entities=100, overlap_ratio=0.5, noise_level="low", seed=42)
        df_a, df_b, gt = generate_synthetic_pair(cfg)
        
        # Create TableResource
        spec = get_schema_spec(schema_name)
        resource = TableResource(
            name=schema_name,
            schema=TableSchema(fields=spec.table_schema_fields())
        )

        # Use the schema's native matching columns and first column as sorting key
        matching_columns = spec.default_matching_columns()
        col_names = spec.column_names()

        er_config = ERPipelineConfiguration(
            indexing_keys=col_names[:2] if len(col_names) > 1 else col_names[:1],
            indexing_threshold=0.10,
            matching_columns=matching_columns,
            reasoning="Integration test config"
        )
        return df_a, df_b, gt, resource, er_config, cfg


    @pytest.mark.anyio
    async def test_evaluate_pipeline_returns_report(self, synthetic_setup):
        df_a, df_b, gt, resource, er_config, syn_cfg = synthetic_setup
        report = await evaluate_entity_resolution(
            df_a, df_b, gt,
            table_name="integration_test",
            override_config=er_config,
        )
        assert isinstance(report, EntityResEvalReport)

    @pytest.mark.anyio
    async def test_report_metrics_in_valid_range(self, synthetic_setup):
        df_a, df_b, gt, resource, er_config, syn_cfg = synthetic_setup
        report = await evaluate_entity_resolution(
            df_a, df_b, gt,
            table_name="range_test",
            override_config=er_config,
        )
        m = report.matching.metrics
        assert 0.0 <= m.precision <= 1.0
        assert 0.0 <= m.recall    <= 1.0
        assert 0.0 <= m.f1        <= 1.0
        assert 0.0 <= report.indexing.reduction_ratio <= 1.0
        assert 0.0 <= report.indexing.pairs_recall    <= 1.0

    @pytest.mark.anyio
    async def test_report_tp_fp_fn_consistent(self, synthetic_setup):
        df_a, df_b, gt, resource, er_config, syn_cfg = synthetic_setup
        report = await evaluate_entity_resolution(
            df_a, df_b, gt,
            table_name="consistency_test",
            override_config=er_config,
        )
        m = report.matching.metrics
        # TP + FP = predicted matches
        assert m.tp + m.fp == report.matching.num_predicted_matches
        # TP + FN = ground truth support
        assert m.tp + m.fn == m.support
        assert m.support == len(gt)

    def test_evaluate_indexing_stage(self, synthetic_setup):
        df_a, df_b, gt, resource, er_config, _ = synthetic_setup
        df_a_c, _ = clean_data(df_a)
        df_b_c, _ = clean_data(df_b)
        candidates = perform_indexing(df_a_c, df_b_c, er_config.indexing_keys, 11)
        idx_eval = evaluate_indexing(candidates, gt, df_a_c, df_b_c, er_config.indexing_keys, 11)
        assert idx_eval.max_possible_pairs == len(df_a) * len(df_b)
        assert idx_eval.num_candidates <= idx_eval.max_possible_pairs
        assert 0.0 <= idx_eval.reduction_ratio <= 1.0

    def test_evaluate_matching_stage(self, simple_dfs, default_er_config, simple_resource):
        df_a, df_b = simple_dfs
        ground_truth = {(0, 0)}  # Only first pair is a true match
        df_a_c, _ = clean_data(df_a)
        df_b_c, _ = clean_data(df_b)
        candidates = perform_indexing(df_a_c, df_b_c, default_er_config.indexing_keys, window_size=9)
        scored = extract_features_and_score(candidates, df_a_c, df_b_c, default_er_config.matching_columns)
        m_df, nm_df, u_df = classify_matches(scored)
        match_eval = evaluate_matching(m_df, u_df, nm_df, ground_truth)
        assert isinstance(match_eval, MatchingEvaluation)
        assert match_eval.metrics.tp + match_eval.metrics.fp == len(m_df)


class TestParseNumericSeries:
    """Tests for parse_numeric_series robust cleaning and parsing."""

    def test_parses_currency_and_thousands_separators(self):
        s = pd.Series(["$1,299.99", "$0.99", "1,500", "€12,50", "Album Only", None, np.nan])
        res = parse_numeric_series(s)
        assert res.iloc[0] == 1299.99
        assert res.iloc[1] == 0.99
        assert res.iloc[2] == 1500.0
        assert res.iloc[3] == 12.50
        assert pd.isna(res.iloc[4])
        assert pd.isna(res.iloc[5])
        assert pd.isna(res.iloc[6])

    def test_parses_duration_and_unit_suffixes(self):
        s = pd.Series(["117 minutes", "91 min", "91 min ", "101.5 mins", "N/A"])
        res = parse_numeric_series(s)
        assert res.iloc[0] == 117.0
        assert res.iloc[1] == 91.0
        assert res.iloc[2] == 91.0
        assert res.iloc[3] == 101.5
        assert pd.isna(res.iloc[4])

    def test_preserves_clean_numeric_series(self):
        s = pd.Series([10.5, 20.0, np.nan, 30])
        res = parse_numeric_series(s)
        assert res.iloc[0] == 10.5
        assert res.iloc[1] == 20.0
        assert pd.isna(res.iloc[2])
        assert res.iloc[3] == 30.0
