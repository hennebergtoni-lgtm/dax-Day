from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def read(name: str) -> str:
    return (DOCS / name).read_text(encoding="utf-8")


def test_project_philosophy_is_single_binding_owner() -> None:
    philosophy = read("PROJECT_PHILOSOPHY.md")
    assert "Status: **BINDING**" in philosophy
    for required in (
        "FAMILY_CAPITAL_PRINCIPLE=ECONOMIC_RETURN_WITH_CAPITAL_SURVIVAL",
        "TURBO_REQUEST_RIGHT=USER_MAY_REQUEST|SYSTEM_MAY_RECOMMEND|HARD_SAFETY_MAY_VETO",
        "TURBO_OVERRIDE_RIGHT=NONE",
        "DEMO IS NOT A TOY MODE. DEMO IS THE FLIGHT SCHOOL.",
        "ROBUST_POSITIVE_ECONOMIC_VALUE_AFTER_REALISTIC_COSTS",
        "RESEARCH LABELS ONLY",
        "TURBO_RUNTIME_ACTIVATION=NO",
        "TURBO_REAL_RISK_CHANGE=NO",
        "execution_capability=NONE",
        "order_execution_enabled=false",
        "HIGH_VALUE_RESEARCH_CANDIDATE",
    ):
        assert required in philosophy


def test_current_owners_reference_philosophy_without_readiness_promotion() -> None:
    for owner in (
        "CURRENT_WORK_STEP.md",
        "MASTERSTAND_LATEST.md",
        "WORK_CONTINUITY_PROTOCOL.md",
        "DAXBOT_CHAT_HANDOFF_PROTOCOL_V1.md",
    ):
        assert "PROJECT_PHILOSOPHY.md" in read(owner)

    current = read("CURRENT_WORK_STEP.md")
    master = read("MASTERSTAND_LATEST.md")
    for text in (current, master):
        assert "Step2239" in text and "WAITING_EXTERNAL" in text
        assert "Step2240" in text and "BLOCKED" in text
        assert "M01" in text and "NOT READY" in text
        assert "8/0/13/6/0" in text or (
            "8 VERIFIED / 0 IMPLEMENTED / 13 WAITING_EXTERNAL / 6 BLOCKED / 0 UNKNOWN" in text
        )


def test_step2246_is_terminal_and_2247_is_not_activated() -> None:
    current = read("CURRENT_WORK_STEP.md")
    assert "Last completed whole-number step: **2246**" in current
    assert "Active whole-number step: **2246**" in current
    assert "Active step state: **COMPLETED / GOVERNANCE VERIFIED**" in current
    assert "Next step after successful completion: **2247**" in current
    assert "Step2247 is RESERVED / NOT ACTIVATED" in current


def test_continuity_preserves_bounded_repository_thread() -> None:
    continuity = read("WORK_CONTINUITY_PROTOCOL.md")
    for required in (
        "REPOSITORY TRUTH",
        "LESSONS LEDGER",
        "HYPOTHESIS/TRIAL REGISTRIES",
        "FILTER GOVERNANCE",
        "EVIDENCE_BEFORE_CONFIDENCE",
        "FAMILY_CAPITAL_PRINCIPLE",
        "does not authorize a Work daemon",
    ):
        assert required in continuity
