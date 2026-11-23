"""String normalization utilities for data fusion evaluation."""

import re
import unicodedata


class NormalizationError(Exception):
    """Raised when string normalization fails due to data integrity errors."""



HONORIFICS: set[str] = {
    "dr",
    "prof",
    "sir",
    "mr",
    "mrs",
    "ms",
}


def normalize_string(text: str) -> set[str]:
    """Normalizes text into a set of words following benchmark protocol.

    Applies NFKD Unicode decomposition, lowercasing, honorific stripping,
    and non-alphanumeric punctuation removal.

    Args:
        text: Input string to normalize.

    Returns:
        Set of clean word tokens.

    Raises:
        NormalizationError: If input cannot be normalized.
    """
    if text is None:
        return set()

    try:
        raw_str = str(text).strip()
        if not raw_str or raw_str.lower() in ("nan", "none", "null"):
            return set()

        # 1. Unicode NFKD decomposition
        normalized = unicodedata.normalize("NFKD", raw_str)

        # 2. Lowercasing
        lowered = normalized.lower()

        # 3. Replace non-alphanumeric characters with space
        cleaned = re.sub(r"[^a-z0-9]", " ", lowered)

        # 4. Tokenize and filter honorifics + empty strings
        tokens = cleaned.split()
        words = {tok for tok in tokens if tok not in HONORIFICS}

        return words
    except Exception as e:
        raise NormalizationError(
            f"Failed to normalize text '{text}': {e}"
        ) from e
