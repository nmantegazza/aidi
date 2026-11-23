import argparse
import logging
import sys
from pathlib import Path
from typing import get_args
from pydantic_ai.models import KnownModelName

def list_available_models(provider_filter: str = None):
    """Prints a list of available models filtered by provider."""
    from shared.console import console
    from rich.table import Table
    
    # Extract known models from Pydantic AI's TypeAlias
    # KnownModelName is a TypeAliasType in recent Pydantic AI versions
    try:
        all_models = get_args(KnownModelName.__value__)
    except AttributeError:
        # Fallback for older versions if applicable
        all_models = get_args(KnownModelName)

    if provider_filter and provider_filter.lower() != "all":
        # Handle cases like 'google' or 'openai' (matching prefix)
        prefix = provider_filter.lower()
        if not prefix.endswith(":"):
            # Special case for google-cloud
            if prefix in ["google-cloud", "google-vertex", "vertex"]:
                prefix = "google-cloud"
            
            # If it's not a common alias, we just search for the prefix
            # Many providers in Pydantic AI use 'provider:model'
        
        models = [m for m in all_models if m.startswith(prefix)]
    else:
        models = list(all_models)

    if not models:
        console.print(f"[yellow]No models found matching provider prefix: '{provider_filter}'[/yellow]")
        return

    table = Table(title=f"Available Models (Provider: {provider_filter or 'all'})")
    table.add_column("Model Name String", style="cyan")
    
    # Sort for better readability
    for model in sorted(models):
        table.add_row(model)
    
    console.print(table)

def list_available_providers():
    """Prints a list of available providers based on configuration and Pydantic AI's known models."""
    from shared.console import console
    from shared.config import config
    from rich.table import Table

    # Pre-configured providers in this project
    configured_providers = set(config.SUPPORTED_MODELS.keys())

    # Dynamically extract all unique providers from KnownModelName
    try:
        all_models = get_args(KnownModelName.__value__)
    except AttributeError:
        all_models = get_args(KnownModelName)

    dynamic_providers = set()
    for m in all_models:
        if ":" in m:
            dynamic_providers.add(m.split(":", 1)[0])

    all_providers = configured_providers.union(dynamic_providers)

    table = Table(title="Available Model Providers")
    table.add_column("Provider Name", style="cyan")
    table.add_column("Type", style="green")

    # Sort for better readability
    for provider in sorted(all_providers):
        p_type = "Configured (Native)" if provider in configured_providers else "Dynamic (Pydantic AI)"
        table.add_row(provider, p_type)

    console.print(table)

def main():
    parser = argparse.ArgumentParser(
        description="Unified Data Integration Pipeline: Ingestion -> Schema Integration -> Porting -> ER"
    )
    
    parser.add_argument(
        "data_root",
        type=str,
        nargs="?",
        help="Path to the root directory containing 'source_a' and 'source_b' folders."
    )
    
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Model name to use (e.g., 'gemini-flash-latest'). Overrides config default."
    )
    
    parser.add_argument(
        "--provider",
        type=str,
        default=None,
        help="Provider name (e.g., 'google-cloud', 'openai'). Overrides config default."
    )

    parser.add_argument(
        "--list-models", "-l",
        type=str,
        metavar="PROVIDER",
        help="List available models for a provider (e.g., 'google-cloud', 'openai', 'all')."
    )

    parser.add_argument(
        "--list-providers",
        action="store_true",
        help="List available model providers."
    )
    
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Enable strict type validation during ingestion."
    )

    parser.add_argument(
        "--refinement",
        action="store_true",
        help="Enable LLM-based refinement of uncertain matches in ER (slow/expensive)."
    )
    
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Launch the Gradio interactive wizard UI."
    )

    parser.add_argument(
        "--save-report",
        action="store_true",
        help="Save the HTML pipeline report to outputs/."
    )

    
    parser.add_argument(
        "--log-level",
        type=str,
        default="WARNING",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level (default: WARNING)."
    )

    args = parser.parse_args()

    # Handle --list-models helper
    if args.list_models:
        list_available_models(args.list_models)
        sys.exit(0)

    # Handle --list-providers helper
    if args.list_providers:
        list_available_providers()
        sys.exit(0)

    # Handle GUI launch
    if args.gui:
        from shared.console import console
        console.print("[bold green]Launching Data Integration Pipeline Wizard...[/bold green]")
        from .gui.app import app
        from .gui.styles import custom_css, force_light_mode_js
        app.launch(css=custom_css, head=force_light_mode_js)
        sys.exit(0)

    # Validate data_root for normal runs
    if not args.data_root:
        parser.error("the following arguments are required: data_root (or use --gui / --list-models)")

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout
    )
    
    logger = logging.getLogger("pipeline_cli")

    try:
        logger.info(f"Starting pipeline run on: {args.data_root}")
        
        from shared.console import console
        with console.status("[bold blue]Loading pipeline components..."):
            from .runner import run_pipeline
            from .visualization import print_pipeline_summary
        console.print("[bold green]Pipeline components loaded.[/bold green]")
        
        report = run_pipeline(
            data_root=args.data_root,
            model_name=args.model,
            provider=args.provider,
            strict_ingestion=args.strict,
            enable_er_refinement=args.refinement,
            save_html=args.save_report
        )

        
        # Display results
        # print_pipeline_summary(report)  # Suppressed as per user request for concise output
        
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        if args.log_level == "DEBUG":
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
