import json
from pathlib import Path

from daxlab.runtime.shadow_soak import run_shadow_soak, soak_recovery_payload
from daxlab.runtime.shadow_soak_fixture import build_bars


FORBIDDEN_CREDENTIAL_KEYS = {
    "password",
    "passcode",
    "otp",
    "token",
    "access_token",
    "refresh_token",
    "secret",
    "api_key",
    "login",
    "account_number",
    "email",
    "phone",
    "tax_id",
}


def _walk_keys(value: object) -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        for key, item in value.items():
            found.add(str(key).lower())
            found.update(_walk_keys(item))
    elif isinstance(value, (list, tuple)):
        for item in value:
            found.update(_walk_keys(item))
    return found


def _web_status() -> dict[str, object]:
    root = Path(__file__).resolve().parents[1]
    return json.loads((root / "web/status.json").read_text())


def test_static_web_cannot_be_used_to_satisfy_real_host_readiness() -> None:
    web = _web_status()
    assert web["runtime_truth_included"] is False
    assert "synthetic_shadow_soak" not in web
    assert "host_readiness" not in web
    assert "pre_host_gate" not in web
    assert web["runtime_boundary"]["static_file_must_not_be_used_for_current_health"] is True


def test_paper_remains_blocked_in_static_governance() -> None:
    web = _web_status()
    assert web["paper_preparation"]["paper_started"] is False
    assert web["paper_preparation"]["broker_adapter_present"] is False
    assert web["readiness"]["paper"] == "BLOCKED"


def test_live_remains_blocked_even_after_successful_synthetic_soak() -> None:
    result = run_shadow_soak(build_bars())
    assert result.processed == 3090
    assert result.blocked == 0
    assert all(decision.action == "NO_ORDER" for decision in result.decisions)
    web = _web_status()
    assert web["readiness"]["live"] == "BLOCKED"
    assert web["runtime_truth_included"] is False


def test_v11_static_status_and_recovery_payloads_are_credential_free() -> None:
    web = _web_status()
    recovery = soak_recovery_payload(run_shadow_soak(build_bars()[:3]))
    assert not (_walk_keys(web) & FORBIDDEN_CREDENTIAL_KEYS)
    assert not (_walk_keys(recovery) & FORBIDDEN_CREDENTIAL_KEYS)
