from daxlab.runtime.prospective_gate import (
    ProspectiveAuthorization,
    ProspectiveMode,
    evaluate_prospective_gate,
)


def test_v10_non_live_authorization_never_unlocks_live() -> None:
    authorization = ProspectiveAuthorization(
        gate_id="STEP_91_USER_AUTHORIZATION",
        shadow_authorized=True,
        paper_authorized=True,
        live_authorized=False,
    )
    result = evaluate_prospective_gate(
        mode=ProspectiveMode.LIVE,
        authorization=authorization,
        host_read_only_healthy=True,
        exact_broker_symbol_resolved=True,
        closed_m5_feed_fresh=True,
        clock_ok=True,
        single_instance_lock_held=True,
        order_execution_enabled=False,
    )
    assert not result.allowed
    assert "LIVE_NOT_AUTHORIZED" in result.blockers
