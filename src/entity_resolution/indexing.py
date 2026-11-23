import pandas as pd
import recordlinkage
import logging
from typing import List, Union

from shared.config import config

logger = logging.getLogger(__name__)

class IndexingError(Exception):
    """Raised when indexing fails to produce candidate pairs."""
    pass

def perform_indexing(
    df_a: pd.DataFrame, 
    df_b: pd.DataFrame, 
    sorting_keys: Union[str, List[str]],
    window_size: int = 11
) -> pd.MultiIndex:
    """
    Multi-pass Sorted Neighborhood indexing.
    
    Performs one SN pass per sorting key and unions all candidate pairs.
    This improves pairs recall by capturing true matches that a single
    noisy sorting key would miss.
    
    Args:
        df_a:         Source A DataFrame.
        df_b:         Source B DataFrame.
        sorting_keys: One or more column names for SN passes.
                      Accepts a single string (backward compat) or a list.
        window_size:  Window size for each SN pass.
    
    Returns:
        MultiIndex of unique candidate pairs (union of all passes).
        
    Raises:
        IndexingError: If no valid keys are found or zero pairs are produced.
    """
    # Normalize to list for uniform handling
    if isinstance(sorting_keys, str):
        sorting_keys = [sorting_keys]
    
    # Filter out empty/falsy keys
    initial_keys = [k for k in sorting_keys if k and k.strip()]
    
    # Validate keys exist in BOTH dataframes
    valid_keys = []
    for k in initial_keys:
        if k in df_a.columns and k in df_b.columns:
            valid_keys.append(k)
        else:
            logger.warning(f"Sorting key '{k}' not found in both sources; skipping pass.")
    
    if not valid_keys:
        raise IndexingError(f"Indexing aborted: none of the provided keys {initial_keys} exist in both sources.")
    
    # Multi-pass: union candidate pairs from each key
    all_pairs = set()
    for key in valid_keys:
        # Cardinality safety warning check
        len_a = len(df_a)
        len_b = len(df_b)
        if len_a > 500:
            card_a = df_a[key].nunique()
            if (card_a / len_a) < 0.10:
                logger.warning(
                    f"Sorting key '{key}' has very low cardinality in df_a "
                    f"({card_a}/{len_a} distinct values). "
                    f"This may generate too many candidate pairs."
                )
        if len_b > 500:
            card_b = df_b[key].nunique()
            if (card_b / len_b) < 0.10:
                logger.warning(
                    f"Sorting key '{key}' has very low cardinality in df_b "
                    f"({card_b}/{len_b} distinct values). "
                    f"This may generate too many candidate pairs."
                )

        df_a_pass = df_a.assign(**{key: df_a[key].astype(str).fillna("")})
        df_b_pass = df_b.assign(**{key: df_b[key].astype(str).fillna("")})

        indexer = recordlinkage.Index()
        indexer.sortedneighbourhood(
            left_on=key, right_on=key, window=window_size
        )
        pairs = indexer.index(df_a_pass, df_b_pass)
        
        # Max pairs safety cap check
        max_pairs = getattr(config, "MAX_CANDIDATE_PAIRS_PER_PASS", 500000)
        if len(pairs) > max_pairs:
            logger.warning(
                f"Sorting key '{key}' produced too many candidate pairs "
                f"({len(pairs)} > {max_pairs}). Skipping this pass to "
                f"prevent pipeline hang."
            )
            continue
            
        all_pairs.update(pairs.tolist())
    
    if not all_pairs:
        raise IndexingError(f"Indexing failed: Sorted Neighborhood produced 0 pairs using keys {valid_keys} (window={window_size}).")
    
    return pd.MultiIndex.from_tuples(sorted(all_pairs), names=["left_id", "right_id"])
