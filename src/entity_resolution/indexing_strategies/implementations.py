"""
Concrete implementation of static indexing strategies.
"""

from __future__ import annotations

from typing import List, Union, Tuple
import pandas as pd
import recordlinkage
import recordlinkage.base
from datasketch import MinHash, MinHashLSH
from sklearn.feature_extraction.text import TfidfVectorizer

from entity_resolution.models import (
    SortedNeighborhoodIndexConfig,
    MinHashLSHIndexConfig,
    QGramIndexConfig,
    TFIDFIndexConfig,
)
from entity_resolution.prompts import (
    SN_INDEXING_SYSTEM_PROMPT,
    MINHASH_LSH_INDEXING_SYSTEM_PROMPT,
    QGRAM_INDEXING_SYSTEM_PROMPT,
    TFIDF_INDEXING_SYSTEM_PROMPT,
)
from .base import BaseIndexingStrategy


class SortedNeighborhoodStrategy(BaseIndexingStrategy):
    """Sorted Neighborhood indexing strategy."""

    config_schema = SortedNeighborhoodIndexConfig
    config_prompt = SN_INDEXING_SYSTEM_PROMPT

    @classmethod
    def from_llm_config(
        cls, config: SortedNeighborhoodIndexConfig
    ) -> SortedNeighborhoodStrategy:
        """Constructs SortedNeighborhoodStrategy from SortedNeighborhoodIndexConfig."""
        keys = config.sorting_keys
        return cls(keys=keys, window_size=config.window_size)

    def __init__(
        self,
        keys: Union[str, List[str]],
        window_size: int = 11,
        name: str | None = None,
    ):
        """Initializes the Sorted Neighborhood strategy.

        Args:
            keys: Column name(s) to use as sorting keys.
            window_size: Window size for neighborhood scanning.
            name: Optional custom strategy display name.
        """
        if isinstance(keys, str):
            self.keys = [keys]
        else:
            self.keys = list(keys)
        self.window_size = window_size
        self._custom_name = name

    @property
    def name(self) -> str:
        """Return display name including keys and window size."""
        if self._custom_name:
            return self._custom_name
        keys_str = ",".join(self.keys)
        return f"SortedNeighborhood(keys=[{keys_str}], w={self.window_size})"

    def _perform_indexing(
        self, df_a: pd.DataFrame, df_b: pd.DataFrame
    ) -> pd.MultiIndex:
        """Runs multi-pass sorted neighborhood indexing on df_a and df_b.

        Args:
            df_a: Left input DataFrame.
            df_b: Right input DataFrame.

        Returns:
            pd.MultiIndex of candidate record pairs.
        """
        all_pairs = set()

        for key in self.keys:
            if key not in df_a.columns or key not in df_b.columns:
                continue

            # Ensure sorting key values are strings across both DataFrames
            df_a_pass = df_a.assign(**{key: df_a[key].astype(str).fillna("")})
            df_b_pass = df_b.assign(**{key: df_b[key].astype(str).fillna("")})

            indexer = recordlinkage.Index()
            indexer.sortedneighbourhood(
                left_on=key, right_on=key, window=self.window_size
            )
            pairs = indexer.index(df_a_pass, df_b_pass)
            all_pairs.update(pairs.tolist())

        if not all_pairs:
            return pd.MultiIndex.from_tuples([], names=[0, 1])

        return pd.MultiIndex.from_tuples(list(all_pairs))


class MinHashLSHIndexAlgorithm(recordlinkage.base.BaseIndexAlgorithm):
    """Custom recordlinkage index algorithm using datasketch MinHash LSH."""

    def __init__(
        self,
        keys: List[str],
        ngram_size: int = 1,
        threshold: float = 0.5,
        num_perm: int = 64,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.keys = keys
        self.ngram_size = ngram_size
        self.threshold = threshold
        self.num_perm = num_perm

    def _link_index(
        self, df_a: pd.DataFrame, df_b: pd.DataFrame
    ) -> pd.MultiIndex:
        """Build candidate pairs index between df_a and df_b using MinHash LSH.

        Args:
            df_a: Left input DataFrame.
            df_b: Right input DataFrame.

        Returns:
            pd.MultiIndex of candidate record pairs.
        """
        valid_keys = [
            k for k in self.keys if k in df_a.columns and k in df_b.columns
        ]
        if not valid_keys or df_a.empty or df_b.empty:
            return pd.MultiIndex.from_tuples([], names=[0, 1])

        lsh = MinHashLSH(threshold=self.threshold, num_perm=self.num_perm)

        # Pre-materialise all text values to avoid per-row Series construction
        # overhead from iterrows(); this is the primary source of the 69x
        # slowdown relative to vectorised SN — keep the loop over plain strings.
        indices_a = df_a.index.tolist()
        texts_a = self._build_texts(df_a, valid_keys)
        for idx_a, text in zip(indices_a, texts_a):
            lsh.insert(idx_a, self._text_to_minhash(text))

        pairs = set()
        indices_b = df_b.index.tolist()
        texts_b = self._build_texts(df_b, valid_keys)
        for idx_b, text in zip(indices_b, texts_b):
            matches = lsh.query(self._text_to_minhash(text))
            for idx_a in matches:
                pairs.add((idx_a, idx_b))

        if not pairs:
            return pd.MultiIndex.from_tuples([], names=[0, 1])

        return pd.MultiIndex.from_tuples(list(pairs), names=[0, 1])

    def _build_texts(
        self, df: pd.DataFrame, keys: List[str]
    ) -> List[str]:
        """Vectorised extraction of concatenated field text for all rows.

        Joins field values with a space separator so that shingles cannot
        bleed across field boundaries (e.g. 'apple tv' + 'remote' must not
        produce the same n-gram set as 'apple' + 'tvremote').

        Args:
            df: Input DataFrame.
            keys: Column names to concatenate.

        Returns:
            List of text strings, one per row, aligned with df.index.
        """
        # Fill NaN with empty string then concatenate with a space separator
        parts = [df[k].fillna("").astype(str) for k in keys]
        combined: pd.Series = parts[0]
        for part in parts[1:]:
            combined = combined + " " + part
        return combined.str.strip().tolist()

    def _text_to_minhash(self, text: str) -> MinHash:
        """Converts a text string to a MinHash signature using word n-grams.

        Uses word-level tokenisation rather than character n-grams. A title of
        50 characters produces ~48 char 3-grams but only ~8 word unigrams,
        meaning ~6x fewer MinHash.update() calls per record. Word n-grams also
        yield higher recall because word-level Jaccard is more meaningful for
        product titles than character-level Jaccard.

        Args:
            text: Input text to shingle into word n-grams.

        Returns:
            MinHash signature object.
        """
        words = text.lower().split()
        # Pad with a sentinel token if the text has fewer words than ngram_size
        # so that every record produces at least one shingle.
        if len(words) < self.ngram_size:
            words += ["<pad>"] * (self.ngram_size - len(words))
        mh = MinHash(num_perm=self.num_perm)
        for i in range(len(words) - self.ngram_size + 1):
            shingle = " ".join(words[i : i + self.ngram_size])
            mh.update(shingle.encode("utf-8"))
        return mh


class MinHashLSHStrategy(BaseIndexingStrategy):
    """MinHash LSH indexing strategy."""

    config_schema = MinHashLSHIndexConfig
    config_prompt = MINHASH_LSH_INDEXING_SYSTEM_PROMPT

    @classmethod
    def from_llm_config(
        cls, config: MinHashLSHIndexConfig
    ) -> MinHashLSHStrategy:
        """Constructs MinHashLSHStrategy from MinHashLSHIndexConfig."""
        return cls(
            keys=config.blocking_keys,
            ngram_size=config.ngram_size,
            threshold=config.threshold,
        )

    def __init__(
        self,
        keys: Union[str, List[str]],
        ngram_size: int = 1,
        threshold: float = 0.5,
        num_perm: int = 64,
        name: str | None = None,
    ):
        """Initializes the MinHash LSH strategy.

        Args:
            keys: Column name(s) to use as blocking keys.
            ngram_size: N-gram shingle size.
            threshold: Jaccard similarity threshold.
            num_perm: Number of hash permutations.
            name: Optional custom strategy display name.
        """
        if isinstance(keys, str):
            self.keys = [keys]
        else:
            self.keys = list(keys)
        self.ngram_size = ngram_size
        self.threshold = threshold
        self.num_perm = num_perm
        self._custom_name = name

    @property
    def name(self) -> str:
        """Return display name including keys, ngram, and threshold."""
        if self._custom_name:
            return self._custom_name
        keys_str = ",".join(self.keys)
        return (
            f"MinHashLSH(keys=[{keys_str}], "
            f"ngram={self.ngram_size}, t={self.threshold})"
        )

    def _perform_indexing(
        self, df_a: pd.DataFrame, df_b: pd.DataFrame
    ) -> pd.MultiIndex:
        """Runs MinHash LSH indexing on df_a and df_b.

        Args:
            df_a: Left input DataFrame.
            df_b: Right input DataFrame.

        Returns:
            pd.MultiIndex of candidate record pairs.
        """
        indexer = MinHashLSHIndexAlgorithm(
            keys=self.keys,
            ngram_size=self.ngram_size,
            threshold=self.threshold,
            num_perm=self.num_perm,
        )
        return indexer.index(df_a, df_b)


class QGramIndexStrategy(BaseIndexingStrategy):
    """Character Q-Gram Inverted Index strategy with automatic q sizing and stop-gram pruning."""

    config_schema = QGramIndexConfig
    config_prompt = QGRAM_INDEXING_SYSTEM_PROMPT

    @classmethod
    def from_llm_config(
        cls, config: QGramIndexConfig
    ) -> QGramIndexStrategy:
        """Constructs QGramIndexStrategy from QGramIndexConfig."""
        return cls(keys=config.keys)

    def __init__(
        self,
        keys: Union[str, List[str]],
        q: int | None = None,
        max_token_freq: float = 0.05,
        name: str | None = None,
    ):
        """Initializes the Q-Gram inverted index strategy.

        Args:
            keys: Column name(s) to use for Q-gram extraction.
            q: Optional explicit character Q-gram length. If None, q is automatically
               computed based on dataset scale.
            max_token_freq: Maximum document frequency fraction (0.0 to 1.0) above which
               a token is pruned as a high-frequency stop-gram. Default is 0.05 (5%).
            name: Optional custom strategy display name.
        """
        if isinstance(keys, str):
            self.keys = [keys]
        else:
            self.keys = list(keys)
        self.user_q = q
        self.max_token_freq = max_token_freq
        self._custom_name = name
        self._computed_q_val = None

    @property
    def name(self) -> str:
        """Return display name including keys and q."""
        if self._custom_name:
            return self._custom_name
        keys_str = ",".join(self.keys)
        if self._computed_q_val is not None:
            q_str = f"q={self._computed_q_val}(auto)" if self.user_q is None else f"q={self._computed_q_val}"
        else:
            q_str = f"q={self.user_q}" if self.user_q is not None else "q=auto"
        return f"QGramIndex(keys=[{keys_str}], {q_str})"

    def _compute_q(self, len_a: int, len_b: int) -> int:
        """Dynamically computes Q-gram length based on dataset Cartesian scale.

        Args:
            len_a: Number of records in left DataFrame.
            len_b: Number of records in right DataFrame.

        Returns:
            Computed character Q-gram length (q).
        """
        if self.user_q is not None:
            return self.user_q
        n_pairs = len_a * len_b
        if n_pairs < 100_000:
            return 3
        else:
            return 5

    def _perform_indexing(
        self, df_a: pd.DataFrame, df_b: pd.DataFrame
    ) -> pd.MultiIndex:
        """Runs Q-gram inverted index join on df_a and df_b with token pruning.

        Args:
            df_a: Left input DataFrame.
            df_b: Right input DataFrame.

        Returns:
            pd.MultiIndex of candidate record pairs.
        """
        valid_keys = [
            k for k in self.keys if k in df_a.columns and k in df_b.columns
        ]
        if not valid_keys or df_a.empty or df_b.empty:
            return pd.MultiIndex.from_tuples([], names=[0, 1])

        effective_q = self._compute_q(len(df_a), len(df_b))
        self._computed_q_val = effective_q

        texts_a = self._build_texts(df_a, valid_keys)
        texts_b = self._build_texts(df_b, valid_keys)

        qgrams_a = texts_a.apply(lambda s: self._extract_qgrams(s, effective_q))
        qgrams_b = texts_b.apply(lambda s: self._extract_qgrams(s, effective_q))

        tokens_a = (
            pd.DataFrame({"id_a": qgrams_a.index, "token": qgrams_a.values})
            .explode("token")
            .dropna()
        )
        tokens_b = (
            pd.DataFrame({"id_b": qgrams_b.index, "token": qgrams_b.values})
            .explode("token")
            .dropna()
        )

        tokens_a = tokens_a[tokens_a["token"] != ""]
        tokens_b = tokens_b[tokens_b["token"] != ""]

        if tokens_a.empty or tokens_b.empty:
            return pd.MultiIndex.from_tuples([], names=[0, 1])

        # Frequency-based stop-gram pruning
        if self.max_token_freq < 1.0:
            threshold_a = max(2.0, len(df_a) * self.max_token_freq)
            threshold_b = max(2.0, len(df_b) * self.max_token_freq)

            freq_a = tokens_a.groupby("token")["id_a"].nunique()
            freq_b = tokens_b.groupby("token")["id_b"].nunique()

            high_freq_a = set(freq_a[freq_a > threshold_a].index)
            high_freq_b = set(freq_b[freq_b > threshold_b].index)
            high_freq_tokens = high_freq_a.union(high_freq_b)

            if high_freq_tokens:
                tokens_a = tokens_a[~tokens_a["token"].isin(high_freq_tokens)]
                tokens_b = tokens_b[~tokens_b["token"].isin(high_freq_tokens)]

        if tokens_a.empty or tokens_b.empty:
            return pd.MultiIndex.from_tuples([], names=[0, 1])

        merged = pd.merge(tokens_a, tokens_b, on="token")
        if merged.empty:
            return pd.MultiIndex.from_tuples([], names=[0, 1])

        pairs_df = merged[["id_a", "id_b"]].drop_duplicates()
        tuples = list(zip(pairs_df["id_a"], pairs_df["id_b"]))
        return pd.MultiIndex.from_tuples(tuples, names=[0, 1])

    @staticmethod
    def _build_texts(df: pd.DataFrame, keys: List[str]) -> pd.Series:
        """Concatenates values of specified keys per row into lowercased strings."""
        parts = [df[k].fillna("").astype(str) for k in keys]
        combined: pd.Series = parts[0]
        for part in parts[1:]:
            combined = combined + " " + part
        return combined.str.lower()

    @staticmethod
    def _extract_qgrams(text: str, q: int) -> List[str]:
        """Extracts character Q-grams of length q from text string."""
        if not text:
            return []
        if len(text) <= q:
            return [text]
        return [text[i : i + q] for i in range(len(text) - q + 1)]


class TFIDFIndexStrategy(BaseIndexingStrategy):
    """TF-IDF sparse vector indexing strategy using cosine similarity."""

    config_schema = TFIDFIndexConfig
    config_prompt = TFIDF_INDEXING_SYSTEM_PROMPT

    @classmethod
    def from_llm_config(
        cls, config: TFIDFIndexConfig
    ) -> TFIDFIndexStrategy:
        """Constructs TFIDFIndexStrategy from TFIDFIndexConfig.

        Defaults tokenization to word 1-2 grams with a lowered 0.1 cosine threshold 
        to prioritize recall over precision during the indexing phase.
        """
        return cls(
            keys=config.keys,
            analyzer="word",
            ngram_range=(1, 2),
            threshold=0.1,
        )

    def __init__(
        self,
        keys: Union[str, List[str]],
        analyzer: str = "char_wb",
        ngram_range: Tuple[int, int] = (3, 3),
        threshold: float = 0.5,
        name: str | None = None,
    ):
        """Initializes the TF-IDF index strategy.

        Args:
            keys: Column name(s) to use for TF-IDF vectorization.
            analyzer: Feature analyzer type ('word', 'char', or 'char_wb').
            ngram_range: Lower and upper boundary of n-grams to extract.
            threshold: Cosine similarity threshold (0.0 to 1.0) for pairing.
            name: Optional custom strategy display name.
        """
        if isinstance(keys, str):
            self.keys = [keys]
        else:
            self.keys = list(keys)
        self.analyzer = analyzer
        self.ngram_range = ngram_range
        self.threshold = threshold
        self._custom_name = name

    @property
    def name(self) -> str:
        """Return display name including keys, analyzer, ngram, and threshold."""
        if self._custom_name:
            return self._custom_name
        keys_str = ",".join(self.keys)
        return (
            f"TFIDFIndex(keys=[{keys_str}], "
            f"analyzer={self.analyzer}, ngram={self.ngram_range}, "
            f"t={self.threshold})"
        )

    def _perform_indexing(
        self, df_a: pd.DataFrame, df_b: pd.DataFrame
    ) -> pd.MultiIndex:
        """Runs TF-IDF sparse matrix cosine similarity indexing on df_a and df_b.

        Args:
            df_a: Left input DataFrame.
            df_b: Right input DataFrame.

        Returns:
            pd.MultiIndex of candidate record pairs.
        """
        import numpy as np

        valid_keys = [
            k for k in self.keys if k in df_a.columns and k in df_b.columns
        ]
        if not valid_keys or df_a.empty or df_b.empty:
            return pd.MultiIndex.from_tuples([], names=[0, 1])

        texts_a = self._build_texts(df_a, valid_keys).tolist()
        texts_b = self._build_texts(df_b, valid_keys).tolist()

        # Using np.float32 halves the memory usage for sparse matrices
        vectorizer = TfidfVectorizer(
            analyzer=self.analyzer, ngram_range=self.ngram_range, dtype=np.float32
        )

        try:
            matrix_a = vectorizer.fit_transform(texts_a)
            del texts_a
            matrix_b = vectorizer.transform(texts_b)
            del texts_b
            del vectorizer
            
            import gc
            gc.collect()
        except ValueError:
            return pd.MultiIndex.from_tuples([], names=[0, 1])

        # Batch dot product calculation to heavily reduce peak memory
        batch_size = 1000
        matrix_b_t = matrix_b.T.tocsc()
        
        idx_a = df_a.index
        idx_b = df_b.index
        
        pairs = []
        
        import gc
        for start_idx in range(0, matrix_a.shape[0], batch_size):
            end_idx = min(start_idx + batch_size, matrix_a.shape[0])
            batch_a = matrix_a[start_idx:end_idx]
            
            similarity_batch = batch_a.dot(matrix_b_t)
            coo = similarity_batch.tocoo()
            
            mask = coo.data >= self.threshold
            if mask.any():
                # Adjust row indices to the global matrix_a row position
                row_indices = coo.row[mask] + start_idx
                col_indices = coo.col[mask]
                
                batch_pairs = zip(idx_a[row_indices], idx_b[col_indices])
                pairs.extend(batch_pairs)
                
            # Explicitly free intermediate batch matrices
            del similarity_batch
            del coo
            del mask
            gc.collect()

        if not pairs:
            return pd.MultiIndex.from_tuples([], names=[0, 1])

        return pd.MultiIndex.from_tuples(pairs, names=[0, 1])

    @staticmethod
    def _build_texts(df: pd.DataFrame, keys: List[str]) -> pd.Series:
        """Concatenates values of specified keys per row into lowercased strings."""
        parts = [df[k].fillna("").astype(str) for k in keys]
        combined: pd.Series = parts[0]
        for part in parts[1:]:
            combined = combined + " " + part
        return combined.str.lower()


