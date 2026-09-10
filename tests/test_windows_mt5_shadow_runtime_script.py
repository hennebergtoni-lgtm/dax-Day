from pathlib import Path


_RUNTIME_CHECK = Path("scripts/check_windows_mt5_shadow_runtime.ps1")


def _source() -> str:
    return _RUNTIME_CHECK.read_text(encoding="utf-8")


def test_runtime_check_fails_closed_when_required_tasks_are_missing():
    source = _source()
    assert 'throw "Scheduled task missing: $Mt5TaskName"' in source
    assert 'throw "Scheduled task missing: $ShadowTaskName"' in source


def test_runtime_check_verifies_bounded_restart_contract():
    source = _source()
    assert "function Assert-TaskRuntimePolicy" in source
    assert "-ExpectedRestartCount 5" in source
    assert "-ExpectedRestartMinutes 2" in source
    assert "-ExpectedRestartCount 3" in source
    assert "-ExpectedRestartMinutes 5" in source
    assert "RestartCount 999" not in source
    assert "Task restart count drift" in source
    assert "Task restart interval drift" in source


def test_runtime_check_verifies_single_instance_and_unlimited_runtime_contract():
    source = _source()
    assert "MultipleInstances" in source
    assert "expected=IgnoreNew" in source
    assert "ExecutionTimeLimit" in source
    assert "Task execution-time-limit drift" in source


def test_runtime_check_preserves_no_order_heartbeat_gate():
    source = _source()
    assert "Heartbeat execution_capability is not NONE." in source
    assert "Heartbeat order_execution_enabled is not false." in source
    assert "execution_capability=NONE" in source
    assert "order_execution_enabled=false" in source
