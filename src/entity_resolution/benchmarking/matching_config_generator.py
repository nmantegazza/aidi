"""
LLM configuration generator with caching for matching and classification.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import pandas as pd

from entity_resolution.agents import (
    _build_comparative_prompt,
    identify_indexing_config_via_llm,
)
from entity_resolution.exemplars import extract_exemplar_candidates
from entity_resolution.matching_strategies.base import BaseMatchingStrategy
from shared.agents import ExecutionMetadata
from shared.config import config
from shared.profiling.models import TableProfile
from shared.schema_models import TableResource

logger = logging.getLogger(__name__)

DEFAULT_CACHE_PATH = Path(".cache/matching_config_cache.json")


def _try_read_log_file(log_path: str | Path | None) -> dict[str, Any] | None:
    """Attempts to read and parse an LLM call JSON log file."""
    if not log_path:
        return None
    try:
        p = Path(log_path)
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
    except (json.JSONDecodeError, OSError, TypeError, KeyError) as err:
        logger.debug("Could not read LLM log file %s: %s", log_path, err)
    return None


class LLMMatchingConfigGenerator:
    """Generates and caches matching strategy parameters using LLMs."""

    def __init__(self, cache_path: Path | str = DEFAULT_CACHE_PATH) -> None:
        """Initializes generator with local cache location."""
        self.cache_path = Path(cache_path)
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)

    def _load_cache(self) -> dict[str, Any]:
        """Loads JSON cache from disk."""
        if not self.cache_path.exists():
            return {}
        try:
            with open(self.cache_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError, ValueError) as err:
            logger.warning(
                f"Failed to read matching config cache at {self.cache_path}: {err}"
            )
            return {}

    def _save_cache(self, cache: dict[str, Any]) -> None:
        """Saves JSON cache dict to disk."""
        try:
            with open(self.cache_path, "w", encoding="utf-8") as f:
                json.dump(cache, f, indent=2)
        except (OSError, TypeError, ValueError) as err:
            logger.warning(
                f"Failed to write matching config cache at {self.cache_path}: {err}"
            )

    async def get_configuration(
        self,
        dataset_name: str,
        profile_a: TableProfile,
        profile_b: TableProfile,
        table_resource: TableResource,
        strategy_cls: type[BaseMatchingStrategy],
        force_llm: bool = False,
        model_name: str = config.DEFAULT_GOOGLE_MODEL,
        provider: str | None = None,
        df_a: pd.DataFrame | None = None,
        df_b: pd.DataFrame | None = None,
    ) -> tuple[BaseMatchingStrategy, ExecutionMetadata | None]:
        """Retrieves or generates strategy configuration via LLM reasoning.

        Args:
            dataset_name: Identifier for dataset.
            profile_a: Profile of DataFrame A.
            profile_b: Profile of DataFrame B.
            table_resource: Global schema and resource metadata.
            strategy_cls: Strategy class to instantiate.
            force_llm: If True, bypass disk cache and re-query LLM.
            model_name: Model name to invoke.
            provider: Optional provider override.
            df_a: Optional cleaned DataFrame A for exemplar extraction.
            df_b: Optional cleaned DataFrame B for exemplar extraction.

        Returns:
            Tuple of (instantiated BaseMatchingStrategy, ExecutionMetadata).
        """
        cache = self._load_cache()
        cache_key = f"{dataset_name}::{strategy_cls.__name__}::{model_name}"

        if not force_llm and cache_key in cache:
            cached_item = cache[cache_key]
            config_data = cached_item.get("config_data")
            raw_meta = cached_item.get("llm_metrics")
            metadata = ExecutionMetadata(**raw_meta) if raw_meta else None
            if metadata:
                if (
                    not metadata.user_prompt
                    or not metadata.prompt_template
                    or metadata.raw_response is None
                ) and metadata.log_file_path:
                    log_json = _try_read_log_file(metadata.log_file_path)
                    if log_json:
                        if not metadata.user_prompt:
                            metadata.user_prompt = log_json.get("user_prompt")
                        if not metadata.prompt_template:
                            metadata.prompt_template = log_json.get(
                                "system_prompt"
                            )
                        if metadata.raw_response is None:
                            metadata.raw_response = log_json.get("response")
                if not metadata.prompt_template:
                    metadata.prompt_template = (
                        cached_item.get("system_prompt")
                        or strategy_cls.config_prompt
                    )
                if not metadata.user_prompt:
                    metadata.user_prompt = cached_item.get("user_prompt")
                if metadata.raw_response is None:
                    metadata.raw_response = config_data
                if not metadata.user_prompt:
                    exemplars = None
                    if df_a is not None and df_b is not None:
                        exemplars = extract_exemplar_candidates(df_a, df_b)
                    metadata.user_prompt = _build_comparative_prompt(
                        profile_a, profile_b, table_resource, exemplars
                    )

            try:
                available_cols = (
                    [f.name for f in table_resource.schema_info.fields]
                    if table_resource and table_resource.schema_info
                    else None
                )
                config_obj = strategy_cls.config_schema.model_validate(
                    config_data,
                    context={"available_columns": available_cols}
                    if available_cols
                    else None,
                )
                strategy_instance = strategy_cls.from_llm_config(config_obj)
                logger.info(
                    f"Loaded cached matching config for dataset '{dataset_name}' "
                    f"and strategy '{strategy_cls.__name__}' with model '{model_name}'"
                )
                return strategy_instance, metadata
            except (ValueError, TypeError, KeyError, AttributeError) as e:
                logger.warning(
                    f"Cached matching config for '{dataset_name}' failed validation ({e}). "
                    f"Invalidating cache entry for key '{cache_key}'."
                )
                del cache[cache_key]

        logger.info(
            f"Generating matching config for strategy '{strategy_cls.__name__}' "
            f"via LLM model '{model_name}' for dataset '{dataset_name}'..."
        )
        exemplars = None
        if df_a is not None and df_b is not None:
            exemplars = extract_exemplar_candidates(df_a, df_b)

        config_obj, metadata = await identify_indexing_config_via_llm(
            profile_a=profile_a,
            profile_b=profile_b,
            table_resource=table_resource,
            config_schema=strategy_cls.config_schema,
            system_prompt=strategy_cls.config_prompt,
            model_name=model_name,
            provider=provider,
            exemplar_candidates=exemplars,
        )

        strategy_instance = strategy_cls.from_llm_config(config_obj)

        if cache_key not in cache:
            cache[cache_key] = {
                "dataset_name": dataset_name,
                "strategy_name": strategy_cls.__name__,
                "model_name": model_name,
                "config_data": config_obj.model_dump(),
                "llm_metrics": metadata.model_dump() if metadata else None,
                "system_prompt": strategy_cls.config_prompt,
                "user_prompt": metadata.user_prompt if metadata else None,
                "log_file_path": metadata.log_file_path if metadata else None,
            }
            self._save_cache(cache)

        return strategy_instance, metadata

    def get_config(
        self,
        profile_a: Any = None,
        profile_b: Any = None,
    ) -> Any | None:
        """Legacy sync interface compatibility method."""
        return None
