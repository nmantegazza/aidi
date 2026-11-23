import pandas as pd

class DatabaseMerger:
    def merge(self, golden_records: pd.DataFrame, unlinked_a: pd.DataFrame, unlinked_b: pd.DataFrame) -> pd.DataFrame:
        """
        Merges the fused golden records with the unlinked records from both sources.
        """
        merged = pd.concat([golden_records, unlinked_a, unlinked_b], ignore_index=True)
        return merged
