import pytest

from daxlab.research.variant_trial_chronology import (
    BLOCKED,
    VERIFIED,
    TrialChronologyEvidence,
    evaluate_trial_chronology,
)


def _declaration(mode: str = "PREDECLARED") -> dict[str, object]:
    return {
        "trial_id": "trial-001",
        "declaration_mode": mode,
        "record_hash": "a" * 64,
    }


def _evidence(**overrides) -> TrialChronologyEvidence:
    values = {
        "trial_id": "trial-001",
        "declaration_record_hash": "a" * 64,
        "declaration_commit": "1" * 40,
        "result_commit": "2" * 40,
        "declaration_present_at_commit": True,
        "declaration_commit_is_ancestor_of_result": True,
        "result_artifact_present_at_declaration_commit": False,
    }
    values.update(overrides)
    return TrialChronologyEvidence(**values)


def test_valid_independent_chronology_evidence_verifies_predeclaration():
    result = evaluate_trial_chronology(_declaration(), _evidence())
    assert result.status == VERIFIED
    assert result.verified_predeclared is True
    assert result.blockers == ()


@pytest.mark.parametrize(
    ("overrides", "blocker"),
    [
        ({"trial_id": "trial-other"}, "TRIAL_ID_MISMATCH"),
        ({"declaration_record_hash": "b" * 64}, "DECLARATION_RECORD_HASH_MISMATCH"),
        ({"declaration_present_at_commit": False}, "DECLARATION_NOT_PRESENT_AT_DECLARATION_COMMIT"),
        (
            {"declaration_commit_is_ancestor_of_result": False},
            "DECLARATION_COMMIT_NOT_ANCESTOR_OF_RESULT",
        ),
        (
            {"result_artifact_present_at_declaration_commit": True},
            "RESULT_ALREADY_PRESENT_AT_DECLARATION_COMMIT",
        ),
        ({"result_commit": "1" * 40}, "DECLARATION_AND_RESULT_COMMIT_IDENTICAL"),
    ],
)
def test_chronology_violations_fail_closed(overrides, blocker):
    result = evaluate_trial_chronology(_declaration(), _evidence(**overrides))
    assert result.status == BLOCKED
    assert result.verified_predeclared is False
    assert blocker in result.blockers


def test_retroactive_declaration_can_never_be_verified_predeclared():
    result = evaluate_trial_chronology(_declaration("RETROACTIVE_RECONSTRUCTED"), _evidence())
    assert result.status == BLOCKED
    assert "DECLARATION_NOT_CLAIMED_PREDECLARED" in result.blockers


def test_invalid_git_sha_is_rejected():
    with pytest.raises(ValueError, match="declaration_commit"):
        evaluate_trial_chronology(
            _declaration(), _evidence(declaration_commit="not-a-git-sha")
        )


def test_invalid_record_hash_is_rejected():
    declaration = _declaration()
    declaration["record_hash"] = "ABC"
    with pytest.raises(ValueError, match="record_hash"):
        evaluate_trial_chronology(declaration, _evidence())
