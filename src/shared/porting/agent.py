from __future__ import annotations
from typing import Tuple, Optional, Dict
import json
from shared.agents import LLMAgent, ExecutionMetadata
from shared.porting.models import PortingInstructionsReport
from shared.schema_models import IntegrationReport

def generate_porting_instructions(
    schema_a: str,
    schema_b: str,
    integration_report: IntegrationReport,
    label_a: str = "source_a",
    label_b: str = "source_b",
    provider: Optional[str] = None,
    model_name: Optional[str] = None,
) -> Tuple[PortingInstructionsReport, ExecutionMetadata]:
    """
    Decoupled GAVEngineer orchestrator to generate data porting instructions.
    """
    eng_sys_prompt = f"""
    ### ROLE
    You are a Senior Data Engineer specializing in Structural Schema Alignment.
    Your task is to generate executable Porting Instructions to align source schemas into a unified Global Schema.
    Focus strictly on **Structural** and **Technical** alignment (naming, granularity, types).
    Use the `PortingInstructionsReport` format.
    Use `SingleTable` or `JoinTables` for `construction_recipes`.
    
    ### FIELD TRANSFORMATIONS
    - `DirectMap`: Simple column-to-column mapping.
    - `Concat`: Combine multiple source columns into one string.
    - `Split`: Extract a specific segment from a bundled source column.
        - `delimiter`: The character to split on (e.g., " ", ",", "|").
        - `index`: 0-based position of the segment to extract.
    - `Slice`: Extract a substring by character positions.
        - `start`: 0-based start position.
        - `end`: 0-based end position (exclusive).
    - `TypeCast`: Technical alignment (Integer -> String).
    - `MathOperation`: Semantic unit alignment. Use ONLY when units are explicitly stated in metadata.
    
    ### CORE PRINCIPLES
    1. Table Construction: Define how to build each global table from source tables (JOINs or single table load).
    2. Column Transformations: Define how to populate each column using the provided AST components.
    3. Accuracy: Ensure all source columns referenced actually exist in the provided source schemas.
    4. Source Explicitly: You MUST populate the `source_label` field in EVERY transformation with the correct source name (e.g., '{label_a}' or '{label_b}').
    """
    
    eng_user_prompt = f"""
    ### SOURCE SCHEMA: {label_a}
    {schema_a}
    
    ### SOURCE SCHEMA: {label_b}
    {schema_b}
    
    ### GLOBAL SCHEMA & CONFLICTS (Architect Report)
    {integration_report.model_dump_json(indent=2)}
    """
    
    eng_agent = LLMAgent(
        name="GAVEngineer",
        response_model=PortingInstructionsReport,
        system_prompt=eng_sys_prompt,
        provider=provider,
        model_name=model_name
    )
    
    porting_report, metadata = eng_agent.run_sync(eng_user_prompt)
    return porting_report, metadata
