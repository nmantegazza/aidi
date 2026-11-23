"""
Abstract base class and data models for entity resolution indexing strategies.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
import time
import tracemalloc
from typing import Type
import pandas as pd
from pydantic import BaseModel


@dataclass
class StrategyResult:
    """Container for candidate pair results and execution telemetry."""
    candidate_pairs: pd.MultiIndex
    indexing_time_sec: float
    peak_memory_mb: float
    peak_cpu_percent: float = 0.0


class BaseIndexingStrategy(ABC):
    """Abstract base class for indexing strategies, handling performance measurement."""

    config_schema: Type[BaseModel]
    config_prompt: str

    @classmethod
    @abstractmethod
    def from_llm_config(cls, config: BaseModel) -> BaseIndexingStrategy:
        """Factory method to construct the strategy from a parsed Pydantic config model."""
        pass

    @property
    def name(self) -> str:
        """Return the display name of the strategy."""
        return self.__class__.__name__

    def execute(self, df_a: pd.DataFrame, df_b: pd.DataFrame) -> StrategyResult:
        """Executes indexing with time and peak memory tracking.

        Args:
            df_a: Left input DataFrame.
            df_b: Right input DataFrame.

        Returns:
            StrategyResult containing candidate pairs and execution telemetry.
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
        status_msg = f"Running indexing strategy: {self.name}"
        status = console.status(status_msg)
        status.start()

        def update_status():
            nonlocal peak_cpu_percent
            while not done.wait(0.1):
                elapsed = time.perf_counter() - start_time
                if proc is not None:
                    cpu_pct = proc.cpu_percent(interval=None)
                    if cpu_pct > peak_cpu_percent:
                        peak_cpu_percent = cpu_pct
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

        try:
            candidate_pairs = self._perform_indexing(df_a, df_b)
        finally:
            done.set()
            t.join()
            status.stop()

        elapsed_time = time.perf_counter() - start_time
        elapsed_cpu = time.process_time() - start_cpu
        _, peak_bytes = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        if proc is None:
            peak_cpu_percent = (elapsed_cpu / max(elapsed_time, 1e-6)) * 100.0

        peak_memory_mb = peak_bytes / (1024 * 1024)
        
        console.print(f"[green]✔ Indexing complete ([bold]{self.name}[/bold]).[/green] "
                      f"Pairs: {len(candidate_pairs)} | "
                      f"Time: {elapsed_time:.2f}s | "
                      f"Peak Mem: {peak_memory_mb:.2f}MB | "
                      f"Peak CPU: {peak_cpu_percent:.1f}%")

        return StrategyResult(
            candidate_pairs=candidate_pairs,
            indexing_time_sec=round(elapsed_time, 6),
            peak_memory_mb=round(peak_memory_mb, 6),
            peak_cpu_percent=round(peak_cpu_percent, 2),
        )

    @abstractmethod
    def _perform_indexing(
        self, df_a: pd.DataFrame, df_b: pd.DataFrame
    ) -> pd.MultiIndex:
        """Core indexing logic implemented by concrete strategy subclasses.

        Args:
            df_a: Left input DataFrame.
            df_b: Right input DataFrame.

        Returns:
            pd.MultiIndex representing candidate pairs.
        """
        pass
