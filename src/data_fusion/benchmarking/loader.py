"""Data loader for benchmark datasets prepared for data fusion."""

import json
from pathlib import Path

import pandas as pd


class BenchmarkDataLoader:
    """Loads standardized 2-source data fusion benchmark datasets."""

    def __init__(self, base_dir: str = "data/data_fusion/processed"):
        """Initializes loader with base directory path.

        Args:
            base_dir: Path to processed datasets directory.
        """
        self.base_dir = Path(base_dir)

    def load_dataset(
        self, dataset_id: str
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
        """Loads metadata and aligned Source A, Source B, GT DataFrames.

        Args:
            dataset_id: Identifier of the dataset (e.g. 'books', 'flights').

        Returns:
            Tuple of (df_a, df_b, df_gt, metadata).

        Raises:
            FileNotFoundError: If dataset path or files do not exist.
        """
        dataset_path = self.base_dir / dataset_id
        if not dataset_path.exists():
            raise FileNotFoundError(
                f"Dataset path '{dataset_path}' does not exist."
            )

        meta_file = dataset_path / "metadata.json"
        src_a_file = dataset_path / "source_a.csv"
        src_b_file = dataset_path / "source_b.csv"
        gt_file = dataset_path / "ground_truth.csv"

        for f in (meta_file, src_a_file, src_b_file, gt_file):
            if not f.exists():
                raise FileNotFoundError(
                    f"Required benchmark file '{f}' is missing."
                )

        with open(meta_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        entity_id_col = metadata["entity_id_column"]

        df_a = pd.read_csv(src_a_file, dtype=str).fillna("")
        df_b = pd.read_csv(src_b_file, dtype=str).fillna("")
        df_gt = pd.read_csv(gt_file, dtype=str).fillna("")

        # Perform inner join on entity_id_col to align entities across all 3
        common_ids = (
            set(df_a[entity_id_col])
            .intersection(set(df_b[entity_id_col]))
            .intersection(set(df_gt[entity_id_col]))
        )

        df_a_aligned = df_a[df_a[entity_id_col].isin(common_ids)].sort_values(entity_id_col).reset_index(drop=True)
        df_b_aligned = df_b[df_b[entity_id_col].isin(common_ids)].sort_values(entity_id_col).reset_index(drop=True)
        df_gt_aligned = df_gt[df_gt[entity_id_col].isin(common_ids)].sort_values(entity_id_col).reset_index(drop=True)

        return df_a_aligned, df_b_aligned, df_gt_aligned, metadata
