from typing import Any, TypeVar

import httpx
import pandas as pd
from dotenv import load_dotenv
from pydantic import BaseModel

# Load environment variables from .env file
load_dotenv()

from shared.agents import ExecutionMetadata, LLMAgent
from shared.profiling.models import TableProfile

from .models import (
    BatchMatchResolution,
    ERPipelineConfiguration,
    MatchResolution,
    TableResource,
)
from .prompts import ER_CONFIG_SYSTEM_PROMPT, REFINEMENT_SYSTEM_PROMPT

LLM_REFINEMENT_BATCH_SIZE: int = 200

def _build_comparative_prompt(
    profile_a: TableProfile,
    profile_b: TableProfile,
    table_resource: TableResource,
    exemplar_candidates: list[dict[str, tuple[str, str]]] | None = None,
) -> str:
    """Builds markdown comparative prompt with exemplar matches."""
    fields = table_resource.schema_info.fields
    profile_rows = []

    primary_exemplar = exemplar_candidates[0] if exemplar_candidates else None

    for field in fields:
        col = field.name
        stats_a = profile_a.column_profiles.get(col)
        stats_b = profile_b.column_profiles.get(col)

        if not stats_a and not stats_b:
            continue

        null_a = f"{stats_a.null_percentage}%" if stats_a else "N/A"
        null_b = f"{stats_b.null_percentage}%" if stats_b else "N/A"
        null_ab = f"{null_a} | {null_b}"

        unique_a = f"{stats_a.uniqueness_percentage}%" if stats_a else "N/A"
        unique_b = f"{stats_b.uniqueness_percentage}%" if stats_b else "N/A"
        unique_ab = f"{unique_a} | {unique_b}"

        card_a = f"{stats_a.cardinality}" if stats_a else "N/A"
        card_b = f"{stats_b.cardinality}" if stats_b else "N/A"
        card_ab = f"{card_a} | {card_b}"

        len_a = (
            f"{stats_a.avg_length}"
            if stats_a and stats_a.avg_length is not None
            else "N/A"
        )
        len_b = (
            f"{stats_b.avg_length}"
            if stats_b and stats_b.avg_length is not None
            else "N/A"
        )
        avg_len_ab = f"{len_a} | {len_b}"

        if primary_exemplar and col in primary_exemplar:
            val_a, val_b = primary_exemplar[col]
            str_a = f'"{val_a}"' if val_a else '""'
            str_b = f'"{val_b}"' if val_b else '""'
            aligned_match = f"{str_a} ↔ {str_b}"
        else:
            aligned_match = "N/A"

        profile_rows.append(
            f"| **{col}** | {null_ab} | {unique_ab} | {card_ab} | "
            f"{avg_len_ab} | {aligned_match} |"
        )

    profile_table = "\n".join(profile_rows)

    desc_lines = []
    for field in fields:
        if field.description:
            desc_lines.append(f"- **{field.name}**: {field.description}")

    section_idx = 2
    semantic_section = ""
    if desc_lines:
        semantic_section = (
            f"\n### {section_idx}. Semantic Column Descriptions\n"
            + "\n".join(desc_lines)
            + "\n"
        )
        section_idx += 1

    exemplar_section = ""
    if exemplar_candidates:
        ex_lines = [
            (
                f"\n### {section_idx}. Exemplar Candidate Matches "
                "(High-Confidence Entity Pairs)"
            ),
            (
                "The following candidate pairs were discovered via holistic "
                "zero-configuration row-level textual overlap."
            ),
            (
                "Inspect how field values, units, abbreviations, typos, and "
                "taxonomies vary across matching records:\n"
            ),
        ]
        for idx, candidate in enumerate(exemplar_candidates, start=1):
            score = getattr(candidate, "score", None)
            score_str = (
                f" (Overall Text Match Score: {score:.2f})"
                if score is not None and score > 0
                else ""
            )
            ex_lines.append(f"#### Candidate Match {idx}{score_str}")
            ex_lines.append("| Column | Value in Source A | Value in Source B |")
            ex_lines.append("| :--- | :--- | :--- |")
            for field in fields:
                col = field.name
                if col in candidate:
                    val_a, val_b = candidate[col]
                    str_a = f'"{val_a}"' if val_a else '""'
                    str_b = f'"{val_b}"' if val_b else '""'
                    ex_lines.append(f"| {col} | {str_a} | {str_b} |")
            ex_lines.append("")
        exemplar_section = "\n".join(ex_lines)
        section_idx += 1

    return f"""### 1. Dataset Comparison Summary
| Metric | Source A | Source B |
| :--- | :--- | :--- |
| **Total Rows** | {profile_a.total_rows} | {profile_b.total_rows} |
| **Column Count** | {profile_a.total_columns} | {profile_b.total_columns} |
{semantic_section}{exemplar_section}
### {section_idx}. Integrated Column Profile (Comparison)
| Column | Null % (A|B) | Unique % (A|B) | Card. (A|B) | Avg Len (A|B) | Aligned Match (Source A ↔ Source B) |
| :--- | :--- | :--- | :--- | :--- | :--- |
{profile_table}
"""


async def identify_er_config_via_llm(
    profile_a: TableProfile, 
    profile_b: TableProfile,
    table_resource: TableResource,
    model_name: str = 'google-cloud:gemini-3.8-flash',
    provider: str | None = None,
    exemplar_candidates: list[dict[str, tuple[str, str]]] | None = None,
) -> tuple[ERPipelineConfiguration, ExecutionMetadata]:
    """Uses a Pydantic AI agent to dynamically select ER configuration."""
    agent = LLMAgent(
        name="ERPipelineConfiguration",
        response_model=ERPipelineConfiguration,
        system_prompt=ER_CONFIG_SYSTEM_PROMPT,
        model_name=model_name,
        provider=provider,
    )
    user_prompt = _build_comparative_prompt(
        profile_a, profile_b, table_resource, exemplar_candidates
    )
    output, metadata = await agent.run(user_prompt)
    return output, metadata


T = TypeVar("T", bound=BaseModel)


async def identify_indexing_config_via_llm(
    profile_a: TableProfile,
    profile_b: TableProfile,
    table_resource: TableResource,
    config_schema: type[T],
    system_prompt: str,
    model_name: str = "google-cloud:gemini-3.8-flash",
    provider: str | None = None,
    exemplar_candidates: list[dict[str, tuple[str, str]]] | None = None,
) -> tuple[T, ExecutionMetadata]:
    """Uses a Pydantic AI agent to dynamically generate an indexing/matching configuration."""
    agent = LLMAgent(
        name=f"IndexingConfig::{config_schema.__name__}",
        response_model=config_schema,
        system_prompt=system_prompt,
        model_name=model_name,
        provider=provider,
    )
    user_prompt = _build_comparative_prompt(
        profile_a, profile_b, table_resource, exemplar_candidates
    )
    output, metadata = await agent.run(user_prompt)
    return output, metadata


async def refine_uncertain_matches_via_llm(

    uncertain_pairs_df: pd.DataFrame,
    df_source_a: pd.DataFrame,
    df_source_b: pd.DataFrame,
    model_name: str = 'google-cloud:gemini-3.8-flash',
    provider: str | None = None,
    batch_size: int = LLM_REFINEMENT_BATCH_SIZE,
    http_client: httpx.AsyncClient | None = None
) -> tuple[dict[tuple[Any, Any], MatchResolution], ExecutionMetadata]:
    """
    Takes the pairs classified as "uncertain" by the deterministic matching phase 
    and uses an LLM to make a final binary decision (Match/No Match).
    Returns a mapping of (idx_a, idx_b) -> MatchResolution and aggregated metadata.
    """
    
    if uncertain_pairs_df.empty:
        return {}, ExecutionMetadata(
            model_name=model_name,
            provider="unknown",
            execution_time_seconds=0,
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0
        )
        
    agent = LLMAgent(
        name="UncertainMatchesRefinement",
        response_model=BatchMatchResolution,
        system_prompt=REFINEMENT_SYSTEM_PROMPT,
        model_name=model_name,
        provider=provider,
        http_client=http_client
    )
    
    all_pairs = list(uncertain_pairs_df.index)
    
    # Chunk pairs into batches
    batches = [all_pairs[i:i + batch_size] for i in range(0, len(all_pairs), batch_size)]
    
    resolutions_map = {}
    agg_metadata = ExecutionMetadata(
        model_name=model_name,
        provider=provider or "unknown",
        execution_time_seconds=0,
        prompt_tokens=0,
        completion_tokens=0,
        total_tokens=0
    )
    
    # Process batches sequentially
    for batch in batches:
        # Build a combined prompt for all pairs in the batch
        comparison_prompt = "Please evaluate if the following candidate pairs represent the same entity:\n\n"
        
        for item in batch:
            index_a, index_b = item
            pair_id = f"{index_a}|||{index_b}"
            
            row_a = df_source_a.loc[index_a].to_dict()
            row_b = df_source_b.loc[index_b].to_dict()
            
            comparison_prompt += f"--- Pair ID: {pair_id} ---\n"
            comparison_prompt += "Record A:\n"
            for k, v in row_a.items():
                comparison_prompt += f"  - {k}: {v}\n"
                
            comparison_prompt += "Record B:\n"
            for k, v in row_b.items():
                comparison_prompt += f"  - {k}: {v}\n"
                
            comparison_prompt += "\n"
            
        output, batch_metadata = await agent.run(comparison_prompt)
        
        # Aggregate metadata
        agg_metadata.execution_time_seconds += batch_metadata.execution_time_seconds
        agg_metadata.prompt_tokens += batch_metadata.prompt_tokens
        agg_metadata.completion_tokens += batch_metadata.completion_tokens
        agg_metadata.total_tokens += batch_metadata.total_tokens
        agg_metadata.cached_tokens += batch_metadata.cached_tokens
        agg_metadata.reasoning_tokens += batch_metadata.reasoning_tokens
        agg_metadata.accepted_prediction_tokens += batch_metadata.accepted_prediction_tokens
        agg_metadata.rejected_prediction_tokens += batch_metadata.rejected_prediction_tokens
        agg_metadata.prompt_audio_tokens += batch_metadata.prompt_audio_tokens
        agg_metadata.completion_audio_tokens += batch_metadata.completion_audio_tokens
        
        for res in output.resolutions:
            idx_a_str, idx_b_str = res.pair_id.split("|||")
            try:
                idx_a = type(df_source_a.index[0])(idx_a_str)
                idx_b = type(df_source_b.index[0])(idx_b_str)
            except (ValueError, TypeError, IndexError):
                idx_a = idx_a_str
                idx_b = idx_b_str
            resolutions_map[(idx_a, idx_b)] = res
                
    return resolutions_map, agg_metadata
