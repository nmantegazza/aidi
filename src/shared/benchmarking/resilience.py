"""Resilience, run directory resolution, and failure recovery utilities."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from .models import FailedIterationDescriptor, RunStatus

logger = logging.getLogger(__name__)


def resolve_run_dir(
    run_target: str | Path,
    base_dir: Path,
    fallback_dirs: list[Path] | None = None,
) -> Path:
    """Resolves a target run directory path from an ID, path, or 'latest' alias.

    Args:
        run_target: Run folder path, run ID (e.g. 'run_20260912_120000'), or
          'latest'.
        base_dir: Root directory where runs are stored.
        fallback_dirs: Optional list of fallback directories to check.

    Returns:
        Resolved absolute Path to the run directory.

    Raises:
        FileNotFoundError: If the target run cannot be located.
    """
    direct_path = Path(run_target)
    if direct_path.is_dir():
        return direct_path.resolve()

    search_dirs: list[Path] = [base_dir]
    if fallback_dirs:
        for fb in fallback_dirs:
            if fb not in search_dirs:
                search_dirs.append(fb)

    target_str = str(run_target).strip()

    if target_str.lower() == "latest":
        candidate_dirs: list[Path] = []
        for s_dir in search_dirs:
            if not s_dir.exists():
                continue
            runs = [
                p
                for p in s_dir.iterdir()
                if p.is_dir() and p.name.startswith("run_")
            ]
            if not runs:
                runs = [p for p in s_dir.iterdir() if p.is_dir()]
            candidate_dirs.extend(runs)

        if not candidate_dirs:
            raise FileNotFoundError(
                f"No run directories found in {base_dir} or fallbacks"
            )

        candidate_dirs.sort(
            key=lambda p: (p.name, p.stat().st_mtime), reverse=True
        )
        return candidate_dirs[0].resolve()

    for s_dir in search_dirs:
        if not s_dir.exists():
            continue
        under_base = s_dir / target_str
        if under_base.is_dir():
            return under_base.resolve()

        prefixed = s_dir / f"run_{target_str}"
        if prefixed.is_dir():
            return prefixed.resolve()

    raise FileNotFoundError(
        f"Could not resolve run directory '{run_target}' under {base_dir}"
    )


def find_failed_iterations(
    run_dir: Path,
    dataset_filter: list[str] | None = None,
    model_filter: list[str] | None = None,
    strategy_filter: list[str] | None = None,
) -> list[FailedIterationDescriptor]:
    """Scans a run directory to identify all failed execution iterations.

    Args:
        run_dir: Path to the benchmark run root.
        dataset_filter: Optional list of dataset names to restrict search.
        model_filter: Optional list of model slugs/names to restrict search.
        strategy_filter: Optional list of strategy slugs to restrict search.

    Returns:
        List of FailedIterationDescriptor instances.
    """
    datasets_dir = run_dir / "datasets"
    failed_items: list[FailedIterationDescriptor] = []

    if not datasets_dir.exists():
        return failed_items

    for metrics_file in sorted(datasets_dir.glob("**/metrics.json")):
        target_dir = metrics_file.parent
        rel_parts = target_dir.relative_to(datasets_dir).parts
        if len(rel_parts) < 2:
            continue

        ds_name = rel_parts[0]
        model_name = rel_parts[1]
        strategy_name = rel_parts[2] if len(rel_parts) > 2 else None

        if dataset_filter and ds_name not in dataset_filter:
            continue
        if model_filter and model_name not in model_filter:
            continue
        if strategy_filter and strategy_name and strategy_name not in strategy_filter:
            continue

        try:
            content = metrics_file.read_text(encoding="utf-8")
            data = json.loads(content)
        except (json.JSONDecodeError, OSError, ValueError) as err:
            logger.warning(
                "Failed to parse metrics file %s: %s", metrics_file, err
            )
            continue

        iterations = data.get("iterations", [])
        if isinstance(iterations, list) and iterations:
            for it in iterations:
                status = it.get("status")
                if (
                    status
                    and status != RunStatus.SUCCESS.value
                    and status != RunStatus.SUCCESS
                ):
                    idx = it.get("iteration_index", 1)
                    err_msg = it.get("error_message")
                    failed_items.append(
                        FailedIterationDescriptor(
                            dataset_name=ds_name,
                            model_name=data.get("model_name") or model_name,
                            iteration_index=idx,
                            target_dir=target_dir,
                            strategy_name=strategy_name,
                            error_message=err_msg,
                        )
                    )
        elif data.get("status") in (RunStatus.FAILED.value, RunStatus.FAILED):
            failed_items.append(
                FailedIterationDescriptor(
                    dataset_name=ds_name,
                    model_name=data.get("model_name") or model_name,
                    iteration_index=1,
                    target_dir=target_dir,
                    strategy_name=strategy_name,
                    error_message=data.get("error_message"),
                )
            )

    return failed_items


class RunResilienceHelper:
    """Facade for failure identification, recovery, and run resolution."""

    resolve_run_dir = staticmethod(resolve_run_dir)
    find_failed_iterations = staticmethod(find_failed_iterations)
