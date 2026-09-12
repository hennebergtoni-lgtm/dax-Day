from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_workflow_integrity_gate_is_binding_and_complete() -> None:
    gate = _read("docs/DAXBOT_WORKFLOW_INTEGRITY_GATE_V1.md")

    required = (
        "Status: BINDING",
        "Step-Close-Gate",
        "Pointer-before-next-step rule",
        "Monotonic interrupted-lane rule",
        "User intervention rule",
        "Visible progress contract",
        "No-background-work truth",
        "CI/evidence discipline",
    )
    missing = [token for token in required if token not in gate]
    assert missing == [], f"workflow integrity gate lost required contracts: {missing}"


def test_handoff_and_refresher_use_monotonic_workflow_gate() -> None:
    handoff = _read("docs/DAXBOT_CHAT_HANDOFF_PROTOCOL_V1.md")
    refresher = _read("docs/SESSION_EXECUTION_REFRESHER.md")

    for text in (handoff, refresher):
        assert "DAXBOT_WORKFLOW_INTEGRITY_GATE_V1.md" in text
        assert "Step-Close-Gate" in text

    assert "visible numbering is monotonic" in handoff
    assert "resume its unfinished scope under the next unused integer" in handoff
    assert "the old wording `Fortsetzung Schritt N` must not be used" in handoff
    assert "pointer-before-next-step" in handoff.lower()
    assert "Monotonic carry-forward" in refresher
    assert "final/turn-ending response ends the active work turn" in refresher


def test_current_pointer_keeps_integer_monotonic_contract() -> None:
    pointer = _read("docs/CURRENT_WORK_STEP.md")

    active_match = re.search(r"Active whole-number step: \*\*(\d+)\*\*", pointer)
    next_match = re.search(r"Next step after successful completion: \*\*(\d+)\*\*", pointer)
    assert active_match is not None
    assert next_match is not None

    active = int(active_match.group(1))
    next_step = int(next_match.group(1))
    assert next_step == active + 1

    assert "Decimal or letter step IDs: **PROHIBITED**" in pointer
    assert "Step-Close-Gate" in pointer
    assert "Pointer-before-next-step" in pointer
    assert "Visible official step numbering is monotonic" in pointer


def test_workflow_drift_failure_is_in_durable_engineering_memory() -> None:
    registry = _read("docs/PROBLEM_SOLUTION_REGISTRY_ADDENDUM_V1.md")
    assert "PSR-018" in registry
    assert "workflow integrity" in registry.lower()
    assert "exact current head" in registry
