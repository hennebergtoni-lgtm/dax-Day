from daxlab.runtime.shadow_soak import run_shadow_soak
from daxlab.runtime.shadow_soak_fixture import BARS_PER_SESSION, SESSIONS, build_bars


def test_30_session_soak_fixture_has_expected_size() -> None:
    bars = build_bars()
    assert len(bars) == SESSIONS * BARS_PER_SESSION == 3090


def test_30_session_soak_is_deterministic_no_order_only() -> None:
    bars = build_bars()
    first = run_shadow_soak(bars)
    second = run_shadow_soak(bars)
    assert first == second
    assert first.processed == 3090
    assert first.blocked == 0
    assert first.duplicates_suppressed == 0
    assert all(item.action == "NO_ORDER" for item in first.decisions)
    assert first.execution_capability == "NONE"
    assert first.order_execution_enabled is False
