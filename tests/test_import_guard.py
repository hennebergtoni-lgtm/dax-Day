from daxlab.import_guard import (
    ArtifactImportSpec,
    ArtifactObservation,
    ImportReconciliation,
    deterministic_source_row_id,
    validate_postimport,
    validate_preimport,
)


SPEC = ArtifactImportSpec(
    experiment_key="V112_REFERENCE_V1",
    expected_sha256="abc",
    expected_rows=243,
    dataset_sha256="dataset",
    engine_sha256="engine",
    schema_version="v1",
)


def test_preimport_accepts_exact_artifact_contract() -> None:
    observation = ArtifactObservation(
        sha256="abc",
        rows=243,
        dataset_sha256="dataset",
        engine_sha256="engine",
        schema_version="v1",
    )
    assert validate_preimport(SPEC, observation) == ()


def test_preimport_blocks_all_material_drift() -> None:
    observation = ArtifactObservation(
        sha256="wrong",
        rows=242,
        dataset_sha256="wrong-dataset",
        engine_sha256="wrong-engine",
        schema_version="v2",
    )
    assert validate_preimport(SPEC, observation) == (
        "ARTIFACT_HASH_MISMATCH",
        "ROW_COUNT_MISMATCH",
        "DATASET_FINGERPRINT_MISMATCH",
        "ENGINE_FINGERPRINT_MISMATCH",
        "SCHEMA_VERSION_MISMATCH",
    )


def test_postimport_requires_exact_reconciliation() -> None:
    assert validate_postimport(
        ImportReconciliation(
            source_rows=10, inserted_rows=7, unchanged_rows=3, conflicting_rows=0
        )
    ) == ()
    assert validate_postimport(
        ImportReconciliation(
            source_rows=10, inserted_rows=7, unchanged_rows=2, conflicting_rows=1
        )
    ) == ("CONFLICTING_ROWS", "SOURCE_ROW_RECONCILIATION_MISMATCH")


def test_source_row_identity_is_deterministic_and_sensitive() -> None:
    first = deterministic_source_row_id("V112_REFERENCE_V1", 1, "normal", "variant-a")
    second = deterministic_source_row_id("V112_REFERENCE_V1", 1, "normal", "variant-a")
    changed = deterministic_source_row_id("V112_REFERENCE_V1", 2, "normal", "variant-a")
    assert first == second
    assert first != changed
