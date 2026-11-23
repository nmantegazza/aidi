import json
from unittest.mock import MagicMock

import pandas as pd

from entity_resolution.benchmarking.models import (
    BenchmarkConfig,
    DatasetModelResult,
    EntityResBenchmarkReport,
)
from entity_resolution.evaluation_models import (
    EntityResEvalReport,
    EvaluationMetrics,
    IndexingEvaluation,
    MatchingEvaluation,
)
from entity_resolution.exporter import EntityResolutionExporter
from entity_resolution.models import (
    ColumnMatchConfig,
    EntityResolutionResult,
    ERPipelineConfiguration,
    SimilarityAlgorithm,
)


def make_dummy_result():
    df_a = pd.DataFrame({"id": ["a1", "a2"], "name": ["Alice", "Bob"]}).set_index("id")
    df_b = pd.DataFrame({"id": ["b1", "b2"], "name": ["Alice", "Robert"]}).set_index("id")

    matches = pd.DataFrame([
        {"left_id": "a1", "right_id": "b1", "aggregate_score": 0.95, "name": 0.95}
    ]).set_index(["left_id", "right_id"])

    uncertain = pd.DataFrame(columns=["left_id", "right_id", "aggregate_score"]).set_index(["left_id", "right_id"])
    non_matches = pd.DataFrame([
        {"left_id": "a2", "right_id": "b2", "aggregate_score": 0.1, "name": 0.1}
    ]).set_index(["left_id", "right_id"])

    config = ERPipelineConfiguration(
        sorting_key="name",
        window_size=3,
        matching_columns={"name": ColumnMatchConfig(algorithm=SimilarityAlgorithm.EXACT, weight=1.0)},
        reasoning="Test reasoning",
    )

    return EntityResolutionResult(
        candidate_pairs=matches.index,
        matches=matches,
        uncertain=uncertain,
        non_matches=non_matches,
        df_a_clean=df_a,
        df_b_clean=df_b,
        config=config,
        er_config_metadata=MagicMock(model_name="test-model"),
        profile_a=MagicMock(total_rows=2, total_columns=1, column_profiles={}, sample_rows=[]),
        profile_b=MagicMock(total_rows=2, total_columns=1, column_profiles={}, sample_rows=[]),
    )


def make_dummy_report(table_name="ds1", f1=0.85):
    metrics = EvaluationMetrics(
        precision=0.8,
        recall=0.9,
        f1=f1,
        tp=8,
        fp=2,
        fn=1,
        support=9,
    )
    idx_eval = IndexingEvaluation(
        num_candidates=10,
        max_possible_pairs=100,
        reduction_ratio=0.9,
        pairs_recall=0.95,
        missed_true_matches=1,
        num_true_matches=9,
        sorting_keys=["name"],
        window_size=5,
    )
    match_eval = MatchingEvaluation(
        metrics=metrics,
        match_threshold=0.8,
        uncertain_threshold=0.6,
        num_predicted_matches=10,
        num_uncertain=1,
        num_non_matches=89,
    )
    return EntityResEvalReport(
        table_name=table_name,
        num_rows_a=10,
        num_rows_b=10,
        num_ground_truth_matches=9,
        indexing=idx_eval,
        matching=match_eval,
    )


def test_export_standalone_run(tmp_path):
    result = make_dummy_result()
    out_dir = tmp_path / "standalone_run"

    returned_dir = EntityResolutionExporter.export_standalone_run(result, output_dir=out_dir)

    assert returned_dir == out_dir
    assert (out_dir / "matches.csv").exists()
    assert (out_dir / "uncertain.csv").exists()
    assert (out_dir / "non_matches.csv").exists()

    df_matches = pd.read_csv(out_dir / "matches.csv")
    assert "left_name" in df_matches.columns
    assert "right_name" in df_matches.columns
    assert len(df_matches) == 1
    assert df_matches.iloc[0]["left_name"] == "Alice"


def test_export_evaluation_run(tmp_path):
    result = make_dummy_result()
    report = make_dummy_report(table_name="test_dataset")
    out_dir = tmp_path / "eval_run"

    gt = {("a1", "b1")}
    returned_dir = EntityResolutionExporter.export_evaluation_run(
        result, report, ground_truth=gt, output_dir=out_dir
    )

    assert returned_dir == out_dir
    assert (out_dir / "report.json").exists()
    assert (out_dir / "report.html").exists()
    assert (out_dir / "matches.csv").exists()
    assert (out_dir / "uncertain.csv").exists()
    assert (out_dir / "non_matches.csv").exists()

    with open(out_dir / "report.json", "r") as f:
        data = json.load(f)
        assert data["table_name"] == "test_dataset"
        assert "boundary_samples" not in data  # Lightweight report invariant

    df_matches = pd.read_csv(out_dir / "matches.csv")
    assert "is_true_match" in df_matches.columns
    assert bool(df_matches.iloc[0]["is_true_match"]) is True

    df_non_matches = pd.read_csv(out_dir / "non_matches.csv")
    assert "is_true_match" in df_non_matches.columns
    assert bool(df_non_matches.iloc[0]["is_true_match"]) is False


def test_export_benchmark_run(tmp_path):
    out_dir = tmp_path / "benchmark_run"
    bench_config = BenchmarkConfig(
        models=["test_model"],
        runs=1,
        dataset_source="recordlinkage",
        datasets=["ds1"],
    )
    dummy_report = make_dummy_report(table_name="ds1", f1=0.9)
    report = EntityResBenchmarkReport(
        config=bench_config,
        dataset_reports={
            "ds1": {
                "test_model": DatasetModelResult(
                    mean_metrics={"f1": 0.9},
                    std_metrics={"f1": 0.0},
                    runs=[dummy_report],
                )
            }
        },
    )

    saved_path = EntityResolutionExporter.export_benchmark_run(report, output_dir=out_dir)

    assert saved_path == out_dir
    assert (out_dir / "report.json").exists()
    assert (out_dir / "summary.csv").exists()
    assert (out_dir / "summary.md").exists()
    assert (out_dir / "datasets" / "ds1" / "test_model" / "report.json").exists()
    assert (out_dir / "datasets" / "ds1" / "test_model" / "report.md").exists()

    df_summary = pd.read_csv(out_dir / "summary.csv")
    assert len(df_summary) == 1
    assert df_summary.iloc[0]["dataset"] == "ds1"
    assert df_summary.iloc[0]["mean_f1"] == 0.9


def test_export_csv_with_id_column(tmp_path):
    df_a = pd.DataFrame({"id": ["1", "2"], "name": ["Alice", "Bob"]}).set_index("id", drop=False)
    df_b = pd.DataFrame({"id": ["10", "20"], "title": ["X", "Y"]}).set_index("id", drop=False)

    index = pd.MultiIndex.from_tuples([("1", "10"), ("2", "20")], names=["left_id", "right_id"])
    matches = pd.DataFrame({"aggregate_score": [0.9, 0.8]}, index=index)

    out_csv = tmp_path / "test_matches.csv"
    EntityResolutionExporter._export_csv(matches, df_a, df_b, out_csv, ground_truth={("1", "10")})

    assert out_csv.exists()
    df_exported = pd.read_csv(out_csv)
    assert "left_id" in df_exported.columns
    assert "right_id" in df_exported.columns
    assert "is_true_match" in df_exported.columns
    assert len(df_exported) == 2
