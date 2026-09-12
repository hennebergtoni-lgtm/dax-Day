from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_stable_branch_governance_documents_manual_enforcement_truth() -> None:
    governance = _read("docs/STABLE_BRANCH_GOVERNANCE_V1.md")
    for required in (
        "WAITING_EXTERNAL / MANUAL_GITHUB_ADMIN",
        "protected=false",
        "protection.enabled=false",
        "repository rulesets endpoint returns an empty list `[]`",
        "Do not claim `main` is protected",
    ):
        assert required in governance


def test_universal_required_check_maps_to_broad_integration_job() -> None:
    governance = _read("docs/STABLE_BRANCH_GOVERNANCE_V1.md")
    broad = _read(".github/workflows/ci.yml")

    assert "require the broad GitHub Actions check named `test`" in governance
    assert "jobs:\n  test:" in broad
    assert "pull_request:" in broad
    assert "run: pytest" in broad


def test_candidate_core_is_not_safe_as_universal_required_check() -> None:
    governance = _read("docs/STABLE_BRANCH_GOVERNANCE_V1.md")
    focused = _read(".github/workflows/dax-bot-1x-ci.yml")

    assert "do not universally require the `candidate-core` check" in governance
    assert "paths:" in focused
    assert "candidate-core:" in focused
    assert "src/daxlab/runtime/candidate_*.py" in focused
