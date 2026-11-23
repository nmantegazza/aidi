"""Unit tests for reference-free schema alignment evaluation metrics."""

from __future__ import annotations

import pytest

from schema_integration.alignment.models import AlignmentReport
from schema_integration.benchmarking.alignment.evaluation import (
    AlignmentEvaluator,
)
from schema_integration.benchmarking.alignment.models import (
    AlignmentIterationMetrics,
)
from schema_integration.benchmarking.alignment.similarity import (
    SentenceTransformerEmbedder,
)
from shared.schema_models import (
    DataPackage,
    ForeignKey,
    ForeignKeyReference,
    TableField,
    TableResource,
    TableSchema,
)


@pytest.fixture
def source_schemas() -> tuple[DataPackage, DataPackage]:
    """Create fixture source schemas A and B."""
    src_a = DataPackage(
        schema_name="source_a",
        resources=[
            TableResource(
                name="patients",
                schema=TableSchema(
                    primaryKey="id",
                    fields=[
                        TableField(name="id", type="integer"),
                        TableField(name="gender", type="string"),
                        TableField(name="birthdate", type="date"),
                    ],
                ),
            ),
            TableResource(
                name="encounters",
                schema=TableSchema(
                    primaryKey="enc_id",
                    fields=[
                        TableField(name="enc_id", type="integer"),
                        TableField(name="patient_id", type="integer"),
                    ],
                    foreignKeys=[
                        ForeignKey(
                            fields="patient_id",
                            reference=ForeignKeyReference(
                                resource="patients",
                                fields="id",
                            ),
                        )
                    ],
                ),
            ),
        ],
    )

    src_b = DataPackage(
        schema_name="source_b",
        resources=[
            TableResource(
                name="person",
                schema=TableSchema(
                    primaryKey="person_id",
                    fields=[
                        TableField(name="person_id", type="integer"),
                        TableField(name="gender_concept_id", type="integer"),
                        TableField(name="year_of_birth", type="integer"),
                    ],
                ),
            ),
            TableResource(
                name="visit_occurrence",
                schema=TableSchema(
                    primaryKey="visit_id",
                    fields=[
                        TableField(name="visit_id", type="integer"),
                        TableField(name="person_id", type="integer"),
                    ],
                ),
            ),
        ],
    )
    return src_a, src_b


def test_completeness_full_coverage(
    source_schemas: tuple[DataPackage, DataPackage],
) -> None:
    """Test completeness calculation when all source columns are retained."""
    src_a, src_b = source_schemas

    target = DataPackage(
        schema_name="target",
        resources=[
            TableResource(
                name="unified_person",
                schema=TableSchema(
                    primaryKey="person_id",
                    fields=[
                        TableField(
                            name="person_id",
                            source_provenance=[
                                "source_a.patients.id",
                                "source_b.person.person_id",
                            ],
                        ),
                        TableField(
                            name="gender",
                            source_provenance=[
                                "source_a.patients.gender",
                                "source_b.person.gender_concept_id",
                            ],
                        ),
                        TableField(
                            name="birth_year",
                            source_provenance=[
                                "source_a.patients.birthdate",
                                "source_b.person.year_of_birth",
                            ],
                        ),
                    ],
                ),
            ),
            TableResource(
                name="unified_visit",
                schema=TableSchema(
                    primaryKey="visit_id",
                    fields=[
                        TableField(
                            name="visit_id",
                            source_provenance=[
                                "source_a.encounters.enc_id",
                                "source_b.visit_occurrence.visit_id",
                            ],
                        ),
                        TableField(
                            name="person_id",
                            source_provenance=[
                                "source_a.encounters.patient_id",
                                "source_b.visit_occurrence.person_id",
                            ],
                        ),
                    ],
                ),
            ),
        ],
    )

    c, unmapped = AlignmentEvaluator.compute_completeness(target, src_a, src_b)
    assert c == 1.0
    assert len(unmapped) == 0


def test_completeness_partial_coverage(
    source_schemas: tuple[DataPackage, DataPackage],
) -> None:
    """Test completeness with dropped columns."""
    src_a, src_b = source_schemas

    # 10 total source columns (5 in A, 5 in B). Target references only 3.
    target = DataPackage(
        schema_name="target",
        resources=[
            TableResource(
                name="unified_person",
                schema=TableSchema(
                    primaryKey="person_id",
                    fields=[
                        TableField(
                            name="person_id",
                            source_provenance=[
                                "source_a.patients.id",
                                "source_b.person.person_id",
                            ],
                        ),
                        TableField(
                            name="gender",
                            source_provenance=["source_a.patients.gender"],
                        ),
                    ],
                ),
            )
        ],
    )

    c, unmapped = AlignmentEvaluator.compute_completeness(target, src_a, src_b)
    assert c == 0.3  # 3 / 10
    assert len(unmapped) == 7


def test_structural_integrity() -> None:
    """Test structural integrity scoring across valid, invalid, and relational preservation topologies."""
    # Valid schema with PKs and valid FK
    valid_schema = DataPackage(
        schema_name="valid",
        resources=[
            TableResource(
                name="parent",
                schema=TableSchema(
                    primaryKey="id",
                    fields=[TableField(name="id", type="integer")],
                ),
            ),
            TableResource(
                name="child",
                schema=TableSchema(
                    primaryKey="c_id",
                    fields=[
                        TableField(name="c_id", type="integer"),
                        TableField(name="p_id", type="integer"),
                    ],
                    foreignKeys=[
                        ForeignKey(
                            fields="p_id",
                            reference=ForeignKeyReference(
                                resource="parent",
                                fields="id",
                            ),
                        )
                    ],
                ),
            ),
        ],
    )
    res_valid = AlignmentEvaluator.compute_structural_integrity(valid_schema)
    assert res_valid.pk_validity == 1.0
    assert res_valid.fk_validity == 1.0
    assert res_valid.source_fk_preservation == 1.0
    assert res_valid.score == 1.0
    assert len(res_valid.broken_fks) == 0

    # Broken FK to non-existent resource
    broken_schema = DataPackage(
        schema_name="broken",
        resources=[
            TableResource(
                name="child",
                schema=TableSchema(
                    primaryKey="c_id",
                    fields=[TableField(name="c_id", type="integer")],
                    foreignKeys=[
                        ForeignKey(
                            fields="p_id",
                            reference=ForeignKeyReference(
                                resource="non_existent_parent",
                                fields="id",
                            ),
                        )
                    ],
                ),
            )
        ],
    )
    res_broken = AlignmentEvaluator.compute_structural_integrity(broken_schema)
    assert res_broken.pk_validity == 1.0
    assert res_broken.fk_validity == 0.0
    assert res_broken.score == 0.0
    assert len(res_broken.broken_fks) == 1

    # Missing primary key declaration
    missing_pk_schema = DataPackage(
        schema_name="missing_pk",
        resources=[
            TableResource(
                name="child",
                schema=TableSchema(
                    fields=[TableField(name="c_id", type="integer")],
                ),
            )
        ],
    )
    res_no_pk = AlignmentEvaluator.compute_structural_integrity(missing_pk_schema)
    assert res_no_pk.pk_validity == 0.0
    assert res_no_pk.fk_validity == 1.0
    assert res_no_pk.score == 0.0


def test_structural_integrity_source_fk_preservation(
    source_schemas: tuple[DataPackage, DataPackage],
) -> None:
    """Test source foreign key preservation detection."""
    src_a, src_b = source_schemas

    # Target schema preserving encounters -> patients FK via unified tables
    target_preserved = DataPackage(
        schema_name="target",
        resources=[
            TableResource(
                name="person",
                schema=TableSchema(
                    primaryKey="person_id",
                    fields=[
                        TableField(
                            name="person_id",
                            source_provenance=[
                                "source_a.patients.id",
                                "source_b.person.person_id",
                            ],
                        )
                    ],
                ),
            ),
            TableResource(
                name="visit",
                schema=TableSchema(
                    primaryKey="visit_id",
                    fields=[
                        TableField(
                            name="visit_id",
                            source_provenance=[
                                "source_a.encounters.enc_id",
                                "source_b.visit_occurrence.visit_id",
                            ],
                        ),
                        TableField(
                            name="person_id",
                            source_provenance=[
                                "source_a.encounters.patient_id",
                                "source_b.visit_occurrence.person_id",
                            ],
                        ),
                    ],
                    foreignKeys=[
                        ForeignKey(
                            fields="person_id",
                            reference=ForeignKeyReference(
                                resource="person",
                                fields="person_id",
                            ),
                        )
                    ],
                ),
            ),
        ],
    )

    stats = AlignmentEvaluator.compute_structural_integrity(
        target_preserved, source_a=src_a, source_b=src_b
    )
    assert stats.total_source_fks == 1
    assert stats.preserved_source_fks == 1
    assert stats.source_fk_preservation == 1.0
    assert stats.score == 1.0
    assert len(stats.unpreserved_source_fks) == 0


def test_reference_free_minimality_and_guardrail(
    source_schemas: tuple[DataPackage, DataPackage],
) -> None:
    """Test intra-table uniqueness and provenance guardrail."""
    src_a, src_b = source_schemas

    # Target where sibling columns are not flagged as clones
    target = DataPackage(
        schema_name="target",
        resources=[
            TableResource(
                name="unified_person",
                schema=TableSchema(
                    primaryKey="person_id",
                    fields=[
                        TableField(
                            name="person_id",
                            type="integer",
                            source_provenance=[
                                "source_a.patients.id",
                                "source_b.person.person_id",
                            ],
                            description="Unique identifier",
                        ),
                        TableField(
                            name="gender",
                            type="string",
                            source_provenance=[
                                "source_a.patients.gender",
                                "source_b.person.gender_concept_id",
                            ],
                            description="Gender classification",
                        ),
                        TableField(
                            name="first_name",
                            type="string",
                            source_provenance=["source_a.patients.gender"],
                            description="First given name",
                        ),
                        TableField(
                            name="last_name",
                            type="string",
                            source_provenance=["source_a.patients.gender"],
                            description="Last family name",
                        ),
                    ],
                ),
            )
        ],
    )

    uniqueness, clones = (
        AlignmentEvaluator.compute_reference_free_minimality(
            target, src_a, src_b, clone_threshold=0.85
        )
    )

    # Sibling columns (first_name and last_name from source_a.patients) are protected by guardrail
    assert uniqueness == 1.0
    assert len(clones) == 0


def test_reference_free_minimality_semantic_clone_penalty(
    source_schemas: tuple[DataPackage, DataPackage],
) -> None:
    """Test intra-table semantic clone detection when duplicate synonym columns are kept."""
    src_a, src_b = source_schemas

    # Pathological schema keeping both 'client_name' and 'customer_name' in same table without fusing
    target = DataPackage(
        schema_name="target",
        resources=[
            TableResource(
                name="customers",
                schema=TableSchema(
                    primaryKey="id",
                    fields=[
                        TableField(
                            name="id",
                            type="integer",
                            source_provenance=["source_a.patients.id"],
                        ),
                        TableField(
                            name="patient_gender",
                            type="string",
                            source_provenance=["source_a.patients.gender"],
                            description="Gender of the patient",
                        ),
                        TableField(
                            name="person_gender",
                            type="string",
                            source_provenance=["source_b.person.gender_concept_id"],
                            description="Gender of the person",
                        ),
                    ],
                ),
            )
        ],
    )

    uniqueness, clones = (
        AlignmentEvaluator.compute_reference_free_minimality(
            target, src_a, src_b, clone_threshold=0.70
        )
    )

    assert len(clones) >= 1
    assert uniqueness < 1.0
    assert clones[0].target_table == "customers"
    assert {clones[0].column_a, clones[0].column_b} == {
        "patient_gender",
        "person_gender",
    }


def test_evaluate_alignment_end_to_end(
    source_schemas: tuple[DataPackage, DataPackage],
) -> None:
    """Test evaluate_alignment produces complete reference-free iteration metrics."""
    src_a, src_b = source_schemas
    target = DataPackage(
        schema_name="target",
        resources=[
            TableResource(
                name="person",
                schema=TableSchema(
                    primaryKey="person_id",
                    fields=[
                        TableField(
                            name="person_id",
                            type="integer",
                            source_provenance=[
                                "source_a.patients.id",
                                "source_b.person.person_id",
                            ],
                        ),
                        TableField(
                            name="gender",
                            type="string",
                            source_provenance=[
                                "source_a.patients.gender",
                                "source_b.person.gender_concept_id",
                            ],
                        ),
                    ],
                ),
            )
        ],
    )
    metrics = AlignmentEvaluator.evaluate_alignment(
        target_schema=target,
        source_a=src_a,
        source_b=src_b,
        iteration_index=1,
    )
    assert metrics.completeness > 0
    assert metrics.structural_integrity >= 0
    assert metrics.intra_table_uniqueness == 1.0
    assert len(metrics.detected_clones) == 0
    assert len(metrics.unmapped_source_columns) > 0


def test_embedder_cache_and_similarity() -> None:
    """Test SentenceTransformerEmbedder singleton and similarity behavior."""
    embedder = SentenceTransformerEmbedder.get_instance()
    sim_identical = embedder.compute_cosine_similarity(
        "patient_id: identifier", "patient_id: identifier"
    )
    assert sim_identical == 1.0

    sim_similar = embedder.compute_cosine_similarity(
        "patient_name: name of patient", "client_name: name of client"
    )
    assert sim_similar > 0.5


def test_extract_coaligned_pairs(
    source_schemas: tuple[DataPackage, DataPackage],
) -> None:
    """Test extracting cross-source co-aligned attribute pairs."""
    src_a, src_b = source_schemas

    target = DataPackage(
        schema_name="target",
        resources=[
            TableResource(
                name="patients_unified",
                schema=TableSchema(
                    primaryKey="id",
                    fields=[
                        TableField(
                            name="id",
                            type="integer",
                            source_provenance=[
                                "source_a.patients.id",
                                "source_b.person.person_id",
                            ],
                        ),
                        TableField(
                            name="birth_info",
                            type="string",
                            source_provenance=[
                                "source_a.patients.birthdate",
                                "source_b.person.year_of_birth",
                            ],
                        ),
                    ],
                ),
            )
        ],
    )

    coaligned = AlignmentEvaluator.extract_coaligned_pairs(
        target, src_a, src_b
    )
    assert ("patients.id", "person.person_id") in coaligned
    assert ("patients.birthdate", "person.year_of_birth") in coaligned
    assert (
        coaligned[("patients.id", "person.person_id")]
        == "patients_unified.id"
    )


def test_compute_multi_iteration_consistency_stable(
    source_schemas: tuple[DataPackage, DataPackage],
) -> None:
    """Test multi-iteration consistency when alignments are identical across runs."""
    src_a, src_b = source_schemas

    def make_report() -> AlignmentReport:
        pkg = DataPackage(
            schema_name="target",
            resources=[
                TableResource(
                    name="patients",
                    schema=TableSchema(
                        primaryKey="id",
                        fields=[
                            TableField(
                                name="id",
                                type="integer",
                                source_provenance=[
                                    "source_a.patients.id",
                                    "source_b.person.person_id",
                                ],
                            ),
                        ],
                    ),
                )
            ],
        )
        return AlignmentReport(target_schema=pkg, conflict_report=[])

    it1 = AlignmentEvaluator.evaluate_alignment(
        target_schema=make_report(),
        source_a=src_a,
        source_b=src_b,
        iteration_index=1,
    )
    it2 = AlignmentEvaluator.evaluate_alignment(
        target_schema=make_report(),
        source_a=src_a,
        source_b=src_b,
        iteration_index=2,
    )

    report = AlignmentEvaluator.compute_multi_iteration_consistency(
        [it1, it2], src_a, src_b
    )
    assert report.stable_pairs_count == 1
    assert report.volatile_pairs_count == 0
    assert report.overall_consensus_ratio == 1.0
    assert len(report.consensus_pairs) == 1
    assert report.consensus_pairs[0].status == "STABLE"
    assert report.consensus_pairs[0].agreement_rate == 1.0


def test_compute_multi_iteration_consistency_volatile(
    source_schemas: tuple[DataPackage, DataPackage],
) -> None:
    """Test multi-iteration consistency when alignments fluctuate across runs."""
    src_a, src_b = source_schemas

    # Run 1 merges id and birthdate
    pkg1 = DataPackage(
        schema_name="target",
        resources=[
            TableResource(
                name="patients",
                schema=TableSchema(
                    primaryKey="id",
                    fields=[
                        TableField(
                            name="id",
                            type="integer",
                            source_provenance=[
                                "source_a.patients.id",
                                "source_b.person.person_id",
                            ],
                        ),
                        TableField(
                            name="dob",
                            type="date",
                            source_provenance=[
                                "source_a.patients.birthdate",
                                "source_b.person.year_of_birth",
                            ],
                        ),
                    ],
                ),
            )
        ],
    )
    # Run 2 only merges id, drops birthdate co-alignment
    pkg2 = DataPackage(
        schema_name="target",
        resources=[
            TableResource(
                name="patients",
                schema=TableSchema(
                    primaryKey="id",
                    fields=[
                        TableField(
                            name="id",
                            type="integer",
                            source_provenance=[
                                "source_a.patients.id",
                                "source_b.person.person_id",
                            ],
                        ),
                        TableField(
                            name="bdate",
                            type="date",
                            source_provenance=["source_a.patients.birthdate"],
                        ),
                    ],
                ),
            )
        ],
    )

    it1 = AlignmentEvaluator.evaluate_alignment(
        target_schema=AlignmentReport(target_schema=pkg1, conflict_report=[]),
        source_a=src_a,
        source_b=src_b,
        iteration_index=1,
    )
    it2 = AlignmentEvaluator.evaluate_alignment(
        target_schema=AlignmentReport(target_schema=pkg2, conflict_report=[]),
        source_a=src_a,
        source_b=src_b,
        iteration_index=2,
    )

    report = AlignmentEvaluator.compute_multi_iteration_consistency(
        [it1, it2], src_a, src_b
    )
    assert report.stable_pairs_count == 1  # id is stable
    assert report.volatile_pairs_count == 1  # birthdate is volatile
    assert report.overall_consensus_ratio == 0.5
    vol_pair = next(
        p for p in report.consensus_pairs if p.status == "VOLATILE"
    )
    assert vol_pair.agreement_rate == 0.5
    assert vol_pair.coaligned_runs == 1


def test_compute_topological_drift() -> None:
    """Test topological drift computation across different schema partitions."""
    pkg1 = DataPackage(
        schema_name="target",
        resources=[
            TableResource(
                name="t1",
                schema=TableSchema(
                    primaryKey="id",
                    fields=[TableField(name="id", type="integer")],
                ),
            ),
            TableResource(
                name="t2",
                schema=TableSchema(
                    primaryKey="ref_id",
                    fields=[TableField(name="ref_id", type="integer")],
                    foreignKeys=[
                        ForeignKey(
                            fields="ref_id",
                            reference=ForeignKeyReference(
                                resource="t1", fields="id"
                            ),
                        )
                    ],
                ),
            ),
        ],
    )
    pkg2 = DataPackage(
        schema_name="target",
        resources=[
            TableResource(
                name="t1_single",
                schema=TableSchema(
                    primaryKey="id",
                    fields=[TableField(name="id", type="integer")],
                ),
            )
        ],
    )

    it1 = AlignmentIterationMetrics(
        iteration_index=1,
        completeness=1.0,
        structural_integrity=1.0,
        intra_table_uniqueness=1.0,
        structural_stats=AlignmentEvaluator.compute_structural_integrity(pkg1),
        alignment_report=AlignmentReport(target_schema=pkg1, conflict_report=[]),
    )
    it2 = AlignmentIterationMetrics(
        iteration_index=2,
        completeness=1.0,
        structural_integrity=1.0,
        intra_table_uniqueness=1.0,
        structural_stats=AlignmentEvaluator.compute_structural_integrity(pkg2),
        alignment_report=AlignmentReport(target_schema=pkg2, conflict_report=[]),
    )

    drift = AlignmentEvaluator.compute_topological_drift([it1, it2])
    assert drift.table_counts == [2, 1]
    assert drift.mean_table_count == 1.5
    assert drift.std_table_count > 0
    assert drift.fk_counts == [1, 0]
    assert drift.fk_edge_stability == 0.0
