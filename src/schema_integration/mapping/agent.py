"""Schema Mapper LLM agent for schema mapping."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Optional, Tuple

from pydantic_ai import ModelRetry

from schema_integration.alignment.models import AlignmentReport
from shared.agents import ExecutionMetadata, LLMAgent
from shared.config import config
from shared.console import console
from shared.schema_models import DataPackage

from .models import MappingReport


@dataclass
class MapperDeps:
    """Dependencies provided to the mapping output validator."""

    source_schema: DataPackage
    target_schema: DataPackage


MAPPING_SYSTEM_PROMPT = """You are a senior Schema Engineer expert in data integration.
Your task is to establish explicit column-to-column mapping rules from a single source schema to a target global schema.

GUIDELINES:
1. Rule Requirements:
   - For each target column that has a valid semantic correspondence in the source schema, produce a MappingRule.
   - If a target column has NO corresponding source column in the source schema, you may omit the rule or provide a rule with source_columns: [] and no transformations.
   - Specify fully-qualified source table, target table, target column, and source label.
   - source_columns is a list of column names (e.g. ["col_a"] for 1:1, ["first_name", "last_name"] for N:1).
   - All referenced source columns must exist in the source schema under source_table.
   - All referenced target columns must exist in the target schema under target_table.

2. Transformations:
   - If no transformation is needed for mapped columns, include a single DirectCopy transformation.
   - If multiple source columns are combined, use Concatenate with the appropriate delimiter.
   - Use SplitUnnest with a delimiter when a delimited multi-value or array source column (e.g. "Action,Drama") must be unnested into multiple individual rows in the target table.
   - Use SplitExtract, Substring, TypeCast, or Arithmetic for scalar value transformations.
   - Chain transformations in logical execution order (e.g., SplitUnnest then TypeCast).

3. Relational Structure & Cross-Table Mapping:
   - Do not assume all columns in a target table originate from a single source table. Target schemas often consolidate or denormalize data from multiple related source tables.
   - Avoid anchoring solely on table name identity: an entity in the target schema may be populated by attributes from the main source entity table as well as from connected associative/junction tables.
   - When a target column (especially a foreign key, identifier, or related entity attribute) has no semantic match in the primary candidate source table, inspect related tables connected through foreign keys or bridge tables.
   - Only map across tables if an explicit or logical relationship exists between them; do not map columns from unrelated source tables.
"""


async def validate_mapping(
    ctx: any, output: MappingReport
) -> MappingReport:
    """Validate mapping output for source/target column existence.

    Args:
        ctx: Run context containing MapperDeps in ctx.deps.
        output: Generated MappingReport.

    Returns:
        The validated MappingReport.

    Raises:
        ModelRetry: If invalid columns or wrong source labels are present.
    """
    source_label = (
        output.rules[0].source_label if output.rules else "unknown"
    )

    valid_sources = {
        f"{source_label}.{table.name}.{field.name}"
        for table in ctx.deps.source_schema.resources
        for field in table.schema_info.fields
    }

    valid_targets = {
        f"{table.name}.{field.name}"
        for table in ctx.deps.target_schema.resources
        for field in table.schema_info.fields
    }

    for rule in output.rules:
        if rule.source_label != source_label:
            retry_msg = (
                f"Rule source_label '{rule.source_label}' does not match "
                f"expected source label '{source_label}'."
            )
            console.print(f"  [yellow]⚠ Validation Retry: {retry_msg}[/yellow]")
            raise ModelRetry(retry_msg)

        for col in rule.source_columns:
            ref = f"{rule.source_label}.{rule.source_table}.{col}"
            if ref not in valid_sources:
                retry_msg = (
                    f"Source column '{ref}' does not exist in source schema."
                )
                console.print(
                    f"  [yellow]⚠ Validation Retry: {retry_msg}[/yellow]"
                )
                raise ModelRetry(retry_msg)

        target_ref = f"{rule.target_table}.{rule.target_column}"
        if target_ref not in valid_targets:
            retry_msg = (
                f"Target column '{target_ref}' does not exist in target schema."
            )
            console.print(
                f"  [yellow]⚠ Validation Retry: {retry_msg}[/yellow]"
            )
            raise ModelRetry(retry_msg)

    return output


async def map_schema(
    source_schema: DataPackage,
    source_label: str,
    alignment_report: AlignmentReport,
    provider: Optional[str] = None,
    model_name: Optional[str] = None,
) -> Tuple[MappingReport, ExecutionMetadata]:
    """Generate mapping report for a single source schema against target schema.

    Args:
        source_schema: Source schema DataPackage.
        source_label: Source label identifier.
        alignment_report: AlignmentReport containing target schema & conflicts.
        provider: Optional LLM provider override.
        model_name: Optional LLM model identifier override.

    Returns:
        Tuple of (MappingReport, ExecutionMetadata).
    """
    effective_model = model_name or config.DEFAULT_GOOGLE_MODEL

    source_json = source_schema.model_dump_json(indent=2, by_alias=True)
    target_json = alignment_report.target_schema.model_dump_json(
        indent=2, by_alias=True
    )
    conflicts_json = json.dumps(
        [g.model_dump() for g in alignment_report.conflict_report],
        indent=2,
    )

    user_prompt = (
        f"### SOURCE LABEL: {source_label}\n\n"
        f"### SOURCE SCHEMA\n{source_json}\n\n"
        f"### TARGET SCHEMA\n{target_json}\n\n"
        f"### CONCEPTUAL CONFLICT AUDIT LOG\n{conflicts_json}"
    )

    deps = MapperDeps(
        source_schema=source_schema,
        target_schema=alignment_report.target_schema,
    )

    agent = LLMAgent[MapperDeps, MappingReport](
        name="SchemaMapper",
        response_model=MappingReport,
        system_prompt=MAPPING_SYSTEM_PROMPT,
        provider=provider,
        model_name=effective_model,
        deps_type=MapperDeps,
        retries=2,
    )
    agent.output_validator(validate_mapping)

    return await agent.run(user_prompt, deps=deps)
