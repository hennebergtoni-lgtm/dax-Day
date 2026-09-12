from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
DOCS = ROOT / "docs"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_ci_ownership_contract_exists_and_preserves_hybrid_model() -> None:
    contract = _read(DOCS / "CI_OWNERSHIP_CONTRACT_V1.md")
    for required in (
        "RETAIN HYBRID CI / CLARIFY OWNERSHIP",
        "research-lab-ci",
        "dax-bot-1x-ci",
        "reference-payload-export",
        "PAPER is not authorized",
        "LIVE is not authorized",
    ):
        assert required in contract


def test_research_lab_ci_remains_broad_integration_owner() -> None:
    workflow = _read(WORKFLOWS / "ci.yml")
    for required in (
        "name: research-lab-ci",
        "run: pytest",
        "Recovery reconstruction preflight",
        "Research registry integrity",
        "Hypothesis ledger integrity",
        "Web status integrity",
        "Static read-only runtime safety smoke",
        "V11.2 engine surface probe",
        "Guarded V11.2 replay smoke",
        "Offline SHADOW soak smoke",
        "Neon connection gate",
        "Isolated database restore drill",
    ):
        assert required in workflow


def test_dax_bot_ci_remains_focused_candidate_and_broker_safety_owner() -> None:
    workflow = _read(WORKFLOWS / "dax-bot-1x-ci.yml")
    for required in (
        "name: dax-bot-1x-ci",
        "src/daxlab/runtime/candidate_*.py",
        "src/daxlab/runtime/broker_*.py",
        "Candidate correctness, restart and broker-neutral safety tests",
        "tests/test_candidate*.py",
        "tests/test_broker*.py",
        "Candidate performance observation",
    ):
        assert required in workflow


def test_reference_payload_export_remains_hash_verified_reference_owner() -> None:
    workflow = _read(WORKFLOWS / "reference-payload-export.yml")
    for required in (
        "name: reference-payload-export",
        "Verify and export recovered engine sources",
        "hash mismatch",
        "v112-verified-reference-sources",
    ):
        assert required in workflow
