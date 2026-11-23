import argparse

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Tuple, List
import pandas as pd

from shared.console import console
from shared.config import config
from shared.agents import normalize_provider
from data_fusion.entrypoint import DataFusionEngine

def detect_provider(model_name: str) -> str:
    """Detects provider prefix or matches with supported models in config."""
    if not model_name:
        return config.DEFAULT_PROVIDER
    if ":" in model_name:
        provider, _ = model_name.split(":", 1)
        return normalize_provider(provider)
        
    # Match against supported models in config
    for provider, models in config.SUPPORTED_MODELS.items():
        if model_name in models:
            return provider
            
    # Raise error with supported models list
    all_supported_models = []
    for prov, models in config.SUPPORTED_MODELS.items():
        all_supported_models.extend(models)
        
    raise ValueError(
        f"Unsupported model '{model_name}'. "
        f"Please provide a provider prefix (e.g., 'openai:gpt-4o') or use one of the supported models: "
        f"{', '.join(all_supported_models)}"
    )

def load_dataset_from_dir(dataset_dir: Path) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Finds A, B, and Links files in the folder and returns them as DataFrames.
    """
    files = list(dataset_dir.glob("*.csv"))
    file_a = next((f for f in files if "_a.csv" in f.name or "_left.csv" in f.name or "left.csv" in f.name), None)
    file_b = next((f for f in files if "_b.csv" in f.name or "_right.csv" in f.name or "right.csv" in f.name), None)
    file_links = next((f for f in files if "_links.csv" in f.name or "links.csv" in f.name), None)
    
    if not (file_a and file_b and file_links):
        raise ValueError(
            f"Directory '{dataset_dir}' must contain one A/left file, one B/right file, and one links file. "
            f"Found: {[f.name for f in files]}"
        )
        
    console.print(f"Loading files:\n - A: {file_a.name}\n - B: {file_b.name}\n - Links: {file_links.name}")
    df_a = pd.read_csv(file_a)
    df_b = pd.read_csv(file_b)
    df_links = pd.read_csv(file_links)
    return df_a, df_b, df_links

def scan_valid_subfolders(base_dir: Path) -> List[Path]:
    """Scans the directory for subfolders containing the required files."""
    valid_subfolders = []
    if not base_dir.exists():
        return valid_subfolders
        
    for subfolder in base_dir.iterdir():
        if not subfolder.is_dir():
            continue
            
        files = list(subfolder.glob("*.csv"))
        has_a = any("_a.csv" in f.name or "_left.csv" in f.name or "left.csv" in f.name for f in files)
        has_b = any("_b.csv" in f.name or "_right.csv" in f.name or "right.csv" in f.name for f in files)
        has_links = any("_links.csv" in f.name or "links.csv" in f.name for f in files)
        
        if has_a and has_b and has_links:
            valid_subfolders.append(subfolder)
            
    return sorted(valid_subfolders, key=lambda x: x.name)

def main():
    parser = argparse.ArgumentParser(
        description="Isolated Data Fusion CLI: Profile -> Policy -> deterministic Fusion"
    )
    
    parser.add_argument(
        "input_dir",
        type=str,
        nargs="?",
        default=None,
        help="Path to the dataset directory containing the A, B, and Links CSV files."
    )
    
    parser.add_argument(
        "--model", "-m",
        type=str,
        default=None,
        help="Model name to use (e.g., 'gemini-3.8-flash'). If None, falls back to config default."
    )
    
    parser.add_argument(
        "--no-merge",
        action="store_true",
        help="If set, outputs only the fused golden records and excludes unlinked rows."
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        default="WARNING",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set logging level (default: WARNING)"
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout
    )

    # 1. Validate model and detect provider first to fail immediately
    try:
        provider = detect_provider(args.model)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)

    model_name_clean = args.model or config.DEFAULT_GOOGLE_MODEL
    model_name_path = model_name_clean.replace(":", "_")
    console.print(f"Using provider: [bold cyan]{provider}[/bold cyan] | model: [bold cyan]{model_name_clean}[/bold cyan]")

    input_base = config.DATA_FUSION_INPUT_DIR
    selected_dir = None

    # 2. Resolve Input Directory
    if args.input_dir:
        input_path = Path(args.input_dir)
        if not input_path.exists() or not input_path.is_dir():
            console.print(f"[red]Error: Input path '{args.input_dir}' is not a valid directory.[/red]")
            sys.exit(1)
        selected_dir = input_path
    else:
        # Scan and prompt interactively
        valid_subfolders = scan_valid_subfolders(input_base)
        if not valid_subfolders:
            console.print(f"[red]Error: No input directory specified, and no valid dataset subfolders found in '{input_base}'[/red]")
            sys.exit(1)
            
        console.print("\n[bold yellow]No input path provided. Choose an available dataset:[/bold yellow]")
        for idx, folder in enumerate(valid_subfolders):
            console.print(f"  [{idx + 1}] {folder.name}")
            
        while True:
            try:
                choice = input("\nSelect dataset index: ")
                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(valid_subfolders):
                    selected_dir = valid_subfolders[choice_idx]
                    break
            except ValueError:
                pass
            print(f"Invalid selection. Enter a number between 1 and {len(valid_subfolders)}.")

    # 2. Load dataset
    try:
        df_a, df_b, df_links = load_dataset_from_dir(selected_dir)
    except Exception as e:
        console.print(f"[red]Error loading dataset: {e}[/red]")
        sys.exit(1)

    # Prepare for engine execution
    # For isolation runs, we'll name the table based on the folder name
    table_name = selected_dir.name
    tables = {table_name: (df_a, df_b, df_links)}

    # 3. Run Engine
    engine = DataFusionEngine(model_name=args.model, provider=provider)
    console.print("[bold yellow]🚀 Running Data Fusion Engine...[/bold yellow]")
    
    try:
        fused_tables = engine.run(
            source_a_origin="source_a",
            source_b_origin="source_b",
            tables=tables,
            merge_unlinked=not args.no_merge
        )
        
        # 4. Save results to structured, timestamped output path
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = config.DATA_FUSION_OUTPUT_DIR / table_name / model_name_path / timestamp
        output_dir.mkdir(parents=True, exist_ok=True)
        
        df_fused = fused_tables[table_name]
        out_file = output_dir / "fused.csv"
        df_fused.to_csv(out_file, index=True)
        console.print(f"✅ Saved fused table to: [green]{out_file}[/green] ({len(df_fused)} rows)")
            
    except Exception as e:
        console.print(f"[red]Execution failed: {e}[/red]")
        if args.log_level == "DEBUG":
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
