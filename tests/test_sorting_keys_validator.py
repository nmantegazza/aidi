import pytest

from entity_resolution.models import (
    ColumnMatchConfig,
    ERPipelineConfiguration,
    SimilarityAlgorithm,
)


def test_er_pipeline_config_valid_sorting_keys():
    """Valid list of sorting keys is preserved cleanly."""
    config = ERPipelineConfiguration(
        sorting_keys=["email", "full_name", "phone"],
        window_size=5,
        matching_columns={
            "full_name": ColumnMatchConfig(
                algorithm=SimilarityAlgorithm.JAROWINKLER, weight=1.0
            ),
            "email": ColumnMatchConfig(
                algorithm=SimilarityAlgorithm.DAMERAU_LEVENSHTEIN, weight=1.0
            ),
            "phone": ColumnMatchConfig(
                algorithm=SimilarityAlgorithm.DAMERAU_LEVENSHTEIN, weight=0.8
            ),
        },
        reasoning="Multi-pass SN over email, full_name, and phone.",
    )
    assert config.sorting_keys == ["email", "full_name", "phone"]
    assert config.all_sorting_keys == ["email", "full_name", "phone"]
    assert config.sorting_key == "email"
    assert config.backup_sorting_key == "full_name"


def test_er_pipeline_config_single_sorting_key():
    """Single sorting key list is supported."""
    config = ERPipelineConfiguration(
        sorting_keys=["name"],
        window_size=5,
        matching_columns={
            "name": ColumnMatchConfig(
                algorithm=SimilarityAlgorithm.JAROWINKLER, weight=1.0
            ),
        },
        reasoning="Single pass SN over name.",
    )
    assert config.sorting_keys == ["name"]
    assert config.all_sorting_keys == ["name"]
    assert config.sorting_key == "name"
    assert config.backup_sorting_key is None


def test_er_pipeline_config_trims_whitespace_and_rejects_empty():
    """Empty or whitespace-only keys in sorting_keys list are cleaned/rejected."""
    config = ERPipelineConfiguration(
        sorting_keys=[" email ", "  "],
        window_size=5,
        matching_columns={
            "email": ColumnMatchConfig(
                algorithm=SimilarityAlgorithm.DAMERAU_LEVENSHTEIN, weight=1.0
            ),
        },
        reasoning="SN over email.",
    )
    assert config.sorting_keys == ["email"]

    with pytest.raises(ValueError, match="sorting_keys cannot be empty"):
        ERPipelineConfiguration(
            sorting_keys=[],
            window_size=5,
            matching_columns={
                "email": ColumnMatchConfig(
                    algorithm=SimilarityAlgorithm.DAMERAU_LEVENSHTEIN, weight=1.0
                ),
            },
            reasoning="Empty keys list",
        )

