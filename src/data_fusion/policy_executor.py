import pandas as pd
from typing import Any, Dict
from data_fusion.models import TableFusionPolicy
from data_fusion.policy_strategies import resolve

class PolicyExecutor:
    def __init__(self, policy: TableFusionPolicy, profile_trust_scores: Dict[str, float]):
        self.policy = policy
        self.profile_trust_scores = profile_trust_scores
        
        # Calculate aggregate trust score
        if profile_trust_scores:
            self._aggregate_trust = sum(profile_trust_scores.values()) / len(profile_trust_scores)
        else:
            self._aggregate_trust = 0.5

    def _resolve_group_row(self, row: pd.Series, group: Any) -> Dict[str, Any]:
        leader_col = group.leader_column
        val_a = row[leader_col + "_a"]
        val_b = row[leader_col + "_b"]
        
        effective_trust = self.profile_trust_scores.get(leader_col, 0.5)
        if effective_trust == 0.5:
            effective_trust = self._aggregate_trust
            
        resolved_val = resolve(group.strategy, val_a, val_b, effective_trust)
        
        def eq(v1, v2):
            if pd.isna(v1) and pd.isna(v2):
                return True
            if pd.isna(v1) or pd.isna(v2):
                return False
            return v1 == v2
            
        if eq(resolved_val, val_a):
            winner = "a"
        elif eq(resolved_val, val_b):
            winner = "b"
        else:
            winner = "a" if effective_trust >= 0.5 else "b"
            
        # Check if all group columns are null/empty in the winning source
        winner_all_empty = True
        for col in group.columns:
            val = row[col + f"_{winner}"]
            if not (pd.isna(val) or (isinstance(val, str) and val.strip() == "")):
                winner_all_empty = False
                break
                
        if winner_all_empty:
            winner = "b" if winner == "a" else "a"
            
        resolved = {}
        for col in group.columns:
            resolved[col] = row[col + f"_{winner}"]
        return resolved

    def execute(self, linked_pairs: pd.DataFrame) -> pd.DataFrame:
        if linked_pairs.empty:
            return pd.DataFrame()
            
        # Copy non-suffixed columns (e.g. id)
        non_suffixed_cols = [c for c in linked_pairs.columns if not (c.endswith("_a") or c.endswith("_b"))]
        fused_df = linked_pairs[non_suffixed_cols].copy()
        
        # Resolve standalone columns
        for col_policy in self.policy.column_policies:
            col_name = col_policy.column_name
            col_a = col_name + "_a"
            col_b = col_name + "_b"
            
            if col_a not in linked_pairs.columns or col_b not in linked_pairs.columns:
                continue
                
            effective_trust = self.profile_trust_scores.get(col_name, 0.5)
            if effective_trust == 0.5:
                effective_trust = self._aggregate_trust
                
            fused_df[col_name] = linked_pairs.apply(
                lambda row: resolve(col_policy.strategy, row[col_a], row[col_b], effective_trust),
                axis=1
            )
            
        # Resolve fusion groups
        for group in self.policy.fusion_groups:
            skip_group = False
            for col in group.columns:
                if col + "_a" not in linked_pairs.columns or col + "_b" not in linked_pairs.columns:
                    skip_group = True
                    break
            if skip_group:
                continue
                
            group_resolved_df = linked_pairs.apply(
                lambda row: pd.Series(self._resolve_group_row(row, group)),
                axis=1
            )
            for col in group.columns:
                fused_df[col] = group_resolved_df[col]
                
        return fused_df
