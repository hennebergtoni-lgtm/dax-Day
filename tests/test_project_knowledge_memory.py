from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def _read(name: str) -> str:
    return (DOCS / name).read_text(encoding="utf-8")


def _problem_solution_entries(registry: str) -> list[str]:
    return [
        "## PSR-" + chunk
        for chunk in registry.split("## PSR-")[1:]
    ]


def _step_value(text: str, label: str) -> int:
    match = re.search(rf"^- {re.escape(label)}: \*\*(\d+)\*\*$", text, re.MULTILINE)
    assert match, f"missing integer work-step pointer: {label}"
    return int(match.group(1))


def test_canonical_engineering_memory_documents_exist() -> None:
    assert (DOCS / "PROJECT_KNOWLEDGE_INDEX.md").is_file()
    assert (DOCS / "PROBLEM_SOLUTION_REGISTRY.md").is_file()
    assert (DOCS / "CURRENT_WORK_STEP.md").is_file()


def test_resume_policy_requires_engineering_memory_lookup() -> None:
    policy = _read("CONTEXT_RESUME_RECOVERY_POLICY.md")
    assert "docs/PROJECT_KNOWLEDGE_INDEX.md" in policy
    assert "docs/PROBLEM_SOLUTION_REGISTRY.md" in policy
    assert "severity 1–2/5" in policy
    assert "recover internally and continue" in policy


def test_resume_navigation_requires_canonical_step_pointer() -> None:
    refresher = _read("SESSION_EXECUTION_REFRESHER.md")
    index = _read("PROJECT_KNOWLEDGE_INDEX.md")
    for text in (refresher, index):
        assert "docs/CURRENT_WORK_STEP.md" in text
    assert "chat memory or raw commit count" in refresher
    assert "Current work-step numbering" in index


def test_current_step_pointer_is_integer_sequential_and_keeps_500_audit() -> None:
    ledger = _read("CURRENT_WORK_STEP.md")
    last_completed = _step_value(ledger, "Last completed whole-number step")
    active = _step_value(ledger, "Active whole-number step")
    next_step = _step_value(ledger, "Next step after successful completion")
    audit = _step_value(ledger, "Next mandatory 500-step full audit")

    assert active == last_completed + 1
    assert next_step == active + 1
    assert audit == 2500
    assert "Decimal or letter step IDs: **PROHIBITED**" in ledger
    assert "2081" in ledger and "2089" in ledger
    assert "reconstruction anchor `199e6bf073da1a717839b37e70a314f203e9ffa4`" in ledger


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


def test_every_problem_solution_entry_is_reusable_engineering_memory() -> None:
    registry = _read("PROBLEM_SOLUTION_REGISTRY.md")
    entries = _problem_solution_entries(registry)
    assert entries, "problem/solution registry must contain durable entries"

    for entry in entries:
        heading = entry.splitlines()[0]
        for required in (
            "**Status:**",
            "**Component:**",
            "**Problem:**",
            "**Root cause:**",
            "**Proof/evidence:**",
            "**Reuse rule:**",
        ):
            assert required in entry, f"{heading} missing {required}"

        assert (
            "**Accepted solution:**" in entry
            or "**Current decision:**" in entry
        ), f"{heading} must preserve the accepted solution or current decision"


def test_known_fixed_defects_keep_regression_test_evidence() -> None:
    registry = _read("PROBLEM_SOLUTION_REGISTRY.md")
    entries = {
        entry.split(" — ", 1)[0].removeprefix("## "): entry
        for entry in _problem_solution_entries(registry)
    }

    for psr_id in ("PSR-003", "PSR-005", "PSR-007", "PSR-010"):
        entry = entries[psr_id]
        assert "test" in entry.lower(), (
            f"{psr_id} must retain regression-test evidence so the solved defect "
            "is not rediscovered without its proof"
        )
