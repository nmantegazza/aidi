import pandas as pd
from pathlib import Path
from shared.porting.executor import DataPorter
from shared.ingestion.models import SourceData
from shared.schema_models import DataPackage, TableResource, IntegrationReport
from shared.porting.models import PortingInstructionsReport, TablePortingInstruction, JoinTables, DirectMap

def test_dot_notation_bug():
    df_users = pd.DataFrame({"id": [1], "name": ["Alice"]})
    df_orders = pd.DataFrame({"order_id": [101], "user_id": [1], "amount": [250]})
    src_a = SourceData(
        package=DataPackage(schema_name="pkg_a"), 
        tables={"users": df_users, "orders": df_orders}, 
        base_path=Path(".")
    )
    src_b = SourceData(package=DataPackage(schema_name="pkg_b"), tables={}, base_path=Path("."))
    
    rep = IntegrationReport(conflicts_report=[], global_schema=DataPackage(schema_name="g", resources=[
        TableResource(name="g_test", schema={"fields": [
            {"name": "user_id", "type": "integer"},
            {"name": "order_id", "type": "integer"},
            {"name": "user_name", "type": "string"}
        ]})
    ]))
    
    porting = PortingInstructionsReport(global_table_instructions={
        "g_test": TablePortingInstruction(
            construction_recipes=[
                JoinTables(
                    type="join",
                    left_source="pkg_a", left_table="users",
                    right_source="pkg_a", right_table="orders",
                    join_type="inner",
                    left_on="id", right_on="user_id"
                )
            ],
            field_transformations={
                "user_id": [DirectMap(type="direct", source_label="pkg_a", source_column="users.id")],
                "order_id": [DirectMap(type="direct", source_label="pkg_a", source_column="orders.order_id")],
                "user_name": [DirectMap(type="direct", source_label="pkg_a", source_column="users.name")]
            }
        )
    })
    
    porter = DataPorter(src_a, src_b, rep, porting)
    res, _ = porter.port()
    
    assert res["g_test"].df_a["user_id"].iloc[0] == 1
    assert res["g_test"].df_a["order_id"].iloc[0] == 101
    assert res["g_test"].df_a["user_name"].iloc[0] == "Alice"
