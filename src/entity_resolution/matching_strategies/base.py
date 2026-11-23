"""
Abstract base class and data models for entity resolution matching strategies.
"""

from __future__ import annotations

import time
import tracemalloc
from abc import ABC, abstractmethod
from dataclasses import dataclass

import pandas as pd
from pydantic import BaseModel

from entity_resolution.matching import filter_one_to_one_bipartite
from entity_resolution.models import ClassificationMode


@dataclass
class MatchingStrategyResult:
    """Container for classified match pairs and execution telemetry."""

    classified_pairs: pd.MultiIndex
    execution_time_sec: float
    peak_memory_mb: float
    peak_cpu_percent: float = 0.0
    features_df: pd.DataFrame | None = None


class BaseMatchingStrategy(ABC):
    """Abstract base class for matching strategies, handling telemetry."""

    config_schema: type[BaseModel]
    config_prompt: str = ""

    @classmethod
    @abstractmethod
    def from_llm_config(cls, config: BaseModel) -> BaseMatchingStrategy:
        """Factory method to construct strategy from parsed config model."""

    @property
    def name(self) -> str:
        """Return the display name of the strategy."""
        return self.__class__.__name__

    def execute(
        self,
        df_a: pd.DataFrame,
        df_b: pd.DataFrame,
        candidate_pairs: pd.MultiIndex,
        enforce_one_to_one: bool = True,
        classification_mode: ClassificationMode = ClassificationMode.TERNARY,
        **kwargs,
    ) -> MatchingStrategyResult:
        """Executes matching with time and peak memory tracking.

        Args:
            df_a: Left input DataFrame.
            df_b: Right input DataFrame.
            candidate_pairs: Candidate pairs MultiIndex to classify.
            enforce_one_to_one: Whether to filter matches to enforce 1-to-1
                mutual exclusivity across tables.
            classification_mode: Binary or ternary classification mode.
            **kwargs: Additional strategy-specific runtime parameters.

        Returns:
            MatchingStrategyResult containing classified pairs and telemetry.
        """
        import threading

        from shared.console import console

        try:
            import psutil
            proc = psutil.Process()
            proc.cpu_percent(interval=None)
        except ImportError:
            proc = None

        tracemalloc.start()
        start_time = time.perf_counter()
        start_cpu = time.process_time()
        peak_cpu_percent = 0.0

        done = threading.Event()
        status_msg = f"Running matching strategy: {self.name}"
        status = console.status(status_msg)
        status.start()

        def update_status():
            nonlocal peak_cpu_percent
            while not done.wait(0.1):
                elapsed = time.perf_counter() - start_time
                if proc is not None:
                    cpu_pct = proc.cpu_percent(interval=None)
                    peak_cpu_percent = max(peak_cpu_percent, cpu_pct)
                else:
                    elapsed_cpu = time.process_time() - start_cpu
                    peak_cpu_percent = (elapsed_cpu / max(elapsed, 1e-6)) * 100.0

                _, peak_bytes = tracemalloc.get_traced_memory()
                peak_mb = peak_bytes / (1024 * 1024)
                status.update(
                    f"{status_msg}... [cyan]Time:[/cyan] {elapsed:.1f}s | "
                    f"[magenta]Peak Memory:[/magenta] {peak_mb:.1f}MB | "
                    f"[yellow]Peak CPU:[/yellow] {peak_cpu_percent:.0f}%"
                )

        t = threading.Thread(target=update_status, daemon=True)
        t.start()

        import inspect

        sig = inspect.signature(self._perform_matching)
        call_kwargs = dict(kwargs)
        if "classification_mode" in sig.parameters or any(
            p.kind == inspect.Parameter.VAR_KEYWORD
            for p in sig.parameters.values()
        ):
            call_kwargs["classification_mode"] = classification_mode

        try:
            match_output = self._perform_matching(
                df_a,
                df_b,
                candidate_pairs,
                **call_kwargs,
            )
        finally:
            done.set()
            t.join()
            status.stop()

        if isinstance(match_output, pd.MultiIndex):
            classified_pairs = match_output
            features_df = None
        elif isinstance(match_output, tuple) and len(match_output) == 2:
            classified_pairs, features_df = match_output
        else:
            classified_pairs = match_output
            features_df = None

        if enforce_one_to_one and not classified_pairs.empty:
            if features_df is not None:
                if "aggregate_score" in features_df.columns:
                    scores = features_df["aggregate_score"]
                elif "match_probability" in features_df.columns:
                    scores = features_df["match_probability"]
                elif "probability" in features_df.columns:
                    scores = features_df["probability"]
                else:
                    num_cols = [
                        c
                        for c in features_df.columns
                        if c not in ("prediction", "is_ground_truth_match")
                        and pd.api.types.is_numeric_dtype(features_df[c])
                    ]
                    scores = (
                        features_df[num_cols].sum(axis=1)
                        if num_cols
                        else pd.Series(1.0, index=features_df.index)
                    )
            else:
                scores = pd.Series(1.0, index=classified_pairs)

            filtered_pairs = filter_one_to_one_bipartite(
                classified_pairs, scores
            )
            if features_df is not None and "prediction" in features_df.columns:
                excluded = classified_pairs.difference(filtered_pairs)
                if not excluded.empty:
                    features_df.loc[excluded, "prediction"] = "non_match"
            classified_pairs = filtered_pairs

        elapsed_time = time.perf_counter() - start_time
        elapsed_cpu = time.process_time() - start_cpu
        _, peak_bytes = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        if proc is None:
            peak_cpu_percent = (elapsed_cpu / max(elapsed_time, 1e-6)) * 100.0

        peak_memory_mb = peak_bytes / (1024 * 1024)
        
        console.print(f"[green]✔ Matching complete ([bold]{self.name}[/bold]).[/green] "
                      f"Matches: {len(classified_pairs)} | "
                      f"Time: {elapsed_time:.2f}s | "
                      f"Peak Mem: {peak_memory_mb:.2f}MB | "
                      f"Peak CPU: {peak_cpu_percent:.1f}%")

        return MatchingStrategyResult(
            classified_pairs=classified_pairs,
            execution_time_sec=round(elapsed_time, 6),
            peak_memory_mb=round(peak_memory_mb, 6),
            peak_cpu_percent=round(peak_cpu_percent, 2),
            features_df=features_df,
        )

    @abstractmethod
    def _perform_matching(
        self,
        df_a: pd.DataFrame,
        df_b: pd.DataFrame,
        candidate_pairs: pd.MultiIndex,
        classification_mode: ClassificationMode = ClassificationMode.TERNARY,
        **kwargs,
    ) -> tuple[pd.MultiIndex, pd.DataFrame | None]:
        """Core matching logic implemented by concrete strategy subclasses.

        Args:
            df_a: Left input DataFrame.
            df_b: Right input DataFrame.
            candidate_pairs: Candidate pairs MultiIndex to evaluate.
            classification_mode: Binary or ternary classification mode.
            **kwargs: Strategy-specific keyword arguments.

        Returns:
            Tuple of (classified positive matches MultiIndex, features DataFrame).
        """
