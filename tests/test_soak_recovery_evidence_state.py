from daxlab.runtime.shadow_soak import run_shadow_soak, soak_recovery_payload


def test_recovery_payload_is_explicitly_synthetic_only() -> None:
    payload = soak_recovery_payload(run_shadow_soak(()))
    assert payload["evidence_state"] == "SYNTHETIC_ONLY_NOT_BROKER_EVIDENCE"
