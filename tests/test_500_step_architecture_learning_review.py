from __future__ import annotations

from pathlib import Path
import re


REPO_ROOT = Path(__file__).resolve().parents[1]
CONTRACT = REPO_ROOT / "docs/FIVE_HUNDRED_STEP_ARCHITECTURE_LEARNING_REVIEW_V1.md"
POINTER = REPO_ROOT / "docs/CURRENT_WORK_STEP.md"


def test_500_step_review_contract_keeps_mandatory_learning_scope() -> None:
    text = CONTRACT.read_text(encoding="utf-8")

    assert "BINDING GOVERNANCE CONTRACT" in text
    assert "Step 2500" in text
    assert "pause ordinary feature expansion" in text
    assert "What do we know now that we did not know" in text
    assert "External / public-source refresh" in text
    assert "Performance and efficiency gate" in text
    assert "Modular-change principle" in text

    for decision in ("KEEP", "IMPROVE", "REFACTOR", "RETIRE", "DEFER"):
        assert f"`{decision}`" in text


def test_500_step_review_requires_evidence_not_refactor_theater() -> None:
    text = CONTRACT.read_text(encoding="utf-8")

    assert "does **not** mandate a rewrite" in text
    assert "Broad rewrites without this evidence are prohibited" in text
    assert "expected benefit, preferably measurable" in text
    assert "compatibility/parity requirements" in text
    assert "failure and rollback path" in text
    assert "VERIFIED historical evidence" in text


def test_current_pointer_names_2500_as_architecture_learning_review() -> None:
    pointer = POINTER.read_text(encoding="utf-8")

    assert "Next mandatory 500-step Architecture & Learning Review: **2500**" in pointer
    active_match = re.search(r"Active whole-number step: \*\*(\d+)\*\*", pointer)
    assert active_match is not None
    assert int(active_match.group(1)) >= 2161
