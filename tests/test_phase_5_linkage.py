from unittest.mock import MagicMock

import pandas as pd
import pytest

from entity_resolution.models import EntityResolutionResult, ERPipelineConfiguration
from pipeline.gui.phases.phase_5_linkage import load_pair_at
from shared.agents import ExecutionMetadata


def test_load_pair_at_basic():
    # 1. Setup sample cleaner dataframes
    df_a = pd.DataFrame({"id": ["a1", "a2"], "name": ["Alice", "Bob"]}, index=["a1", "a2"])
    df_b = pd.DataFrame({"id": ["b1", "b2"], "name": ["Alicia", "Bobby"]}, index=["b1", "b2"])
    
    # 2. Setup mock matches, uncertain, non_matches indices and dfs
    idx_matches = pd.MultiIndex.from_tuples([("a1", "b1")], names=["left_id", "right_id"])
    idx_uncertain = pd.MultiIndex.from_tuples([("a2", "b2")], names=["left_id", "right_id"])
    idx_non_matches = pd.MultiIndex.from_tuples([], names=["left_id", "right_id"])
    
    df_matches = pd.DataFrame({"aggregate_score": [0.9]}, index=idx_matches)
    df_uncertain = pd.DataFrame({"aggregate_score": [0.55]}, index=idx_uncertain)
    df_non_matches = pd.DataFrame(columns=["aggregate_score"], index=idx_non_matches)
    
    er_config = ERPipelineConfiguration(
        indexing_keys=["name"],
        indexing_threshold=0.10,
        matching_columns={"name": {"algorithm": "jarowinkler", "weight": 1.0}},
        reasoning="test"
    )
    
    result = EntityResolutionResult(
        config=er_config,
        er_config_metadata=ExecutionMetadata(model_name="m", provider="p", execution_time_seconds=1, prompt_tokens=1, completion_tokens=1, total_tokens=2),
        profile_a=MagicMock(),
        profile_b=MagicMock(),
        df_a_clean=df_a,
        df_b_clean=df_b,
        matches=df_matches,
        uncertain=df_uncertain,
        non_matches=df_non_matches,
        candidate_pairs=pd.MultiIndex.from_tuples([("a1", "b1"), ("a2", "b2")])
    )
    
    # Test loading matches bucket index 0
    (
        comp_df, pair_header_md, pair_label, pair_id,
        llm_visible, llm_md, accept_btn_visible,
        match_btn_vis, uncertain_btn_vis, non_match_btn_vis,
        first_ia, prev_ia, next_ia, last_ia
    ) = load_pair_at(result, "matches", 0)
    
    assert pair_id == ("a1", "b1")
    assert "Alice" in comp_df.iloc[0].values or "Alice" in comp_df.iloc[1].values
    assert "**Score**: 0.9000" in pair_header_md
    assert pair_label == "Pair 1 of 1"
    assert match_btn_vis is False
    assert uncertain_btn_vis is True
    assert non_match_btn_vis is True
    assert first_ia is False
    assert prev_ia is False
    assert next_ia is False
    assert last_ia is False

def test_load_pair_at_empty_and_out_of_bounds():
    df_a = pd.DataFrame({"id": ["a1"], "name": ["Alice"]}, index=["a1"])
    df_b = pd.DataFrame({"id": ["b1"], "name": ["Alicia"]}, index=["b1"])
    
    er_config = ERPipelineConfiguration(
        indexing_keys=["name"],
        indexing_threshold=0.10,
        matching_columns={"name": {"algorithm": "jarowinkler", "weight": 1.0}},
        reasoning="test"
    )
    
    result = EntityResolutionResult(
        config=er_config,
        er_config_metadata=ExecutionMetadata(model_name="m", provider="p", execution_time_seconds=1, prompt_tokens=1, completion_tokens=1, total_tokens=2),
        profile_a=MagicMock(),
        profile_b=MagicMock(),
        df_a_clean=df_a,
        df_b_clean=df_b,
        matches=pd.DataFrame(columns=["aggregate_score"], index=pd.MultiIndex.from_tuples([], names=["left_id", "right_id"])),
        uncertain=pd.DataFrame(columns=["aggregate_score"], index=pd.MultiIndex.from_tuples([], names=["left_id", "right_id"])),
        non_matches=pd.DataFrame(columns=["aggregate_score"], index=pd.MultiIndex.from_tuples([], names=["left_id", "right_id"])),
        candidate_pairs=pd.MultiIndex.from_tuples([], names=["left_id", "right_id"])
    )
    
    # Test loading empty matches bucket
    (
        comp_df, pair_header_md, pair_label, pair_id,
        llm_visible, llm_md, accept_btn_visible,
        match_btn_vis, uncertain_btn_vis, non_match_btn_vis,
        first_ia, prev_ia, next_ia, last_ia
    ) = load_pair_at(result, "matches", 0)
    
    assert len(comp_df) == 0
    assert pair_header_md == ""
    assert pair_label == "Pair 0 of 0"
    assert pair_id is None
    assert match_btn_vis is False
    assert uncertain_btn_vis is False
    assert non_match_btn_vis is False


@pytest.mark.asyncio
async def test_refine_uncertain_matches_via_llm():
    # Mock LLMAgent
    from unittest.mock import AsyncMock, patch

    import pandas as pd

    from entity_resolution.agents import refine_uncertain_matches_via_llm
    from entity_resolution.models import BatchMatchResolution, MatchResolution
    from shared.agents import ExecutionMetadata
    
    df_uncertain = pd.DataFrame({"aggregate_score": [0.6, 0.7]}, index=pd.MultiIndex.from_tuples([("a1", "b1"), ("a2", "b2")]))
    df_a = pd.DataFrame({"name": ["Alice", "Bob"]}, index=["a1", "a2"])
    df_b = pd.DataFrame({"name": ["Alicia", "Bobby"]}, index=["b1", "b2"])
    
    mock_resolutions = [
        MatchResolution(pair_id="a1|||b1", is_match=True, reasoning="Good match"),
        MatchResolution(pair_id="a2|||b2", is_match=False, reasoning="Not a match")
    ]
    mock_batch_res = BatchMatchResolution(resolutions=mock_resolutions)
    mock_metadata = ExecutionMetadata(
        model_name="test-model", provider="test-provider", execution_time_seconds=1.0,
        prompt_tokens=10, completion_tokens=5, total_tokens=15
    )
    
    with patch("entity_resolution.agents.LLMAgent") as MockLLMAgent:
        instance = MockLLMAgent.return_value
        instance.run = AsyncMock(return_value=(mock_batch_res, mock_metadata))
        instance.model_name = "test-model"
        instance.provider = "test-provider"
        
        # Test sequential batching with batch_size=1, should result in 2 runs
        res_map, meta = await refine_uncertain_matches_via_llm(
            df_uncertain, df_a, df_b, model_name="test-model", provider="test-provider", batch_size=1
        )
        
        assert len(res_map) == 2
        assert ("a1", "b1") in res_map
        assert ("a2", "b2") in res_map
        assert res_map[("a1", "b1")].is_match is True
        assert res_map[("a2", "b2")].is_match is False
        
        # Sequential check: instance.run should have been called twice (one for each batch of size 1)
        assert instance.run.call_count == 2
        assert meta.prompt_tokens == 20
        assert meta.completion_tokens == 10
        assert meta.total_tokens == 30

def test_handle_llm_refinement():
    from unittest.mock import MagicMock, patch

    import pandas as pd

    from entity_resolution.models import (
        EntityResolutionResult,
        ERPipelineConfiguration,
        MatchResolution,
    )
    from pipeline.gui.handlers import handle_llm_refinement
    from shared.agents import ExecutionMetadata
    
    df_uncertain = pd.DataFrame({"aggregate_score": [0.6, 0.7]}, index=pd.MultiIndex.from_tuples([("a1", "b1"), ("a2", "b2")]))
    df_a = pd.DataFrame({"name": ["Alice", "Bob"]}, index=["a1", "a2"])
    df_b = pd.DataFrame({"name": ["Alicia", "Bobby"]}, index=["b1", "b2"])
    
    er_config = ERPipelineConfiguration(
        indexing_keys=["name"],
        indexing_threshold=0.10,
        matching_columns={"name": {"algorithm": "jarowinkler", "weight": 1.0}},
        reasoning="test"
    )
    
    result = EntityResolutionResult(
        config=er_config,
        er_config_metadata=ExecutionMetadata(model_name="m", provider="p", execution_time_seconds=1, prompt_tokens=1, completion_tokens=1, total_tokens=2),
        profile_a=MagicMock(),
        profile_b=MagicMock(),
        df_a_clean=df_a,
        df_b_clean=df_b,
        matches=pd.DataFrame(columns=["aggregate_score"], index=pd.MultiIndex.from_tuples([], names=["left_id", "right_id"])),
        uncertain=df_uncertain.copy(),
        non_matches=pd.DataFrame(columns=["aggregate_score"], index=pd.MultiIndex.from_tuples([], names=["left_id", "right_id"])),
        candidate_pairs=pd.MultiIndex.from_tuples([("a1", "b1"), ("a2", "b2")])
    )
    
    mock_resolutions_map = {
        ("a1", "b1"): MatchResolution(pair_id="a1|||b1", is_match=True, reasoning="Good match"),
        ("a2", "b2"): MatchResolution(pair_id="a2|||b2", is_match=False, reasoning="Not a match")
    }
    mock_metadata = ExecutionMetadata(
        model_name="test-model", provider="test-provider", execution_time_seconds=1.0,
        prompt_tokens=10, completion_tokens=5, total_tokens=15
    )
    
    with patch("pipeline.gui.handlers.refine_uncertain_matches_via_llm") as mock_refine:
        mock_refine.return_value = (mock_resolutions_map, mock_metadata)
        
        updated_res, log_msg = handle_llm_refinement(result, "test-model", "test-provider")
        
        assert "llm_decision" in updated_res.uncertain.columns
        assert "llm_reasoning" in updated_res.uncertain.columns
        
        assert updated_res.uncertain.loc[("a1", "b1"), "llm_decision"] == True
        assert updated_res.uncertain.loc[("a1", "b1"), "llm_reasoning"] == "Good match"
        
        assert updated_res.uncertain.loc[("a2", "b2"), "llm_decision"] == False
        assert updated_res.uncertain.loc[("a2", "b2"), "llm_reasoning"] == "Not a match"
        
        assert "LLM refined 2 pairs" in log_msg

def test_load_pair_at_with_llm_columns():
    df_a = pd.DataFrame({"name": ["Alice", "Bob"]}, index=["a1", "a2"])
    df_b = pd.DataFrame({"name": ["Alicia", "Bobby"]}, index=["b1", "b2"])
    
    er_config = ERPipelineConfiguration(
        indexing_keys=["name"],
        indexing_threshold=0.10,
        matching_columns={"name": {"algorithm": "jarowinkler", "weight": 1.0}},
        reasoning="test"
    )
    
    idx_uncertain = pd.MultiIndex.from_tuples([("a1", "b1"), ("a2", "b2")])
    df_uncertain = pd.DataFrame({
        "aggregate_score": [0.9, 0.5],
        "llm_decision": [True, False],
        "llm_reasoning": ["Reason A", "Reason B"]
    }, index=idx_uncertain)
    
    result = EntityResolutionResult(
        config=er_config,
        er_config_metadata=ExecutionMetadata(model_name="m", provider="p", execution_time_seconds=1, prompt_tokens=1, completion_tokens=1, total_tokens=2),
        profile_a=MagicMock(),
        profile_b=MagicMock(),
        df_a_clean=df_a,
        df_b_clean=df_b,
        matches=pd.DataFrame(columns=["aggregate_score"], index=pd.MultiIndex.from_tuples([], names=["left_id", "right_id"])),
        uncertain=df_uncertain,
        non_matches=pd.DataFrame(columns=["aggregate_score"], index=pd.MultiIndex.from_tuples([], names=["left_id", "right_id"])),
        candidate_pairs=idx_uncertain
    )
    
    # Check loading pair 0: has true match suggestion
    (
        comp_df, pair_header_md, pair_label, pair_id,
        llm_visible, llm_md, accept_btn_visible,
        match_btn_vis, uncertain_btn_vis, non_match_btn_vis,
        first_ia, prev_ia, next_ia, last_ia
    ) = load_pair_at(result, "uncertain", 0)
    
    assert llm_visible is True
    assert accept_btn_visible is True
    assert "Match" in llm_md
    assert "Reason A" in llm_md
    assert next_ia is True  # Since there's pair at index 1


