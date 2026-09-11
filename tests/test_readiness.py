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
        "broker_order_lifecycle_verified": True,
        "broker_reconciliation_verified": True,
        "execution_protection_gates_verified": True,
        "mt5_readonly_health_verified": True,
        "dataset_identity": RecoveryIdentity.HASH_VERIFIED,
        "broker_economics_verified": True,
        "broker_risk_sizing_verified": True,
        "risk_profile_policy_verified": True,
        "loss_cap_policy_verified": True,
        "paper_user_authorized": True,
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
            execution_boundary_verified=False,
            broker_order_lifecycle_verified=False,
            broker_reconciliation_verified=False,
            execution_protection_gates_verified=False,
            broker_economics_verified=False,
            broker_risk_sizing_verified=False,
            risk_profile_policy_verified=False,
            loss_cap_policy_verified=False,
            paper_user_authorized=False,
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


def test_hash_verified_recovered_source_allows_clean_replay_without_original_zip() -> None:
    result = evaluate_run_readiness(
        RunKind.CLEAN_REFERENCE_REPLAY,
        ready_snapshot(audited_bundle_available=False),
    )
    assert result.allowed
    assert "AUDITED_BUNDLE_UNAVAILABLE" not in result.blockers


def test_paper_allows_only_when_all_readiness_evidence_and_user_gate_are_verified() -> None:
    result = evaluate_run_readiness(RunKind.PAPER, ready_snapshot())
    assert result.allowed
    assert result.blockers == ()


def test_paper_requires_explicit_user_stop_gate_even_when_all_technical_gates_pass() -> None:
    result = evaluate_run_readiness(
        RunKind.PAPER,
        ready_snapshot(paper_user_authorized=False),
    )
    assert not result.allowed
    assert result.blockers == ("PAPER_USER_AUTHORIZATION_REQUIRED",)


def test_paper_user_authorization_default_is_fail_closed() -> None:
    snapshot = ReadinessSnapshot(
        ci_green=True,
        dataset_verified=True,
        engine_verified=True,
        database_verified=True,
        technical_replay_verified=True,
        audited_bundle_available=True,
        full_reference_replay_verified=True,
        execution_boundary_verified=True,
        broker_order_lifecycle_verified=True,
        broker_reconciliation_verified=True,
        execution_protection_gates_verified=True,
        mt5_readonly_health_verified=True,
        dataset_identity=RecoveryIdentity.HASH_VERIFIED,
        broker_economics_verified=True,
        broker_risk_sizing_verified=True,
        risk_profile_policy_verified=True,
        loss_cap_policy_verified=True,
    )
    result = evaluate_run_readiness(RunKind.PAPER, snapshot)
    assert not result.allowed
    assert result.blockers == ("PAPER_USER_AUTHORIZATION_REQUIRED",)


def test_paper_still_requires_original_audited_bundle_provenance() -> None:
    result = evaluate_run_readiness(
        RunKind.PAPER,
        ready_snapshot(audited_bundle_available=False),
    )
    assert not result.allowed
    assert "AUDITED_BUNDLE_UNAVAILABLE" in result.blockers


def test_paper_requires_full_reference_replay() -> None:
    result = evaluate_run_readiness(
        RunKind.PAPER,
        ready_snapshot(full_reference_replay_verified=False),
    )
    assert not result.allowed
    assert "FULL_REFERENCE_REPLAY_UNVERIFIED" in result.blockers


def test_paper_still_requires_legacy_execution_boundary_evidence() -> None:
    result = evaluate_run_readiness(
        RunKind.PAPER,
        ready_snapshot(execution_boundary_verified=False),
    )
    assert not result.allowed
    assert "EXECUTION_BOUNDARY_UNVERIFIED" in result.blockers


def test_legacy_execution_boundary_true_is_not_sufficient_for_paper() -> None:
    result = evaluate_run_readiness(
        RunKind.PAPER,
        ready_snapshot(
            execution_boundary_verified=True,
            broker_order_lifecycle_verified=False,
            broker_reconciliation_verified=False,
            execution_protection_gates_verified=False,
        ),
    )
    assert not result.allowed
    assert result.blockers == (
        "BROKER_ORDER_LIFECYCLE_UNVERIFIED",
        "BROKER_RECONCILIATION_UNVERIFIED",
        "EXECUTION_PROTECTION_GATES_UNVERIFIED",
    )


def test_paper_requires_verified_broker_order_lifecycle() -> None:
    result = evaluate_run_readiness(
        RunKind.PAPER,
        ready_snapshot(broker_order_lifecycle_verified=False),
    )
    assert not result.allowed
    assert result.blockers == ("BROKER_ORDER_LIFECYCLE_UNVERIFIED",)


def test_paper_requires_verified_broker_reconciliation() -> None:
    result = evaluate_run_readiness(
        RunKind.PAPER,
        ready_snapshot(broker_reconciliation_verified=False),
    )
    assert not result.allowed
    assert result.blockers == ("BROKER_RECONCILIATION_UNVERIFIED",)


def test_paper_requires_verified_execution_protection_gates() -> None:
    result = evaluate_run_readiness(
        RunKind.PAPER,
        ready_snapshot(execution_protection_gates_verified=False),
    )
    assert not result.allowed
    assert result.blockers == ("EXECUTION_PROTECTION_GATES_UNVERIFIED",)


def test_paper_requires_verified_mt5_readonly_health() -> None:
    result = evaluate_run_readiness(
        RunKind.PAPER,
        ready_snapshot(mt5_readonly_health_verified=False),
    )
    assert not result.allowed
    assert "MT5_READONLY_HEALTH_UNVERIFIED" in result.blockers


def test_paper_requires_verified_broker_economics() -> None:
    result = evaluate_run_readiness(
        RunKind.PAPER,
        ready_snapshot(broker_economics_verified=False),
    )
    assert not result.allowed
    assert "BROKER_ECONOMICS_UNVERIFIED" in result.blockers


def test_paper_requires_verified_broker_risk_sizing() -> None:
    result = evaluate_run_readiness(
        RunKind.PAPER,
        ready_snapshot(broker_risk_sizing_verified=False),
    )
    assert not result.allowed
    assert "BROKER_RISK_SIZING_UNVERIFIED" in result.blockers


def test_paper_requires_verified_risk_profile_policy() -> None:
    result = evaluate_run_readiness(
        RunKind.PAPER,
        ready_snapshot(risk_profile_policy_verified=False),
    )
    assert not result.allowed
    assert "RISK_PROFILE_POLICY_UNVERIFIED" in result.blockers


def test_paper_requires_verified_loss_cap_policy() -> None:
    result = evaluate_run_readiness(
        RunKind.PAPER,
        ready_snapshot(loss_cap_policy_verified=False),
    )
    assert not result.allowed
    assert "LOSS_CAP_POLICY_UNVERIFIED" in result.blockers


def test_clean_reference_replay_does_not_depend_on_paper_execution_risk_or_user_evidence() -> None:
    result = evaluate_run_readiness(
        RunKind.CLEAN_REFERENCE_REPLAY,
        ready_snapshot(
            execution_boundary_verified=False,
            broker_order_lifecycle_verified=False,
            broker_reconciliation_verified=False,
            execution_protection_gates_verified=False,
            broker_economics_verified=False,
            broker_risk_sizing_verified=False,
            risk_profile_policy_verified=False,
            loss_cap_policy_verified=False,
            paper_user_authorized=False,
        ),
    )
    assert result.allowed
    assert result.blockers == ()
