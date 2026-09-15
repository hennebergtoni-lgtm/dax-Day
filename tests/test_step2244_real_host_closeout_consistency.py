from __future__ import annotations

from collections import Counter
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
EVIDENCE_HEAD = "ae0efbcaff5650f9e8a8f31bc8fd603cfae212a2"


def _read(name: str) -> str:
    return (DOCS / name).read_text(encoding="utf-8")


def test_step2244_real_host_truth_is_present_in_all_current_pointers() -> None:
    current_documents = (
        "CURRENT_WORK_STEP.md",
        "MASTERSTAND_LATEST.md",
        "DAXBOT_CHAT_HANDOFF_PROTOCOL_V1.md",
        "UEBERGABE.md",
        "STEP_2244_MARKET_ECONOMICS_DERIVATION_CLOSEOUT.md",
        "STEP_2238_2240_PREDEMO_PROGRAM.md",
        "STEP_2238_IG_READINESS_MATRIX.md",
        "STEP_2238_WINDOWS_HOST_LANE_AUDIT.md",
    )
    for name in current_documents:
        text = _read(name)
        assert EVIDENCE_HEAD in text, name
        assert "8/8" in text, name
        assert "10/10" in text, name
        assert "NONE/false" in text or (
            "execution_capability=NONE" in text
            and "order_execution_enabled=false" in text
        ), name


def test_recomputed_gate_matrix_has_exactly_27_unique_rows_and_tally() -> None:
    matrix = _read("ACCELERATION_M01_DEMO_READINESS_MATRIX.md")
    section = matrix.split("### Recomputed 27 Pre-DEMO gates", 1)[1].split(
        "### Smallest remaining work", 1
    )[0]
    rows = re.findall(
        r"^\|\s*(\d{1,2})\s*\|[^\n]*?\|\s*"
        r"(VERIFIED|IMPLEMENTED|WAITING_EXTERNAL|BLOCKED|UNKNOWN)\s*\|",
        section,
        re.MULTILINE,
    )

    assert [int(gate) for gate, _ in rows] == list(range(1, 28))
    counts = Counter(status for _, status in rows)
    assert counts == Counter(
        {
            "VERIFIED": 8,
            "IMPLEMENTED": 0,
            "WAITING_EXTERNAL": 13,
            "BLOCKED": 6,
            "UNKNOWN": 0,
        }
    )
    assert "8 VERIFIED / 0 IMPLEMENTED / 13 WAITING_EXTERNAL /" in section
    assert "6 BLOCKED / 0 UNKNOWN = 27" in section


def test_gate_recount_keeps_read_truth_separate_from_execution_truth() -> None:
    matrix = _read("ACCELERATION_M01_DEMO_READINESS_MATRIX.md")
    assert "economics_verified=false" not in matrix.split(
        "## Step2244 real-host evidence recount", 1
    )[0]
    assert "canonical tick/value/quantity/margin/cost binding is explicitly incomplete" in matrix
    assert "No native IG submission/deal-reference binding" in matrix
    assert "Capability deliberately remains NONE/false" in matrix
    assert re.search(r"real-host\s+read is not execution", matrix)


def test_step2242_working_orders_contract_matches_runtime_owner() -> None:
    adapter = (ROOT / "src/daxlab/adapters/ig_rest_readonly.py").read_text(
        encoding="utf-8"
    )
    contract = _read("STEP_2238_IG_READINESS_MATRIX.md")
    current_contract = contract.split("## Canonical authenticated-read contract", 1)[1]
    assert 'path="/workingorders"' in adapter
    assert "`GET /workingorders`, v2" in current_contract
    assert "The earlier `/working-orders` route was rejected" in current_contract


def test_scoped_step_states_are_consistent_and_do_not_authorize_orders() -> None:
    program = _read("STEP_2238_2240_PREDEMO_PROGRAM.md").split(
        "## Exact-clone collector path contract", 1
    )[0]
    assert "Step2238: **COMPLETED / REAL-HOST VERIFIED**" in program
    assert "PARTIALLY REAL-HOST VERIFIED /\n  WAITING_EXTERNAL" in program
    assert "Step2240: **IN_PROGRESS / BLOCKED**" in program
    assert "No read result authorizes execution" in program

    closeout = _read("STEP_2244_MARKET_ECONOMICS_DERIVATION_CLOSEOUT.md")
    assert "Status: COMPLETED / REAL-HOST VERIFIED" in closeout
    assert "no retry, resubmit, dealing method or order" in closeout
    assert "`economics_verified=false` remains correct" in closeout
