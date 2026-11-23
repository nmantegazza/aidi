"""Unit tests for the scaled thesis running example dataset."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from entity_resolution.indexing_strategies.implementations import TFIDFIndexStrategy
from entity_resolution.models import (
    ClassificationMode,
    ColumnMatchConfig,
    SimilarityAlgorithm,
)
from entity_resolution.pipeline import score_and_classify_pairs
from shared.ingestion.engine import DataLoader

DATA_ROOT = Path("data/test_cases/running_example")


@pytest.fixture(scope="module")
def running_example_sources():
    """Loads Source A and Source B using DataLoader."""
    loader = DataLoader(strict_type_validation=True)
    source_a, report_a, source_b, report_b = loader.load_integration_input(DATA_ROOT)
    return source_a, report_a, source_b, report_b


def test_running_example_ingestion(running_example_sources):
    """Verifies that all 6 tables load cleanly and satisfy row count bounds."""
    source_a, _, source_b, _ = running_example_sources

    assert set(source_a.tables.keys()) == {"organizations", "departments", "staff"}
    assert set(source_b.tables.keys()) == {"businesses", "locations", "workers"}

    for name, df in source_a.tables.items():
        assert 50 <= len(df) <= 100, f"Source A table {name} has {len(df)} rows, outside [50, 100]"

    for name, df in source_b.tables.items():
        assert 50 <= len(df) <= 100, f"Source B table {name} has {len(df)} rows, outside [50, 100]"

    assert len(source_a.tables["organizations"]) == 75
    assert len(source_a.tables["departments"]) == 80
    assert len(source_a.tables["staff"]) == 100

    assert len(source_b.tables["businesses"]) == 75
    assert len(source_b.tables["locations"]) == 75
    assert len(source_b.tables["workers"]) == 100


def test_running_example_foreign_keys(running_example_sources):
    """Verifies complete referential integrity across all relationships."""
    source_a, _, source_b, _ = running_example_sources

    df_orgs = source_a.tables["organizations"]
    df_depts = source_a.tables["departments"]
    df_staff = source_a.tables["staff"]

    df_biz = source_b.tables["businesses"]
    df_locs = source_b.tables["locations"]
    df_workers = source_b.tables["workers"]

    # 1. departments.org_id -> organizations.org_id
    org_ids = set(df_orgs["org_id"])
    assert set(df_depts["org_id"]).issubset(org_ids), "Orphan departments found"

    # 2. staff.org_id -> organizations.org_id
    assert set(df_staff["org_id"]).issubset(org_ids), "Orphan staff found"

    # 3. businesses.location_ref -> locations.loc_id
    loc_ids = set(df_locs["loc_id"])
    valid_loc_refs = set(df_biz["location_ref"].dropna())
    assert valid_loc_refs.issubset(loc_ids), "Orphan business location_ref found"

    # 4. workers.business_ref -> businesses.biz_id
    biz_ids = set(df_biz["biz_id"])
    valid_biz_refs = set(df_workers["business_ref"].dropna())
    assert valid_biz_refs.issubset(biz_ids), "Orphan worker business_ref found"


def test_running_example_ground_truth_and_metadata():
    """Verifies that ground truth files and metadata exist and match table primary keys."""
    meta_path = DATA_ROOT / "dataset_metadata.json"
    gt_orgs_path = DATA_ROOT / "ground_truth_organizations.csv"
    gt_staff_path = DATA_ROOT / "ground_truth_staff.csv"

    assert meta_path.exists(), "dataset_metadata.json missing"
    assert gt_orgs_path.exists(), "ground_truth_organizations.csv missing"
    assert gt_staff_path.exists(), "ground_truth_staff.csv missing"

    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    assert meta["dataset_name"] == "thesis_running_example"
    assert meta["ground_truth"]["organizations"]["total_matches"] >= 30
    assert meta["ground_truth"]["staff"]["total_matches"] >= 45

    df_gt_orgs = pd.read_csv(gt_orgs_path)
    df_gt_staff = pd.read_csv(gt_staff_path)

    df_orgs = pd.read_parquet(DATA_ROOT / "source_a" / "organizations.parquet")
    df_biz = pd.read_parquet(DATA_ROOT / "source_b" / "businesses.parquet")
    df_staff = pd.read_parquet(DATA_ROOT / "source_a" / "staff.parquet")
    df_workers = pd.read_parquet(DATA_ROOT / "source_b" / "workers.parquet")

    assert set(df_gt_orgs["org_id"]).issubset(set(df_orgs["org_id"]))
    assert set(df_gt_orgs["biz_id"]).issubset(set(df_biz["biz_id"]))

    assert set(df_gt_staff["emp_id"]).issubset(set(df_staff["emp_id"]))
    assert set(df_gt_staff["worker_id"]).issubset(set(df_workers["worker_id"]))


def test_running_example_er_organizations(running_example_sources):
    """Verifies TF-IDF indexing and dynamic thresholding on organizations vs businesses."""
    source_a, _, source_b, _ = running_example_sources

    df_orgs = source_a.tables["organizations"]
    df_biz = source_b.tables["businesses"]

    df_a = pd.DataFrame({
        "name": df_orgs["org_name"],
        "industry": df_orgs["industry"],
    })
    df_b = pd.DataFrame({
        "name": df_biz["name"],
        "industry": df_biz["sector"],
    })

    # TF-IDF candidate indexing
    strat = TFIDFIndexStrategy(keys=["name"], threshold=0.10)
    index_res = strat.execute(df_a, df_b)
    assert len(index_res.candidate_pairs) >= 50, "Insufficient candidate pairs generated"

    # Multi-feature scoring and dynamic classification
    col_configs = {
        "name": ColumnMatchConfig(algorithm=SimilarityAlgorithm.JAROWINKLER, weight=0.7),
        "industry": ColumnMatchConfig(algorithm=SimilarityAlgorithm.JAROWINKLER, weight=0.3),
    }

    matches, non_matches, uncertain = score_and_classify_pairs(
        index_res.candidate_pairs,
        df_a,
        df_b,
        col_configs,
        classification_mode=ClassificationMode.TERNARY,
    )

    assert len(matches) >= 20, f"Expected >= 20 matches, got {len(matches)}"
    assert len(uncertain) >= 5, f"Expected >= 5 uncertain pairs, got {len(uncertain)}"
    assert len(non_matches) >= 10, f"Expected >= 10 non-matches, got {len(non_matches)}"


def test_running_example_er_staff(running_example_sources):
    """Verifies TF-IDF indexing and dynamic thresholding on staff vs workers."""
    source_a, _, source_b, _ = running_example_sources

    df_staff = source_a.tables["staff"]
    df_workers = source_b.tables["workers"]

    df_a = pd.DataFrame({
        "first_name": df_staff["first_name"],
        "last_name": df_staff["last_name"],
        "role": df_staff["role"],
    })
    df_b = pd.DataFrame({
        "first_name": df_workers["first_name"],
        "last_name": df_workers["last_name"],
        "role": df_workers["job_title"],
    })

    # TF-IDF candidate indexing
    strat = TFIDFIndexStrategy(keys=["first_name", "last_name"], threshold=0.10)
    index_res = strat.execute(df_a, df_b)
    assert len(index_res.candidate_pairs) >= 50, "Insufficient candidate pairs generated"

    # Multi-feature scoring and dynamic classification
    col_configs = {
        "first_name": ColumnMatchConfig(algorithm=SimilarityAlgorithm.JAROWINKLER, weight=0.4),
        "last_name": ColumnMatchConfig(algorithm=SimilarityAlgorithm.JAROWINKLER, weight=0.4),
        "role": ColumnMatchConfig(algorithm=SimilarityAlgorithm.JAROWINKLER, weight=0.2),
    }

    matches, non_matches, uncertain = score_and_classify_pairs(
        index_res.candidate_pairs,
        df_a,
        df_b,
        col_configs,
        classification_mode=ClassificationMode.TERNARY,
    )

    assert len(matches) >= 25, f"Expected >= 25 matches, got {len(matches)}"
    assert len(uncertain) >= 5, f"Expected >= 5 uncertain pairs, got {len(uncertain)}"
    assert len(non_matches) >= 10, f"Expected >= 10 non-matches, got {len(non_matches)}"
