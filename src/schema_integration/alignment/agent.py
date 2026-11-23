"""Schema Architect LLM agent for schema alignment."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from pydantic_ai import ModelRetry

from shared.agents import ExecutionMetadata, LLMAgent
from shared.config import config
from shared.schema_models import DataPackage

from .models import AlignmentReport


@dataclass
class AlignmentDeps:
    """Dependencies provided to the alignment output validator."""

    source_schema_a: DataPackage
    source_schema_b: DataPackage


ALIGNMENT_SYSTEM_PROMPT = """You are a senior Schema Architect expert in data integration.
Your task is to analyze two source schemas (Frictionless Data Packages) and create a single, unified global target schema that resolves all structural and semantic conflicts between them.

GUIDELINES:
1. Target Schema Construction:
   - Target schema, table, and field names MUST use snake_case.
   - Use standard SI units for physical quantities (e.g., meters, kilograms).
   - Ensure fields are atomic (split composite or multi-value fields into individual components).
   - Restrict field types strictly to generic Frictionless types: integer, string, number, boolean, date, datetime.
   - Reuse source table/entity structures where appropriate, merging overlapping attributes into clean, normalized resources.

   - Source Provenance Population:
     * For every target field derived from source columns, populate `source_provenance` with all fully-qualified dot-notation source column paths that map to it (e.g. ["source_a.table.column", "source_b.table.column"]).
     * For unified entity tables, the target primary key MUST list the corresponding source primary keys in `source_provenance` (e.g. ["source_a.entity.id", "source_b.item.item_id"]).
     * Only purely synthetic surrogate keys introduced strictly for target table mechanics that have no counterpart in any source schema must have `source_provenance: []`.

   - Semantic Homogeneity:
     * A target column's `source_provenance` MUST ONLY group source columns that represent the exact same semantic attribute or identity.
     * NEVER merge foreign keys, primary keys of different entity types, sequence counters, or distinct categorical attributes into the same column provenance.

   - Structural Normalization:
     * When normalizing nested, array, or many-to-many structures into child or bridge tables, capture entity relationships exclusively through foreign key columns referencing the parent entities.

2. Conceptual Conflict Report:
   - Audit and categorize all identified conflicts into the 6 canonical conflict types:
     * Naming: Synonym/homonym differences in table or column names.
     * Type: Data type mismatches or representation differences.
     * Data Semantic: Unit, scale, encoding, or semantic scale differences.
     * Structure: Differences in schema normalization, nesting, or table decomposition.
     * Cardinality: 1:1, 1:N, or N:M structural relationship mismatches.
     * Key: Primary or foreign key identification differences.
   - For each conflict, record source references (dot-notation paths), description, and resolution rationale.
   - IMPORTANT: The conflict report is strictly a high-level conceptual audit log. Do NOT generate column-to-column mapping rules or execution directives here.
"""


async def validate_alignment(
    ctx: any, output: AlignmentReport
) -> AlignmentReport:
    """Validate alignment output for valid table structures and field types.

    Args:
        ctx: Run context containing AlignmentDeps in ctx.deps.
        output: Generated AlignmentReport.

    Returns:
        The validated AlignmentReport.

    Raises:
        ModelRetry: If target schema has no resources or invalid field types.
    """
    valid_types = {
        "integer",
        "string",
        "number",
        "boolean",
        "date",
        "datetime",
    }

    if not output.target_schema.resources:
        raise ModelRetry(
            "Target schema must contain at least one resource/table."
        )

    for resource in output.target_schema.resources:
        if not resource.schema_info.fields:
            raise ModelRetry(
                f"Resource '{resource.name}' must contain at least one field."
            )
        for field in resource.schema_info.fields:
            if field.type not in valid_types:
                allowed = ", ".join(sorted(valid_types))
                raise ModelRetry(
                    f"Field '{resource.name}.{field.name}' has invalid "
                    f"type '{field.type}'. Allowed types: {allowed}"
                )

    return output


async def align_schemas(
    schema_a: str,
    schema_b: str,
    label_a: str = "source_a",
    label_b: str = "source_b",
    provider: Optional[str] = None,
    model_name: Optional[str] = None,
) -> Tuple[AlignmentReport, ExecutionMetadata]:
    """Align two source schemas into a unified target schema with conflict audit.

    Args:
        schema_a: Serialized JSON representation of source schema A.
        schema_b: Serialized JSON representation of source schema B.
        label_a: Label identifier for source A.
        label_b: Label identifier for source B.
        provider: Optional LLM provider override.
        model_name: Optional LLM model identifier override.

    Returns:
        Tuple of (AlignmentReport, ExecutionMetadata).
    """
    effective_model = model_name or config.DEFAULT_GOOGLE_MODEL

    source_a_pkg = DataPackage.model_validate_json(schema_a)
    source_b_pkg = DataPackage.model_validate_json(schema_b)
    deps = AlignmentDeps(
        source_schema_a=source_a_pkg,
        source_schema_b=source_b_pkg,
    )

    user_prompt = (
        f"### SCHEMA {label_a}\n{schema_a}\n\n"
        f"### SCHEMA {label_b}\n{schema_b}"
    )

    agent = LLMAgent[AlignmentDeps, AlignmentReport](
        name="SchemaArchitect",
        response_model=AlignmentReport,
        system_prompt=ALIGNMENT_SYSTEM_PROMPT,
        provider=provider,
        model_name=effective_model,
        deps_type=AlignmentDeps,
        retries=2,
    )
    agent.output_validator(validate_alignment)

    return await agent.run(user_prompt, deps=deps)
