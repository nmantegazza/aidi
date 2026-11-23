"""Entity resolution module public interface."""

import shared.patches  # noqa: F401

from .classification import (
    BaseClassificationEngine,
    ClassificationResult,
    DynamicThresholdClassificationEngine,
)
from .dataset_loader import (
    DatasetLoadError,
    DatasetMetadata,
    DatasetNotFoundError,
    GroundTruthType,
    LoadedDataset,
    MissingFileError,
    discover_and_load,
    load_dataset,
)
from .evaluation import evaluate_entity_resolution
from .evaluation_models import (
    EntityResEvalReport,
    EvaluationMetrics,
    IndexingEvaluation,
    MatchingEvaluation,
)
from .metrics import (
    compute_pairs_recall,
    compute_precision_recall_f1,
    compute_reduction_ratio,
    pairs_to_set,
)
from .models import (
    ClassificationMode,
    ColumnMatchConfig,
    EntityResolutionResult,
    ERPipelineConfiguration,
    SimilarityAlgorithm,
)
from .pipeline import (
    execute_tfidf_indexing,
    refine_uncertain_matches,
    run_entity_resolution,
    score_and_classify_pairs,
)
from .synthetic_generator import (
    SyntheticConfig,
    generate_synthetic_pair,
    get_default_table_schema,
)

__all__ = [
    "BaseClassificationEngine",
    "ClassificationMode",
    "ClassificationResult",
    "ColumnMatchConfig",
    "DatasetLoadError",
    "DatasetMetadata",
    "DatasetNotFoundError",
    "DynamicThresholdClassificationEngine",
    "ERPipelineConfiguration",
    "EntityResEvalReport",
    "EntityResolutionResult",
    "EvaluationMetrics",
    "GroundTruthType",
    "IndexingEvaluation",
    "LoadedDataset",
    "MatchingEvaluation",
    "MissingFileError",
    "SimilarityAlgorithm",
    "SyntheticConfig",
    "compute_pairs_recall",
    "compute_precision_recall_f1",
    "compute_reduction_ratio",
    "discover_and_load",
    "evaluate_entity_resolution",
    "execute_tfidf_indexing",
    "generate_synthetic_pair",
    "get_default_table_schema",
    "load_dataset",
    "pairs_to_set",
    "refine_uncertain_matches",
    "run_entity_resolution",
    "score_and_classify_pairs",
]
