import json
from pydantic import ValidationError
from typing import Any, List, Dict, Optional, Tuple
from pydantic_ai import RunContext

from shared.agents import ExecutionMetadata, LLMAgent
from data_fusion.models import (
    MultiTableFusionProfile, TableFusionProfile, MultiTableFusionPolicy, TableFusionPolicy,
    FusionStrategy, SemanticType, ColumnPolicy, FusionGroup, PhysicalType
)

# Strategy Compatibility Matrix
STRATEGY_COMPATIBILITY_MATRIX = {
    PhysicalType.INTEGER: [
        FusionStrategy.TRUST_SOURCE,
        FusionStrategy.COALESCE,
        FusionStrategy.NUMERIC_MAX,
        FusionStrategy.NUMERIC_MIN,
    ],
    PhysicalType.FLOAT: [
        FusionStrategy.TRUST_SOURCE,
        FusionStrategy.COALESCE,
        FusionStrategy.NUMERIC_MAX,
        FusionStrategy.NUMERIC_MIN,
        FusionStrategy.NUMERIC_AVG,
    ],
    PhysicalType.BOOLEAN: [
        FusionStrategy.TRUST_SOURCE,
        FusionStrategy.COALESCE,
    ],
    PhysicalType.DATETIME: [
        FusionStrategy.TRUST_SOURCE,
        FusionStrategy.COALESCE,
        FusionStrategy.MOST_RECENT,
    ],
    PhysicalType.TEXT: [
        FusionStrategy.TRUST_SOURCE,
        FusionStrategy.COALESCE,
        FusionStrategy.LONGEST_STRING,
        FusionStrategy.SHORTEST_STRING,
        FusionStrategy.UNION,
        FusionStrategy.INTERSECTION,
        FusionStrategy.MOST_WORDS,
    ],
}

class FusionPolicyAgent:
    def __init__(self, model_name: str = "gemini-3.8-flash", provider: Optional[str] = None):
        self.system_prompt = self._build_system_prompt()
        self.last_metadata: Dict[str, ExecutionMetadata] = {}
        # Initialize LLMAgent mapping output to TableFusionPolicy
        self.agent = LLMAgent[TableFusionProfile, TableFusionPolicy](
            name="FusionPolicyAgent",
            provider=provider,
            model_name=model_name,
            response_model=TableFusionPolicy,
            system_prompt=self.system_prompt,
            deps_type=TableFusionProfile,
            retries=0  #No automatic retries, raise immediately on invalid output
        )
        
        # Register output validator
        @self.agent.output_validator
        def validate_policy_output(ctx: RunContext[TableFusionProfile], policy: TableFusionPolicy) -> TableFusionPolicy:
            self._validate_policy(ctx.deps, policy)
            return policy

    def _build_system_prompt(self) -> str:
        # Stringify STRATEGY_COMPATIBILITY_MATRIX
        matrix_lines = []
        for phys_type, strategies in STRATEGY_COMPATIBILITY_MATRIX.items():
            strats_str = ", ".join([s.value for s in strategies])
            matrix_lines.append(f"- **{phys_type.value}**: {strats_str}")
        matrix_str = "\n".join(matrix_lines)

        return f"""You are an expert Data Integration Engineer tasked with defining a TableFusionPolicy for a database table.
A TableFusionPolicy maps every column in a table to a specific ResolutionStrategy, either as a standalone policy or as part of a FusionGroup.

Your goal is to choose the most appropriate resolution strategy for each column to merge conflicting records from two sources while:
1. Ensuring data quality and coherence (preventing "Frankenstein records").
2. Adhering strictly to the Strategy Compatibility Matrix.
3. Making sure 100% of columns are covered exactly once.

### Strategy Compatibility Matrix
Only select strategies compatible with each column's Physical Type as defined below:
{matrix_str}

*Note: The format_preserving strategy is also eligible, but ONLY for columns with physical type TEXT where semantic type is NOT NONE (i.e. EMAIL, PHONE, URL, GEOSPATIAL, UUID).*

### Primary Objective: Attribute-Level Conflict Resolution
The primary objective of Data Fusion is **attribute-level conflict resolution**, selecting the optimal and most accurate value for each individual attribute independently. Columns describing the same entity are normally independent and should be resolved separately with standalone column policies unless a strict atomic dependency exists between them.

### Fusion Groups Rules
A Fusion Group is strictly defined as an **atomic, indivisible unit with strong functional, physical, or mathematical dependency** where combining values from different sources creates an impossible, contradictory, or nonsensical entity state. When grouped, all member columns resolve jointly from the single winning source determined by the designated `leader_column`.

#### The Independent Validity Test (CRITICAL)
Before creating any Fusion Group, you MUST apply this test:
> "Before creating a Fusion Group, ask: If Source A provides the optimal value for Column 1, and Source B provides the optimal value for Column 2, does combining them result in an impossible, contradictory, or corrupted entity? If NO, DO NOT group them."

#### When to Group (Valid Atomic Clusters)
Only create a Fusion Group when an unbreakable atomic dependency exists:
- **Coupled Physical/Spatial Coordinates**: e.g., `coordinate_lat` + `coordinate_lon`, or `x_pos` + `y_pos`.
- **Value and Unit Pairs**: e.g., `amount` + `currency`, `weight` + `weight_unit`, `dimension_length` + `measurement_unit`.
- **Atomic Compound Address Components**: e.g., `street_address` + `postal_code` + `city` where postal codes are strictly bound to specific streets.
- **Person Name Components**: `first_name`, `last_name`, `middle_name`, `honorific_salutation` (e.g., Dr./Mr./Ms.) should be grouped. Do NOT confuse honorific salutations with work titles, article titles, or role descriptions.
- **Mathematical Dependencies**: Columns tied by strict arithmetic relationships where values must originate from the exact same temporal snapshot.

#### Negative Rules (When NOT to Group - Strict Restrictions)
- **Do NOT group independent descriptive attributes**: Attributes that describe different aspects of an entity (e.g., identifier vs description, creation vs creator, dimensions vs category, status vs notes) MUST be resolved independently. Taking a more complete description from Source A and a cleaner name/title from Source B is valid and preferred.
- **Do NOT group multi-valued or set attributes**: Multi-valued attributes (e.g., list of contributors, tags, classifications) must remain separate to allow set-based resolution strategies (such as union or intersection).
- **Do NOT group primary entity identifiers with descriptive attributes**: Keys, IDs, or codes (`primary_record_id`, `code`, `uuid`) must never be grouped with descriptive or metadata columns.
- **Default to standalone policies**: When in doubt, do NOT create a Fusion Group. Standalone column resolution is the expected standard.

For each Fusion Group:
- You must designate a `leader_column` that belongs to the group.
- The `strategy` of the group is applied to the `leader_column` to decide the winning source for the entire group.
- The leader column should be the most discriminative/trustworthy column in the group (usually the one with higher conflict rate or clearer data).
- The strategy for the group must be compatible with the leader column's physical type (or semantic type check for format_preserving).
- Must contain ≥2 columns (use standalone policies for single columns).

### General Policy Requirements
- Every single column from the input table profile MUST be covered.
- No column may be covered more than once (e.g. cannot be in a standalone policy and a fusion group, or in multiple fusion groups).
- All strategy assignments must be compatible with the corresponding column's (or leader column's) physical type.
"""

    def _construct_table_prompt(self, profile: TableFusionProfile) -> str:
        prompt = f"Define a fusion policy for table '{profile.table_name}'.\n"
        prompt += f"Total record pairs to merge: {profile.total_pairs}\n\n"
        prompt += "Columns metadata:\n"
        for col_name, col_profile in profile.columns.items():
            prompt += f"- **Column**: {col_name}\n"
            prompt += f"  - Physical Type: {col_profile.physical_type.value}\n"
            prompt += f"  - Semantic Type: {col_profile.semantic_type.value}\n"
            prompt += f"  - Conflict Rate: {col_profile.conflict_rate:.2%}\n"
            prompt += f"  - Source A Null Rate: {col_profile.source_a_null_rate:.2%}\n"
            prompt += f"  - Source B Null Rate: {col_profile.source_b_null_rate:.2%}\n"
            prompt += f"  - Source Trust Score: {col_profile.source_trust_score:.2f}\n"
            
            # Eligible strategies
            eligible = list(STRATEGY_COMPATIBILITY_MATRIX.get(col_profile.physical_type, []))
            if col_profile.physical_type == PhysicalType.TEXT and col_profile.semantic_type != SemanticType.NONE:
                eligible.append(FusionStrategy.FORMAT_PRESERVING)
            eligible_str = ", ".join([s.value for s in eligible])
            prompt += f"  - Eligible Strategies: {eligible_str}\n"
            
            if col_profile.samples:
                prompt += "  - Sample Conflict Pairs:\n"
                for sample in col_profile.samples[:3]:
                    prompt += f"    - Source A: {sample.value_a} | Source B: {sample.value_b}\n"
            prompt += "\n"
        
        prompt += "Analyze the table profile above. Construct the TableFusionPolicy, identifying any necessary fusion groups (with leader column and compatible strategy), and assigning standalone column policies for all other columns."
        return prompt

    def _validate_policy(self, profile: TableFusionProfile, policy: TableFusionPolicy) -> None:
        errors = []
        profile_columns = set(profile.columns.keys())
        assigned_columns: Dict[str, str] = {}  # col_name -> source of assignment (standalone or group name)
        
        # 1. Validate standalone column policies
        for idx, cp in enumerate(policy.column_policies):
            col = cp.column_name
            if col not in profile_columns:
                errors.append({
                    "type": "value_error",
                    "loc": ("column_policies", idx, "column_name"),
                    "input": col,
                    "ctx": {"error": ValueError(f"Column '{col}' does not exist in the table profile.")}
                })
                continue
            
            # Check strategy compatibility
            col_prof = profile.columns[col]
            phys_type = col_prof.physical_type
            sem_type = col_prof.semantic_type
            allowed_strategies = list(STRATEGY_COMPATIBILITY_MATRIX.get(phys_type, []))
            if phys_type == PhysicalType.TEXT and sem_type != SemanticType.NONE:
                allowed_strategies.append(FusionStrategy.FORMAT_PRESERVING)
            if cp.strategy not in allowed_strategies:
                errors.append({
                    "type": "value_error",
                    "loc": ("column_policies", idx, "strategy"),
                    "input": cp.strategy.value,
                    "ctx": {"error": ValueError(f"Strategy '{cp.strategy}' is not compatible with physical type '{phys_type}' (semantic type '{sem_type}') of column '{col}'.")}
                })
            
            # Track assignment for overlap checks
            if col in assigned_columns:
                errors.append({
                    "type": "value_error",
                    "loc": ("column_policies", idx, "column_name"),
                    "input": col,
                    "ctx": {"error": ValueError(f"Column '{col}' is assigned multiple times. Already assigned to: {assigned_columns[col]}.")}
                })
            else:
                assigned_columns[col] = "standalone"
                
        # 2. Validate fusion groups
        for g_idx, fg in enumerate(policy.fusion_groups):
            # Check leader column
            leader = fg.leader_column
            if leader not in fg.columns:
                errors.append({
                    "type": "value_error",
                    "loc": ("fusion_groups", g_idx, "leader_column"),
                    "input": leader,
                    "ctx": {"error": ValueError(f"Leader column '{leader}' must be one of the group columns: {fg.columns}.")}
                })
            
            if leader not in profile_columns:
                errors.append({
                    "type": "value_error",
                    "loc": ("fusion_groups", g_idx, "leader_column"),
                    "input": leader,
                    "ctx": {"error": ValueError(f"Leader column '{leader}' does not exist in the table profile.")}
                })
            else:
                # Check group strategy compatibility with the leader column
                leader_prof = profile.columns[leader]
                leader_phys_type = leader_prof.physical_type
                leader_sem_type = leader_prof.semantic_type
                allowed_strategies = list(STRATEGY_COMPATIBILITY_MATRIX.get(leader_phys_type, []))
                if leader_phys_type == PhysicalType.TEXT and leader_sem_type != SemanticType.NONE:
                    allowed_strategies.append(FusionStrategy.FORMAT_PRESERVING)
                if fg.strategy not in allowed_strategies:
                    errors.append({
                        "type": "value_error",
                        "loc": ("fusion_groups", g_idx, "strategy"),
                        "input": fg.strategy.value,
                        "ctx": {"error": ValueError(f"Group strategy '{fg.strategy}' is not compatible with physical type '{leader_phys_type}' (semantic type '{leader_sem_type}') of leader column '{leader}'.")}
                    })
            
            # Check all columns in group
            for col_idx, col in enumerate(fg.columns):
                if col not in profile_columns:
                    errors.append({
                        "type": "value_error",
                        "loc": ("fusion_groups", g_idx, "columns", col_idx),
                        "input": col,
                        "ctx": {"error": ValueError(f"Group column '{col}' does not exist in the table profile.")}
                    })
                    continue
                
                # Check overlap
                if col in assigned_columns:
                    errors.append({
                        "type": "value_error",
                        "loc": ("fusion_groups", g_idx, "columns", col_idx),
                        "input": col,
                        "ctx": {"error": ValueError(f"Column '{col}' is assigned multiple times. Already assigned to: {assigned_columns[col]}.")}
                    })
                else:
                    assigned_columns[col] = f"group '{fg.group_name}'"
                    
        # 3. Check 100% column coverage
        missing_cols = profile_columns - set(assigned_columns.keys())
        if missing_cols:
            errors.append({
                "type": "value_error",
                "loc": ("column_policies",),
                "input": policy.model_dump(),
                "ctx": {"error": ValueError(f"Incomplete column coverage. Missing column policies/fusion groups for: {sorted(list(missing_cols))}.")}
            })
            
        if errors:
            raise ValidationError.from_exception_data(
                title="TableFusionPolicy",
                line_errors=errors
            )

    def generate_policy(
        self,
        multi_profile: MultiTableFusionProfile,
        return_metadata: bool = False,
    ) -> MultiTableFusionPolicy | Tuple[MultiTableFusionPolicy, Dict[str, ExecutionMetadata]]:
        tables = {}
        metadata_dict: Dict[str, ExecutionMetadata] = {}
        for table_name, table_profile in multi_profile.tables.items():
            if not table_profile.columns or table_profile.total_pairs == 0:
                tables[table_name] = TableFusionPolicy(
                    table_name=table_name,
                    column_policies=[],
                    fusion_groups=[],
                    reasoning="No linked record pairs to resolve for this table."
                )
                metadata_dict[table_name] = ExecutionMetadata(
                    model_name=self.agent.model_name,
                    provider=self.agent.provider,
                    execution_time_seconds=0.0,
                    prompt_tokens=0,
                    completion_tokens=0,
                    total_tokens=0
                )
                continue

            user_prompt = self._construct_table_prompt(table_profile)
            try:
                policy, metadata = self.agent.run_sync(user_prompt, deps=table_profile)
                self._validate_policy(table_profile, policy)
                tables[table_name] = policy
                metadata_dict[table_name] = metadata
            except Exception as e:
                # Extract original ValidationError if it was raised inside the output validator
                # and wrapped by pydantic_ai
                cause = e.__cause__ or e.__context__
                while cause is not None:
                    if isinstance(cause, ValidationError):
                        raise cause
                    cause = cause.__cause__ or cause.__context__
                raise e

        self.last_metadata = metadata_dict
        policy = MultiTableFusionPolicy(tables=tables)
        if return_metadata:
            return policy, metadata_dict
        return policy
