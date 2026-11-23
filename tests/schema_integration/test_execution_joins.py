"""Unit tests for multi-table source foreign key joins in execution engine."""

from pathlib import Path
import pandas as pd
import pytest

from schema_integration.execution.exceptions import UnresolvableJoinError
from schema_integration.execution.executor import execute_porting
from schema_integration.mapping.models import (
    DirectCopy,
    MappingReport,
    MappingRule,
)
from shared.ingestion.models import SourceData
from shared.schema_models import (
    DataPackage,
    ForeignKey,
    ForeignKeyReference,
    TableField,
    TableResource,
    TableSchema,
)


def _create_synthetic_source_data(
    include_fk: bool = True,
) -> SourceData:
    """Helper to create synthetic SourceData with 2 tables in reverse row order.

    Args:
        include_fk: If True, attach ForeignKey metadata to Contacts resource.

    Returns:
        SourceData instance with Users and Contacts tables.
    """
    df_users = pd.DataFrame(
        {
            "id": [1, 2],
            "name": ["Alice", "Bob"],
        }
    )
    df_contacts = pd.DataFrame(
        {
            "user_id": [2, 1],
            "email": ["bob@example.com", "alice@example.com"],
        }
    )

    users_schema = TableSchema(
        primaryKey="id",
        fields=[
            TableField(name="id", type="integer"),
            TableField(name="name", type="string"),
        ],
    )

    contacts_fk = (
        [
            ForeignKey(
                fields="user_id",
                reference=ForeignKeyReference(
                    resource="Users",
                    fields="id",
                ),
            )
        ]
        if include_fk
        else []
    )

    contacts_schema = TableSchema(
        primaryKey="user_id",
        fields=[
            TableField(name="user_id", type="integer"),
            TableField(name="email", type="string"),
        ],
        foreignKeys=contacts_fk,
    )

    package = DataPackage(
        schema_name="source_pkg",
        resources=[
            TableResource(name="Users", schema=users_schema),
            TableResource(name="Contacts", schema=contacts_schema),
        ],
    )

    return SourceData(
        package=package,
        tables={"Users": df_users, "Contacts": df_contacts},
        base_path=Path("."),
    )


def _create_target_schema() -> DataPackage:
    """Helper to create target DataPackage schema with Customers table."""
    customers_schema = TableSchema(
        fields=[
            TableField(name="name", type="string"),
            TableField(name="email", type="string"),
        ]
    )
    return DataPackage(
        schema_name="target_pkg",
        resources=[TableResource(name="Customers", schema=customers_schema)],
    )


def test_execution_multi_table_fk_join() -> None:
    """Test that multi-table source join aligns rows via Foreign Key."""
    source_data = _create_synthetic_source_data(include_fk=True)
    target_schema = _create_target_schema()

    rules = [
        MappingRule(
            source_label="source_pkg",
            source_table="Users",
            source_columns=["name"],
            target_table="Customers",
            target_column="name",
            transformations=[DirectCopy(type="direct_copy")],
        ),
        MappingRule(
            source_label="source_pkg",
            source_table="Contacts",
            source_columns=["email"],
            target_table="Customers",
            target_column="email",
            transformations=[DirectCopy(type="direct_copy")],
        ),
    ]
    report = MappingReport(source_label="source_pkg", rules=rules)

    result = execute_porting(report, source_data, target_schema)
    customers_df = result.tables["Customers"].dataframe

    assert len(customers_df) == 2
    # Verify row alignment: Alice -> alice@example.com, Bob -> bob@example.com
    row_alice = customers_df[customers_df["name"] == "Alice"].iloc[0]
    assert row_alice["email"] == "alice@example.com"

    row_bob = customers_df[customers_df["name"] == "Bob"].iloc[0]
    assert row_bob["email"] == "bob@example.com"


def test_execution_multi_table_missing_fk_raises_error() -> None:
    """Test that multi-table mapping without FK metadata fails fast."""
    source_data = _create_synthetic_source_data(include_fk=False)
    target_schema = _create_target_schema()

    rules = [
        MappingRule(
            source_label="source_pkg",
            source_table="Users",
            source_columns=["name"],
            target_table="Customers",
            target_column="name",
            transformations=[DirectCopy(type="direct_copy")],
        ),
        MappingRule(
            source_label="source_pkg",
            source_table="Contacts",
            source_columns=["email"],
            target_table="Customers",
            target_column="email",
            transformations=[DirectCopy(type="direct_copy")],
        ),
    ]
    report = MappingReport(source_label="source_pkg", rules=rules)

    with pytest.raises(UnresolvableJoinError) as exc_info:
        execute_porting(report, source_data, target_schema)

    assert "no Foreign Key relationship is declared" in str(exc_info.value)


def test_execution_split_unnest_transformation() -> None:
    """Test that SplitUnnest explodes delimited multi-value column into multiple rows."""
    from schema_integration.mapping.models import SplitUnnest

    df_movies = pd.DataFrame(
        {
            "id": ["tt1", "tt2", "tt3"],
            "genres": ["Action, Drama", "Comedy", "\\N"],
        }
    )

    movies_schema = TableSchema(
        primaryKey="id",
        fields=[
            TableField(name="id", type="string"),
            TableField(name="genres", type="string"),
        ],
    )

    src_pkg = DataPackage(
        schema_name="source_pkg",
        resources=[TableResource(name="Movies", schema=movies_schema)],
    )

    source_data = SourceData(
        package=src_pkg,
        tables={"Movies": df_movies},
        base_path=Path("."),
    )

    tgt_schema = TableSchema(
        fields=[
            TableField(name="title_id", type="string"),
            TableField(name="genre", type="string"),
        ]
    )
    target_pkg = DataPackage(
        schema_name="target_pkg",
        resources=[TableResource(name="MovieGenres", schema=tgt_schema)],
    )

    rules = [
        MappingRule(
            source_label="source_pkg",
            source_table="Movies",
            source_columns=["id"],
            target_table="MovieGenres",
            target_column="title_id",
            transformations=[DirectCopy(type="direct_copy")],
        ),
        MappingRule(
            source_label="source_pkg",
            source_table="Movies",
            source_columns=["genres"],
            target_table="MovieGenres",
            target_column="genre",
            transformations=[SplitUnnest(delimiter=",")],
        ),
    ]

    report = MappingReport(source_label="source_pkg", rules=rules)
    result = execute_porting(report, source_data, target_pkg)
    df_genres = result.tables["MovieGenres"].dataframe

    # tt1 produces "Action" and "Drama", tt2 produces "Comedy", tt3 has "\\N" (preserved with <NA>)
    assert len(df_genres) == 4
    tt1_rows = df_genres[df_genres["title_id"] == "tt1"]
    assert set(tt1_rows["genre"]) == {"Action", "Drama"}
    tt2_rows = df_genres[df_genres["title_id"] == "tt2"]
    assert set(tt2_rows["genre"]) == {"Comedy"}
    tt3_rows = df_genres[df_genres["title_id"] == "tt3"]
    assert pd.isna(tt3_rows["genre"].iloc[0])
