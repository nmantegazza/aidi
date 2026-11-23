import pandas as pd
from typing import Dict, Tuple, Optional

from shared.agents import ExecutionMetadata
from data_fusion.profiler import DataFusionProfiler
from data_fusion.agents import FusionPolicyAgent
from data_fusion.policy_executor import PolicyExecutor
from data_fusion.database_merger import DatabaseMerger
from data_fusion.models import (
    MultiTableFusionPolicy, MultiTableFusionProfile, TableFusionPolicy, TableFusionProfile
)

from shared.config import config

class DataFusionEngine:
    def __init__(self, model_name: str = None, provider: str = None):
        model_name = model_name or config.DEFAULT_GOOGLE_MODEL
        self.profiler = DataFusionProfiler()
        self.policy_agent = FusionPolicyAgent(model_name=model_name, provider=provider)
        self.merger = DatabaseMerger()
        self.last_metadata: Dict[str, ExecutionMetadata] = {}

    def _execute_table(
        self,
        table_name: str,
        df_a: pd.DataFrame,
        df_b: pd.DataFrame,
        df_links: pd.DataFrame,
        table_policy: TableFusionPolicy,
        table_profile: TableFusionProfile,
        merge_unlinked: bool = True
    ) -> pd.DataFrame:
        if df_links.empty:
            golden_records = pd.DataFrame(columns=df_a.columns)
            unlinked_a = df_a.copy()
            unlinked_b = df_b.copy()
        else:
            # Align rows based on links
            aligned_a = df_a.loc[df_links['left_id']].reset_index(drop=True)
            aligned_b = df_b.loc[df_links['right_id']].reset_index(drop=True)

            # Prepare DataFrame for executor (suffixing _a and _b)
            linked_pairs = pd.DataFrame()
            
            for c in df_a.columns:
                linked_pairs[c + '_a'] = aligned_a[c]
                linked_pairs[c + '_b'] = aligned_b[c]
            
            trust_scores = {c: p.source_trust_score for c, p in table_profile.columns.items()}

            executor = PolicyExecutor(table_policy, trust_scores)
            golden_records = executor.execute(linked_pairs)

            # Find unlinked records
            unlinked_a = df_a.drop(df_links['left_id'])
            unlinked_b = df_b.drop(df_links['right_id'])

        if merge_unlinked:
            return self.merger.merge(golden_records, unlinked_a, unlinked_b)
        else:
            return golden_records

    def profile_and_propose(
        self, 
        source_a_origin: str, 
        source_b_origin: str, 
        tables: Dict[str, Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]],
        return_metadata: bool = False,
    ) -> Tuple[MultiTableFusionProfile, MultiTableFusionPolicy] | Tuple[MultiTableFusionProfile, MultiTableFusionPolicy, Dict[str, ExecutionMetadata]]:
        # 1. Profile
        multi_profile = self.profiler.profile(source_a_origin, source_b_origin, tables)

        # 2. Generate Policy
        multi_policy = self.policy_agent.generate_policy(multi_profile)
        self.last_metadata = self.policy_agent.last_metadata

        if return_metadata:
            return multi_profile, multi_policy, self.last_metadata
        return multi_profile, multi_policy

    def execute(
        self,
        tables: Dict[str, Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]],
        policy: MultiTableFusionPolicy,
        profile: MultiTableFusionProfile,
        merge_unlinked: bool = True
    ) -> Dict[str, pd.DataFrame]:
        fused_tables = {}
        for table_name, (df_a, df_b, df_links) in tables.items():
            table_policy = policy.tables[table_name]
            table_profile = profile.tables[table_name]
            fused_tables[table_name] = self._execute_table(
                table_name, df_a, df_b, df_links, table_policy, table_profile, merge_unlinked
            )
        return fused_tables

    def run(
        self, 
        source_a_origin: str, 
        source_b_origin: str, 
        tables: Dict[str, Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]],
        merge_unlinked: bool = True
    ) -> Dict[str, pd.DataFrame]:
        """
        Runs the full data fusion pipeline.
        
        Args:
            tables: Dict mapping table_name to (df_a, df_b, df_links).
            merge_unlinked: If True, uses DatabaseMerger to append unlinked rows to the golden records.
        """
        multi_profile, multi_policy = self.profile_and_propose(
            source_a_origin, source_b_origin, tables
        )
        return self.execute(tables, multi_policy, multi_profile, merge_unlinked)
