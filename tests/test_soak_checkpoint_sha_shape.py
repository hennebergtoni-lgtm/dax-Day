from daxlab.runtime.shadow_soak import initial_soak_checkpoint, verify_soak_checkpoint


def test_initial_checkpoint_is_valid_sha_sealed_identity() -> None:
    checkpoint = initial_soak_checkpoint()
    verify_soak_checkpoint(checkpoint)
    assert checkpoint.processed_count == 0
    assert checkpoint.last_bar_fingerprint is None
    assert checkpoint.seen_decision_ids == ()
    assert len(checkpoint.payload_sha256) == 64
