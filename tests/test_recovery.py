from daxlab.data.recovery import RecoveryEvidence, RecoveryIdentity, classify_recovery


EXPECTED_SHA = "e51bba6cb2befe5e7eb0376318e43b096a3e2ecaae3f556019862975c60286a2"


def evidence(*, observed_sha: str | None = None, session_rows: int = 172319) -> RecoveryEvidence:
    return RecoveryEvidence(
        raw_rows=481824,
        session_days=1673,
        session_rows=session_rows,
        bars_per_day=103,
        invalid_ohlc_rows=0,
        expected_raw_rows=481824,
        expected_session_days=1673,
        expected_session_rows=172319,
        expected_bars_per_day=103,
        expected_session_sha256=EXPECTED_SHA,
        observed_session_sha256=observed_sha,
    )


def test_structural_match_does_not_claim_hash_identity() -> None:
    result = evidence()
    assert classify_recovery(result) is RecoveryIdentity.STRUCTURAL_MATCH
    assert not result.clean_reference_eligible


def test_hash_verified_is_clean_reference_eligible() -> None:
    result = evidence(observed_sha=EXPECTED_SHA)
    assert classify_recovery(result) is RecoveryIdentity.HASH_VERIFIED
    assert result.clean_reference_eligible


def test_structural_mismatch_blocks_identity() -> None:
    result = evidence(observed_sha=EXPECTED_SHA, session_rows=172318)
    assert classify_recovery(result) is RecoveryIdentity.MISMATCH
    assert not result.clean_reference_eligible
