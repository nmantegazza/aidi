"""Unit and integration tests for bipartite matching and guardrails."""

from __future__ import annotations

import numpy as np
import pandas as pd

from entity_resolution.matching import (
    classify_matches,
    filter_one_to_one_bipartite,
)
from entity_resolution.matching_strategies.implementations import (
    DynamicWeightedMatchingStrategy,
    WeightedScoreMatchingConfig,
    WeightedScoreMatchingStrategy,
)
from entity_resolution.models import ColumnMatchConfig, SimilarityAlgorithm


class TestFilterOneToOneBipartite:
    """Tests greedy 1-to-1 bipartite candidate match assignment."""

    def test_empty_candidate_multiindex(self) -> None:
        """Verifies empty MultiIndex is returned gracefully with names."""
        empty_pairs = pd.MultiIndex.from_tuples(
            [], names=["left_id", "right_id"]
        )
        scores = pd.Series(dtype=float)
        result = filter_one_to_one_bipartite(empty_pairs, scores)
        assert result.empty
        assert result.names == ["left_id", "right_id"]

    def test_preserves_unique_one_to_one_pairs(self) -> None:
        """Verifies candidate pairs already 1-to-1 are entirely retained."""
        pairs = pd.MultiIndex.from_tuples(
            [(0, 10), (1, 11), (2, 12)], names=["left_id", "right_id"]
        )
        scores = pd.Series([0.90, 0.85, 0.95], index=pairs)
        result = filter_one_to_one_bipartite(pairs, scores)

        assert len(result) == 3
        assert set(result) == {(0, 10), (1, 11), (2, 12)}
        assert result.names == ["left_id", "right_id"]

    def test_disambiguates_duplicate_source_a(self) -> None:
        """Verifies duplicate source A IDs retain the highest scoring pair."""
        pairs = pd.MultiIndex.from_tuples(
            [(0, 10), (0, 11)], names=["left_id", "right_id"]
        )
        scores = pd.Series([0.95, 0.85], index=pairs)
        result = filter_one_to_one_bipartite(pairs, scores)

        assert len(result) == 1
        assert list(result) == [(0, 10)]

    def test_disambiguates_duplicate_source_b(self) -> None:
        """Verifies duplicate source B IDs retain the highest scoring pair."""
        pairs = pd.MultiIndex.from_tuples(
            [(0, 10), (1, 10)], names=["left_id", "right_id"]
        )
        scores = pd.Series([0.80, 0.92], index=pairs)
        result = filter_one_to_one_bipartite(pairs, scores)

        assert len(result) == 1
        assert list(result) == [(1, 10)]

    def test_greedy_cascade_assignment(self) -> None:
        """Verifies cascade assignment when multiple entities compete."""
        pairs = pd.MultiIndex.from_tuples(
            [(0, 10), (0, 11), (1, 11), (1, 12)],
            names=["left_id", "right_id"],
        )
        # (0, 10): 0.90, (0, 11): 0.85, (1, 11): 0.80, (1, 12): 0.70
        scores = pd.Series([0.90, 0.85, 0.80, 0.70], index=pairs)
        result = filter_one_to_one_bipartite(pairs, scores)

        # 1) (0, 10) selected (0.90) -> 0 and 10 claimed
        # 2) (0, 11) skipped (0 claimed)
        # 3) (1, 11) selected (0.80) -> 1 and 11 claimed
        # 4) (1, 12) skipped (1 claimed)
        assert len(result) == 2
        assert list(result) == [(0, 10), (1, 11)]


class TestClassifyMatchesGuardrails:
    """Tests core discriminator comparison guardrail in classify_matches."""

    def test_standard_classification_without_matching_columns(self) -> None:
        """Verifies backward compatibility when matching_columns is None."""
        df = pd.DataFrame(
            {"aggregate_score": [0.95, 0.70, 0.40]},
            index=pd.MultiIndex.from_tuples([(0, 0), (1, 1), (2, 2)]),
        )
        matches, non_matches, uncertain = classify_matches(
            df, lower_threshold=0.60, upper_threshold=0.85
        )

        assert len(matches) == 1
        assert (0, 0) in matches.index
        assert len(uncertain) == 1
        assert (1, 1) in uncertain.index
        assert len(non_matches) == 1
        assert (2, 2) in non_matches.index

    def test_core_discriminator_compared_stays_match(self) -> None:
        """Confirms match when core discriminator is compared and score high."""
        df = pd.DataFrame(
            {
                "title": [0.90],
                "brand": [1.00],
                "aggregate_score": [0.92],
            },
            index=pd.MultiIndex.from_tuples([(0, 0)]),
        )
        matching_columns = {
            "title": ColumnMatchConfig(
                algorithm=SimilarityAlgorithm.COSINE, weight=0.8
            ),
            "brand": ColumnMatchConfig(
                algorithm=SimilarityAlgorithm.EXACT, weight=0.2
            ),
        }
        matches, non_matches, uncertain = classify_matches(
            df,
            lower_threshold=0.60,
            upper_threshold=0.85,
            matching_columns=matching_columns,
        )

        assert len(matches) == 1
        assert (0, 0) in matches.index
        assert uncertain.empty
        assert non_matches.empty

    def test_core_discriminator_uncompared_downgraded_to_uncertain(
        self,
    ) -> None:
        """Downgrades match to uncertain when top-weighted column was NaN."""
        df = pd.DataFrame(
            {
                "title": [np.nan],
                "brand": [1.00],
                "aggregate_score": [0.90],
            },
            index=pd.MultiIndex.from_tuples([(0, 0)]),
        )
        matching_columns = {
            "title": ColumnMatchConfig(
                algorithm=SimilarityAlgorithm.COSINE, weight=0.9
            ),
            "brand": ColumnMatchConfig(
                algorithm=SimilarityAlgorithm.EXACT, weight=0.2
            ),
        }
        matches, non_matches, uncertain = classify_matches(
            df,
            lower_threshold=0.60,
            upper_threshold=0.85,
            matching_columns=matching_columns,
        )

        assert matches.empty
        assert len(uncertain) == 1
        assert (0, 0) in uncertain.index
        assert non_matches.empty

    def test_multiple_core_discriminators_partial_comparison(self) -> None:
        """Verifies match retained if at least one of multiple cores present."""
        # Top weight = 0.90, threshold = 0.90 * 0.85 = 0.765
        # Both title (0.90) and model_no (0.80) qualify as core discriminators
        matching_columns = {
            "title": ColumnMatchConfig(
                algorithm=SimilarityAlgorithm.COSINE, weight=0.90
            ),
            "model_no": ColumnMatchConfig(
                algorithm=SimilarityAlgorithm.EXACT, weight=0.80
            ),
            "brand": ColumnMatchConfig(
                algorithm=SimilarityAlgorithm.EXACT, weight=0.20
            ),
        }

        # Pair 1: title is NaN, model_no was compared -> core compared -> match
        # Pair 2: title is NaN, model_no is NaN -> uncompared -> uncertain
        df = pd.DataFrame(
            {
                "title": [np.nan, np.nan],
                "model_no": [0.95, np.nan],
                "brand": [1.00, 1.00],
                "aggregate_score": [0.92, 0.90],
            },
            index=pd.MultiIndex.from_tuples([(0, 0), (1, 1)]),
        )

        matches, _, uncertain = classify_matches(
            df,
            lower_threshold=0.60,
            upper_threshold=0.85,
            matching_columns=matching_columns,
        )

        assert len(matches) == 1
        assert (0, 0) in matches.index
        assert len(uncertain) == 1
        assert (1, 1) in uncertain.index


class TestStrategyIntegrationOneToOne:
    """Integration tests for strategy execution with enforce_one_to_one."""

    def test_weighted_score_strategy_enforce_one_to_one(self) -> None:
        """Verifies WeightedScoreMatchingStrategy enforces 1-to-1."""
        df_a = pd.DataFrame(
            {"title": ["Sony TV", "LG TV"], "brand": ["Sony", "LG"]},
            index=["a0", "a1"],
        )
        df_b = pd.DataFrame(
            {
                "title": ["Sony TV 55", "Sony TV OLED", "LG TV 65"],
                "brand": ["Sony", "Sony", "LG"],
            },
            index=["b0", "b1", "b2"],
        )
        # a0 pairs with b0 and b1
        pairs = pd.MultiIndex.from_tuples(
            [("a0", "b0"), ("a0", "b1"), ("a1", "b2")],
            names=["left_id", "right_id"],
        )
        cfg = WeightedScoreMatchingConfig(
            reasoning="Testing 1-to-1 bipartite matching.",
            matching_columns={
                "title": ColumnMatchConfig(
                    algorithm=SimilarityAlgorithm.JAROWINKLER, weight=0.7
                ),
                "brand": ColumnMatchConfig(
                    algorithm=SimilarityAlgorithm.EXACT, weight=0.3
                ),
            },
        )
        strategy = WeightedScoreMatchingStrategy(cfg)

        # 1. With enforce_one_to_one=True
        res_1to1 = strategy.execute(
            df_a, df_b, pairs, enforce_one_to_one=True
        )
        assert len(res_1to1.classified_pairs) <= 2
        # Check uniqueness of left and right indices
        left_ids = [a for a, _ in res_1to1.classified_pairs]
        right_ids = [b for _, b in res_1to1.classified_pairs]
        assert len(left_ids) == len(set(left_ids))
        assert len(right_ids) == len(set(right_ids))

        # Check prediction column reflects downgraded pair
        assert res_1to1.features_df is not None
        match_preds = res_1to1.features_df[
            res_1to1.features_df["prediction"] == "match"
        ]
        assert set(match_preds.index) == set(res_1to1.classified_pairs)

    def test_dynamic_weighted_strategy_enforce_one_to_one(self) -> None:
        """Verifies DynamicWeightedMatchingStrategy enforces 1-to-1."""
        df_a = pd.DataFrame(
            {"title": [f"Product {i}" for i in range(10)]},
            index=[f"a{i}" for i in range(10)],
        )
        df_b = pd.DataFrame(
            {"title": [f"Product {i}" for i in range(10)]},
            index=[f"b{i}" for i in range(10)],
        )
        # Candidate pairs with conflict on a0: (a0, b0) and (a0, b1)
        pair_list = [(f"a{i}", f"b{i}") for i in range(10)]
        pair_list.append(("a0", "b1"))
        pairs = pd.MultiIndex.from_tuples(
            pair_list, names=["left_id", "right_id"]
        )

        cfg = WeightedScoreMatchingConfig(
            reasoning="Testing dynamic 1-to-1.",
            matching_columns={
                "title": ColumnMatchConfig(
                    algorithm=SimilarityAlgorithm.JAROWINKLER, weight=1.0
                ),
            },
        )
        strategy = DynamicWeightedMatchingStrategy(cfg)

        res = strategy.execute(df_a, df_b, pairs, enforce_one_to_one=True)
        left_ids = [a for a, _ in res.classified_pairs]
        right_ids = [b for _, b in res.classified_pairs]
        assert len(left_ids) == len(set(left_ids))
        assert len(right_ids) == len(set(right_ids))
