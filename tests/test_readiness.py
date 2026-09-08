from daxlab.data.recovery import RecoveryIdentity
from daxlab.runtime.readiness import (
    ReadinessSnapshot,
    RunKind,
    evaluate_run_readiness,
)


def ready_snapshot(**overrides: object) -> ReadinessSnapshot:
    values: dict[str, object] = {
        "ci_green": True,
        "dataset_verified": True,
        "engine_verified": True,
        "database_verified": True,
        "technical_replay_verified": True,
        "audited_bundle_available": True,
        "full_reference_replay_verified": True,
        "execution_boundary_verified": True,
        "dataset_identity": RecoveryIdentity.HASH_VERIFIED,
    }
    values.update(overrides)
    return ReadinessSnapshot(**values)  # type: ignore[arg-type]


def test_fixture_smoke_does_not_require_clean_reference_identity() -> None:
    result = evaluate_run_readiness(
        RunKind.FIXTURE_REPLAY_SMOKE,
        ready_snapshot(
            dataset_verified=False,
            audited_bundle_available=False,
            full_reference_replay_verified=False,
            dataset_identity=RecoveryIdentity.STRUCTURAL_MATCH,
        ),
    )
    assert result.allowed
    assert result.blockers == ()


def test_structural_match_blocks_clean_reference_replay() -> None:
    result = evaluate_run_readiness(
        RunKind.CLEAN_REFERENCE_REPLAY,
        ready_snapshot(dataset_identity=RecoveryIdentity.STRUCTURAL_MATCH),
    )
    assert not result.allowed
    assert "DATASET_IDENTITY_NOT_HASH_VERIFIED" in result.blockers


def test_clean_reference_replay_does_not_require_its_own_future_result() -> None:
    result = evaluate_run_readiness(
        RunKind.CLEAN_REFERENCE_REPLAY,
        ready_snapshot(full_reference_replay_verified=False),
    )
    assert result.allowed
    assert "FULL_REFERENCE_REPLAY_UNVERIFIED" not in result.blockers


def test_hash_verified_allows_clean_reference_replay_when_other_gates_pass() -> None:
    result = evaluate_run_readiness(RunKind.CLEAN_REFERENCE_REPLAY, ready_snapshot())
    assert result.allowed
    assert result.blockers == ()


def test_paper_requires_full_reference_replay() -> None:
    result = evaluate_run_readiness(
        RunKind.PAPER,
        ready_snapshot(full_reference_replay_verified=False),
    )
    assert not result.allowed
    assert "FULL_REFERENCE_REPLAY_UNVERIFIED" in result.blockers


def test_paper_still_requires_execution_boundary() -> None:
    result = evaluate_run_readiness(
        RunKind.PAPER,
        ready_snapshot(execution_boundary_verified=False),
    )
    assert not result.allowed
    assert "EXECUTION_BOUNDARY_UNVERIFIED" in result.blockers
