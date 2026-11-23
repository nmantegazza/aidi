"""Synchronous runner for end-to-end schema integration pipeline."""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

from schema_integration.alignment.agent import align_schemas
from schema_integration.execution.executor import execute_porting
from schema_integration.mapping.agent import map_schema
from schema_integration.models import SchemaIntegrationResult
from shared.ingestion.models import SourceData

logger = logging.getLogger(__name__)


def run_schema_integration(
    source_a: SourceData,
    source_b: SourceData,
    provider: Optional[str] = None,
    model_name: Optional[str] = None,
) -> SchemaIntegrationResult:
    """Run full 3-step schema integration pipeline synchronously.

    Args:
        source_a: Ingested SourceData for dataset A.
        source_b: Ingested SourceData for dataset B.
        provider: Optional LLM provider override.
        model_name: Optional LLM model identifier override.

    Returns:
        SchemaIntegrationResult containing alignment, mapping, and execution outputs.
    """
    label_a = source_a.package.name
    label_b = source_b.package.name

    # Step 1 — Alignment
    schema_a_str = source_a.package.model_dump_json(indent=2, by_alias=True)
    schema_b_str = source_b.package.model_dump_json(indent=2, by_alias=True)

    alignment_report, al_meta = asyncio.run(
        align_schemas(
            schema_a_str,
            schema_b_str,
            label_a=label_a,
            label_b=label_b,
            provider=provider,
            model_name=model_name,
        )
    )
    logger.info("Step 1 (Alignment) complete.")

    # Step 2 — Mapping (sequential: source A then source B)
    mapping_report_a, map_meta_a = asyncio.run(
        map_schema(
            source_a.package,
            label_a,
            alignment_report,
            provider=provider,
            model_name=model_name,
        )
    )
    logger.info("Step 2 (Mapping) complete for %s.", label_a)

    mapping_report_b, map_meta_b = asyncio.run(
        map_schema(
            source_b.package,
            label_b,
            alignment_report,
            provider=provider,
            model_name=model_name,
        )
    )
    logger.info("Step 2 (Mapping) complete for %s.", label_b)

    # Step 3 — Execution (sequential: source A then source B)
    exec_result_a = execute_porting(
        mapping_report_a,
        source_a,
        alignment_report.target_schema,
    )
    logger.info("Step 3 (Execution) complete for %s.", label_a)

    exec_result_b = execute_porting(
        mapping_report_b,
        source_b,
        alignment_report.target_schema,
    )
    logger.info("Step 3 (Execution) complete for %s.", label_b)

    return SchemaIntegrationResult(
        alignment_report=alignment_report,
        alignment_metadata=al_meta,
        mapping_reports={
            label_a: mapping_report_a,
            label_b: mapping_report_b,
        },
        mapping_metadata={
            label_a: map_meta_a,
            label_b: map_meta_b,
        },
        execution_results={
            label_a: exec_result_a,
            label_b: exec_result_b,
        },
    )
