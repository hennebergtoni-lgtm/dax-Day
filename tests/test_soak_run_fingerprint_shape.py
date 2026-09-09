from daxlab.runtime.shadow_soak import run_shadow_soak


def test_soak_run_fingerprint_is_sha256_hex() -> None:
    value = run_shadow_soak(()).run_fingerprint
    assert len(value) == 64
    int(value, 16)
