import pandas as pd
import pytest
from shared.profiling import DataProfiler, TableProfile

def test_data_profiler_basic():
    # Create sample data
    data = {
        "id": [1, 2, 3, 4, 5],
        "name": ["Alice", "Bob", "Charlie", "David", None],
        "age": [25, 30, 35, 40, 45],
        "city": ["NY", "LA", "NY", "SF", "LA"]
    }
    df = pd.DataFrame(data)
    
    # Profile
    profile = DataProfiler.profile_dataframe(df, "test_table")
    
    # Assertions
    assert isinstance(profile, TableProfile)
    assert profile.table_name == "test_table"
    assert profile.total_rows == 5
    assert profile.total_columns == 4
    
    # Column specific checks
    name_profile = profile.get_column("name")
    assert name_profile is not None
    assert name_profile.null_count == 1
    assert name_profile.null_percentage == 20.0
    assert name_profile.cardinality == 4
    assert "Alice" in name_profile.distinct_samples
    
    city_profile = profile.get_column("city")
    assert city_profile.cardinality == 3
    assert city_profile.uniqueness_percentage == 60.0 # 3/5
    
    # Sample rows check
    assert len(profile.sample_rows) == 5
    assert profile.sample_rows[4]["name"] is None # Handled NaN -> None

def test_data_profiler_empty_df():
    df = pd.DataFrame(columns=["a", "b"])
    profile = DataProfiler.profile_dataframe(df, "empty_table")
    
    assert profile.total_rows == 0
    assert profile.column_profiles["a"].null_percentage == 100.0

if __name__ == "__main__":
    # Manual run if needed
    test_data_profiler_basic()
    print("Tests passed!")
