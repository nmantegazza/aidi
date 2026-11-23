"""
Matching strategies module for entity resolution scoring and classification.
"""

from entity_resolution.matching_strategies.base import (
    BaseMatchingStrategy,
    MatchingStrategyResult,
)
from entity_resolution.matching_strategies.ecm import (
    ECMMatchingStrategy,
)
from entity_resolution.matching_strategies.implementations import (
    DynamicWeightedMatchingStrategy,
    WeightedScoreMatchingConfig,
    WeightedScoreMatchingStrategy,
)
from entity_resolution.matching_strategies.kmeans import (
    KMeansMatchingStrategy,
)
from entity_resolution.models import (
    ECMMatchingConfig,
    KMeansMatchingConfig,
)

__all__ = [
    "BaseMatchingStrategy",
    "DynamicWeightedMatchingStrategy",
    "ECMMatchingConfig",
    "ECMMatchingStrategy",
    "KMeansMatchingConfig",
    "KMeansMatchingStrategy",
    "MatchingStrategyResult",
    "WeightedScoreMatchingConfig",
    "WeightedScoreMatchingStrategy",
]
