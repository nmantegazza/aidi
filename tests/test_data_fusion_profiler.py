import pandas as pd
import pytest

from data_fusion.models import PhysicalType, SemanticType
from data_fusion.profiler import DataFusionProfiler


@pytest.fixture
def profiler():
    return DataFusionProfiler()

def test_profiler_conflict_rates_and_samples(profiler):
    df_a = pd.DataFrame({
        "email": ["test@example.com", "valid@google.com", "another@google.com", None],
        "name": ["Alice", "Bob", "Charlie", "Dave"],
        "age": [25, 30, 35, 40]
    })
    
    df_b = pd.DataFrame({
        "email": ["test@example.com", "other@google.com", "nope", "some@email.com"],
        "name": ["Alice", "Robert", None, "Dave"],
        "age": [25, 31, 35, 40]
    })
    
    df_links = pd.DataFrame({
        "left_id": [0, 1, 2, 3],
        "right_id": [0, 1, 2, 3]
    })
    
    tables = {"users": (df_a, df_b, df_links)}
    
    profile = profiler.profile("SourceA", "SourceB", tables)
    
    assert profile.source_a_origin == "SourceA"
    assert profile.source_b_origin == "SourceB"
    assert "users" in profile.tables
    
    user_profile = profile.tables["users"]
    assert user_profile.total_pairs == 4
    
    email_prof = user_profile.columns["email"]
    assert email_prof.conflict_rate == 0.75
    assert email_prof.source_a_null_rate == 0.25
    assert email_prof.source_b_null_rate == 0.0
    assert email_prof.physical_type == PhysicalType.TEXT
    assert email_prof.semantic_type == SemanticType.EMAIL
    assert pytest.approx(email_prof.source_trust_score, abs=1e-3) == 0.429
    assert len(email_prof.samples) > 0

    age_prof = user_profile.columns["age"]
    assert age_prof.physical_type == PhysicalType.INTEGER
    assert age_prof.semantic_type == SemanticType.NONE

def test_profiler_fallback_types_and_trust(profiler):
    df_a = pd.DataFrame({"bio": ["short bio A", "hello world", None]})
    df_b = pd.DataFrame({"bio": ["very long biography B that exceeds fifty characters by a wide margin here we go", "hi", "test"]})
    df_links = pd.DataFrame({"left_id": [0, 1, 2], "right_id": [0, 1, 2]})
    
    profile = profiler.profile("A", "B", {"test": (df_a, df_b, df_links)})
    bio_prof = profile.tables["test"].columns["bio"]
    
    assert bio_prof.physical_type == PhysicalType.TEXT
    assert bio_prof.semantic_type == SemanticType.NONE
    assert pytest.approx(bio_prof.source_trust_score, abs=1e-3) == 0.400

def test_profiler_empty_data(profiler):
    df_a = pd.DataFrame({"col1": [None, None], "col2": [None, None]})
    df_b = pd.DataFrame({"col1": [None, None], "col2": [None, None]})
    df_links = pd.DataFrame({"left_id": [0, 1], "right_id": [0, 1]})
    
    profile = profiler.profile("A", "B", {"empty": (df_a, df_b, df_links)})
    col1_prof = profile.tables["empty"].columns["col1"]
    
    assert col1_prof.source_trust_score == 0.5
    assert col1_prof.physical_type == PhysicalType.TEXT
    assert col1_prof.semantic_type == SemanticType.NONE

def test_profiler_all_semantic_types(profiler):
    df_a = pd.DataFrame({
        "phone": ["+123456789", "+39 02 1234567", None],
        "url": ["https://google.com", "http://test.org/path", None],
        "timestamp": pd.to_datetime(["2026-07-08T18:00:00Z", "2026-08-12T00:00:00Z", None]),
        "geospatial": ["45.4642, 9.1900", "-12.34, 56.78", None],
        "uuid": ["123e4567-e89b-12d3-a456-426614174000", "00000000-0000-0000-0000-000000000000", None],
        "numeric": pd.to_numeric(["123.45", "-999.0", None]),
        "long_text": ["This is a very long string designed to exceed the default limit of fifty characters in length to test the fallback mechanism.", "Another very long string that should easily exceed the default text limit of fifty characters.", None]
    })
    df_b = df_a.copy()
    df_links = pd.DataFrame({"left_id": [0, 1, 2], "right_id": [0, 1, 2]})

    profile = profiler.profile("A", "B", {"types": (df_a, df_b, df_links)})
    cols = profile.tables["types"].columns

    assert cols["phone"].physical_type == PhysicalType.TEXT
    assert cols["phone"].semantic_type == SemanticType.PHONE
    assert cols["url"].physical_type == PhysicalType.TEXT
    assert cols["url"].semantic_type == SemanticType.URL
    assert cols["timestamp"].physical_type == PhysicalType.DATETIME
    assert cols["timestamp"].semantic_type == SemanticType.NONE
    assert cols["geospatial"].physical_type == PhysicalType.TEXT
    assert cols["geospatial"].semantic_type == SemanticType.GEOSPATIAL
    assert cols["uuid"].physical_type == PhysicalType.TEXT
    assert cols["uuid"].semantic_type == SemanticType.UUID
    assert cols["numeric"].physical_type == PhysicalType.FLOAT
    assert cols["numeric"].semantic_type == SemanticType.NONE
    assert cols["long_text"].physical_type == PhysicalType.TEXT
    assert cols["long_text"].semantic_type == SemanticType.NONE

def test_profiler_schema_mismatch_and_empty_links(profiler):
    df_a = pd.DataFrame({"col_a": ["val1", "val2"]})
    df_b = pd.DataFrame({"col_b": ["val1", "val2"]})
    
    # 1. Test empty links
    df_links_empty = pd.DataFrame(columns=["left_id", "right_id"])
    profile_empty = profiler.profile("A", "B", {"test": (df_a, df_b, df_links_empty)})
    assert profile_empty.tables["test"].total_pairs == 0
    assert len(profile_empty.tables["test"].columns) == 0

    # 2. Test mismatched columns
    df_links = pd.DataFrame({"left_id": [0, 1], "right_id": [0, 1]})
    profile_mismatch = profiler.profile("A", "B", {"test": (df_a, df_b, df_links)})
    assert len(profile_mismatch.tables["test"].columns) == 0


def test_second_pass_physical_type_inference(profiler):
    """Tests that object/string columns with numeric or datetime content are properly inferred."""
    df_a = pd.DataFrame({
        "price_str": ["12.50", "343.26", "$99.99"],
        "count_str": ["10", "20", "30"],
        "date_str": ["2011-12-01 05:08 PM", "2011-12-02 06:00 AM", "2011-12-03 07:30 PM"],
        "text_str": ["hello", "world", "data fusion"],
        "id_str": ["101", "102", "103"],
    }, dtype=str)
    df_b = df_a.copy()
    df_links = pd.DataFrame({"left_id": [0, 1, 2], "right_id": [0, 1, 2]})

    profile = profiler.profile("A", "B", {"table": (df_a, df_b, df_links)})
    cols = profile.tables["table"].columns

    assert cols["price_str"].physical_type == PhysicalType.FLOAT
    assert cols["count_str"].physical_type == PhysicalType.INTEGER
    assert cols["date_str"].physical_type == PhysicalType.DATETIME
    assert cols["text_str"].physical_type == PhysicalType.TEXT
    # ID column should remain TEXT to avoid inappropriate numeric operations
    assert cols["id_str"].physical_type == PhysicalType.TEXT


def test_isbn_not_phone(profiler):
    """Tests that ISBN columns are not misclassified as PHONE."""
    df_a = pd.DataFrame({
        "ISBN": ["0120455994", "0122290631", "978-0-123-45678-9"],
        "Title": ["Book A", "Book B", "Book C"],
    }, dtype=str)
    df_b = df_a.copy()
    df_links = pd.DataFrame({"left_id": [0, 1, 2], "right_id": [0, 1, 2]})

    profile = profiler.profile("A", "B", {"books": (df_a, df_b, df_links)})
    cols = profile.tables["books"].columns

    assert cols["ISBN"].semantic_type == SemanticType.NONE
    assert cols["ISBN"].physical_type == PhysicalType.TEXT


def test_profiler_physical_type_conformity(profiler):
    """Tests that physical type conformity V(S) penalizes non-coercible values."""
    df_a = pd.DataFrame({"count": [10, 20, 30, 40]})
    df_b = pd.DataFrame({"count": ["10", "corrupt", "30", "bad"]})
    df_links = pd.DataFrame({"left_id": [0, 1, 2, 3], "right_id": [0, 1, 2, 3]})

    profile = profiler.profile("A", "B", {"table": (df_a, df_b, df_links)})
    count_prof = profile.tables["table"].columns["count"]

    assert count_prof.physical_type == PhysicalType.INTEGER
    # Source A has V(A)=1.0, Source B has V(B)=0.5 -> Source A trusted more
    assert count_prof.source_trust_score > 0.55


def test_profiler_entropy_penalizes_dummy_constants(profiler):
    """Tests that normalized Shannon entropy penalizes repeated dummy defaults."""
    df_a = pd.DataFrame({"score": [100.5, 205.2, 310.8, 415.1, 520.0]})
    df_b = pd.DataFrame({"score": [0.0, 0.0, 0.0, 0.0, 0.0]})
    df_links = pd.DataFrame({"left_id": list(range(5)), "right_id": list(range(5))})

    profile = profiler.profile("A", "B", {"table": (df_a, df_b, df_links)})
    score_prof = profile.tables["table"].columns["score"]

    assert score_prof.physical_type == PhysicalType.FLOAT
    # Source A has H_norm=1.0, Source B has H_norm=0.0 -> Source A trusted more
    assert score_prof.source_trust_score > 0.53


def test_profiler_sentinel_handling(profiler):
    """Tests that sentinel placeholders like 'N/A', '-', '?' are penalized."""
    df_a = pd.DataFrame({"val": ["actual", "another", "third", "fourth"]})
    df_b = pd.DataFrame({"val": ["actual", "N/A", "-", "?"]})
    df_links = pd.DataFrame({"left_id": [0, 1, 2, 3], "right_id": [0, 1, 2, 3]})

    profile = profiler.profile("A", "B", {"table": (df_a, df_b, df_links)})
    val_prof = profile.tables["table"].columns["val"]

    # Effective completeness of B is 1/4 = 0.25 vs A's 4/4 = 1.0
    assert val_prof.source_trust_score > 0.70


def test_profiler_pyarrow_backed_series(profiler):
    """Tests that ArrowExtensionArray backed Series (e.g. string[pyarrow]) do not cause TypeError during entropy calculation."""
    df_a = pd.DataFrame({"title": pd.Series(["apple", "banana", "cherry", "date"], dtype="string[pyarrow]")})
    df_b = pd.DataFrame({"title": pd.Series(["apple", "banana", "banana", "date"], dtype="string[pyarrow]")})
    df_links = pd.DataFrame({"left_id": [0, 1, 2, 3], "right_id": [0, 1, 2, 3]})

    profile = profiler.profile("A", "B", {"table": (df_a, df_b, df_links)})
    title_prof = profile.tables["table"].columns["title"]

    assert title_prof.physical_type == PhysicalType.TEXT
    assert 0.0 <= title_prof.source_trust_score <= 1.0


