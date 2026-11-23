import os
from pathlib import Path
from typing import ClassVar

import pandas as pd
from dotenv import load_dotenv

# Monkey-patch Series.append which was removed in pandas 2.0+ but is used by recordlinkage
if not hasattr(pd.Series, "append"):
    def _append(self, to_append, ignore_index=False, verify_integrity=False):
        return pd.concat([self, to_append], ignore_index=ignore_index, verify_integrity=verify_integrity)
    pd.Series.append = _append

# Load environment variables from .env file at the root level if possible
load_dotenv()

class Config:
    
    # --- LLM API KEYS ---
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
    DEEPSEEK_BASE_URL = "https://api.deepseek.com"
    HF_TOKEN = os.getenv("HF_TOKEN")

    # --- PROVIDER NAMES ---
    PROVIDER_GOOGLE = "google-cloud"
    PROVIDER_OPENAI = "openai"
    PROVIDER_DEEPSEEK = "deepseek"
    PROVIDER_MISTRAL = "mistral"

    DEFAULT_PROVIDER = PROVIDER_GOOGLE

    # --- MODELS ---
    DEFAULT_GOOGLE_MODEL = "gemini-3.8-flash"
    DEFAULT_OPENAI_MODEL = "gpt-5.6-sol"
    DEFAULT_MISTRAL_MODEL = "mistral-medium-latest"
    DEFAULT_DEEPSEEK_MODEL = "deepseek-v4.1-flash"

    # --- REASONING / THINKING ---
    DEFAULT_THINKING_LEVEL = "medium"
    DEFAULT_GOOGLE_THINKING_LEVEL = "low"

    # --- LLM TIMEOUT & RETRY SETTINGS ---
    LLM_HTTP_TIMEOUT: float = 1200.0
    LLM_CONNECT_TIMEOUT: float = 30.0
    LLM_MAX_RETRIES: int = 3

    # --- MODEL MAPPINGS ---
    SUPPORTED_MODELS: ClassVar[dict[str, list[str]]] = {
        PROVIDER_OPENAI: ["gpt-5.6-terra", "gpt-5.6-sol", "gpt-5.6-luna"],
        PROVIDER_DEEPSEEK: [
            "deepseek-v4-pro",
            "deepseek-v4.1-flash",
            "deepseek-v4-flash",
            "deepseek-flash",
        ],
        PROVIDER_MISTRAL: [
            "mistral-large-latest",
            "mistral-small-latest",
            "mistral-medium-latest",
        ],
        PROVIDER_GOOGLE: ["gemini-3.8-flash", "gemini-3.1-pro"],
    }
    """Dictionary mapping LLM providers to their supported model identifiers."""

    # --- EMBEDDING SETTINGS ---
    EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

    # --- ENTITY RESOLUTION THRESHOLDS ---
    # Thresholds for classifying candidate pairs
    MATCH_THRESHOLD = 0.80
    UNCERTAIN_THRESHOLD = 0.60
    ECM_MATCH_PROBABILITY = 0.85
    ECM_UNCERTAIN_PROBABILITY = 0.40
    ECM_KMEANS_SAFETY_FLOOR = 0.70
    ECM_FALLBACK_THRESHOLD = 0.85
    KMEANS_CENTROID_SAFETY_FLOOR = 0.50
    KMEANS_MATCH_THRESHOLD = 0.60
    KMEANS_UNCERTAIN_THRESHOLD = 0.40
    DYNAMIC_THRESHOLD_SAFETY_FLOOR: float = 0.60
    DYNAMIC_THRESHOLD_ASYMMETRIC_ALPHA: float = 0.60
    DYNAMIC_THRESHOLD_DISPERSION_BOOST_BETA: float = 2.50
    DYNAMIC_THRESHOLD_PREFILTER_CUTOFF: float = 0.20

    # Backward-compatible aliases for legacy weighted matching constants
    WEIGHTED_CENTROID_SAFETY_FLOOR = DYNAMIC_THRESHOLD_SAFETY_FLOOR
    WEIGHTED_ASYMMETRIC_ALPHA = DYNAMIC_THRESHOLD_ASYMMETRIC_ALPHA
    WEIGHTED_DISPERSION_BOOST_BETA = DYNAMIC_THRESHOLD_DISPERSION_BOOST_BETA
    WEIGHTED_PREFILTER_CUTOFF = DYNAMIC_THRESHOLD_PREFILTER_CUTOFF

    # --- SHARED HYPERPARAMETERS ---
    TEMPERATURE = 0.0
    SEED = 42

    # --- LOGGING ---
    LLM_LOG_DIR = "data/logs/llm_calls"

    # --- LLM CACHE ---
    LLM_CACHE_MODE: str = os.getenv("LLM_CACHE_MODE", "off").lower()
    LLM_CACHE_DIR: Path = Path(os.getenv("LLM_CACHE_DIR", "data/cache/llm"))

    # --- OUTPUTS ---
    OUTPUT_BASE_DIR = Path("outputs")

    # --- DATA FUSION ---
    DATA_FUSION_INPUT_DIR = Path("data/data_fusion/inputs")
    DATA_FUSION_OUTPUT_DIR = Path("outputs/data_fusion")

    # --- BENCHMARKING ---
    ER_DATASETS_DIR = Path("data/entity_resolution/datasets")
    ER_BENCHMARK_OUTPUT_DIR = Path(
        "outputs/entity_resolution/benchmarks/complete"
    )
    ER_INDEXING_BENCHMARK_OUTPUT_DIR = Path(
        "outputs/entity_resolution/benchmarks/indexing"
    )
    ER_MATCHING_BENCHMARK_OUTPUT_DIR = Path(
        "outputs/entity_resolution/benchmarks/matching"
    )
    # Legacy aliases for backwards compatibility
    LEGACY_ER_BENCHMARK_OUTPUT_DIR = Path(
        "outputs/entity_resolution/benchmarks"
    )
    LEGACY_ER_INDEXING_BENCHMARK_OUTPUT_DIR = Path(
        "outputs/entity_resolution/indexing_benchmarks"
    )
    LEGACY_ER_MATCHING_BENCHMARK_OUTPUT_DIR = Path(
        "outputs/entity_resolution/matching_benchmarks"
    )
    DF_BENCHMARK_OUTPUT_DIR = Path("outputs/data_fusion/benchmarks")
    MAX_CANDIDATE_PAIRS_PER_PASS = 500000
    MAX_EXPORT_ROWS_PER_CSV: int = 5000

config = Config()
