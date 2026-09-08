from daxlab.data.recovery import RecoveryIdentity
from daxlab.runtime.health import (
    HealthState,
    build_system_health,
    recovery_identity_health,
)


def test_system_health_green_allows_trading() -> None:
    health = build_system_health(
        data=HealthState.GREEN,
        reference=HealthState.GREEN,
        replay=HealthState.GREEN,
        database=HealthState.GREEN,
        execution=HealthState.GREEN,
    )
    assert health.overall is HealthState.GREEN
    assert health.trading_allowed


def test_system_health_yellow_is_not_trade_ready() -> None:
    health = build_system_health(
        data=HealthState.GREEN,
        reference=HealthState.GREEN,
        replay=HealthState.YELLOW,
        database=HealthState.GREEN,
        execution=HealthState.GREEN,
    )
    assert health.overall is HealthState.YELLOW
    assert not health.trading_allowed


def test_blocker_forces_red_health() -> None:
    health = build_system_health(
        data=HealthState.GREEN,
        reference=HealthState.GREEN,
        replay=HealthState.GREEN,
        database=HealthState.GREEN,
        execution=HealthState.GREEN,
        blockers=("AUDITED_DATA_SOURCE_MISSING",),
    )
    assert health.overall is HealthState.RED
    assert not health.trading_allowed


def test_recovery_structural_match_is_yellow() -> None:
    assert (
        recovery_identity_health(RecoveryIdentity.STRUCTURAL_MATCH)
        is HealthState.YELLOW
    )


def test_recovery_hash_verified_is_green() -> None:
    assert recovery_identity_health(RecoveryIdentity.HASH_VERIFIED) is HealthState.GREEN


def test_recovery_mismatch_is_red() -> None:
    assert recovery_identity_health(RecoveryIdentity.MISMATCH) is HealthState.RED
