"""Core Entity Resolution pipeline execution.

Decoupled from evaluation and console reporting.
"""

from __future__ import annotations

import logging

import httpx
import pandas as pd

from shared.agents import ExecutionMetadata
from shared.console import console as r_console

from .agents import identify_er_config_via_llm, refine_uncertain_matches_via_llm
from .classification import DynamicThresholdClassificationEngine
from .exemplars import extract_exemplar_candidates
from .indexing_strategies.implementations import TFIDFIndexStrategy
from .matching import (
    classify_matches,
    extract_features_and_score,
    filter_one_to_one_bipartite,
)
from .models import (
    ClassificationMode,
    CleaningReport,
    ColumnMatchConfig,
    EntityResolutionResult,
    ERPipelineConfiguration,
    TableProfile,
    TableResource,
)

logger = logging.getLogger(__name__)


def execute_tfidf_indexing(
    df_a: pd.DataFrame,
    df_b: pd.DataFrame,
    keys: list[str],
    threshold: float = 0.10,
    analyzer: str = "word",
    ngram_range: tuple[int, int] = (1, 2),
) -> pd.MultiIndex:
    """Generates candidate record pairs using TF-IDF sparse cosine similarity.

    Args:
        df_a: Cleaned Source A DataFrame.
        df_b: Cleaned Source B DataFrame.
        keys: Ordered list of column names to concatenate for vectorization.
        threshold: Cosine similarity cutoff threshold.
        analyzer: Tokenizer feature analyzer ('word', 'char', 'char_wb').
        ngram_range: Lower and upper boundary of n-grams.

    Returns:
        pd.MultiIndex of candidate index pairs.
    """
    strategy = TFIDFIndexStrategy(
        keys=keys,
        analyzer=analyzer,
        ngram_range=ngram_range,
        threshold=threshold,
    )
    result = strategy.execute(df_a, df_b)
    return result.candidate_pairs


def score_and_classify_pairs(
    candidate_pairs: pd.MultiIndex,
    df_a: pd.DataFrame,
    df_b: pd.DataFrame,
    matching_columns: dict[str, ColumnMatchConfig],
    classification_mode: ClassificationMode = ClassificationMode.TERNARY,
    enforce_one_to_one: bool = True,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Scores candidate pairs on configured columns and classifies them.

    Applies dynamic 1D K-Means thresholding with fallback to static heuristics
    when score variance is zero or sample size is insufficient. Enforces 1-to-1
    mutual exclusivity filtering when enabled.

    Args:
        candidate_pairs: MultiIndex of candidate record pairs.
        df_a: Source A DataFrame.
        df_b: Source B DataFrame.
        matching_columns: Mapping of column names to matching configurations.
        classification_mode: Binary or ternary classification mode.
        enforce_one_to_one: Whether to filter positive matches to 1-to-1.

    Returns:
        Tuple of (matches, non_matches, uncertain) DataFrames.
    """
    if candidate_pairs is None or len(candidate_pairs) == 0:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    scored = extract_features_and_score(
        candidate_pairs,
        df_a,
        df_b,
        matching_columns,
    )

    if scored.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    try:
        engine = DynamicThresholdClassificationEngine()
        res = engine.classify(
            scored["aggregate_score"],
            index=scored.index,
            classification_mode=classification_mode,
        )
        if classification_mode == ClassificationMode.BINARY:
            matches = scored.loc[res.predictions == "match"]
            non_matches = scored.loc[res.predictions == "non_match"]
            uncertain = pd.DataFrame()
        else:
            matches = scored.loc[res.predictions == "match"]
            non_matches = scored.loc[res.predictions == "non_match"]
            uncertain = scored.loc[res.predictions == "uncertain"]
    except ValueError as e:
        logger.warning(
            "Dynamic thresholding failed (%s). Falling back to static cutoffs.",
            e,
        )
        matches, non_matches, uncertain = classify_matches(
            scored,
            matching_columns=matching_columns,
        )

    if enforce_one_to_one and not matches.empty:
        scores_series = (
            matches["aggregate_score"]
            if "aggregate_score" in matches.columns
            else pd.Series(1.0, index=matches.index)
        )
        filtered_idx = filter_one_to_one_bipartite(
            matches.index,
            scores_series,
        )
        excluded_idx = matches.index.difference(filtered_idx)
        if not excluded_idx.empty:
            non_matches = pd.concat([non_matches, scored.loc[excluded_idx]])
            matches = scored.loc[filtered_idx]

    return matches, non_matches, uncertain


async def refine_uncertain_matches(
    uncertain_pairs_df: pd.DataFrame,
    df_source_a: pd.DataFrame,
    df_source_b: pd.DataFrame,
    model_name: str = "google-cloud:gemini-3.8-flash",
    provider: str | None = None,
    http_client: httpx.AsyncClient | None = None,
) -> tuple[pd.DataFrame, ExecutionMetadata | None]:
    """Refines uncertain candidate pairs via structured LLM adjudication.

    Args:
        uncertain_pairs_df: DataFrame of uncertain pairs with aggregate_score.
        df_source_a: Original Source A DataFrame.
        df_source_b: Original Source B DataFrame.
        model_name: LLM model name to invoke.
        provider: Swappable LLM provider string.
        http_client: Optional HTTP client.

    Returns:
        Tuple of (confirmed_matches_df, execution_metadata).
    """
    if uncertain_pairs_df.empty:
        return pd.DataFrame(), None

    return await refine_uncertain_matches_via_llm(
        uncertain_pairs_df,
        df_source_a,
        df_source_b,
        model_name=model_name,
        provider=provider,
        http_client=http_client,
    )


async def run_entity_resolution(
    df_a_clean: pd.DataFrame,
    df_b_clean: pd.DataFrame,
    profile_a: TableProfile,
    profile_b: TableProfile,
    table_resource: TableResource,
    override_config: ERPipelineConfiguration | None = None,
    model_name: str = "google-cloud:gemini-3.8-flash",
    provider: str | None = None,
    cleaning_report_a: CleaningReport | None = None,
    cleaning_report_b: CleaningReport | None = None,
    enable_refinement: bool = False,
    http_client: httpx.AsyncClient | None = None,
    enforce_one_to_one: bool = True,
) -> EntityResolutionResult:
    """Executes the complete Entity Resolution pipeline in a single call.

    Args:
        df_a_clean: Cleaned Source A DataFrame.
        df_b_clean: Cleaned Source B DataFrame.
        profile_a: Profile of cleaned Source A.
        profile_b: Profile of cleaned Source B.
        table_resource: Resource describing the logical table and schema.
        override_config: If set, skips LLM config; uses this configuration.
        model_name: LLM model to use if override_config is None.
        provider: Provider name for LLM invocation.
        cleaning_report_a: Optional cleaning report for Source A.
        cleaning_report_b: Optional cleaning report for Source B.
        enable_refinement: If True, performs LLM refinement on uncertain matches.
        http_client: Optional HTTP client for API requests.
        enforce_one_to_one: Whether to enforce 1-to-1 mutual exclusivity.

    Returns:
        Structured EntityResolutionResult with matches and metadata.
    """
    # 1. Configuration
    er_config_metadata = ExecutionMetadata(
        model_name="manual",
        provider="manual",
        execution_time_seconds=0,
        prompt_tokens=0,
        completion_tokens=0,
        total_tokens=0,
    )
    if override_config is not None:
        config = override_config
    else:
        exemplars = extract_exemplar_candidates(df_a_clean, df_b_clean)
        config, er_config_metadata = await identify_er_config_via_llm(
            profile_a,
            profile_b,
            table_resource,
            model_name=model_name,
            provider=provider,
            exemplar_candidates=exemplars,
        )

    # 2. Indexing (TF-IDF Sparse Cosine Similarity)
    with r_console.status(
        "[bold yellow]📦 Indexing: generating candidate pairs via TF-IDF..."
    ):
        try:
            candidate_pairs = execute_tfidf_indexing(
                df_a_clean,
                df_b_clean,
                keys=config.indexing_keys,
                threshold=config.indexing_threshold,
            )
        except (ValueError, KeyError, TypeError, RuntimeError) as e:
            r_console.print(
                f"  └─ [yellow]⚠️ Skipping ER for this table: {e}[/yellow]"
            )
            candidate_pairs = pd.MultiIndex.from_tuples(
                [], names=["left_id", "right_id"]
            )

    # 3. Matching & Classification
    if len(candidate_pairs) == 0:
        matches = pd.DataFrame()
        uncertain = pd.DataFrame()
        non_matches = pd.DataFrame()
        er_refinement_metadata = None
    else:
        with r_console.status(
            "[bold yellow]⚖️  Matching: scoring and classifying pairs..."
        ):
            matches, non_matches, uncertain = score_and_classify_pairs(
                candidate_pairs,
                df_a_clean,
                df_b_clean,
                config.matching_columns,
                classification_mode=ClassificationMode.TERNARY,
                enforce_one_to_one=enforce_one_to_one,
            )

        # 4. Refinement
        er_refinement_metadata = None
        if enable_refinement and not uncertain.empty:
            refined_matches, er_refinement_metadata = (
                await refine_uncertain_matches(
                    uncertain,
                    df_a_clean,
                    df_b_clean,
                    model_name=model_name,
                    provider=provider,
                    http_client=http_client,
                )
            )
            if not refined_matches.empty:
                matches = pd.concat([matches, refined_matches])
                uncertain = uncertain.drop(refined_matches.index)
                if enforce_one_to_one and not matches.empty:
                    scores_series = (
                        matches["aggregate_score"]
                        if "aggregate_score" in matches.columns
                        else pd.Series(1.0, index=matches.index)
                    )
                    filtered_idx = filter_one_to_one_bipartite(
                        matches.index, scores_series
                    )
                    excluded_idx = matches.index.difference(filtered_idx)
                    if not excluded_idx.empty:
                        non_matches = pd.concat(
                            [non_matches, matches.loc[excluded_idx]]
                        )
                        matches = matches.loc[filtered_idx]

    return EntityResolutionResult(
        config=config,
        er_config_metadata=er_config_metadata,
        er_refinement_metadata=er_refinement_metadata,
        profile_a=profile_a,
        profile_b=profile_b,
        df_a_clean=df_a_clean,
        df_b_clean=df_b_clean,
        cleaning_report_a=cleaning_report_a,
        cleaning_report_b=cleaning_report_b,
        candidate_pairs=candidate_pairs,
        matches=matches,
        uncertain=uncertain,
        non_matches=non_matches,
    )
