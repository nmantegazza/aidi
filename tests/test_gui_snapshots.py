import shutil
from pathlib import Path
import pytest
from pipeline.gui.snapshot import save_snapshot, load_snapshot, list_snapshots, SNAPSHOT_DIR

def test_save_load_list_snapshots():
    # Setup temp snapshots path or cleanup afterward
    test_snapshot_name = "pytest_test_snapshot"
    test_state = {
        "ingestion_state": "dummy_ingestion",
        "cleaning_state": {"a": 1, "b": [2, 3]},
        "matching_state": None,
        "current_stage": "initial",
    }
    
    # Save snapshot
    filepath = save_snapshot(test_snapshot_name, test_state)
    assert filepath.exists()
    assert filepath.suffix == ".pkl"
    assert test_snapshot_name + ".pkl" in list_snapshots()
    
    # Load snapshot
    loaded_state = load_snapshot(test_snapshot_name)
    assert loaded_state == test_state
    
    # Test load with suffix
    loaded_state_with_suffix = load_snapshot(test_snapshot_name + ".pkl")
    assert loaded_state_with_suffix == test_state
    
    # Cleanup
    filepath.unlink()
    assert test_snapshot_name + ".pkl" not in list_snapshots()
