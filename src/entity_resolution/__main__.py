import asyncio
import argparse
import sys
import pandas as pd
from typing import Optional

from shared.cleaning.engine import clean_data
from shared.profiling.engine import DataProfiler
from shared.schema_models import TableResource, TableSchema

from .pipeline import run_entity_resolution
from .evaluation import evaluate_entity_resolution_run, console_helper
from .models import ERPipelineConfiguration
from .synthetic_generator import SYNTHETIC_SCHEMAS, SyntheticConfig, generate_synthetic_pair, get_schema_spec


async def run_pipeline(args):
    """
    Orchestrates the data generation, pipeline execution, and evaluation.
    """
    # 1. Config for synthetic data
    lang = args.locale.split("_")[0]
    table_name = f"{args.schema}_{lang}_{args.noise}_{args.num}"
    
    cfg = SyntheticConfig(
        schema_name=args.schema,
        num_entities=args.num,
        overlap_ratio=0.5,
        noise_level=args.noise,
        locale=args.locale,
        table_name=table_name
    )
    
    # 2. Generate/Prepare data
    df_a, df_b, ground_truth = generate_synthetic_pair(cfg)
    spec = get_schema_spec(cfg.schema_name)
    
    # Create TableResource for the pipeline
    table_resource = TableResource(
        name=args.schema,
        schema=TableSchema(fields=spec.table_schema_fields())
    )
    
    # 3. Cleaning (Standardized shared layer)
    df_a_clean, report_a = clean_data(df_a)
    df_b_clean, report_b = clean_data(df_b)

    # 4. Profiling (Standardized shared layer)
    profile_a = DataProfiler.profile_dataframe(df_a_clean, f"{table_name}_a")
    profile_b = DataProfiler.profile_dataframe(df_b_clean, f"{table_name}_b")
    
    # 5. Determine override configuration (None if --llm is set)
    def _get_override(s_name: str) -> Optional[ERPipelineConfiguration]:
        if args.llm:
            return None
            
        spec_inner = SYNTHETIC_SCHEMAS[s_name]
        col_names = spec_inner.column_names()
        return ERPipelineConfiguration(
            sorting_keys=col_names[:2] if len(col_names) > 1 else col_names[:1],
            window_size=11,
            matching_columns=spec_inner.default_matching_columns(),
            reasoning=f"Oracle config for '{s_name}' evaluation.",
        )

    console_helper.print_eval_start(cfg.table_name, len(df_a), len(df_b), len(ground_truth))

    # 6. Execute Pipeline
    result = await run_entity_resolution(
        df_a_clean, df_b_clean,
        profile_a, profile_b,
        table_resource,
        override_config=_get_override(args.schema),
        model_name=args.model,
        cleaning_report_a=report_a,
        cleaning_report_b=report_b
    )
    
    # 7. Evaluate if ground truth exists
    if ground_truth:
        evaluate_entity_resolution_run(
            result, 
            ground_truth, 
            table_name=cfg.table_name, 
            save_html=args.save_report
        )


def main():
    parser = argparse.ArgumentParser(description="Unified Entity Resolution Interface")
    
    # Selection
    parser.add_argument("--schema", type=str, choices=list(SYNTHETIC_SCHEMAS.keys()), 
                        help="Specify a synthetic domain schema to evaluate. (Required if not using custom files)")
    
    # Configuration
    parser.add_argument("--llm", action="store_true", 
                        help="If set, uses LLM to identify ER configuration. Otherwise, uses oracle configuration.")
    parser.add_argument("--model", type=str, default="google-cloud:gemini-3.8-flash", 
                        help="LLM model name to use for configuration (only if --llm is set).")
    
    parser.add_argument("--save-report", action="store_true",
                        help="Save the HTML evaluation report to outputs/")

    parser.add_argument("--num", type=int, default=500, 
                        help="Number of entities to generate for synthetic schemas (default: 500).")
    parser.add_argument("--noise", type=str, choices=["low", "medium", "high"], default="medium",
                        help="Noise level for synthetic data generation (default: medium).")
    parser.add_argument("--locale", type=str, default="en_US",
                        help="Locale for synthetic data generation (default: en_US).")
    
    args = parser.parse_args()

    if not args.schema:
        parser.print_help()
        sys.exit(0)

    asyncio.run(run_pipeline(args))


if __name__ == "__main__":
    main()
