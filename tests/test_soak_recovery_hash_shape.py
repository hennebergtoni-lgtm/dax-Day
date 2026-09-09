from daxlab.runtime.shadow_soak import run_shadow_soak, soak_recovery_payload


def test_soak_recovery_payload_hash_is_sha256_hex() -> None:
    value = soak_recovery_payload(run_shadow_soak(()))["payload_sha256"]
    assert len(value) == 64
    int(value, 16)
