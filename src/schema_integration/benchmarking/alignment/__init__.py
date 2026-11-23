"""Schema alignment benchmarking suite using SchemaNet multi-table datasets."""

from .evaluation import AlignmentEvaluator
from .loader import SchemaAlignmentDataset, SchemaAlignmentLoader
from .models import (
    AlignmentBenchmarkResult,
    AlignmentDatasetMetrics,
    AlignmentIterationMetrics,
    AlignmentRunSummary,
    MacroModelSummary,
    StructuralIntegrityStats,
    SynonymPair,
)
from .runner import AlignmentRunner

__all__ = [
    "AlignmentBenchmarkResult",
    "AlignmentDatasetMetrics",
    "AlignmentEvaluator",
    "AlignmentIterationMetrics",
    "AlignmentRunSummary",
    "AlignmentRunner",
    "MacroModelSummary",
    "SchemaAlignmentDataset",
    "SchemaAlignmentLoader",
    "StructuralIntegrityStats",
    "SynonymPair",
]
