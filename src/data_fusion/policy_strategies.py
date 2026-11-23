import re
import pandas as pd
from typing import Any
from data_fusion.models import FusionStrategy

def _is_null_or_empty(val: Any) -> bool:
    return pd.isna(val) or (isinstance(val, str) and val.strip() == "")

def resolve_trust_source(value_a: Any, value_b: Any, trust_score: float) -> Any:
    if trust_score >= 0.5:
        return value_a
    return value_b

def resolve_coalesce(value_a: Any, value_b: Any, trust_score: float) -> Any:
    a_empty = _is_null_or_empty(value_a)
    b_empty = _is_null_or_empty(value_b)
    
    if a_empty and b_empty:
        return resolve_trust_source(value_a, value_b, trust_score)
    elif a_empty:
        return value_b
    elif b_empty:
        return value_a
    else:
        return resolve_trust_source(value_a, value_b, trust_score)

def _str_len(val: Any) -> int:
    if _is_null_or_empty(val):
        return 0
    return len(str(val))

def resolve_longest_string(value_a: Any, value_b: Any, trust_score: float) -> Any:
    len_a = _str_len(value_a)
    len_b = _str_len(value_b)
    if len_a > len_b:
        return value_a
    elif len_b > len_a:
        return value_b
    else:
        return resolve_trust_source(value_a, value_b, trust_score)

def resolve_shortest_string(value_a: Any, value_b: Any, trust_score: float) -> Any:
    a_empty = _is_null_or_empty(value_a)
    b_empty = _is_null_or_empty(value_b)
    
    if a_empty and b_empty:
        return resolve_trust_source(value_a, value_b, trust_score)
    elif a_empty:
        return value_b
    elif b_empty:
        return value_a
        
    len_a = len(str(value_a))
    len_b = len(str(value_b))
    if len_a < len_b:
        return value_a
    elif len_b < len_a:
        return value_b
    else:
        return resolve_trust_source(value_a, value_b, trust_score)

def resolve_most_recent(value_a: Any, value_b: Any, trust_score: float) -> Any:
    dt_a = pd.to_datetime(value_a, errors='coerce') if not _is_null_or_empty(value_a) else pd.NaT
    dt_b = pd.to_datetime(value_b, errors='coerce') if not _is_null_or_empty(value_b) else pd.NaT
    
    a_nat = pd.isna(dt_a)
    b_nat = pd.isna(dt_b)
    
    if a_nat and b_nat:
        return resolve_trust_source(value_a, value_b, trust_score)
    elif a_nat:
        return value_b
    elif b_nat:
        return value_a
        
    if dt_a > dt_b:
        return value_a
    elif dt_b > dt_a:
        return value_b
    else:
        return resolve_trust_source(value_a, value_b, trust_score)

def _parse_float_safe(val: Any) -> float | None:
    if _is_null_or_empty(val):
        return None
    try:
        cleaned = (
            str(val)
            .replace(",", "")
            .replace("$", "")
            .replace("€", "")
            .replace("£", "")
            .replace("%", "")
            .strip()
        )
        return float(cleaned)
    except (ValueError, TypeError):
        return None

def resolve_numeric_max(value_a: Any, value_b: Any, trust_score: float) -> Any:
    num_a = _parse_float_safe(value_a)
    num_b = _parse_float_safe(value_b)
    
    if num_a is None and num_b is None:
        return resolve_trust_source(value_a, value_b, trust_score)
    elif num_a is None:
        return value_b
    elif num_b is None:
        return value_a
        
    if num_a > num_b:
        return value_a
    elif num_b > num_a:
        return value_b
    else:
        return resolve_trust_source(value_a, value_b, trust_score)

def resolve_numeric_min(value_a: Any, value_b: Any, trust_score: float) -> Any:
    num_a = _parse_float_safe(value_a)
    num_b = _parse_float_safe(value_b)
    
    if num_a is None and num_b is None:
        return resolve_trust_source(value_a, value_b, trust_score)
    elif num_a is None:
        return value_b
    elif num_b is None:
        return value_a
        
    if num_a < num_b:
        return value_a
    elif num_b < num_a:
        return value_b
    else:
        return resolve_trust_source(value_a, value_b, trust_score)

def resolve_numeric_avg(value_a: Any, value_b: Any, trust_score: float) -> Any:
    num_a = _parse_float_safe(value_a)
    num_b = _parse_float_safe(value_b)
    
    if num_a is None and num_b is None:
        return resolve_trust_source(value_a, value_b, trust_score)
    elif num_a is None:
        return value_b
    elif num_b is None:
        return value_a
    else:
        avg_val = (num_a + num_b) / 2.0
        # Preserve integer formatting if both were ints
        if float(num_a).is_integer() and float(num_b).is_integer() and avg_val.is_integer():
            return int(avg_val)
        return round(avg_val, 4)

def _split_and_strip(val: Any, delimiters: list[str] | None) -> tuple[list[str], str]:
    if not delimiters:
        delimiters = ["|"]
    sorted_delims = sorted(delimiters, key=len, reverse=True)
    re_pattern = "|".join(map(re.escape, sorted_delims))
    items = [item.strip() for item in re.split(re_pattern, str(val)) if item.strip()]
    return items, delimiters[0]

def resolve_union(value_a: Any, value_b: Any, trust_score: float, delimiters: list[str] | None) -> Any:
    a_empty = _is_null_or_empty(value_a)
    b_empty = _is_null_or_empty(value_b)
    
    if a_empty and b_empty:
        return resolve_trust_source(value_a, value_b, trust_score)
    elif a_empty:
        return value_b
    elif b_empty:
        return value_a
        
    items_a, primary_delim = _split_and_strip(value_a, delimiters)
    items_b, _ = _split_and_strip(value_b, delimiters)
    
    seen_lower = set()
    result_items = []
    
    for item in items_a + items_b:
        lower_item = item.lower()
        if lower_item not in seen_lower:
            seen_lower.add(lower_item)
            result_items.append(item)
            
    return primary_delim.join(result_items)

def resolve_intersection(value_a: Any, value_b: Any, trust_score: float, delimiters: list[str] | None) -> Any:
    a_empty = _is_null_or_empty(value_a)
    b_empty = _is_null_or_empty(value_b)
    
    if a_empty and b_empty:
        return resolve_trust_source(value_a, value_b, trust_score)
    elif a_empty:
        return value_b
    elif b_empty:
        return value_a
        
    items_a, primary_delim = _split_and_strip(value_a, delimiters)
    items_b, _ = _split_and_strip(value_b, delimiters)
    
    lower_a = [item.lower() for item in items_a]
    lower_b = [item.lower() for item in items_b]
    
    intersection_lower = set(lower_a).intersection(set(lower_b))
    
    if not intersection_lower:
        return resolve_trust_source(value_a, value_b, trust_score)
        
    trusted_items = items_a if trust_score >= 0.5 else items_b
    
    result_items = []
    seen = set()
    for item in trusted_items:
        lower_item = item.lower()
        if lower_item in intersection_lower and lower_item not in seen:
            result_items.append(item)
            seen.add(lower_item)
            
    return primary_delim.join(result_items)

def resolve_most_words(value_a: Any, value_b: Any, trust_score: float) -> Any:
    a_empty = _is_null_or_empty(value_a)
    b_empty = _is_null_or_empty(value_b)
    
    if a_empty and b_empty:
        return resolve_trust_source(value_a, value_b, trust_score)
    elif a_empty:
        return value_b
    elif b_empty:
        return value_a
        
    words_a = len(str(value_a).split())
    words_b = len(str(value_b).split())
    
    if words_a > words_b:
        return value_a
    elif words_b > words_a:
        return value_b
    else:
        return resolve_trust_source(value_a, value_b, trust_score)

def resolve_format_preserving(value_a: Any, value_b: Any, trust_score: float, pattern: str) -> Any:
    regex = re.compile(pattern)
    a_ok = False
    if not _is_null_or_empty(value_a):
        a_ok = bool(regex.search(str(value_a)))
        
    b_ok = False
    if not _is_null_or_empty(value_b):
        b_ok = bool(regex.search(str(value_b)))
        
    if a_ok and not b_ok:
        return value_a
    elif b_ok and not a_ok:
        return value_b
    else:
        return resolve_trust_source(value_a, value_b, trust_score)

def resolve(strategy: FusionStrategy, value_a: Any, value_b: Any, trust_score: float, *, pattern: str | None = None, delimiters: list[str] | None = None) -> Any:
    match strategy:
        case FusionStrategy.TRUST_SOURCE:
            return resolve_trust_source(value_a, value_b, trust_score)
        case FusionStrategy.COALESCE:
            return resolve_coalesce(value_a, value_b, trust_score)
        case FusionStrategy.LONGEST_STRING:
            return resolve_longest_string(value_a, value_b, trust_score)
        case FusionStrategy.SHORTEST_STRING:
            return resolve_shortest_string(value_a, value_b, trust_score)
        case FusionStrategy.MOST_RECENT:
            return resolve_most_recent(value_a, value_b, trust_score)
        case FusionStrategy.NUMERIC_MAX:
            return resolve_numeric_max(value_a, value_b, trust_score)
        case FusionStrategy.NUMERIC_MIN:
            return resolve_numeric_min(value_a, value_b, trust_score)
        case FusionStrategy.NUMERIC_AVG:
            return resolve_numeric_avg(value_a, value_b, trust_score)
        case FusionStrategy.UNION:
            return resolve_union(value_a, value_b, trust_score, delimiters)
        case FusionStrategy.INTERSECTION:
            return resolve_intersection(value_a, value_b, trust_score, delimiters)
        case FusionStrategy.MOST_WORDS:
            return resolve_most_words(value_a, value_b, trust_score)
        case FusionStrategy.FORMAT_PRESERVING:
            if pattern is None:
                raise ValueError("pattern is required for FORMAT_PRESERVING strategy")
            return resolve_format_preserving(value_a, value_b, trust_score, pattern)
        case _:
            raise ValueError(f"Unknown resolution strategy: {strategy}")
