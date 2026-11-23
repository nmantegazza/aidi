from __future__ import annotations
from typing import Tuple, Optional, Set, Dict
from dataclasses import dataclass
import json

from shared.schema_models import DataPackage, IntegrationReport
from shared.agents import LLMAgent, ExecutionMetadata

@dataclass
class SchemaArchitectDeps:
    valid_source_columns: Set[str]

def perform_schema_architect(
    schema_a: str, 
    schema_b: str,
    label_a: str = "source_a",
    label_b: str = "source_b",
    deps: Optional[SchemaArchitectDeps] = None,
    provider: Optional[str] = None,
    model_name: Optional[str] = None
) -> Tuple[IntegrationReport, ExecutionMetadata]:
    """Runs the Schema Architect agent to integrate schemas and identify conflicts."""
    sys_prompt = """
    ### ROLE
    You are a Senior Data Architect specializing in Data Integration.
    Your task is to integrate two source schemas into a single Global Schema following the Global-as-View (GAV) approach.

    ### TASK
    1. CONFLICT ANALYSIS: Identify all conflicts between the two source schemas. Group them by type according to the classification below.
    2. GLOBAL SCHEMA DESIGN: Create a unified, complete, and coherent Global Schema based on the resolved conflicts.

    ### OUTPUT CONVENTIONS
    1. Standardized Naming: Use `snake_case` in English for all output names (tables, columns, entities).
    2. Units of Measure: Convert all units to standard International System of Units (SI) where applicable.
    3. Nullability: If data is missing from a source schema, allow NULL values. Do not invent data.
    4. Data Types: Use the following generic data types: `integer`, `string`, `number`, `boolean`, `date`, `datetime`. Do NOT use SQL-specific types like INT or VARCHAR.
    5. Schema Structure (DataPackage):
       - Use `resources` to list global tables.
       - Each resource has a `name` and a `schema`.
       - The `schema` contains `fields` (columns), `primaryKey` (list of column names), and `foreignKeys` (list of objects).
       - Each `foreignKey` must have `fields` (local column) and a `reference` object with `resource` (target table) and `fields` (target column).

    ### CORE PRINCIPLES
    1. Information Preservation: Choose data types and structures that preserve the most information.
    2. Atomicity: Prefer atomic fields over concatenated or composite fields.
    3. Type Resolution: In case of type conflicts, use the wider or more flexible data type.
    4. Synonym Resolution: Use industry-standard terms to resolve synonyms.
    5. Table Names: The name of a global table MUST be selected from the source table names being unified. Do not introduce new terms or synonyms for table names.
    6. Every conflict identified must be atomic, referring to one semantic concept.
    7. True Integration Conflicts: A conflict represents a schema discrepancy between the two sources. 

    ### CONFLICT CLASSIFICATION
    1. Naming Conflict: Different names for the same semantic concept across sources (Synonyms) or the same name for different semantic concepts across sources (Homonyms).
    2. Type Conflict: Semantic equality across sources but different technical data types (e.g., integer vs string).
    3. Data Semantic Conflict: The same concept expressed in different units of measure, formats, or currencies.
    4. Structure Conflict: Different structural representations for the same concept.
    5. Cardinality Conflict: Different numerical constraints on relationships between entities.
    6. Key Conflict: Different primary key definitions for the same entity across sources.
    """

    user_prompt = f"""
    ### SCHEMA {label_a}
    \n{schema_a}\n
    ### SCHEMA {label_b}
    \n{schema_b}\n
    """

    agent = LLMAgent(
        name="SchemaArchitect",
        response_model=IntegrationReport,
        system_prompt=sys_prompt,
        provider=provider,
        model_name=model_name,
        deps_type=SchemaArchitectDeps
    )

    report, metadata_1 = agent.run_sync(user_prompt, deps=deps)
    return report, metadata_1

# Alias for backwards compatibility with pipeline callers
perform_gav_architect = perform_schema_architect


def refine_schema_via_llm(
    current_report: IntegrationReport,
    user_prompt: str,
    provider: Optional[str] = None,
    model_name: Optional[str] = None
) -> Tuple[IntegrationReport, ExecutionMetadata]:
    """Refines the current integration report based on user feedback."""
    sys_prompt = """
    ### ROLE
    You are an expert Data Architect.
    Your task is to refine/update an existing integrated Global Schema based on user instructions.

    ### INPUT
    You will receive the current `IntegrationReport` in JSON format and a user's natural language request.

    ### REQUIREMENTS & OUTPUT CONVENTIONS
    1. Apply the user's modifications to the `global_schema` and update the `conflicts_report` if relevant.
    2. Standardized Naming: Use `snake_case` in English for all output names.
    3. Units of Measure: Convert all units to standard SI where applicable.
    4. Nullability: If data is missing from a source schema, allow NULL values.
    5. Data Types: Use generic data types: `integer`, `string`, `number`, `boolean`, `date`, `datetime`.
    6. Schema Structure (DataPackage): `resources`, `schema`, `fields`, `primaryKey`, `foreignKeys`.
    7. Referential Integrity: Keep column references consistent.
    8. You MUST return a complete, valid `IntegrationReport` matching the schema definition.
    """

    user_content = f"""
    ### CURRENT INTEGRATION REPORT
    ```json
    {current_report.model_dump_json(indent=2)}
    ```

    ### USER REQUEST
    {user_prompt}
    """

    agent = LLMAgent(
        name="SchemaRefinement",
        response_model=IntegrationReport,
        system_prompt=sys_prompt,
        provider=provider,
        model_name=model_name
    )

    return agent.run_sync(user_content)
