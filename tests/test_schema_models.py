# Create tests/test_schema_models.py
import pytest
from pydantic import ValidationError
from shared.schema_models import TableResource
from shared.porting.models import (
    DirectMap, Concat, Split, Slice,
    SingleTable, JoinTables
)

def test_column_transformations():
    # DirectMap
    t1 = DirectMap(type="direct", source_label="source_a", source_column="source_a.users.name")
    assert t1.type == "direct"
    
    # Concat
    t2 = Concat(type="concat", source_label="source_a", source_columns=["a", "b"], delimiter=" ")
    assert t2.type == "concat"

    # Split
    t3 = Split(type="split", source_label="source_a", source_column="full_name", delimiter=" ", index=0)
    assert t3.type == "split"

    # Slice
    t4 = Slice(type="slice", source_label="source_a", source_column="date", start=0, end=2)
    assert t4.type == "slice"

def test_table_construction():
    c1 = SingleTable(type="single", source_label="source_a", table_name="users")
    assert c1.type == "single"
    
    c2 = JoinTables(
        type="join", 
        left_source="source_a", left_table="users",
        right_source="source_b", right_table="orders",
        join_type="left", left_on="id", right_on="user_id"
    )
    
    res = TableResource(
        name="global_users",
        schema={"fields": [{"name": "id"}]}
    )
    assert res.name == "global_users"
