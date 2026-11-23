"""Semantic similarity and neural embedding cache for schema alignment."""

from __future__ import annotations

import logging
from typing import Any, ClassVar, Optional

import numpy as np

logger = logging.getLogger(__name__)


def _compute_jaccard_string_similarity(text_a: str, text_b: str) -> float:
    """Compute fallback token Jaccard similarity between two strings."""
    tokens_a = set(text_a.lower().replace(":", " ").replace("_", " ").split())
    tokens_b = set(text_b.lower().replace(":", " ").replace("_", " ").split())
    if not tokens_a and not tokens_b:
        return 1.0
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = len(tokens_a & tokens_b)
    union = len(tokens_a | tokens_b)
    return float(intersection / union) if union > 0 else 0.0


class SentenceTransformerEmbedder:
    """Lazy-loaded singleton embedder utilizing sentence-transformers."""

    _instance: ClassVar[Optional[SentenceTransformerEmbedder]] = None
    _model: ClassVar[Optional[Any]] = None
    _model_load_failed: ClassVar[bool] = False
    _model_name: ClassVar[str] = "all-MiniLM-L6-v2"

    def __init__(self) -> None:
        """Initialize embedder instance with internal memory cache."""
        self._cache: dict[str, np.ndarray] = {}

    @classmethod
    def get_instance(cls) -> SentenceTransformerEmbedder:
        """Get or create singleton instance of SentenceTransformerEmbedder."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def _load_model(cls) -> Optional[Any]:
        """Lazy load the sentence transformer model singleton."""
        if cls._model is None and not cls._model_load_failed:
            try:
                from sentence_transformers import SentenceTransformer

                cls._model = SentenceTransformer(cls._model_name)
            except Exception as e:  # noqa: BLE001
                logger.warning(
                    "Failed to load SentenceTransformer model '%s': %s. "
                    "Falling back to token Jaccard similarity.",
                    cls._model_name,
                    e,
                )
                cls._model_load_failed = True
        return cls._model

    def get_embedding(self, text: str) -> Optional[np.ndarray]:
        """Get normalized dense embedding vector for text.

        Args:
            text: Input string to embed.

        Returns:
            Normalized 1D numpy array or None if model unavailable.
        """
        normalized_text = text.strip().lower()
        if not normalized_text:
            return None

        if normalized_text in self._cache:
            return self._cache[normalized_text]

        model = self._load_model()
        if model is None:
            return None

        try:
            vec = model.encode(
                normalized_text,
                convert_to_numpy=True,
                normalize_embeddings=True,
            )
            self._cache[normalized_text] = vec
            return vec
        except Exception as e:  # noqa: BLE001
            logger.warning(
                "Error embedding text '%s': %s",
                normalized_text,
                e,
            )
            return None

    def compute_cosine_similarity(self, text_a: str, text_b: str) -> float:
        """Compute cosine similarity between two attribute descriptions.

        Args:
            text_a: First attribute text (e.g. 'col: description').
            text_b: Second attribute text (e.g. 'col: description').

        Returns:
            Cosine similarity score in range [-1.0, 1.0], or fallback similarity.
        """
        clean_a = text_a.strip().lower()
        clean_b = text_b.strip().lower()

        if clean_a == clean_b:
            return 1.0

        vec_a = self.get_embedding(clean_a)
        vec_b = self.get_embedding(clean_b)

        if vec_a is not None and vec_b is not None:
            # Normalized embeddings: dot product equals cosine similarity
            sim = float(np.dot(vec_a, vec_b))
            return max(0.0, min(1.0, sim))

        return _compute_jaccard_string_similarity(clean_a, clean_b)
