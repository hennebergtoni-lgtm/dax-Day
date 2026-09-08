from daxlab.runtime.health import HealthState
from daxlab.runtime.mt5_health_bridge import mt5_execution_health
from daxlab.runtime.mt5_readonly import Mt5Health


def test_all_read_only_health_gates_green() -> None:
    health, blockers = mt5_execution_health(Mt5Health(True, True, True, True, True, True, True))
    assert health is HealthState.GREEN
    assert blockers == ()


def test_disconnected_or_unsafe_state_is_red() -> None:
    health, blockers = mt5_execution_health(Mt5Health(False, True, True, False, True, True, True))
    assert health is HealthState.RED
    assert "MT5_TERMINAL_DISCONNECTED" in blockers
    assert "MT5_MARKET_DATA_STALE" in blockers
