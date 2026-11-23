import json
import pytest
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from pathlib import Path
from shared.ingestion import (
    DataLoader, SourceData, DataPackageNotFound, 
    ResourceFileNotFound, SchemaMismatchError
)
from shared.schema_models import DataPackage

@pytest.fixture
def temp_integration_root(tmp_path):
    """
    Creates a temporary directory structure:
    root/
      source_a/
        datapackage.json
        data/table_a.parquet
      source_b/
        datapackage.json
        data/table_b.parquet
    """
    root = tmp_path / "integration_test"
    root.mkdir()
    
    # Source A
    source_a = root / "source_a"
    source_a.mkdir()
    (source_a / "data").mkdir()
    
    df_a = pd.DataFrame({"id": [1, 2], "name": ["a", "b"]})
    df_a.to_parquet(source_a / "data" / "table_a.parquet")
    
    pkg_a = {
        "name": "source_a",
        "resources": [
            {
                "name": "table_a",
                "path": "data/table_a.parquet",
                "schema": {
                    "primaryKey": "id",
                    "fields": [
                        {"name": "id", "type": "integer"},
                        {"name": "name", "type": "string"}
                    ]
                }
            }
        ]
    }
    with open(source_a / "datapackage.json", "w") as f:
        json.dump(pkg_a, f)
        
    # Source B
    source_b = root / "source_b"
    source_b.mkdir()
    (source_b / "data").mkdir()
    
    df_b = pd.DataFrame({"code": ["x", "y"], "value": [10.5, 20.0]})
    df_b.to_parquet(source_b / "data" / "table_b.parquet")
    
    pkg_b = {
        "name": "source_b",
        "resources": [
            {
                "name": "table_b",
                "path": "data/table_b.parquet",
                "schema": {
                    "primaryKey": "code",
                    "fields": [
                        {"name": "code", "type": "string"},
                        {"name": "value", "type": "number"}
                    ]
                }
            }
        ]
    }
    with open(source_b / "datapackage.json", "w") as f:
        json.dump(pkg_b, f)
        
    return root

def test_load_integration_input_success(temp_integration_root):
    loader = DataLoader()
    source_a, report_a, source_b, report_b = loader.load_integration_input(temp_integration_root)
    
    assert isinstance(source_a, SourceData)
    assert isinstance(source_b, SourceData)
    assert "table_a" in source_a.tables
    assert "table_b" in source_b.tables
    assert source_a.tables["table_a"].shape == (2, 2)
    assert source_b.tables["table_b"].shape == (2, 2)

def test_load_source_missing_descriptor(tmp_path):
    loader = DataLoader()
    with pytest.raises(DataPackageNotFound):
        loader.load_source(tmp_path)

def test_load_resource_missing_file(tmp_path):
    descriptor_path = tmp_path / "datapackage.json"
    pkg = {
        "name": "test",
        "resources": [
            {
                "name": "missing",
                "path": "data/missing.parquet",
                "schema": {"fields": [{"name": "id", "type": "integer"}]}
            }
        ]
    }
    with open(descriptor_path, "w") as f:
        json.dump(pkg, f)
        
    loader = DataLoader()
    with pytest.raises(ResourceFileNotFound):
        loader.load_source(tmp_path)

def test_schema_column_mismatch(tmp_path):
    # Create parquet with only ONE column
    (tmp_path / "data").mkdir()
    df = pd.DataFrame({"id": [1]})
    df.to_parquet(tmp_path / "data" / "test.parquet")
    
    # Schema expects TWO columns
    pkg = {
        "name": "test",
        "resources": [
            {
                "name": "test",
                "path": "data/test.parquet",
                "schema": {
                    "fields": [
                        {"name": "id", "type": "integer"},
                        {"name": "name", "type": "string"} # Missing in parquet
                    ]
                }
            }
        ]
    }
    with open(tmp_path / "datapackage.json", "w") as f:
        json.dump(pkg, f)
        
    loader = DataLoader()
    with pytest.raises(SchemaMismatchError):
        loader.load_source(tmp_path)

def test_extra_columns_allowed(tmp_path):
    # Create parquet with extra col
    (tmp_path / "data").mkdir()
    df = pd.DataFrame({"id": [1], "extra": ["suppose"]})
    df.to_parquet(tmp_path / "data" / "test.parquet")
    
    # Schema expects only 'id'
    pkg = {
        "name": "test",
        "resources": [
            {
                "name": "test",
                "path": "data/test.parquet",
                "schema": {
                    "fields": [{"name": "id", "type": "integer"}]
                }
            }
        ]
    }
    with open(tmp_path / "datapackage.json", "w") as f:
        json.dump(pkg, f)
        
    loader = DataLoader()
    source, report = loader.load_source(tmp_path)
    assert "id" in source.tables["test"].columns
    assert "extra" in source.tables["test"].columns # Preserved

def test_handle_ingestion_with_file_explorer_path(temp_integration_root):
    from pipeline.gui.handlers import handle_ingestion
    
    # 1. Test with a single string pointing directly to a datapackage.json file
    target_file = str(temp_integration_root / "source_a" / "datapackage.json")
    
    result, _, _, _, _, _ = handle_ingestion(target_file, 0)
    
    # Assert successful ingestion return structure and values
    assert result.source_a is not None
    assert result.source_b is not None
    assert result.profiles_a is not None
    assert result.profiles_b is not None

    # 2. Test with a list containing a single file path string
    result_list, _, _, _, _, _ = handle_ingestion([target_file], 0)
    assert result_list.source_a is not None


