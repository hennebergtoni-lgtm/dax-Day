from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def _read(name: str) -> str:
    return (DOCS / name).read_text(encoding="utf-8")


def test_canonical_engineering_memory_documents_exist() -> None:
    assert (DOCS / "PROJECT_KNOWLEDGE_INDEX.md").is_file()
    assert (DOCS / "PROBLEM_SOLUTION_REGISTRY.md").is_file()


def test_resume_policy_requires_engineering_memory_lookup() -> None:
    policy = _read("CONTEXT_RESUME_RECOVERY_POLICY.md")
    assert "docs/PROJECT_KNOWLEDGE_INDEX.md" in policy
    assert "docs/PROBLEM_SOLUTION_REGISTRY.md" in policy
    assert "severity 1–2/5" in policy
    assert "recover internally and continue" in policy


def test_knowledge_index_maps_core_reuse_topics() -> None:
    index = _read("PROJECT_KNOWLEDGE_INDEX.md")
    for required in (
        "Mandatory resume order",
        "Previously solved problems",
        "Public/open-source donor knowledge",
        "Paper preparation/contracts",
        "Recovery architecture",
        "Test / contract lookup rule",
    ):
        assert required in index


def test_problem_solution_registry_preserves_reusable_reasoning_shape() -> None:
    registry = _read("PROBLEM_SOLUTION_REGISTRY.md")
    for required in (
        "Mandatory use",
        "Root cause",
        "Accepted solution",
        "Proof/evidence",
        "Reuse rule",
        "PSR-001",
        "PSR-003",
        "PSR-005",
        "PSR-007",
        "PSR-008",
    ):
        assert required in registry
