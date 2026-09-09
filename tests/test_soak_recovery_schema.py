from daxlab.runtime.shadow_soak import run_shadow_soak, soak_recovery_payload


def test_soak_recovery_schema_and_hash_are_explicit() -> None:
    payload = soak_recovery_payload(run_shadow_soak(()))
    assert payload["schema_version"] == "DAXLAB_SHADOW_SOAK_RECOVERY_V2"
    assert payload["execution_capability"] == "NONE"
    assert payload["order_execution_enabled"] is False
    assert len(payload["payload_sha256"]) == 64
