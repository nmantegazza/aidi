"""Reference-free evaluation and metric computation for schema alignment."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from schema_integration.alignment.models import AlignmentReport
from schema_integration.benchmarking.alignment.models import (
    AlignmentIterationMetrics,
    AttributeConsensusPair,
    DetectedCloneRecord,
    MultiIterationConsistencyReport,
    StructuralIntegrityStats,
    TopologicalDriftStats,
)
from schema_integration.benchmarking.alignment.similarity import (
    SentenceTransformerEmbedder,
)
from schema_integration.benchmarking.common.models import TokenUsage
from shared.agents import ExecutionMetadata
from shared.schema_models import DataPackage


class AlignmentEvaluator:
    """Evaluates Information Preservation, Structural Integrity, and Minimality."""

    @staticmethod
    def _normalize_col_ref(ref: str) -> tuple[str | None, str, str]:
        """Normalize a column reference string.

        Extracts (schema_or_source_prefix, table_name, column_name).
        Examples:
          "source_a.patients.id" -> ("source_a", "patients", "id")
          "patients.id" -> (None, "patients", "id")
          "bank1.branch.branch_id" -> ("bank1", "branch", "branch_id")
        """
        parts = [p.strip().lower() for p in ref.strip().split(".") if p.strip()]
        if len(parts) >= 3:
            return (parts[0], parts[1], parts[2])
        if len(parts) == 2:
            return (None, parts[0], parts[1])
        if len(parts) == 1:
            return (None, "", parts[0])
        return (None, "", "")

    @classmethod
    def _extract_source_columns(
        cls,
        pkg: DataPackage,
    ) -> set[tuple[str, str]]:
        """Extract all (table, col) pairs from a DataPackage in lowercase."""
        cols: set[tuple[str, str]] = set()
        for res in pkg.resources:
            t_name = res.name.strip().lower()
            for f in res.schema_info.fields:
                cols.add((t_name, f.name.strip().lower()))
        return cols

    @classmethod
    def compute_completeness(
        cls,
        target_schema: DataPackage,
        source_a: DataPackage,
        source_b: DataPackage,
    ) -> tuple[float, list[str]]:
        """Compute proportion of source columns referenced in target schema.

        Args:
            target_schema: Unified target DataPackage.
            source_a: Source A DataPackage.
            source_b: Source B DataPackage.

        Returns:
            Tuple of (Completeness score [0.0, 1.0], list of unmapped columns).
        """
        cols_a = cls._extract_source_columns(source_a)
        cols_b = cls._extract_source_columns(source_b)
        all_source_cols = {(f"a:{t}.{c}") for t, c in cols_a} | {
            (f"b:{t}.{c}") for t, c in cols_b
        }

        if not all_source_cols:
            return 1.0, []

        schema_a_name = source_a.name.strip().lower()
        schema_b_name = source_b.name.strip().lower()

        referenced_source_cols: set[str] = set()

        for res in target_schema.resources:
            for field in res.schema_info.fields:
                for prov in field.source_provenance or []:
                    prefix, tbl, col = cls._normalize_col_ref(prov)
                    if not tbl or not col:
                        continue

                    # Check source A match
                    if (tbl, col) in cols_a and prefix in [
                        None,
                        "source_a",
                        "a",
                        schema_a_name,
                    ]:
                        referenced_source_cols.add(f"a:{tbl}.{col}")

                    # Check source B match
                    if (tbl, col) in cols_b and prefix in [
                        None,
                        "source_b",
                        "b",
                        schema_b_name,
                    ]:
                        referenced_source_cols.add(f"b:{tbl}.{col}")

        completeness = len(referenced_source_cols) / len(all_source_cols)
        unmapped = sorted(all_source_cols - referenced_source_cols)
        return round(min(1.0, completeness), 4), unmapped

    @classmethod
    def compute_structural_integrity(
        cls,
        target_schema: DataPackage,
        source_a: DataPackage | None = None,
        source_b: DataPackage | None = None,
    ) -> StructuralIntegrityStats:
        """Evaluate primary and foreign key validity plus source relationship preservation.

        Args:
            target_schema: Unified target DataPackage.
            source_a: Optional Source A DataPackage.
            source_b: Optional Source B DataPackage.

        Returns:
            StructuralIntegrityStats with PK/FK validity, source FK preservation, score, and alerts.
        """
        table_map: dict[str, set[str]] = {}
        for res in target_schema.resources:
            t_name = res.name.strip().lower()
            field_names = {f.name.strip().lower() for f in res.schema_info.fields}
            table_map[t_name] = field_names

        total_tables = len(target_schema.resources)
        valid_pk_tables = 0

        for res in target_schema.resources:
            t_name = res.name.strip().lower()
            pks = res.schema_info.primary_key_columns
            if pks:
                pks_lower = [str(k).strip().lower() for k in pks]
                if all(k in table_map[t_name] for k in pks_lower):
                    valid_pk_tables += 1

        pk_validity = (
            (valid_pk_tables / total_tables) if total_tables > 0 else 1.0
        )

        total_fks = 0
        valid_fks = 0
        broken_fks: list[str] = []
        target_fk_tables: set[tuple[str, str]] = set()

        for res in target_schema.resources:
            src_tbl = res.name.strip().lower()
            for fk in res.schema_info.foreignKeys:
                total_fks += 1
                ref_tbl = fk.reference.resource.strip().lower()
                ref_fields = (
                    [fk.reference.fields]
                    if isinstance(fk.reference.fields, str)
                    else fk.reference.fields
                )
                ref_fields_lower = [str(f).strip().lower() for f in ref_fields]

                if ref_tbl not in table_map:
                    broken_fks.append(
                        f"Table '{src_tbl}' references missing table '{ref_tbl}'"
                    )
                    continue

                missing_cols = [
                    c for c in ref_fields_lower if c not in table_map[ref_tbl]
                ]
                if missing_cols:
                    broken_fks.append(
                        f"Table '{src_tbl}' references missing column(s) {missing_cols} "
                        f"in '{ref_tbl}'"
                    )
                    continue

                valid_fks += 1
                target_fk_tables.add((src_tbl, ref_tbl))

        fk_validity = (valid_fks / total_fks) if total_fks > 0 else 1.0

        # Source Foreign Key Preservation Check
        total_source_fks = 0
        preserved_source_fks = 0
        unpreserved_source_fks: list[str] = []

        if source_a is not None and source_b is not None:
            cols_a = cls._extract_source_columns(source_a)
            cols_b = cls._extract_source_columns(source_b)
            schema_a_name = source_a.name.strip().lower()
            schema_b_name = source_b.name.strip().lower()

            col_map: dict[tuple[str, str, str], set[tuple[str, str]]] = defaultdict(set)
            for res in target_schema.resources:
                t_name = res.name.strip().lower()
                for field in res.schema_info.fields:
                    f_name = field.name.strip().lower()
                    for prov in field.source_provenance or []:
                        prefix, tbl, col = cls._normalize_col_ref(prov)
                        if not tbl or not col:
                            continue
                        if (tbl, col) in cols_a and prefix in [
                            None,
                            "source_a",
                            "a",
                            schema_a_name,
                        ]:
                            col_map[("a", tbl, col)].add((t_name, f_name))
                        if (tbl, col) in cols_b and prefix in [
                            None,
                            "source_b",
                            "b",
                            schema_b_name,
                        ]:
                            col_map[("b", tbl, col)].add((t_name, f_name))

            for src_pkg, tag, s_name in [
                (source_a, "a", schema_a_name),
                (source_b, "b", schema_b_name),
            ]:
                for res in src_pkg.resources:
                    src_tbl = res.name.strip().lower()
                    for fk in res.schema_info.foreignKeys:
                        total_source_fks += 1
                        ref_tbl = fk.reference.resource.strip().lower()
                        fk_fields = (
                            [fk.fields]
                            if isinstance(fk.fields, str)
                            else fk.fields
                        )
                        ref_fields = (
                            [fk.reference.fields]
                            if isinstance(fk.reference.fields, str)
                            else fk.reference.fields
                        )

                        src_loc_sets = [
                            col_map.get((tag, src_tbl, str(c).strip().lower()), set())
                            for c in fk_fields
                        ]
                        ref_loc_sets = [
                            col_map.get((tag, ref_tbl, str(c).strip().lower()), set())
                            for c in ref_fields
                        ]

                        if any(len(s) == 0 for s in src_loc_sets) or any(len(s) == 0 for s in ref_loc_sets):
                            unpreserved_source_fks.append(
                                f"Source {s_name} FK '{src_tbl}' -> '{ref_tbl}' "
                                "has unmapped columns in target"
                            )
                            continue

                        candidate_src_tables = set.intersection(*[{loc[0] for loc in s} for s in src_loc_sets])
                        candidate_ref_tables = set.intersection(*[{loc[0] for loc in s} for s in ref_loc_sets])

                        if not candidate_src_tables or not candidate_ref_tables:
                            unpreserved_source_fks.append(
                                f"Source {s_name} FK '{src_tbl}' -> '{ref_tbl}' "
                                "spans multiple target tables"
                            )
                            continue

                        is_preserved = False
                        for t_s in candidate_src_tables:
                            for t_r in candidate_ref_tables:
                                if t_s == t_r or (t_s, t_r) in target_fk_tables:
                                    is_preserved = True
                                    break
                            if is_preserved:
                                break

                        if is_preserved:
                            preserved_source_fks += 1
                        else:
                            unpreserved_source_fks.append(
                                f"Source {s_name} FK '{src_tbl}' -> '{ref_tbl}' "
                                f"missing relationship in target (candidates: '{candidate_src_tables}' -> '{candidate_ref_tables}')"
                            )

        source_fk_preservation = (
            (preserved_source_fks / total_source_fks)
            if total_source_fks > 0
            else 1.0
        )
        score = pk_validity * fk_validity * source_fk_preservation

        return StructuralIntegrityStats(
            pk_validity=round(pk_validity, 4),
            fk_validity=round(fk_validity, 4),
            source_fk_preservation=round(source_fk_preservation, 4),
            score=round(score, 4),
            total_tables=total_tables,
            total_fks=total_fks,
            total_source_fks=total_source_fks,
            preserved_source_fks=preserved_source_fks,
            broken_fks=broken_fks,
            unpreserved_source_fks=unpreserved_source_fks,
        )

    @classmethod
    def _are_types_compatible(cls, type_a: str, type_b: str) -> bool:
        """Check if two Frictionless field data types are comparable."""
        t_a = type_a.strip().lower()
        t_b = type_b.strip().lower()
        if t_a == t_b:
            return True
        numeric_types = {"integer", "number"}
        if t_a in numeric_types and t_b in numeric_types:
            return True
        date_types = {"date", "datetime"}
        if t_a in date_types and t_b in date_types:
            return True
        return False

    @classmethod
    def compute_reference_free_minimality(
        cls,
        target_schema: DataPackage,
        source_a: DataPackage,
        source_b: DataPackage,
        clone_threshold: float = 0.85,
    ) -> tuple[float, list[DetectedCloneRecord]]:
        """Compute Intra-Table Uniqueness and detect semantic clone columns.

        Args:
            target_schema: Unified target DataPackage.
            source_a: Source A DataPackage.
            source_b: Source B DataPackage.
            clone_threshold: Cosine similarity threshold to flag duplicate columns.

        Returns:
            Tuple of (intra_table_uniqueness [0.0, 1.0], list of DetectedCloneRecord).
        """
        schema_a_name = source_a.name.strip().lower()
        schema_b_name = source_b.name.strip().lower()

        embedder = SentenceTransformerEmbedder.get_instance()
        detected_clones: list[DetectedCloneRecord] = []
        table_uniqueness_scores: list[float] = []

        for res in target_schema.resources:
            fields = res.schema_info.fields
            if len(fields) < 2:
                table_uniqueness_scores.append(1.0)
                continue

            table_penalty = 0.0

            for i in range(len(fields)):
                for j in range(i + 1, len(fields)):
                    fld_i = fields[i]
                    fld_j = fields[j]

                    if not cls._are_types_compatible(fld_i.type, fld_j.type):
                        continue

                    # Provenance Guardrail (Tier 1)
                    prov_i = fld_i.source_provenance or []
                    prov_j = fld_j.source_provenance or []

                    origins_i: set[tuple[str, str]] = set()
                    for p in prov_i:
                        pref, tbl, _ = cls._normalize_col_ref(p)
                        if tbl:
                            src_tag = "b" if pref in ["source_b", "b", schema_b_name] else "a"
                            origins_i.add((src_tag, tbl))

                    origins_j: set[tuple[str, str]] = set()
                    for p in prov_j:
                        pref, tbl, _ = cls._normalize_col_ref(p)
                        if tbl:
                            src_tag = "b" if pref in ["source_b", "b", schema_b_name] else "a"
                            origins_j.add((src_tag, tbl))

                    # If both fields originate strictly from the same single source table without cross-source mapping
                    if (
                        len(origins_i) == 1
                        and len(origins_j) == 1
                        and origins_i == origins_j
                    ):
                        # Guardrail: intra-source sibling attributes are not semantic clones
                        continue

                    # Semantic Embedding Similarity (Tier 2)
                    text_i = f"{fld_i.name}: {fld_i.description or ''}"
                    text_j = f"{fld_j.name}: {fld_j.description or ''}"

                    sim = embedder.compute_cosine_similarity(text_i, text_j)

                    if sim >= clone_threshold:
                        detected_clones.append(
                            DetectedCloneRecord(
                                target_table=res.name,
                                column_a=fld_i.name,
                                column_b=fld_j.name,
                                source_prov_a=prov_i,
                                source_prov_b=prov_j,
                                data_type=fld_i.type,
                                similarity_score=round(sim, 4),
                                description_a=fld_i.description,
                                description_b=fld_j.description,
                            )
                        )
                        table_penalty += sim - clone_threshold

            m_unique_t = max(0.0, 1.0 - table_penalty)
            table_uniqueness_scores.append(m_unique_t)

        intra_table_uniqueness = (
            (sum(table_uniqueness_scores) / len(table_uniqueness_scores))
            if table_uniqueness_scores
            else 1.0
        )

        return (
            round(max(0.0, min(1.0, intra_table_uniqueness)), 4),
            detected_clones,
        )

    @classmethod
    def compute_flakiness(
        cls,
        iterations: list[AlignmentIterationMetrics],
    ) -> dict[str, Any]:
        """Analyze stability and consistency across benchmark iterations.

        Args:
            iterations: List of evaluated iteration metrics.

        Returns:
            Dictionary with stability statistics.
        """
        if not iterations:
            return {
                "total_distinct_clones": 0,
                "stable_clones_count": 0,
                "stability_ratio": 1.0,
            }

        total_runs = len(iterations)
        clone_counts: dict[tuple[str, str, str], int] = {}

        for it in iterations:
            for rec in it.detected_clones:
                key = (rec.target_table, rec.column_a, rec.column_b)
                clone_counts[key] = clone_counts.get(key, 0) + 1

        stable_clones = [c for c, count in clone_counts.items() if count == total_runs]
        total_distinct = len(clone_counts)
        stability_ratio = (
            (len(stable_clones) / total_distinct) if total_distinct > 0 else 1.0
        )

        return {
            "total_distinct_clones": total_distinct,
            "stable_clones_count": len(stable_clones),
            "stability_ratio": round(stability_ratio, 4),
        }

    @classmethod
    def extract_coaligned_pairs(
        cls,
        target_schema: DataPackage,
        source_a: DataPackage,
        source_b: DataPackage,
    ) -> dict[tuple[str, str], str]:
        """Extract cross-source attribute pairs mapped to the same target field.

        Args:
            target_schema: Unified target schema DataPackage.
            source_a: Source A DataPackage.
            source_b: Source B DataPackage.

        Returns:
            Dictionary mapping (qual_col_a, qual_col_b) to qualified target field.
        """
        cols_a = cls._extract_source_columns(source_a)
        cols_b = cls._extract_source_columns(source_b)
        schema_a_name = source_a.name.strip().lower()
        schema_b_name = source_b.name.strip().lower()

        coaligned: dict[tuple[str, str], str] = {}

        for res in target_schema.resources:
            t_name = res.name.strip()
            for field in res.schema_info.fields:
                target_field_qual = f"{t_name}.{field.name.strip()}"
                matched_a: set[str] = set()
                matched_b: set[str] = set()

                for prov in field.source_provenance or []:
                    prefix, tbl, col = cls._normalize_col_ref(prov)
                    if not tbl or not col:
                        continue
                    if (tbl, col) in cols_a and prefix in [
                        None,
                        "source_a",
                        "a",
                        schema_a_name,
                    ]:
                        matched_a.add(f"{tbl}.{col}")
                    if (tbl, col) in cols_b and prefix in [
                        None,
                        "source_b",
                        "b",
                        schema_b_name,
                    ]:
                        matched_b.add(f"{tbl}.{col}")

                for a_col in matched_a:
                    for b_col in matched_b:
                        coaligned[(a_col, b_col)] = target_field_qual

        return coaligned

    @classmethod
    def compute_topological_drift(
        cls,
        iterations: list[AlignmentIterationMetrics],
    ) -> TopologicalDriftStats:
        """Analyze relational partitioning and foreign key graph stability.

        Args:
            iterations: List of evaluated iteration metrics.

        Returns:
            TopologicalDriftStats with table count variance and FK edge stability.
        """
        if not iterations:
            return TopologicalDriftStats()

        table_counts: list[int] = []
        fk_counts: list[int] = []
        fk_edge_sets: list[set[tuple[str, str, str, str]]] = []

        for it in iterations:
            pkg = None
            if it.alignment_report and it.alignment_report.target_schema:
                pkg = it.alignment_report.target_schema

            if pkg is None:
                continue

            table_counts.append(len(pkg.resources))
            edge_set: set[tuple[str, str, str, str]] = set()
            total_fks = 0
            for res in pkg.resources:
                local_tbl = res.name.strip().lower()
                for fk in res.schema_info.foreignKeys:
                    total_fks += 1
                    ref_tbl = fk.reference.resource.strip().lower()
                    fk_fields = (
                        [fk.fields] if isinstance(fk.fields, str) else fk.fields
                    )
                    ref_fields = (
                        [fk.reference.fields]
                        if isinstance(fk.reference.fields, str)
                        else fk.reference.fields
                    )
                    for lf, rf in zip(fk_fields, ref_fields):
                        edge_set.add(
                            (
                                local_tbl,
                                str(lf).strip().lower(),
                                ref_tbl,
                                str(rf).strip().lower(),
                            )
                        )
            fk_counts.append(total_fks)
            fk_edge_sets.append(edge_set)

        if not table_counts:
            return TopologicalDriftStats()

        mean_tables = sum(table_counts) / len(table_counts)
        variance_tables = sum(
            (x - mean_tables) ** 2 for x in table_counts
        ) / len(table_counts)
        std_tables = variance_tables ** 0.5

        # Pairwise FK edge Jaccard similarity across iterations
        pairwise_jaccards: list[float] = []
        for i in range(len(fk_edge_sets)):
            for j in range(i + 1, len(fk_edge_sets)):
                s1, s2 = fk_edge_sets[i], fk_edge_sets[j]
                if not s1 and not s2:
                    pairwise_jaccards.append(1.0)
                else:
                    union_len = len(s1 | s2)
                    jaccard = (len(s1 & s2) / union_len) if union_len > 0 else 1.0
                    pairwise_jaccards.append(jaccard)

        mean_jaccard = (
            sum(pairwise_jaccards) / len(pairwise_jaccards)
            if pairwise_jaccards
            else 1.0
        )

        return TopologicalDriftStats(
            table_counts=table_counts,
            mean_table_count=round(mean_tables, 2),
            std_table_count=round(std_tables, 4),
            fk_counts=fk_counts,
            fk_edge_stability=round(mean_jaccard, 4),
        )

    @classmethod
    def compute_multi_iteration_consistency(
        cls,
        iterations: list[AlignmentIterationMetrics],
        source_a: DataPackage,
        source_b: DataPackage,
    ) -> MultiIterationConsistencyReport:
        """Compute multi-iteration consistency, consensus, and drift analysis.

        Args:
            iterations: List of evaluated iteration metrics.
            source_a: Source A DataPackage.
            source_b: Source B DataPackage.

        Returns:
            MultiIterationConsistencyReport with consensus pairs and topological drift.
        """
        if not iterations:
            return MultiIterationConsistencyReport()

        valid_iterations = [
            it
            for it in iterations
            if not it.error_message and it.alignment_report
        ]
        total_runs = len(valid_iterations)
        if total_runs == 0:
            return MultiIterationConsistencyReport()

        clone_flakiness = cls.compute_flakiness(valid_iterations)
        topological_drift = cls.compute_topological_drift(valid_iterations)

        # Track co-aligned pairs across runs
        pair_runs: dict[tuple[str, str], int] = defaultdict(int)
        pair_field_names: dict[tuple[str, str], set[str]] = defaultdict(set)

        for it in valid_iterations:
            if not it.alignment_report:
                continue
            pkg = it.alignment_report.target_schema
            coaligned = cls.extract_coaligned_pairs(pkg, source_a, source_b)
            for (col_a, col_b), target_field in coaligned.items():
                pair_runs[(col_a, col_b)] += 1
                pair_field_names[(col_a, col_b)].add(target_field)

        consensus_pairs: list[AttributeConsensusPair] = []
        stable_count = 0
        volatile_count = 0

        for (col_a, col_b), runs in sorted(
            pair_runs.items(), key=lambda x: (x[0][0], x[0][1])
        ):
            agreement_rate = runs / total_runs
            is_stable = runs == total_runs
            if is_stable:
                stable_count += 1
                status = "STABLE"
            else:
                volatile_count += 1
                status = "VOLATILE"

            consensus_pairs.append(
                AttributeConsensusPair(
                    source_col_a=col_a,
                    source_col_b=col_b,
                    coaligned_runs=runs,
                    total_runs=total_runs,
                    agreement_rate=round(agreement_rate, 4),
                    status=status,
                    target_field_names=sorted(pair_field_names[(col_a, col_b)]),
                )
            )

        total_pairs = len(consensus_pairs)
        overall_ratio = (stable_count / total_pairs) if total_pairs > 0 else 1.0

        return MultiIterationConsistencyReport(
            consensus_pairs=consensus_pairs,
            overall_consensus_ratio=round(overall_ratio, 4),
            stable_pairs_count=stable_count,
            volatile_pairs_count=volatile_count,
            topological_drift=topological_drift,
            clone_flakiness=clone_flakiness,
        )

    @classmethod
    def evaluate_alignment(
        cls,
        target_schema: DataPackage | AlignmentReport,
        source_a: DataPackage,
        source_b: DataPackage,
        execution_meta: ExecutionMetadata | None = None,
        iteration_index: int = 1,
        clone_threshold: float = 0.85,
    ) -> AlignmentIterationMetrics:
        """Execute full reference-free evaluation suite on a schema alignment result.

        Args:
            target_schema: Target DataPackage or AlignmentReport.
            source_a: Source A DataPackage.
            source_b: Source B DataPackage.
            execution_meta: Optional agent telemetry metadata.
            iteration_index: 1-based iteration counter.
            clone_threshold: Cosine similarity threshold for clone detection.

        Returns:
            AlignmentIterationMetrics with comprehensive reference-free evaluation scores.
        """
        if isinstance(target_schema, AlignmentReport):
            report = target_schema
            pkg = target_schema.target_schema
        else:
            report = None
            pkg = target_schema

        completeness, unmapped = cls.compute_completeness(pkg, source_a, source_b)
        structural_stats = cls.compute_structural_integrity(
            pkg, source_a=source_a, source_b=source_b
        )
        (
            intra_table_uniqueness,
            detected_clones,
        ) = cls.compute_reference_free_minimality(
            pkg, source_a, source_b, clone_threshold=clone_threshold
        )

        latency = (
            execution_meta.execution_time_seconds if execution_meta else 0.0
        )
        token_usage = (
            TokenUsage(
                prompt_tokens=execution_meta.prompt_tokens,
                completion_tokens=execution_meta.completion_tokens,
                total_tokens=execution_meta.total_tokens,
                latency_seconds=latency,
                cost_usd=execution_meta.cost_usd,
            )
            if execution_meta
            else TokenUsage()
        )

        return AlignmentIterationMetrics(
            iteration_index=iteration_index,
            completeness=completeness,
            structural_integrity=structural_stats.score,
            intra_table_uniqueness=intra_table_uniqueness,
            unmapped_source_columns=unmapped,
            broken_fks=structural_stats.broken_fks,
            unpreserved_source_fks=structural_stats.unpreserved_source_fks,
            detected_clones=detected_clones,
            structural_stats=structural_stats,
            latency_seconds=round(latency, 3),
            token_usage=token_usage,
            alignment_report=report,
        )

