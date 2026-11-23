"""
Unit tests for the indexing benchmarking framework.
"""

from __future__ import annotations

import json
import pandas as pd
import pytest

from entity_resolution.evaluation_models import IndexingBenchmarkReport
from entity_resolution.benchmarking.index_evaluation import IndexingMetricsEvaluator
from entity_resolution.indexing_strategies import (
    BaseIndexingStrategy,
    StrategyResult,
    SortedNeighborhoodStrategy,
)
from entity_resolution.benchmarking.config_generator import LLMIndexConfigGenerator


from pydantic import BaseModel


class DummyConfig(BaseModel):
    pass


class DummyStrategy(BaseIndexingStrategy):
    """Dummy strategy for testing telemetry."""

    config_schema = DummyConfig
    config_prompt = "Dummy prompt"

    @classmethod
    def from_llm_config(cls, config: BaseModel) -> DummyStrategy:
        return cls()

    @property
    def name(self) -> str:
        return "DummyStrategy"

    def _perform_indexing(
        self, df_a: pd.DataFrame, df_b: pd.DataFrame
    ) -> pd.MultiIndex:
        return pd.MultiIndex.from_tuples([(df_a.index[0], df_b.index[0])])


def test_indexing_benchmark_report_model():
    """Verify IndexingBenchmarkReport instantiates and validates fields."""
    report = IndexingBenchmarkReport(
        dataset_name="test_ds",
        strategy_name="SortedNeighborhood",
        recall=0.85,
        precision=0.40,
        reduction_ratio=0.95,
        indexing_time_sec=0.123,
        peak_memory_mb=12.5,
    )
    assert report.dataset_name == "test_ds"
    assert report.recall == 0.85
    assert report.llm_metrics is None


def test_indexing_metrics_evaluator():
    """Verify IndexingMetricsEvaluator calculates metrics correctly."""
    df_a = pd.DataFrame({"id": ["a1", "a2", "a3"], "val": ["x", "y", "z"]}).set_index("id")
    df_b = pd.DataFrame({"id": ["b1", "b2", "b3"], "val": ["x", "y", "w"]}).set_index("id")

    candidate_pairs = pd.MultiIndex.from_tuples([("a1", "b1"), ("a2", "b2")])
    ground_truth = pd.MultiIndex.from_tuples([("a1", "b1"), ("a3", "b3")])

    evaluator = IndexingMetricsEvaluator()
    res = evaluator.evaluate(candidate_pairs, ground_truth, df_a, df_b)

    # Max possible = 3 * 3 = 9
    # Candidates = 2 -> RR = 1 - (2/9) = 7/9 = 0.777778
    # Ground truth = 2: ("a1", "b1") [TP], ("a3", "b3") [FN] -> Recall = 1/2 = 0.5
    # Candidate ("a2", "b2") is FP -> Precision = 1/2 = 0.5
    assert round(res["reduction_ratio"], 4) == round(1.0 - 2 / 9, 4)
    assert res["recall"] == 0.5
    assert res["precision"] == 0.5


def test_base_indexing_strategy_telemetry():
    """Verify BaseIndexingStrategy tracks time and peak memory."""
    df_a = pd.DataFrame({"id": ["a1"], "title": ["book"]}).set_index("id")
    df_b = pd.DataFrame({"id": ["b1"], "title": ["book"]}).set_index("id")

    strategy = DummyStrategy()
    res = strategy.execute(df_a, df_b)

    assert isinstance(res, StrategyResult)
    assert len(res.candidate_pairs) == 1
    assert res.indexing_time_sec >= 0.0
    assert res.peak_memory_mb >= 0.0


def test_sorted_neighborhood_strategy():
    """Verify SortedNeighborhoodStrategy produces candidate pairs."""
    df_a = pd.DataFrame({"id": ["a1", "a2"], "brand": ["nike", "adidas"]}).set_index("id")
    df_b = pd.DataFrame({"id": ["b1", "b2"], "brand": ["nike", "puma"]}).set_index("id")

    strategy = SortedNeighborhoodStrategy(keys=["brand"], window_size=3)
    res = strategy.execute(df_a, df_b)

    assert ("a1", "b1") in res.candidate_pairs


@pytest.mark.asyncio
async def test_llm_index_config_generator_cache(tmp_path):
    """Verify LLMIndexConfigGenerator loads from local JSON cache on hit."""
    cache_file = tmp_path / "cache.json"
    cache_data = {
        "dataset1::SortedNeighborhoodStrategy::gemini-3.8-flash": {
            "dataset_name": "dataset1",
            "strategy_name": "SortedNeighborhoodStrategy",
            "model_name": "gemini-3.8-flash",
            "config_data": {
                "sorting_keys": ["title"],
                "window_size": 9,
                "reasoning": "dummy reasoning",
            },
            "llm_metrics": None,
        }
    }
    with open(cache_file, "w") as f:
        json.dump(cache_data, f)

    config_gen = LLMIndexConfigGenerator(cache_path=cache_file)
    strategy_instance, meta = await config_gen.get_configuration(
        dataset_name="dataset1",
        profile_a=None,
        profile_b=None,
        table_resource=None,
        strategy_cls=SortedNeighborhoodStrategy,
        force_llm=False,
    )

    assert isinstance(strategy_instance, SortedNeighborhoodStrategy)
    assert strategy_instance.keys == ["title"]
    assert strategy_instance.window_size == 9
    assert meta is None


def test_save_candidate_set_on_full_recall(tmp_path):
    """Verify save_candidate_set writes CSV, updates metadata, and skips if already present."""
    from entity_resolution.dataset_loader import load_dataset, save_candidate_set

    dataset_dir = tmp_path / "ds1"
    dataset_dir.mkdir()

    table_a_df = pd.DataFrame({"id": ["a1", "a2"], "name": ["Alice", "Bob"]})
    table_b_df = pd.DataFrame({"id": ["b1", "b2"], "name": ["Alce", "Bobby"]})
    gt_df = pd.DataFrame({"id_a": ["a1"], "id_b": ["b1"]})

    table_a_df.to_csv(dataset_dir / "table_a.csv", index=False)
    table_b_df.to_csv(dataset_dir / "table_b.csv", index=False)
    gt_df.to_csv(dataset_dir / "ground_truth.csv", index=False)

    metadata = {
        "name": "ds1",
        "domain": "synthetic",
        "ground_truth_type": "exhaustive",
        "table_a": {"file": "table_a.csv", "id_column": "id"},
        "table_b": {"file": "table_b.csv", "id_column": "id"},
        "ground_truth": {
            "file": "ground_truth.csv",
            "column_a": "id_a",
            "column_b": "id_b",
        },
        "candidates": None,
    }

    with open(dataset_dir / "metadata.json", "w") as f:
        json.dump(metadata, f)

    dataset = load_dataset(str(dataset_dir))
    assert dataset.metadata.candidates is None
    assert dataset.candidates is None

    candidate_pairs = pd.MultiIndex.from_tuples([("a1", "b1"), ("a2", "b2")])

    # First call: should save candidate set and update metadata.json
    cand_path = save_candidate_set(dataset, candidate_pairs)
    assert cand_path is not None
    assert cand_path.is_file()

    cand_csv = pd.read_csv(cand_path)
    assert list(cand_csv.columns) == ["id_a", "id_b"]
    assert len(cand_csv) == 2

    # Verify updated metadata.json content
    with open(dataset_dir / "metadata.json", "r") as f:
        updated_meta = json.load(f)
    assert updated_meta["candidates"] == {
        "file": "candidate_pairs.csv",
        "column_a": "id_a",
        "column_b": "id_b",
    }
    assert dataset.candidates is not None

    # Second call: should skip because candidate set is already present
    second_path = save_candidate_set(dataset, candidate_pairs)
    assert second_path is None


def test_save_candidate_set_skips_sampled_dataset(tmp_path):
    """Verify save_candidate_set skips datasets with sampled ground truth type."""
    from entity_resolution.dataset_loader import load_dataset, save_candidate_set

    dataset_dir = tmp_path / "ds_sampled"
    dataset_dir.mkdir()

    table_a_df = pd.DataFrame({"id": ["a1"], "name": ["Alice"]})
    table_b_df = pd.DataFrame({"id": ["b1"], "name": ["Alce"]})
    gt_df = pd.DataFrame({"id_a": ["a1"], "id_b": ["b1"]})

    table_a_df.to_csv(dataset_dir / "table_a.csv", index=False)
    table_b_df.to_csv(dataset_dir / "table_b.csv", index=False)
    gt_df.to_csv(dataset_dir / "ground_truth.csv", index=False)

    metadata = {
        "name": "ds_sampled",
        "domain": "synthetic",
        "ground_truth_type": "sampled",
        "table_a": {"file": "table_a.csv", "id_column": "id"},
        "table_b": {"file": "table_b.csv", "id_column": "id"},
        "ground_truth": {
            "file": "ground_truth.csv",
            "column_a": "id_a",
            "column_b": "id_b",
        },
        "candidates": None,
    }

    with open(dataset_dir / "metadata.json", "w") as f:
        json.dump(metadata, f)

    dataset = load_dataset(str(dataset_dir))
    candidate_pairs = pd.MultiIndex.from_tuples([("a1", "b1")])

    res_path = save_candidate_set(dataset, candidate_pairs)
    assert res_path is None
    assert not (dataset_dir / "candidate_pairs.csv").exists()

