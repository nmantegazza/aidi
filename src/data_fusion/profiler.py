import pandas as pd
import numpy as np
import random
import re
import warnings
from typing import Dict, Tuple, List, Any
from .models import (
    MultiTableFusionProfile, TableFusionProfile, ColumnConflictProfile,
    ConflictSample, SemanticType, PhysicalType
)

SENTINEL_VALUES = frozenset(
    {"", "-", "--", "n/a", "na", "null", "none", "?", "nan", "nil"}
)


class DataFusionProfiler:
    def profile(
        self, 
        source_a_origin: str, 
        source_b_origin: str, 
        tables: Dict[str, Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]]
    ) -> MultiTableFusionProfile:
        """
        Profiles the schema-matched entity pairs and computes conflict metrics and source trust scores.
        
        Args:
            source_a_origin: The origin name of Source A (e.g., 'CRM').
            source_b_origin: The origin name of Source B (e.g., 'ERP').
            tables: A mapping of table names to a tuple of (df_a, df_b, df_links).
                df_links should contain 'left_id' and 'right_id' corresponding to indices in df_a and df_b.
                
        Returns:
            A MultiTableFusionProfile object containing the computed metrics.
        """
        table_profiles = {}
        
        for table_name, (df_a, df_b, df_links) in tables.items():
            if df_links.empty:
                table_profiles[table_name] = TableFusionProfile(
                    table_name=table_name,
                    total_pairs=0,
                    columns={}
                )
                continue
                
            # Perform aligned inner join on the specified links
            # Reset index to ensure alignment by the provided IDs
            aligned_a = df_a.loc[df_links['left_id']].reset_index(drop=True)
            aligned_b = df_b.loc[df_links['right_id']].reset_index(drop=True)
            
            total_pairs = len(df_links)
            # They should have the same columns as they are schema-matched
            columns_to_profile = [col for col in aligned_a.columns if col in aligned_b.columns and col not in ["id", "left_id", "right_id"]]
            
            column_profiles = {}
            for col in columns_to_profile:
                series_a = aligned_a[col]
                series_b = aligned_b[col]
                
                # Metric Extraction: Conflict Rate & Null Rates
                # Consider conflict only if both are non-null and not equal, or one is null and the other is not.
                # Actually, conflict rate is usually where values differ. If both are null, they don't differ.
                # If one is null and one is not, they differ.
                
                # To handle Pandas NA/NaN safely:
                # We can treat pd.isna as a mask.
                na_a = series_a.isna()
                na_b = series_b.isna()
                
                # They conflict if neither is NA and they are not equal, 
                # OR if exactly one of them is NA (and the other is not)
                both_not_na = ~na_a & ~na_b
                values_differ = series_a != series_b
                
                conflict_mask = (both_not_na & values_differ) | (na_a ^ na_b)
                
                conflict_rate = float(conflict_mask.mean()) if total_pairs > 0 else 0.0
                
                source_a_null_rate = float(na_a.mean()) if total_pairs > 0 else 0.0
                source_b_null_rate = float(na_b.mean()) if total_pairs > 0 else 0.0
                
                # Determine physical type from pandas dtype with second pass for string/object
                dtype = series_a.dtype
                if pd.api.types.is_integer_dtype(dtype):
                    physical_type = PhysicalType.INTEGER
                elif pd.api.types.is_float_dtype(dtype):
                    physical_type = PhysicalType.FLOAT
                elif pd.api.types.is_bool_dtype(dtype):
                    physical_type = PhysicalType.BOOLEAN
                elif pd.api.types.is_datetime64_any_dtype(dtype):
                    physical_type = PhysicalType.DATETIME
                else:
                    physical_type = self._infer_physical_type_from_values(
                        series_a, series_b, col
                    )

                # Trust Score & Semantic Type Inference
                semantic_type, trust_score = self._compute_semantic_type_and_trust(
                    series_a, series_b, physical_type, col
                )
                
                # Extract conflict samples deterministically
                conflict_indices = conflict_mask[conflict_mask].index.tolist()
                rng = random.Random(42)
                sample_indices = rng.sample(
                    conflict_indices, min(5, len(conflict_indices))
                )
                
                samples = []
                for idx in sample_indices:
                    val_a = series_a.iloc[idx]
                    val_b = series_b.iloc[idx]
                    # Convert pandas NA/NaN to None for JSON serialization
                    if pd.isna(val_a):
                        val_a = None
                    if pd.isna(val_b):
                        val_b = None
                    samples.append(ConflictSample(value_a=val_a, value_b=val_b))
                    
                column_profiles[col] = ColumnConflictProfile(
                    column_name=col,
                    physical_type=physical_type,
                    semantic_type=semantic_type,
                    conflict_rate=conflict_rate,
                    source_a_null_rate=source_a_null_rate,
                    source_b_null_rate=source_b_null_rate,
                    source_trust_score=trust_score,
                    samples=samples
                )
                
            table_profiles[table_name] = TableFusionProfile(
                table_name=table_name,
                total_pairs=total_pairs,
                columns=column_profiles
            )
            
        return MultiTableFusionProfile(
            source_a_origin=source_a_origin,
            source_b_origin=source_b_origin,
            tables=table_profiles
        )

    def _infer_physical_type_from_values(
        self, series_a: pd.Series, series_b: pd.Series, col_name: str
    ) -> PhysicalType:
        col_lower = col_name.lower()
        tokens = set(re.split(r"[_\s\-]+", col_lower))
        if (
            col_lower in {"id", "isbn", "ticker", "flightid", "uuid", "guid", "key"}
            or col_lower.endswith(("_id", "_isbn", "_key", "_code", "_pk"))
            or col_lower.startswith(("id_", "isbn_"))
            or "id" in tokens
            or "isbn" in tokens
        ):
            return PhysicalType.TEXT

        non_null_a = series_a[series_a.notna() & (series_a.astype(str).str.strip() != "")]
        non_null_b = series_b[series_b.notna() & (series_b.astype(str).str.strip() != "")]
        combined = pd.concat([non_null_a, non_null_b])
        if combined.empty:
            return PhysicalType.TEXT

        sample = combined.sample(min(100, len(combined)), random_state=42)
        str_sample = sample.astype(str).str.strip()

        # 1. Check boolean
        lower_sample = str_sample.str.lower()
        bool_matches = lower_sample.isin({"true", "false", "t", "f", "yes", "no"}).mean()
        if bool_matches >= 0.9:
            return PhysicalType.BOOLEAN

        # 2. Check numeric
        cleaned_num = (
            str_sample
            .str.replace(",", "", regex=False)
            .str.replace("$", "", regex=False)
            .str.replace("€", "", regex=False)
            .str.replace("£", "", regex=False)
            .str.rstrip("%")
            .str.strip()
        )
        parsed_num = pd.to_numeric(cleaned_num, errors="coerce")
        if parsed_num.notna().mean() >= 0.85:
            valid_nums = parsed_num.dropna()
            if len(valid_nums) > 0 and (valid_nums % 1 == 0).all():
                return PhysicalType.INTEGER
            return PhysicalType.FLOAT

        # 3. Check datetime
        has_date_chars = str_sample.str.contains(
            r"[-/:,\s]|(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|am|pm)",
            case=False,
            regex=True,
        ).mean() >= 0.8
        if has_date_chars:
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", category=UserWarning)
                    parsed_dt = pd.to_datetime(str_sample, errors="coerce")
                if parsed_dt.notna().mean() >= 0.85:
                    return PhysicalType.DATETIME
            except Exception:
                pass

        return PhysicalType.TEXT

    def _get_effective_series(self, series: pd.Series) -> pd.Series:
        """Returns non-null series excluding sentinel placeholders."""
        if series.empty:
            return series
        non_null = series.dropna()
        if non_null.empty:
            return non_null
        mask = (
            ~non_null.astype(str)
            .str.strip()
            .str.lower()
            .isin(SENTINEL_VALUES)
        )
        return non_null[mask]

    def _compute_physical_conformity(
        self, series: pd.Series, physical_type: PhysicalType
    ) -> float:
        """Computes physical type conformity V(S) in [0.0, 1.0]."""
        if physical_type == PhysicalType.TEXT:
            return 1.0

        valid = self._get_effective_series(series)
        if valid.empty:
            return 1.0

        if physical_type == PhysicalType.INTEGER:
            def _is_int(val: Any) -> bool:
                if isinstance(val, bool):
                    return False
                if isinstance(val, (int, np.integer)):
                    return True
                try:
                    s = str(val).strip().replace(",", "")
                    f = float(s)
                    return f.is_integer()
                except (ValueError, TypeError, OverflowError):
                    return False

            return float(valid.apply(_is_int).mean())

        if physical_type == PhysicalType.FLOAT:
            def _is_float(val: Any) -> bool:
                if isinstance(val, bool):
                    return False
                if isinstance(val, (int, float, np.number)):
                    return not np.isnan(val)
                try:
                    s = (
                        str(val)
                        .strip()
                        .replace(",", "")
                        .replace("$", "")
                        .replace("€", "")
                        .replace("£", "")
                        .rstrip("%")
                        .strip()
                    )
                    float(s)
                    return True
                except (ValueError, TypeError, OverflowError):
                    return False

            return float(valid.apply(_is_float).mean())

        if physical_type == PhysicalType.DATETIME:
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    parsed = pd.to_datetime(valid, errors="coerce")
                return float(parsed.notna().mean())
            except Exception:
                return 0.0

        if physical_type == PhysicalType.BOOLEAN:
            bool_set = {
                "true", "false", "t", "f", "yes", "no", "1", "0", "y", "n"
            }
            def _is_bool(val: Any) -> bool:
                if isinstance(val, bool):
                    return True
                if isinstance(val, (int, np.integer)):
                    return val in (0, 1)
                return str(val).strip().lower() in bool_set

            return float(valid.apply(_is_bool).mean())

        return 1.0

    def _compute_normalized_entropy(self, series: pd.Series) -> float:
        """Computes normalized Shannon entropy H_norm(X) in [0.0, 1.0]."""
        valid = self._get_effective_series(series)
        n = len(valid)
        if n <= 1:
            return 0.0

        value_counts = valid.value_counts()
        k = len(value_counts)
        if k <= 1:
            return 0.0

        counts = np.asarray(value_counts.to_numpy(), dtype=float)
        probs = counts / n
        probs = probs[probs > 0]
        shannon_entropy = -float(np.sum(probs * np.log2(probs)))
        denom = float(np.log2(min(n, k)))
        if denom <= 0.0:
            return 0.0

        h_norm = shannon_entropy / denom
        return float(np.clip(h_norm, 0.0, 1.0))

    def _compute_source_quality(
        self, series: pd.Series, physical_type: PhysicalType
    ) -> float:
        """Computes composite source quality Q(S) in [0.0, 1.0]."""
        total = len(series)
        if total == 0:
            return 0.0

        effective = self._get_effective_series(series)
        completeness = len(effective) / total
        if completeness == 0.0:
            return 0.0

        v = self._compute_physical_conformity(series, physical_type)
        e = self._compute_normalized_entropy(series)
        diversity_factor = min(1.0, 0.5 + 0.5 * e)
        q = completeness * (0.7 * v + 0.3 * diversity_factor)
        return float(np.clip(q, 0.0, 1.0))

    def _compute_relative_trust(
        self,
        series_a: pd.Series,
        series_b: pd.Series,
        physical_type: PhysicalType,
    ) -> float:
        """Calculates normalized relative trust score Q(A) / (Q(A) + Q(B))."""
        q_a = self._compute_source_quality(series_a, physical_type)
        q_b = self._compute_source_quality(series_b, physical_type)
        denom = q_a + q_b
        if denom <= 0.0:
            return 0.5
        return float(np.clip(q_a / denom, 0.0, 1.0))

    def _infer_semantic_type(
        self,
        series_a: pd.Series,
        series_b: pd.Series,
        physical_type: PhysicalType,
        col_name: str = "",
    ) -> SemanticType:
        """Infers semantic type for TEXT columns via regex sniffing."""
        if physical_type != PhysicalType.TEXT:
            return SemanticType.NONE

        eff_a = self._get_effective_series(series_a).astype(str)
        eff_b = self._get_effective_series(series_b).astype(str)
        combined = pd.concat([eff_a, eff_b])
        if combined.empty:
            return SemanticType.NONE

        if len(combined) > 100:
            combined = combined.sample(100, random_state=42)

        col_lower = col_name.lower()
        tokens = set(re.split(r"[_\s\-]+", col_lower))
        is_id_col = (
            col_lower in {
                "id", "isbn", "ticker", "flightid", "uuid", "guid", "key"
            }
            or col_lower.endswith(("_id", "_isbn", "_key", "_code", "_pk"))
            or col_lower.startswith(("id_", "isbn_"))
            or "id" in tokens
            or "isbn" in tokens
        )

        for sem_type in SemanticType:
            if sem_type == SemanticType.PHONE and is_id_col:
                continue
            pattern = sem_type.regex_pattern
            if not pattern:
                continue
            if combined.str.match(pattern).mean() > 0.80:
                return sem_type

        return SemanticType.NONE

    def _compute_semantic_type_and_trust(
        self,
        series_a: pd.Series,
        series_b: pd.Series,
        physical_type: PhysicalType,
        col_name: str = "",
    ) -> Tuple[SemanticType, float]:
        """Infers semantic type and calculates domain-agnostic trust score."""
        semantic_type = self._infer_semantic_type(
            series_a, series_b, physical_type, col_name
        )
        trust_score = self._compute_relative_trust(
            series_a, series_b, physical_type
        )
        return semantic_type, trust_score
