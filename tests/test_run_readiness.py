from daxlab.data.recovery import RecoveryIdentity
from daxlab.runtime.readiness import (
    ReadinessSnapshot,
    RunKind,
    evaluate_run_readiness,
)


def current_snapshot() -> ReadinessSnapshot:
    return ReadinessSnapshot(
        ci_green=True,
        dataset_verified=True,
        engine_verified=True,
        database_verified=True,
        technical_replay_verified=True,
        audited_bundle_available=False,
        full_reference_replay_verified=False,
        execution_boundary_verified=False,
        dataset_identity=RecoveryIdentity.HASH_VERIFIED,
    )


def test_current_fixture_smoke_is_allowed() -> None:
    result = evaluate_run_readiness(RunKind.FIXTURE_REPLAY_SMOKE, current_snapshot())
    assert result.allowed
    assert result.blockers == ()


def test_current_clean_reference_replay_is_allowed() -> None:
    result = evaluate_run_readiness(RunKind.CLEAN_REFERENCE_REPLAY, current_snapshot())
    assert result.allowed
    assert result.blockers == ()


def test_paper_requires_all_reference_and_execution_gates() -> None:
    result = evaluate_run_readiness(RunKind.PAPER, current_snapshot())
    assert not result.allowed
    assert "AUDITED_BUNDLE_UNAVAILABLE" in result.blockers
    assert "FULL_REFERENCE_REPLAY_UNVERIFIED" in result.blockers
    assert "EXECUTION_BOUNDARY_UNVERIFIED" in result.blockers
