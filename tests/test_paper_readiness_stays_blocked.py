from daxlab.data.recovery import RecoveryIdentity
from daxlab.runtime.readiness import ReadinessSnapshot, RunKind, evaluate_run_readiness


def test_paper_stays_blocked_even_with_new_simulation_contracts() -> None:
    snapshot = ReadinessSnapshot(
        ci_green=True,
        dataset_verified=True,
        engine_verified=True,
        database_verified=True,
        technical_replay_verified=True,
        audited_bundle_available=True,
        full_reference_replay_verified=False,
        execution_boundary_verified=True,
        mt5_readonly_health_verified=False,
        dataset_identity=RecoveryIdentity.HASH_VERIFIED,
    )
    result = evaluate_run_readiness(RunKind.PAPER, snapshot)
    assert not result.allowed
    assert "FULL_REFERENCE_REPLAY_UNVERIFIED" in result.blockers
    assert "MT5_READONLY_HEALTH_UNVERIFIED" in result.blockers
