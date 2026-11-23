"""Unit tests for schema mapping models, validator, and partial overlap."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from pydantic_ai import ModelRetry

from schema_integration.mapping.agent import MapperDeps, validate_mapping
from schema_integration.mapping.models import DirectCopy, MappingReport, MappingRule
from shared.schema_models import (
    DataPackage,
    TableField,
    TableResource,
    TableSchema,
)


@pytest.fixture
def sample_mapping_deps() -> MapperDeps:
    """Create mock MapperDeps with 2 source fields and 4 target fields."""
    src_fields = [
        TableField(name="first_name", type="string"),
        TableField(name="last_name", type="string"),
    ]
    tgt_fields = [
        TableField(name="first_name", type="string"),
        TableField(name="last_name", type="string"),
        TableField(name="email", type="string"),
        TableField(name="phone", type="string"),
    ]
    src_pkg = DataPackage(
        name="source_a",
        resources=[
            TableResource(name="users", schema=TableSchema(fields=src_fields))
        ],
    )
    tgt_pkg = DataPackage(
        name="global_target",
        resources=[
            TableResource(name="customers", schema=TableSchema(fields=tgt_fields))
        ],
    )
    return MapperDeps(source_schema=src_pkg, target_schema=tgt_pkg)


def test_mapping_rule_default_empty_source_columns() -> None:
    """Test MappingRule allows default empty source_columns."""
    rule = MappingRule(
        target_table="customers",
        target_column="email",
        source_label="source_a",
        source_table="users",
    )
    assert rule.source_columns == []
    assert rule.transformations == []


@pytest.mark.asyncio
async def test_validate_mapping_partial_coverage(
    sample_mapping_deps: MapperDeps,
) -> None:
    """Test validate_mapping succeeds when target schema has unmapped columns."""
    report = MappingReport(
        rules=[
            MappingRule(
                target_table="customers",
                target_column="first_name",
                source_label="source_a",
                source_table="users",
                source_columns=["first_name"],
                transformations=[DirectCopy()],
            ),
            MappingRule(
                target_table="customers",
                target_column="last_name",
                source_label="source_a",
                source_table="users",
                source_columns=["last_name"],
                transformations=[DirectCopy()],
            ),
        ]
    )
    ctx = SimpleNamespace(deps=sample_mapping_deps)
    validated = await validate_mapping(ctx, report)
    assert len(validated.rules) == 2


@pytest.mark.asyncio
async def test_validate_mapping_with_empty_source_columns(
    sample_mapping_deps: MapperDeps,
) -> None:
    """Test validate_mapping succeeds with explicit empty source_columns."""
    report = MappingReport(
        rules=[
            MappingRule(
                target_table="customers",
                target_column="first_name",
                source_label="source_a",
                source_table="users",
                source_columns=["first_name"],
                transformations=[DirectCopy()],
            ),
            MappingRule(
                target_table="customers",
                target_column="email",
                source_label="source_a",
                source_table="users",
                source_columns=[],
            ),
        ]
    )
    ctx = SimpleNamespace(deps=sample_mapping_deps)
    validated = await validate_mapping(ctx, report)
    assert len(validated.rules) == 2


@pytest.mark.asyncio
async def test_validate_mapping_invalid_source_column_raises_retry(
    sample_mapping_deps: MapperDeps,
) -> None:
    """Test validate_mapping raises ModelRetry on non-existent source column."""
    report = MappingReport(
        rules=[
            MappingRule(
                target_table="customers",
                target_column="first_name",
                source_label="source_a",
                source_table="users",
                source_columns=["non_existent_col"],
            )
        ]
    )
    ctx = SimpleNamespace(deps=sample_mapping_deps)
    with pytest.raises(ModelRetry, match="does not exist in source schema"):
        await validate_mapping(ctx, report)


@pytest.mark.asyncio
async def test_validate_mapping_invalid_target_column_raises_retry(
    sample_mapping_deps: MapperDeps,
) -> None:
    """Test validate_mapping raises ModelRetry on non-existent target column."""
    report = MappingReport(
        rules=[
            MappingRule(
                target_table="customers",
                target_column="non_existent_target",
                source_label="source_a",
                source_table="users",
                source_columns=["first_name"],
            )
        ]
    )
    ctx = SimpleNamespace(deps=sample_mapping_deps)
    with pytest.raises(ModelRetry, match="does not exist in target schema"):
        await validate_mapping(ctx, report)


@pytest.mark.asyncio
async def test_validate_mapping_with_split_unnest(
    sample_mapping_deps: MapperDeps,
) -> None:
    """Test validate_mapping accepts SplitUnnest transformation."""
    from schema_integration.mapping.models import SplitUnnest

    report = MappingReport(
        rules=[
            MappingRule(
                target_table="customers",
                target_column="first_name",
                source_label="source_a",
                source_table="users",
                source_columns=["first_name"],
                transformations=[SplitUnnest(delimiter=",")],
            )
        ]
    )
    ctx = SimpleNamespace(deps=sample_mapping_deps)
    validated = await validate_mapping(ctx, report)
    assert len(validated.rules) == 1
    assert isinstance(validated.rules[0].transformations[0], SplitUnnest)
    assert validated.rules[0].transformations[0].delimiter == ","
