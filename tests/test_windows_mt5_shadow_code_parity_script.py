from pathlib import Path


SCRIPT = Path("scripts/check_windows_mt5_shadow_code_parity.ps1")
PINNED_COMMIT = "8fe0b61a4da0b5637df372343d67b202bfbe8222"

CRITICAL_PATHS = (
    "scripts/windows_mt5_shadow_start.ps1",
    "scripts/mt5_shadow_supervisor.py",
    "scripts/mt5_windows_probe.py",
    "scripts/check_windows_mt5_shadow_runtime.ps1",
    "scripts/install_windows_mt5_shadow_task.ps1",
    "src/daxlab/runtime/atomic_json.py",
    "src/daxlab/runtime/mt5_broker_session.py",
    "src/daxlab/runtime/mt5_cross_cycle_integrity.py",
    "src/daxlab/runtime/mt5_heartbeat_history.py",
    "src/daxlab/runtime/mt5_readonly.py",
    "src/daxlab/runtime/mt5_shadow_integration.py",
    "src/daxlab/runtime/mt5_shadow_supervisor.py",
    "src/daxlab/runtime/mt5_windows_bundle.py",
    "src/daxlab/runtime/prospective_gate.py",
    "src/daxlab/runtime/shadow_observation.py",
    "src/daxlab/runtime/shadow_resume_anchor.py",
    "src/daxlab/runtime/shadow_soak.py",
    "src/daxlab/runtime/single_instance.py",
)


def _text() -> str:
    return SCRIPT.read_text(encoding="utf-8")


def test_parity_checker_is_pinned_and_covers_runtime_surface() -> None:
    text = _text()
    assert PINNED_COMMIT in text
    for path in CRITICAL_PATHS:
        assert path in text
    assert "raw.githubusercontent.com/$repository/$ExpectedCommit/$relativePath" in text
    assert "Get-FileHash" in text
    assert "MISMATCH" in text
    assert "MISSING" in text
    assert "exit 1" in text


def test_parity_checker_has_no_execution_or_scheduler_mutation_surface() -> None:
    text = _text().lower()
    forbidden = (
        "start-scheduledtask",
        "stop-scheduledtask",
        "register-scheduledtask",
        "unregister-scheduledtask",
        "set-scheduledtask",
        "order_send",
        "ordersend",
        "trade.request",
        "execution_capability=true",
        "order_execution_enabled=true",
    )
    for token in forbidden:
        assert token not in text
    assert "read_only / no_order / no_scheduler_changes" in text
    assert "execution_capability=none" in text
    assert "order_execution_enabled=false" in text


def test_parity_checker_requires_full_lowercase_commit_sha() -> None:
    text = _text()
    assert "^[0-9a-f]{40}$" in text
