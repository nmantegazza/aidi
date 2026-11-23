"""
Configuration generator leveraging LLMs with local caching for indexing benchmarking.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from entity_resolution.agents import identify_indexing_config_via_llm
from entity_resolution.indexing_strategies.base import BaseIndexingStrategy
from shared.agents import ExecutionMetadata
from shared.config import config as shared_config
from shared.profiling.models import TableProfile
from shared.schema_models import TableResource

logger = logging.getLogger(__name__)

DEFAULT_CACHE_PATH = Path(".cache/indexing_config_cache.json")


class LLMIndexConfigGenerator:
    """Generates and caches indexing parameters using LLMs."""

    def __init__(self, cache_path: Path | str = DEFAULT_CACHE_PATH):
        """Initializes the LLM config generator with cache path.

        Args:
            cache_path: Path to the local JSON cache file.
        """
        self.cache_path = Path(cache_path)
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)

    def _load_cache(self) -> dict[str, Any]:
        """Loads cache dict from disk."""
        if not self.cache_path.exists():
            return {}
        try:
            with open(self.cache_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError, ValueError) as e:
            logger.warning(f"Failed to read config cache at {self.cache_path}: {e}")
            return {}

    def _save_cache(self, cache: dict[str, Any]) -> None:
        """Saves cache dict to disk."""
        try:
            with open(self.cache_path, "w", encoding="utf-8") as f:
                json.dump(cache, f, indent=2)
        except (OSError, TypeError, ValueError) as e:
            logger.warning(f"Failed to write config cache at {self.cache_path}: {e}")

    async def get_configuration(
        self,
        dataset_name: str,
        profile_a: TableProfile,
        profile_b: TableProfile,
        table_resource: TableResource,
        strategy_cls: type[BaseIndexingStrategy],
        force_llm: bool = False,
        model_name: str = shared_config.DEFAULT_GOOGLE_MODEL,
        provider: str | None = None,
    ) -> tuple[BaseIndexingStrategy, ExecutionMetadata | None]:
        """Retrieves indexing configuration and instantiates the strategy via cache or LLM.

        Args:
            dataset_name: Identifier for the dataset being configured.
            profile_a: Profile of source DataFrame A.
            profile_b: Profile of source DataFrame B.
            table_resource: Global schema and resource metadata.
            strategy_cls: The indexing strategy class to generate config for.
            force_llm: If True, bypass cache and re-query LLM.
            model_name: Model to use for configuration.
            provider: Optional LLM provider override.

        Returns:
            Tuple of (instantiated BaseIndexingStrategy, llm_execution_metadata).
        """
        cache = self._load_cache()
        cache_key = f"{dataset_name}::{strategy_cls.__name__}::{model_name}"

        if not force_llm and cache_key in cache:
            cached_item = cache[cache_key]
            config_data = cached_item.get("config_data")
            raw_meta = cached_item.get("llm_metrics")
            metadata = ExecutionMetadata(**raw_meta) if raw_meta else None
            config_obj = strategy_cls.config_schema.model_validate(config_data)
            strategy_instance = strategy_cls.from_llm_config(config_obj)
            logger.info(
                f"Loaded cached index config for dataset '{dataset_name}' and strategy '{strategy_cls.__name__}' with model '{model_name}'"
            )
            return strategy_instance, metadata


        logger.info(
            f"Generating config for strategy '{strategy_cls.__name__}' via LLM model '{model_name}' for dataset '{dataset_name}'..."
        )
        config_obj, metadata = await identify_indexing_config_via_llm(
            profile_a=profile_a,
            profile_b=profile_b,
            table_resource=table_resource,
            config_schema=strategy_cls.config_schema,
            system_prompt=strategy_cls.config_prompt,
            model_name=model_name,
            provider=provider,
        )

        strategy_instance = strategy_cls.from_llm_config(config_obj)

        cache[cache_key] = {
            "dataset_name": dataset_name,
            "strategy_name": strategy_cls.__name__,
            "model_name": model_name,
            "config_data": config_obj.model_dump(),
            "llm_metrics": metadata.model_dump() if metadata else None,
        }
        self._save_cache(cache)

        return strategy_instance, metadata

