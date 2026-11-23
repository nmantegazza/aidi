# Create tests/test_data_porter.py
import pandas as pd
from pathlib import Path
from shared.porting.executor import DataPorter
from shared.ingestion import SourceData
from shared.schema_models import DataPackage, TableResource, IntegrationReport
from shared.porting.models import PortingInstructionsReport, TablePortingInstruction, SingleTable, JoinTables, DirectMap, Concat

def test_data_porter_ast():
    df_a = pd.DataFrame({"first": ["John"], "last": ["Doe"]})
    src_a = SourceData(package=DataPackage(schema_name="pkg_a"), tables={"users": df_a}, base_path=Path("."))
    src_b = SourceData(package=DataPackage(schema_name="pkg_b"), tables={}, base_path=Path("."))
    
    rep = IntegrationReport(conflicts_report=[], global_schema=DataPackage(schema_name="g", resources=[
        TableResource(name="g_users", schema={"fields": [{"name": "full_name", "type": "string"}]})
    ]))
    
    porting = PortingInstructionsReport(global_table_instructions={
        "g_users": TablePortingInstruction(
            construction_recipes=[SingleTable(type="single", source_label="pkg_a", table_name="users")],
            field_transformations={"full_name": [Concat(type="concat", source_label="pkg_a", source_columns=["first", "last"], delimiter=" ")]}
        )
    })
    
    porter = DataPorter(src_a, src_b, rep, porting)
    res, _ = porter.port()
    
    assert res["g_users"].df_a["full_name"].iloc[0] == "John Doe"

def test_data_porter_join_tables():
    df_users = pd.DataFrame({"id": [1, 2], "name": ["Alice", "Bob"]})
    df_orders = pd.DataFrame({"order_id": [101, 102], "user_id": [1, 2], "amount": [250.0, 50.0]})
    src_a = SourceData(
        package=DataPackage(schema_name="pkg_a"), 
        tables={"users": df_users, "orders": df_orders}, 
        base_path=Path(".")
    )
    src_b = SourceData(package=DataPackage(schema_name="pkg_b"), tables={}, base_path=Path("."))
    
    rep = IntegrationReport(conflicts_report=[], global_schema=DataPackage(schema_name="g", resources=[
        TableResource(name="g_user_orders", schema={"fields": [
            {"name": "user_name", "type": "string"},
            {"name": "order_amount", "type": "number"}
        ]})
    ]))
    
    porting = PortingInstructionsReport(global_table_instructions={
        "g_user_orders": TablePortingInstruction(
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
                "user_name": [DirectMap(type="direct", source_label="pkg_a", source_column="name")],
                "order_amount": [DirectMap(type="direct", source_label="pkg_a", source_column="amount")]
            }
        )
    })
    
    porter = DataPorter(src_a, src_b, rep, porting)
    res, _ = porter.port()
    
    # Check that df_a has 2 rows and columns 'user_name' and 'order_amount'
    assert len(res["g_user_orders"].df_a) == 2
    assert res["g_user_orders"].df_a["user_name"].iloc[0] == "Alice"
    assert res["g_user_orders"].df_a["order_amount"].iloc[0] == 250.0

def test_data_porter_column_resolution_dot_notation():
    df_users = pd.DataFrame({"id": [1], "name": ["Alice"]})
    df_orders = pd.DataFrame({"id": [101], "user_id": [1]})
    src_a = SourceData(
        package=DataPackage(schema_name="pkg_a"), 
        tables={"users": df_users, "orders": df_orders}, 
        base_path=Path(".")
    )
    src_b = SourceData(package=DataPackage(schema_name="pkg_b"), tables={}, base_path=Path("."))
    
    rep = IntegrationReport(conflicts_report=[], global_schema=DataPackage(schema_name="g", resources=[
        TableResource(name="g_test", schema={"fields": [
            {"name": "user_id", "type": "integer"},
            {"name": "order_id", "type": "integer"}
        ]})
    ]))
    
    from shared.porting.models import JoinTables, DirectMap
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
                # Use dot notation to specify exactly which 'id' we want
                "user_id": [DirectMap(type="direct", source_label="pkg_a", source_column="users.id")],
                "order_id": [DirectMap(type="direct", source_label="pkg_a", source_column="orders.id")]
            }
        )
    })
    
    porter = DataPorter(src_a, src_b, rep, porting)
    res, _ = porter.port()
    
    assert res["g_test"].df_a["user_id"].iloc[0] == 1
    assert res["g_test"].df_a["order_id"].iloc[0] == 101

from shared.porting.models import Split, Slice, MathOperation, SingleTable, TypeCast, TablePortingInstruction

def test_data_porter_date_slicing():
    df_users = pd.DataFrame({"birth_date": ["15051992", "01012000"]})
    src_a = SourceData(
        package=DataPackage(schema_name="pkg_a"), 
        tables={"users": df_users}, 
        base_path=Path(".")
    )
    src_b = SourceData(package=DataPackage(schema_name="pkg_b"), tables={}, base_path=Path("."))
    
    rep = IntegrationReport(conflicts_report=[], global_schema=DataPackage(schema_name="g", resources=[
        TableResource(name="g_test", schema={"fields": [
            {"name": "day", "type": "string"},
            {"name": "month", "type": "string"},
            {"name": "year", "type": "string"}
        ]})
    ]))
    
    porting = PortingInstructionsReport(global_table_instructions={
        "g_test": TablePortingInstruction(
            construction_recipes=[SingleTable(type="single", source_label="pkg_a", table_name="users")],
            field_transformations={
                "day": [Slice(type="slice", source_label="pkg_a", source_column="birth_date", start=0, end=2)],
                "month": [Slice(type="slice", source_label="pkg_a", source_column="birth_date", start=2, end=4)],
                "year": [Slice(type="slice", source_label="pkg_a", source_column="birth_date", start=4, end=8)]
            }
        )
    })
    
    porter = DataPorter(src_a, src_b, rep, porting)
    res, _ = porter.port()
    
    assert res["g_test"].df_a["day"].iloc[0] == "15"
    assert res["g_test"].df_a["month"].iloc[0] == "05"
    assert res["g_test"].df_a["year"].iloc[0] == "1992"

def test_data_porter_transformation_chaining():
    df_users = pd.DataFrame({"raw_value": ["user_100", "user_200"]})
    src_a = SourceData(
        package=DataPackage(schema_name="pkg_a"), 
        tables={"users": df_users}, 
        base_path=Path(".")
    )
    src_b = SourceData(package=DataPackage(schema_name="pkg_b"), tables={}, base_path=Path("."))
    
    rep = IntegrationReport(conflicts_report=[], global_schema=DataPackage(schema_name="g", resources=[
        TableResource(name="g_test", schema={"fields": [
            {"name": "calculated_value", "type": "number"}
        ]})
    ]))
    
    porting = PortingInstructionsReport(global_table_instructions={
        "g_test": TablePortingInstruction(
            construction_recipes=[SingleTable(type="single", source_label="pkg_a", table_name="users")],
            field_transformations={
                "calculated_value": [
                    Split(type="split", source_label="pkg_a", source_column="raw_value", delimiter="_", index=1),
                    MathOperation(type="math_operation", source_label="pkg_a", source_column="calculated_value", operator="*", operand=2.0)
                ]
            }
        )
    })
    
    porter = DataPorter(src_a, src_b, rep, porting)
    res, _ = porter.port()
    
    # 100 * 2 = 200, 200 * 2 = 400
    assert res["g_test"].df_a["calculated_value"].iloc[0] == 200.0
    assert res["g_test"].df_a["calculated_value"].iloc[1] == 400.0

def test_data_porter_boolean_coercion():
    df_users = pd.DataFrame({"active_y": ["Y", "N", "Yes", "No", "T", "F"]})
    src_a = SourceData(
        package=DataPackage(schema_name="pkg_a"), 
        tables={"users": df_users}, 
        base_path=Path(".")
    )
    src_b = SourceData(package=DataPackage(schema_name="pkg_b"), tables={}, base_path=Path("."))
    
    rep = IntegrationReport(conflicts_report=[], global_schema=DataPackage(schema_name="g", resources=[
        TableResource(name="g_test", schema={"fields": [
            {"name": "is_active", "type": "boolean"}
        ]})
    ]))
    
    porting = PortingInstructionsReport(global_table_instructions={
        "g_test": TablePortingInstruction(
            construction_recipes=[SingleTable(type="single", source_label="pkg_a", table_name="users")],
            field_transformations={
                "is_active": [
                    TypeCast(type="type_cast", source_label="pkg_a", source_column="active_y", target_type="boolean")
                ]
            }
        )
    })
    
    porter = DataPorter(src_a, src_b, rep, porting)
    res, _ = porter.port()
    
    assert res["g_test"].df_a["is_active"].tolist() == [True, False, True, False, True, False]

