from daxlab.reference.detail_artifacts import (
    DetailEvidenceIdentity,
    V112_CLEAN_DETAIL_ARTIFACTS,
    artifact_spec,
)


def test_clean_detail_artifact_specs_are_unique_and_complete() -> None:
    kinds = [spec.detail_kind for spec in V112_CLEAN_DETAIL_ARTIFACTS]
    assert kinds == ["WF_METRICS", "SELECTED_VARIANTS", "TRADES"]
    assert len({spec.sha256 for spec in V112_CLEAN_DETAIL_ARTIFACTS}) == 3
    assert [spec.expected_rows for spec in V112_CLEAN_DETAIL_ARTIFACTS] == [243, 81, 856]


def test_trade_hash_is_not_mislabeled_as_historical_identity() -> None:
    trades = artifact_spec("TRADES")
    assert trades.identity is DetailEvidenceIdentity.NEW_REPRODUCIBLE_CLEAN_EVIDENCE
    assert trades.sha256 == "f60bb5fc15b5e620a37ca44bdb5bdcea20381261c06d40cb78aba34387f56023"


def test_historical_hash_matched_artifacts_remain_distinct() -> None:
    assert artifact_spec("WF_METRICS").identity is DetailEvidenceIdentity.HISTORICAL_HASH_MATCH
    assert artifact_spec("SELECTED_VARIANTS").identity is DetailEvidenceIdentity.HISTORICAL_HASH_MATCH
