from daxlab.runtime.shadow_soak import run_shadow_soak


def test_soak_result_schema_and_evidence_marker_are_explicit() -> None:
    result = run_shadow_soak(())
    assert result.schema_version == "DAXLAB_SHADOW_SOAK_RESULT_V1"
    assert result.evidence_state == "SYNTHETIC_ONLY_NOT_BROKER_EVIDENCE"
    assert result.execution_capability == "NONE"
