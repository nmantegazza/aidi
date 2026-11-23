import pytest
from pydantic import ValidationError
from data_fusion.models import (
    FusionStrategy,
    ColumnPolicy,
    FusionGroup,
    TableFusionPolicy,
    MultiTableFusionPolicy,
)
from data_fusion.policy_strategies import (
    resolve_trust_source,
    resolve_coalesce,
    resolve_longest_string,
    resolve_shortest_string,
    resolve_most_recent,
    resolve_numeric_max,
    resolve_numeric_min,
    resolve_numeric_avg,
    resolve_union,
    resolve_intersection,
    resolve_most_words,
    resolve_format_preserving,
    resolve,
)
from data_fusion.policy_executor import PolicyExecutor
from data_fusion.database_merger import DatabaseMerger
import pandas as pd
import numpy as np

def test_public_api_imports():
    # Attempt importing from package root
    try:
        from data_fusion import (
            FusionStrategy,
            ColumnPolicy,
            FusionGroup,
            TableFusionPolicy,
            MultiTableFusionPolicy,
            PolicyExecutor,
            DatabaseMerger,
        )
    except ImportError as e:
        pytest.fail(f"Failed to import public API: {e}")

def test_database_merger_row_count():
    # 100 fused/golden records
    golden_records = pd.DataFrame([{"id": f"fused_{i}", "name": f"fused_{i}"} for i in range(100)])
    # 50 unlinked from source A
    unlinked_a = pd.DataFrame([{"id": f"a_{i}", "name": f"a_{i}"} for i in range(50)])
    # 30 unlinked from source B
    unlinked_b = pd.DataFrame([{"id": f"b_{i}", "name": f"b_{i}"} for i in range(30)])
    
    merger = DatabaseMerger()
    merged_df = merger.merge(golden_records, unlinked_a, unlinked_b)
    
    # 100 + 50 + 30 = 180
    assert len(merged_df) == 180

def test_database_merger_no_duplicates():
    # IDs are distinct across golden records and both unlinked sets
    # (collision handling is deferred to a later milestone)
    golden_records = pd.DataFrame([{"id": "fused_1", "name": "fused_1"}])
    unlinked_a = pd.DataFrame([{"id": "a_1", "name": "a_1"}])
    unlinked_b = pd.DataFrame([{"id": "b_1", "name": "b_1"}])

    merger = DatabaseMerger()
    merged_df = merger.merge(golden_records, unlinked_a, unlinked_b)

    # All three IDs are present and unique
    assert len(merged_df) == 3
    assert set(merged_df["id"]) == {"fused_1", "a_1", "b_1"}

def test_database_merger_order():
    # IDs are distinct: golden records use 'fused_' prefix, unlinked use 'a_' / 'b_'
    golden_records = pd.DataFrame([{"id": f"fused_{i}", "name": f"fused_{i}"} for i in range(100)])
    unlinked_a = pd.DataFrame([{"id": f"a_{i}", "name": f"a_{i}"} for i in range(50)])
    unlinked_b = pd.DataFrame([{"id": f"b_{i}", "name": f"b_{i}"} for i in range(30)])

    merger = DatabaseMerger()
    merged_df = merger.merge(golden_records, unlinked_a, unlinked_b)

    assert len(merged_df) == 180

    # Golden records come first
    for i in range(100):
        assert merged_df.loc[i, "id"] == f"fused_{i}"
        assert merged_df.loc[i, "name"] == f"fused_{i}"

    # Unlinked A follows, IDs unchanged
    for i in range(50):
        assert merged_df.loc[100 + i, "id"] == f"a_{i}"

    # Unlinked B follows, IDs unchanged
    for i in range(30):
        assert merged_df.loc[150 + i, "id"] == f"b_{i}"

def test_policy_executor_standalone():
    # Construct a minimal TableFusionPolicy with a single standalone column policy
    policy = TableFusionPolicy(
        table_name="companies",
        column_policies=[
            ColumnPolicy(
                column_name="name",
                strategy=FusionStrategy.LONGEST_STRING,
                reasoning="Longer name is usually more complete"
            )
        ],
        reasoning="Simple test policy"
    )
    
    # Profile trust scores (Source A trust = 0.6)
    profile_trust_scores = {"name": 0.6}
    
    # Create input DataFrame representing a linked pair
    # Each column from Source A gets suffixed with _a, Source B with _b
    # The primary key (id) could be present, let's include it
    linked_pairs = pd.DataFrame([
        {"id": "pair1", "name_a": "Google LLC", "name_b": "Google"}
    ])
    
    executor = PolicyExecutor(policy, profile_trust_scores)
    fused_df = executor.execute(linked_pairs)
    
    # Verify the output DataFrame has the correct column(s) and values
    assert "name" in fused_df.columns
    assert fused_df.loc[0, "name"] == "Google LLC"
    assert fused_df.loc[0, "id"] == "pair1"

def test_policy_executor_vectorized_scale():
    policy = TableFusionPolicy(
        table_name="companies",
        column_policies=[
            ColumnPolicy(column_name="name", strategy=FusionStrategy.LONGEST_STRING, reasoning="Longest string"),
            ColumnPolicy(column_name="score", strategy=FusionStrategy.NUMERIC_AVG, reasoning="Average scores")
        ],
        reasoning="Vectorized scale test"
    )
    
    profile_trust_scores = {"name": 0.6, "score": 0.5}
    
    # Create 100 rows
    rows = []
    for i in range(100):
        # We vary inputs
        if i == 10:
            name_a, name_b = "Alice Long", "Alice"
            score_a, score_b = 8.0, 10.0
        elif i == 50:
            name_a, name_b = "Bob", "Bob Long Name"
            score_a, score_b = None, 5.0
        elif i == 90:
            name_a, name_b = "Charlie", "Charlie"
            score_a, score_b = 6.0, 6.0
        else:
            name_a, name_b = f"A_{i}", f"B_{i}"
            score_a, score_b = float(i), float(i+1)
            
        rows.append({
            "id": f"pair_{i}",
            "name_a": name_a, "name_b": name_b,
            "score_a": score_a, "score_b": score_b
        })
        
    linked_pairs = pd.DataFrame(rows)
    executor = PolicyExecutor(policy, profile_trust_scores)
    fused_df = executor.execute(linked_pairs)
    
    assert len(fused_df) == 100
    
    # Spot-check row 10
    assert fused_df.loc[10, "name"] == "Alice Long"
    assert fused_df.loc[10, "score"] == 9.0
    
    # Spot-check row 50
    assert fused_df.loc[50, "name"] == "Bob Long Name"
    assert fused_df.loc[50, "score"] == 5.0 # one is null
    
    # Spot-check row 90
    assert fused_df.loc[90, "name"] == "Charlie" # same length -> trust A wins
    assert fused_df.loc[90, "score"] == 6.0

def test_policy_executor_aggregate_trust_tie_break():
    # Column policy uses TRUST_SOURCE, and its score is exactly 0.5.
    # Other scores in profile: {"name": 0.5, "age": 0.9, "email": 0.7}.
    # Mean of trust scores: (0.5 + 0.9 + 0.7) / 3 = 0.7.
    # Thus, effective trust for name should fall back to 0.7, making Source A win.
    policy = TableFusionPolicy(
        table_name="companies",
        column_policies=[
            ColumnPolicy(column_name="name", strategy=FusionStrategy.TRUST_SOURCE, reasoning="neutral col")
        ],
        reasoning="tie break test"
    )
    
    profile_trust_scores = {"name": 0.5, "age": 0.9, "email": 0.7}
    linked_pairs = pd.DataFrame([
        {"id": "pair1", "name_a": "A_val", "name_b": "B_val"}
    ])
    
    executor = PolicyExecutor(policy, profile_trust_scores)
    fused_df = executor.execute(linked_pairs)
    
    # Verify it falls back to aggregate trust (0.7) -> Source A wins
    assert fused_df.loc[0, "name"] == "A_val"

def test_policy_executor_fusion_group_clear_winner():
    # Fusion group city/state/zip, city is leader with LONGEST_STRING
    group = FusionGroup(
        group_name="address",
        columns=["city", "state", "zip"],
        leader_column="city",
        strategy=FusionStrategy.LONGEST_STRING,
        reasoning="City determines source for address"
    )
    policy = TableFusionPolicy(
        table_name="companies",
        fusion_groups=[group],
        reasoning="Fusion group test policy"
    )
    
    profile_trust_scores = {"city": 0.7, "state": 0.7, "zip": 0.7}
    
    # Pair 1: Source A has longer city -> all address fields should come from Source A
    # Pair 2: Source B has longer city -> all address fields should come from Source B
    linked_pairs = pd.DataFrame([
        {
            "id": "pair1",
            "city_a": "Mountain View", "city_b": "Mtv",
            "state_a": "CA", "state_b": "California",
            "zip_a": "94043", "zip_b": "94043-1234"
        },
        {
            "id": "pair2",
            "city_a": "SF", "city_b": "San Francisco",
            "state_a": "California", "state_b": "CA",
            "zip_a": "94103-1111", "zip_b": "94103"
        }
    ])
    
    executor = PolicyExecutor(policy, profile_trust_scores)
    fused_df = executor.execute(linked_pairs)
    
    assert list(fused_df.loc[0, ["city", "state", "zip"]]) == ["Mountain View", "CA", "94043"]
    assert list(fused_df.loc[1, ["city", "state", "zip"]]) == ["San Francisco", "CA", "94103"]

def test_policy_executor_fusion_group_all_null_fallback():
    # Fusion group city/state/zip, city is leader with LONGEST_STRING
    group = FusionGroup(
        group_name="address",
        columns=["city", "state", "zip"],
        leader_column="city",
        strategy=FusionStrategy.LONGEST_STRING,
        reasoning="City determines source for address"
    )
    policy = TableFusionPolicy(
        table_name="companies",
        fusion_groups=[group],
        reasoning="Fusion group test policy"
    )
    
    profile_trust_scores = {"city": 0.7, "state": 0.7, "zip": 0.7}
    
    # Pair 1: Source A has longer city ("Mountain View") but state and zip in A are null/empty,
    # and city is also empty/null (Wait, if city is "Mountain View" it's not all null, but let's make it all null)
    # Wait, if all group columns in A are null/empty:
    # city_a = None, state_a = None, zip_a = None.
    # city_b = "San Jose", state_b = "CA", zip_b = "95112"
    # Even if trust/strategy says A wins (e.g. LONGEST_STRING where both are None/empty but trust is 0.7 for A),
    # since all columns in A are empty, we fall back to B.
    linked_pairs = pd.DataFrame([
        {
            "id": "pair1",
            "city_a": None, "city_b": "San Jose",
            "state_a": "", "state_b": "CA",
            "zip_a": None, "zip_b": "95112"
        }
    ])
    
    executor = PolicyExecutor(policy, profile_trust_scores)
    fused_df = executor.execute(linked_pairs)
    
    # Verify it falls back to B
    assert list(fused_df.loc[0, ["city", "state", "zip"]]) == ["San Jose", "CA", "95112"]

def test_resolve_dispatcher():
    # Test routing to trust_source
    assert resolve(FusionStrategy.TRUST_SOURCE, "a", "b", 0.6) == "a"
    assert resolve(FusionStrategy.TRUST_SOURCE, "a", "b", 0.4) == "b"

    # Test routing to longest_string
    assert resolve(FusionStrategy.LONGEST_STRING, "hi", "hello", 0.4) == "hello"

    # Test routing to format_preserving with pattern
    email_regex = r"^[^@]+@[^@]+\.[^@]+$"
    assert resolve(FusionStrategy.FORMAT_PRESERVING, "alice@example.com", "not_an_email", 0.4, pattern=email_regex) == "alice@example.com"

    # Missing pattern for format_preserving -> raise ValueError
    with pytest.raises(ValueError) as exc_info:
        resolve(FusionStrategy.FORMAT_PRESERVING, "a", "b", 0.5)
    assert "pattern" in str(exc_info.value)

    # Invalid strategy type (e.g. string or unknown enum) -> raise ValueError
    with pytest.raises(ValueError):
        resolve("UNKNOWN_STRATEGY", "a", "b", 0.5)

def test_resolve_format_preserving():
    email_regex = r"^[^@]+@[^@]+\.[^@]+$"
    
    # Only one matches
    assert resolve_format_preserving("alice@example.com", "not_an_email", 0.4, email_regex) == "alice@example.com"
    assert resolve_format_preserving("not_an_email", "bob@example.com", 0.6, email_regex) == "bob@example.com"

    # Both match -> delegate to trust_source
    assert resolve_format_preserving("alice@example.com", "bob@example.com", 0.6, email_regex) == "alice@example.com"
    assert resolve_format_preserving("alice@example.com", "bob@example.com", 0.4, email_regex) == "bob@example.com"

    # Neither match -> delegate to trust_source
    assert resolve_format_preserving("bad1", "bad2", 0.6, email_regex) == "bad1"
    assert resolve_format_preserving("bad1", "bad2", 0.4, email_regex) == "bad2"

    # One null (doesn't match) and one valid
    assert resolve_format_preserving(None, "bob@example.com", 0.6, email_regex) == "bob@example.com"

def test_resolve_union():
    assert resolve_union("apple", "banana", 0.6, None) == "apple|banana"
    assert resolve_union("apple", "apple", 0.6, None) == "apple"
    assert resolve_union("apple", "", 0.4, None) == "apple"
    assert resolve_union(None, None, 0.6, None) is None
    
def test_resolve_intersection():
    assert resolve_intersection("apple", "banana", 0.6, None) == "apple" # Actually wait, intersection of distinct is empty, which falls back to trust_source. trust_source=0.6 -> A ("apple")
    assert resolve_intersection("apple | cherry", "banana | cherry", 0.6, None) == "cherry"
    
def test_resolve_most_words():
    assert resolve_most_words("apple pie", "apple", 0.6) == "apple pie"
    assert resolve_most_words("apple", "apple pie", 0.4) == "apple pie"
    assert resolve_most_words("apple", "banana", 0.6) == "apple" # tie falls back to trust_source

def test_resolve_numeric_avg():
    # Both non-null
    assert resolve_numeric_avg(10, 5, 0.4) == 7.5
    assert resolve_numeric_avg(5, 10.5, 0.6) == 7.75
    assert resolve_numeric_avg("5.5", "10", 0.6) == 7.75

    # One null -> return the valid one
    assert resolve_numeric_avg(10, None, 0.4) == 10
    assert resolve_numeric_avg(np.nan, 10, 0.6) == 10

    # Both null -> delegate to trust_source
    assert resolve_numeric_avg(None, None, 0.6) is None

def test_resolve_numeric_min():
    # Different values
    assert resolve_numeric_min(10, 5, 0.4) == 5
    assert resolve_numeric_min(5, 10.5, 0.6) == 5
    assert resolve_numeric_min("5.5", "10", 0.6) == "5.5"

    # Same value -> delegate to trust_source
    assert resolve_numeric_min(10, 10, 0.6) == 10
    assert resolve_numeric_min(10, 10, 0.4) == 10

    # One null -> return the valid one
    assert resolve_numeric_min(10, None, 0.4) == 10
    assert resolve_numeric_min(np.nan, 10, 0.6) == 10

    # Both null -> delegate to trust_source
    assert resolve_numeric_min(None, None, 0.6) is None

def test_resolve_numeric_max():
    # Different values
    assert resolve_numeric_max(10, 5, 0.4) == 10
    assert resolve_numeric_max(5, 10.5, 0.6) == 10.5
    assert resolve_numeric_max("5.5", "10", 0.6) == "10"

    # Same value -> delegate to trust_source
    assert resolve_numeric_max(10, 10, 0.6) == 10
    assert resolve_numeric_max(10, 10, 0.4) == 10

    # One null -> return the valid one
    assert resolve_numeric_max(10, None, 0.4) == 10
    assert resolve_numeric_max(np.nan, 10, 0.6) == 10

    # Both null -> delegate to trust_source
    assert resolve_numeric_max(None, None, 0.6) is None

def test_resolve_most_recent():
    # Both valid, A newer
    assert resolve_most_recent("2026-07-08 12:00:00", "2026-07-07 12:00:00", 0.4) == "2026-07-08 12:00:00"
    # Both valid, B newer
    assert resolve_most_recent("2026-07-07 12:00:00", "2026-07-08 12:00:00", 0.6) == "2026-07-08 12:00:00"

    # Same timestamp -> delegate to trust_source
    assert resolve_most_recent("2026-07-08 12:00:00", "2026-07-08 12:00:00", 0.6) == "2026-07-08 12:00:00"
    assert resolve_most_recent("2026-07-08 12:00:00", "2026-07-08 12:00:00", 0.4) == "2026-07-08 12:00:00"

    # One unparseable/null -> return the valid one
    assert resolve_most_recent("2026-07-08 12:00:00", "invalid_date", 0.4) == "2026-07-08 12:00:00"
    assert resolve_most_recent(None, "2026-07-08 12:00:00", 0.6) == "2026-07-08 12:00:00"

    # Both unparseable/null -> delegate to trust_source
    assert resolve_most_recent(None, "invalid_date", 0.6) is None
    assert resolve_most_recent("invalid_date", None, 0.4) is None

def test_resolve_shortest_string():
    # Different lengths
    assert resolve_shortest_string("hello", "hi", 0.4) == "hi"
    assert resolve_shortest_string("hi", "hello", 0.6) == "hi"

    # Same length -> delegate to trust_source
    assert resolve_shortest_string("abc", "xyz", 0.6) == "abc"
    assert resolve_shortest_string("abc", "xyz", 0.4) == "xyz"

    # Handling nulls (prefer non-null over null)
    assert resolve_shortest_string("abc", None, 0.4) == "abc"
    assert resolve_shortest_string(None, "abc", 0.6) == "abc"
    assert resolve_shortest_string(None, None, 0.6) is None

def test_resolve_longest_string():
    # Different lengths
    assert resolve_longest_string("hello", "hi", 0.4) == "hello"
    assert resolve_longest_string("hi", "hello", 0.6) == "hello"

    # Same length -> delegate to trust_source
    assert resolve_longest_string("abc", "xyz", 0.6) == "abc"
    assert resolve_longest_string("abc", "xyz", 0.4) == "xyz"

    # Handling nulls
    assert resolve_longest_string("abc", None, 0.4) == "abc"
    assert resolve_longest_string(None, "abc", 0.6) == "abc"
    assert resolve_longest_string(None, None, 0.6) is None

def test_resolve_coalesce():
    # Both non-null -> delegate to trust_source
    assert resolve_coalesce("val_a", "val_b", 0.6) == "val_a"
    assert resolve_coalesce("val_a", "val_b", 0.4) == "val_b"

    # Only one non-null -> return non-null
    assert resolve_coalesce("val_a", "", 0.4) == "val_a"
    assert resolve_coalesce(None, "val_b", 0.6) == "val_b"
    assert resolve_coalesce("val_a", pd.NA, 0.4) == "val_a"
    assert resolve_coalesce(np.nan, "val_b", 0.6) == "val_b"
    assert resolve_coalesce(" ", "val_b", 0.4) == "val_b"

    # Both null -> returns first null (or delegates to trust_source with nulls)
    # Let's say if both are null, it resolves using trust_source
    assert pd.isna(resolve_coalesce(None, np.nan, 0.6))

def test_resolve_trust_source():
    # trust_score >= 0.5 -> prefer Source A
    assert resolve_trust_source("val_a", "val_b", 0.6) == "val_a"
    assert resolve_trust_source("val_a", "val_b", 0.5) == "val_a"
    
    # trust_score < 0.5 -> prefer Source B
    assert resolve_trust_source("val_a", "val_b", 0.4) == "val_b"

def test_fusion_group_validation():
    # Valid group
    group = FusionGroup(
        group_name="address",
        columns=["city", "state", "zip"],
        leader_column="city",
        strategy=FusionStrategy.LONGEST_STRING,
        reasoning="City is most detailed."
    )
    assert group.group_name == "address"

    # Leader not in columns
    with pytest.raises(ValidationError) as exc_info:
        FusionGroup(
            group_name="address",
            columns=["city", "state", "zip"],
            leader_column="country",
            strategy=FusionStrategy.LONGEST_STRING,
            reasoning="Invalid group."
        )
    assert "leader_column" in str(exc_info.value)

    # Less than 2 columns
    with pytest.raises(ValidationError) as exc_info:
        FusionGroup(
            group_name="address",
            columns=["city"],
            leader_column="city",
            strategy=FusionStrategy.LONGEST_STRING,
            reasoning="Too few columns."
        )
    assert "columns" in str(exc_info.value)
