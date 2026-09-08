from daxlab.runtime.prospective_gate import (
    ProspectiveAuthorization,
    ProspectiveMode,
    evaluate_prospective_gate,
)


def auth() -> ProspectiveAuthorization:
    return ProspectiveAuthorization(
        gate_id="STEP_91_USER_AUTHORIZATION",
        shadow_authorized=True,
        paper_authorized=True,
        live_authorized=False,
    )


def healthy_kwargs() -> dict[str, bool]:
    return {
        "host_read_only_healthy": True,
        "exact_broker_symbol_resolved": True,
        "closed_m5_feed_fresh": True,
        "clock_ok": True,
        "single_instance_lock_held": True,
        "order_execution_enabled": False,
    }


def test_shadow_and_paper_can_pass_readiness_after_step_91_authorization() -> None:
    shadow = evaluate_prospective_gate(
        mode=ProspectiveMode.SHADOW,
        authorization=auth(),
        **healthy_kwargs(),
    )
    paper = evaluate_prospective_gate(
        mode=ProspectiveMode.PAPER,
        authorization=auth(),
        **healthy_kwargs(),
    )
    assert shadow.allowed
    assert paper.allowed


def test_live_remains_separately_blocked() -> None:
    result = evaluate_prospective_gate(
        mode=ProspectiveMode.LIVE,
        authorization=auth(),
        **healthy_kwargs(),
    )
    assert not result.allowed
    assert "LIVE_NOT_AUTHORIZED" in result.blockers


def test_execution_flag_breaks_shadow_and_paper_readiness() -> None:
    values = healthy_kwargs()
    values["order_execution_enabled"] = True
    result = evaluate_prospective_gate(
        mode=ProspectiveMode.PAPER,
        authorization=auth(),
        **values,
    )
    assert not result.allowed
    assert "EXECUTION_MUST_REMAIN_DISABLED" in result.blockers


def test_missing_host_evidence_blocks_readiness() -> None:
    values = healthy_kwargs()
    values["host_read_only_healthy"] = False
    values["exact_broker_symbol_resolved"] = False
    result = evaluate_prospective_gate(
        mode=ProspectiveMode.SHADOW,
        authorization=auth(),
        **values,
    )
    assert not result.allowed
    assert "MT5_HOST_NOT_HEALTHY" in result.blockers
    assert "BROKER_SYMBOL_NOT_EXACT" in result.blockers
