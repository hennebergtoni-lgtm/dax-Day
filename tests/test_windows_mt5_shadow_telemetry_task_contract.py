from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(name: str) -> str:
    return (ROOT / "scripts" / name).read_text(encoding="utf-8")


def test_shadow_installer_preserves_verified_bypass_and_40_bar_default() -> None:
    source = _read("install_windows_mt5_shadow_task.ps1")
    assert "[int]$Bars = 40" in source
    assert "-ExecutionPolicy Bypass" in source


def test_shadow_start_wrapper_preserves_40_bar_default() -> None:
    source = _read("windows_mt5_shadow_start.ps1")
    assert "[int]$Bars = 40" in source


def test_telemetry_task_is_independent_and_observation_only() -> None:
    installer = _read("install_windows_mt5_shadow_telemetry_task.ps1")
    wrapper = _read("windows_mt5_shadow_telemetry_export.ps1")
    combined = installer + wrapper
    assert "DAXLAB MT5 SHADOW TELEMETRY" in installer
    assert "-ExecutionPolicy Bypass" in installer
    assert "export_mt5_shadow_telemetry.py" in wrapper
    assert "NEON_DATABASE_URL" in combined
    assert "MetaTrader5" not in combined
    assert "order_send" not in combined
    assert "execution_capability=NONE" in combined


def test_telemetry_task_does_not_start_or_stop_shadow_task() -> None:
    source = _read("install_windows_mt5_shadow_telemetry_task.ps1")
    assert "Start-ScheduledTask" not in source
    assert "Stop-ScheduledTask" not in source
    assert "Unregister-ScheduledTask" not in source


def test_telemetry_task_uses_bounded_repetition_duration() -> None:
    source = _read("install_windows_mt5_shadow_telemetry_task.ps1")
    assert "[TimeSpan]::MaxValue" not in source
    assert "-RepetitionDuration (New-TimeSpan -Days 3650)" in source
