from unittest.mock import patch

import pytest
from pydantic import ValidationError

from data_fusion.agents import STRATEGY_COMPATIBILITY_MATRIX, FusionPolicyAgent
from data_fusion.models import (
    ColumnConflictProfile,
    ColumnPolicy,
    ConflictSample,
    FusionGroup,
    FusionStrategy,
    MultiTableFusionPolicy,
    MultiTableFusionProfile,
    PhysicalType,
    SemanticType,
    TableFusionPolicy,
    TableFusionProfile,
)
from shared.agents import ExecutionMetadata


@pytest.fixture
def sample_profile() -> TableFusionProfile:
    return TableFusionProfile(
        table_name="users",
        total_pairs=100,
        columns={
            "id": ColumnConflictProfile(
                column_name="id",
                physical_type=PhysicalType.TEXT,
                semantic_type=SemanticType.UUID,
                conflict_rate=0.05,
                source_a_null_rate=0.0,
                source_b_null_rate=0.0,
                source_trust_score=0.9,
                samples=[]
            ),
            "email": ColumnConflictProfile(
                column_name="email",
                physical_type=PhysicalType.TEXT,
                semantic_type=SemanticType.EMAIL,
                conflict_rate=0.15,
                source_a_null_rate=0.02,
                source_b_null_rate=0.01,
                source_trust_score=0.8,
                samples=[ConflictSample(value_a="a@example.com", value_b="a.b@example.com")]
            ),
            "first_name": ColumnConflictProfile(
                column_name="first_name",
                physical_type=PhysicalType.TEXT,
                semantic_type=SemanticType.NONE,
                conflict_rate=0.25,
                source_a_null_rate=0.05,
                source_b_null_rate=0.08,
                source_trust_score=0.7,
                samples=[]
            ),
            "last_name": ColumnConflictProfile(
                column_name="last_name",
                physical_type=PhysicalType.TEXT,
                semantic_type=SemanticType.NONE,
                conflict_rate=0.2,
                source_a_null_rate=0.05,
                source_b_null_rate=0.08,
                source_trust_score=0.7,
                samples=[]
            ),
            "age": ColumnConflictProfile(
                column_name="age",
                physical_type=PhysicalType.FLOAT,
                semantic_type=SemanticType.NONE,
                conflict_rate=0.1,
                source_a_null_rate=0.1,
                source_b_null_rate=0.15,
                source_trust_score=0.6,
                samples=[]
            ),
            "updated_at": ColumnConflictProfile(
                column_name="updated_at",
                physical_type=PhysicalType.DATETIME,
                semantic_type=SemanticType.NONE,
                conflict_rate=0.3,
                source_a_null_rate=0.0,
                source_b_null_rate=0.0,
                source_trust_score=0.5,
                samples=[]
            )
        }
    )

@pytest.fixture
def valid_policy() -> TableFusionPolicy:
    return TableFusionPolicy(
        table_name="users",
        column_policies=[
            ColumnPolicy(
                column_name="id",
                strategy=FusionStrategy.TRUST_SOURCE,
                reasoning="Unique identifier"
            ),
            ColumnPolicy(
                column_name="email",
                strategy=FusionStrategy.FORMAT_PRESERVING,
                reasoning="Validate email format"
            ),
            ColumnPolicy(
                column_name="age",
                strategy=FusionStrategy.NUMERIC_AVG,
                reasoning="Average age if conflicting"
            ),
            ColumnPolicy(
                column_name="updated_at",
                strategy=FusionStrategy.MOST_RECENT,
                reasoning="Get newest timestamp"
            )
        ],
        fusion_groups=[
            FusionGroup(
                group_name="names",
                columns=["first_name", "last_name"],
                leader_column="first_name",
                strategy=FusionStrategy.LONGEST_STRING,
                reasoning="Keep first and last names together based on longer first name"
            )
        ],
        reasoning="Overall table fusion strategy"
    )

def test_strategy_compatibility_matrix():
    # Verify that the matrix maps correctly to expected lists of strategies
    assert FusionStrategy.TRUST_SOURCE in STRATEGY_COMPATIBILITY_MATRIX[PhysicalType.TEXT]
    assert FusionStrategy.COALESCE in STRATEGY_COMPATIBILITY_MATRIX[PhysicalType.TEXT]
    assert FusionStrategy.MOST_RECENT in STRATEGY_COMPATIBILITY_MATRIX[PhysicalType.DATETIME]
    assert FusionStrategy.NUMERIC_AVG in STRATEGY_COMPATIBILITY_MATRIX[PhysicalType.FLOAT]
    
    # Assert restricted strategies are NOT allowed
    assert FusionStrategy.NUMERIC_AVG not in STRATEGY_COMPATIBILITY_MATRIX[PhysicalType.TEXT]
    assert FusionStrategy.MOST_RECENT not in STRATEGY_COMPATIBILITY_MATRIX[PhysicalType.FLOAT]

def test_validation_valid_policy(sample_profile, valid_policy):
    agent = FusionPolicyAgent()
    # Should not raise any exception
    agent._validate_policy(sample_profile, valid_policy)

def test_validation_incompatible_strategy(sample_profile, valid_policy):
    agent = FusionPolicyAgent()
    
    # Change email policy to an incompatible strategy
    valid_policy.column_policies[1].strategy = FusionStrategy.NUMERIC_AVG
    
    with pytest.raises(ValidationError) as excinfo:
        agent._validate_policy(sample_profile, valid_policy)
        
    assert "is not compatible with physical type" in str(excinfo.value)
    assert "email" in str(excinfo.value)

def test_validation_incomplete_coverage(sample_profile, valid_policy):
    agent = FusionPolicyAgent()
    
    # Remove id policy
    valid_policy.column_policies = valid_policy.column_policies[1:]
    
    with pytest.raises(ValidationError) as excinfo:
        agent._validate_policy(sample_profile, valid_policy)
        
    assert "Incomplete column coverage" in str(excinfo.value)
    assert "id" in str(excinfo.value)

def test_validation_overlapping_columns(sample_profile, valid_policy):
    agent = FusionPolicyAgent()
    
    # Add id column to the names fusion group as well (should overlap with standalone id policy)
    valid_policy.fusion_groups[0].columns.append("id")
    
    with pytest.raises(ValidationError) as excinfo:
        agent._validate_policy(sample_profile, valid_policy)
        
    assert "is assigned multiple times" in str(excinfo.value)
    assert "id" in str(excinfo.value)

def test_validation_invalid_group_leader(sample_profile, valid_policy):
    agent = FusionPolicyAgent()
    
    # Set group leader column to a column not in the group's columns list
    # Note: FusionGroup's internal validator already checks that the leader is in 'columns',
    # but we can check what happens if we bypass or force it.
    # To test _validate_policy's logic, we can construct the policy with a leader column not in the profile
    # or a leader column in the group but not compatible.
    # Let's test leader column strategy incompatibility.
    valid_policy.fusion_groups[0].strategy = FusionStrategy.MOST_RECENT # Not compatible with SHORT_TEXT
    
    with pytest.raises(ValidationError) as excinfo:
        agent._validate_policy(sample_profile, valid_policy)
        
    assert "Group strategy" in str(excinfo.value)
    assert "is not compatible with physical type" in str(excinfo.value)

def test_validation_non_existent_column(sample_profile, valid_policy):
    agent = FusionPolicyAgent()
    
    # Add policy for a non-existent column
    valid_policy.column_policies.append(
        ColumnPolicy(
            column_name="non_existent",
            strategy=FusionStrategy.TRUST_SOURCE,
            reasoning="Does not exist"
        )
    )
    
    with pytest.raises(ValidationError) as excinfo:
        agent._validate_policy(sample_profile, valid_policy)
        
    assert "does not exist in the table profile" in str(excinfo.value)
    assert "non_existent" in str(excinfo.value)

@patch("shared.agents.LLMAgent.run_sync")
def test_generate_policy_success(mock_run, sample_profile, valid_policy):
    # Setup mock return value
    mock_run.return_value = (valid_policy, ExecutionMetadata(
        model_name="openai:gpt-4o",
        provider="openai",
        execution_time_seconds=1.2,
        prompt_tokens=100,
        completion_tokens=50,
        total_tokens=150
    ))
    
    multi_profile = MultiTableFusionProfile(
        source_a_origin="source_a",
        source_b_origin="source_b",
        tables={"users": sample_profile}
    )
    
    agent = FusionPolicyAgent()
    multi_policy = agent.generate_policy(multi_profile)
    
    assert isinstance(multi_policy, MultiTableFusionPolicy)
    assert "users" in multi_policy.tables
    assert multi_policy.tables["users"] == valid_policy
    
    # Verify that the LLMAgent run was called with table prompt and deps
    mock_run.assert_called_once()
    args, kwargs = mock_run.call_args
    assert "Define a fusion policy for table 'users'" in args[0]
    assert kwargs["deps"] == sample_profile

@patch("shared.agents.LLMAgent.run_sync")
def test_generate_policy_validation_failure(mock_run, sample_profile, valid_policy):
    # Make policy invalid (e.g. incompatible strategy)
    valid_policy.column_policies[1].strategy = FusionStrategy.NUMERIC_AVG
    
    mock_run.return_value = (valid_policy, ExecutionMetadata(
        model_name="openai:gpt-4o",
        provider="openai",
        execution_time_seconds=1.2,
        prompt_tokens=100,
        completion_tokens=50,
        total_tokens=150
    ))
    
    multi_profile = MultiTableFusionProfile(
        source_a_origin="source_a",
        source_b_origin="source_b",
        tables={"users": sample_profile}
    )
    
    agent = FusionPolicyAgent()
    
    with pytest.raises(ValidationError) as excinfo:
        agent.generate_policy(multi_profile)
        
    assert "is not compatible with physical type" in str(excinfo.value)
    assert "email" in str(excinfo.value)


@patch("shared.agents.LLMAgent.run_sync")
def test_generate_policy_skips_empty_table(mock_run):
    empty_profile = TableFusionProfile(
        table_name="departments",
        total_pairs=0,
        columns={}
    )
    multi_profile = MultiTableFusionProfile(
        source_a_origin="source_a",
        source_b_origin="source_b",
        tables={"departments": empty_profile}
    )

    agent = FusionPolicyAgent()
    policy, metadata = agent.generate_policy(multi_profile, return_metadata=True)

    # LLM should not be called
    mock_run.assert_not_called()
    assert "departments" in policy.tables
    dept_policy = policy.tables["departments"]
    assert dept_policy.table_name == "departments"
    assert dept_policy.column_policies == []
    assert dept_policy.fusion_groups == []
    assert metadata["departments"].total_tokens == 0

