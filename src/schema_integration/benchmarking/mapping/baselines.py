"""Classical and heuristic baseline matchers for schema mapping."""

from __future__ import annotations

import logging
import time
from typing import ClassVar

import pandas as pd

from shared.schema_models import DataPackage

logger = logging.getLogger(__name__)


class ExactMatcher:
    """Exact case-insensitive column name matching baseline."""

    @staticmethod
    def match(
        df_source: pd.DataFrame,
        df_target: pd.DataFrame,
    ) -> set[tuple[str, str]]:
        """Perform exact case-insensitive column name matching.

        Args:
            df_source: Source pandas DataFrame.
            df_target: Target pandas DataFrame.

        Returns:
            Set of matched (source_col, target_col) tuples.
        """
        target_map: dict[str, str] = {
            str(col).strip().lower(): str(col) for col in df_target.columns
        }
        matches: set[tuple[str, str]] = set()

        for s_col in df_source.columns:
            s_norm = str(s_col).strip().lower()
            if s_norm in target_map:
                matches.add((str(s_col), target_map[s_norm]))

        return matches

    @staticmethod
    def match_multi_table(
        source_package: DataPackage,
        target_package: DataPackage,
    ) -> set[tuple[str, str]]:
        """Perform strict qualified exact matching across multi-table schemas.

        Matches if and only if table.column matches identically (case-insensitive).

        Args:
            source_package: Source schema DataPackage.
            target_package: Target schema DataPackage.

        Returns:
            Set of matched (source_table.col, target_table.col) tuples.
        """
        target_map: dict[str, str] = {
            f"{r.name.strip().lower()}.{f.name.strip().lower()}": f"{r.name}.{f.name}"
            for r in target_package.resources
            for f in r.schema_info.fields
        }
        matches: set[tuple[str, str]] = set()

        for r in source_package.resources:
            for f in r.schema_info.fields:
                key = f"{r.name.strip().lower()}.{f.name.strip().lower()}"
                if key in target_map:
                    matches.add((f"{r.name}.{f.name}", target_map[key]))

        return matches


class BaselineRunner:
    """Runner for classical baseline matching algorithms."""

    SUPPORTED_VALENTINE_ALGORITHMS: ClassVar[list[str]] = [
        "exact",
        "jaccard",
        "cupid",
        "distribution_based",
        "coma",
    ]

    @classmethod
    def run_exact(
        cls,
        df_source: pd.DataFrame,
        df_target: pd.DataFrame,
    ) -> tuple[set[tuple[str, str]], float]:
        """Execute ExactMatcher baseline on single-table DataFrames and record latency.

        Args:
            df_source: Source DataFrame.
            df_target: Target DataFrame.

        Returns:
            Tuple of (predicted_pairs, latency_seconds).
        """
        start_time = time.perf_counter()
        matches = ExactMatcher.match(df_source, df_target)
        latency = time.perf_counter() - start_time
        return matches, latency

    @classmethod
    def run_exact_multi_table(
        cls,
        source_package: DataPackage,
        target_package: DataPackage,
    ) -> tuple[set[tuple[str, str]], float]:
        """Execute strict qualified ExactMatcher baseline on multi-table schemas.

        Args:
            source_package: Source schema DataPackage.
            target_package: Target schema DataPackage.

        Returns:
            Tuple of (predicted_pairs, latency_seconds).
        """
        start_time = time.perf_counter()
        matches = ExactMatcher.match_multi_table(source_package, target_package)
        latency = time.perf_counter() - start_time
        return matches, latency

    @classmethod
    def run_valentine(
        cls,
        df_source: pd.DataFrame,
        df_target: pd.DataFrame,
        algorithm_name: str,
        threshold: float = 0.5,
    ) -> tuple[set[tuple[str, str]], float]:
        """Execute a Valentine classical schema matcher.

        Args:
            df_source: Source DataFrame.
            df_target: Target DataFrame.
            algorithm_name: Name of algorithm ('jaccard', 'cupid',
                'distribution_based', 'coma').
            threshold: Confidence threshold for match acceptance.

        Returns:
            Tuple of (predicted_pairs, latency_seconds).

        Raises:
            ValueError: If algorithm_name is unsupported.
        """
        from valentine import valentine_match
        from valentine.algorithms import (
            Coma,
            Cupid,
            DistributionBased,
            JaccardDistanceMatcher,
        )

        algo_key = algorithm_name.strip().lower()
        matcher_instance = None

        if algo_key in ["jaccard", "jaccard_distance", "jaccarddistancematcher"]:
            matcher_instance = JaccardDistanceMatcher()
        elif algo_key == "cupid":
            matcher_instance = Cupid()
        elif algo_key in [
            "distribution_based",
            "distributionbased",
            "distribution",
        ]:
            matcher_instance = DistributionBased()
        elif algo_key == "coma":
            matcher_instance = Coma(use_instances=True)
        else:
            raise ValueError(
                f"Unsupported Valentine algorithm: '{algorithm_name}'. "
                f"Supported: {cls.SUPPORTED_VALENTINE_ALGORITHMS}"
            )

        start_time = time.perf_counter()
        matches: set[tuple[str, str]] = set()

        try:
            results = valentine_match(
                [df_source, df_target],
                matcher_instance,
            )
            candidates: list[tuple[str, str, float]] = []
            for pair, score in results.items():
                if score >= threshold:
                    s_col = (
                        pair.source_column
                        if hasattr(pair, "source_column")
                        else pair[0][1]
                    )
                    t_col = (
                        pair.target_column
                        if hasattr(pair, "target_column")
                        else pair[1][1]
                    )
                    candidates.append((str(s_col), str(t_col), float(score)))

            # Sort candidates by score descending for greedy 1:1 assignment
            candidates.sort(key=lambda item: item[2], reverse=True)

            matched_sources: set[str] = set()
            matched_targets: set[str] = set()

            for s_col, t_col, _ in candidates:
                if (
                    s_col not in matched_sources
                    and t_col not in matched_targets
                ):
                    matches.add((s_col, t_col))
                    matched_sources.add(s_col)
                    matched_targets.add(t_col)
        except Exception as e:  # noqa: BLE001
            logger.warning(
                "Valentine matcher '%s' encountered an error: %s",
                algorithm_name,
                e,
            )

        latency = time.perf_counter() - start_time
        return matches, latency
