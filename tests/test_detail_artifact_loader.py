import hashlib

from daxlab.detail_artifact_loader import preflight_detail_csv
from daxlab.reference.detail_artifacts import DetailArtifactSpec, DetailEvidenceIdentity


def _content() -> bytes:
    return (
        "wf,cost,variant_index,trades,pf,avg_r,return_r,max_dd_r\n"
        "1,normal,120,12,1.4,0.2,2.5,-3.0\n"
    ).encode()


def _spec(content: bytes, *, rows: int = 1) -> DetailArtifactSpec:
    return DetailArtifactSpec(
        detail_kind="WF_METRICS",
        filename="fixture.csv",
        expected_rows=rows,
        sha256=hashlib.sha256(content).hexdigest(),
        identity=DetailEvidenceIdentity.HISTORICAL_HASH_MATCH,
    )


def test_valid_csv_preflights_to_planned_rows() -> None:
    content = _content()
    result = preflight_detail_csv(content=content, spec=_spec(content))
    assert result.observed_rows == 1
    assert len(result.planned_rows) == 1


def test_hash_mismatch_fails_before_parsing() -> None:
    content = _content()
    spec = _spec(content)
    bad = DetailArtifactSpec(
        detail_kind=spec.detail_kind,
        filename=spec.filename,
        expected_rows=spec.expected_rows,
        sha256="0" * 64,
        identity=spec.identity,
    )
    try:
        preflight_detail_csv(content=content, spec=bad)
    except ValueError as exc:
        assert str(exc) == "ARTIFACT_HASH_MISMATCH"
    else:
        raise AssertionError("hash mismatch must fail closed")


def test_row_count_mismatch_fails_closed() -> None:
    content = _content()
    try:
        preflight_detail_csv(content=content, spec=_spec(content, rows=2))
    except ValueError as exc:
        assert str(exc) == "ROW_COUNT_MISMATCH"
    else:
        raise AssertionError("row mismatch must fail closed")
