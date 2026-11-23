"""Directory layout management for benchmark execution artifacts."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path


class RunLayoutManager:
    """Manages standardized benchmark directory hierarchies."""

    @staticmethod
    def sanitize_slug(name: str) -> str:
        """Sanitizes model or strategy names for file system directory paths.

        Replaces colons, slashes, spaces, and punctuation with underscores.

        Args:
            name: Original string name or identifier.

        Returns:
            Sanitized slug safe for directory paths.
        """
        slug = re.sub(r"[:/\s\\]+", "_", name.strip())
        return re.sub(r"_+", "_", slug).strip("_")

    @staticmethod
    def get_run_dir(
        base_output_dir: Path,
        timestamp: datetime | None = None,
    ) -> Path:
        """Generates a standardized run directory path.

        Args:
            base_output_dir: Root directory for the module's benchmark runs.
            timestamp: Optional datetime object; defaults to current local time.

        Returns:
            Path object pointing to `base_output_dir / run_YYYYMMDD_HHMMSS`.
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        ts_str = timestamp.strftime("%Y%m%d_%H%M%S")
        return base_output_dir / f"run_{ts_str}"

    @staticmethod
    def get_dataset_model_dir(
        run_dir: Path,
        dataset_name: str,
        model_name: str,
        strategy: str | None = None,
    ) -> Path:
        """Returns the dataset-model directory path.

        Args:
            run_dir: Root path of the benchmark run.
            dataset_name: Name of the dataset.
            model_name: Name of the model.
            strategy: Optional strategy identifier.

        Returns:
            Path pointing to `run_dir/datasets/<dataset>/<model>/[<strategy>]`.
        """
        model_slug = RunLayoutManager.sanitize_slug(model_name)
        base = run_dir / "datasets" / dataset_name / model_slug
        if strategy:
            strat_slug = RunLayoutManager.sanitize_slug(strategy)
            return base / strat_slug
        return base

    @staticmethod
    def get_iteration_dir(
        model_ds_dir: Path,
        iteration_index: int,
    ) -> Path:
        """Returns the isolated iteration directory path.

        Args:
            model_ds_dir: Parent dataset-model (or dataset-model-strategy) dir.
            iteration_index: 1-indexed iteration number.

        Returns:
            Path pointing to `model_ds_dir / iterations / iter_<iteration_index>`.
        """
        return model_ds_dir / "iterations" / f"iter_{iteration_index}"
