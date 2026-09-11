from __future__ import annotations

from pathlib import Path
import shutil
import subprocess

import pytest


SCRIPTS = (
    Path("scripts/windows_mt5_shadow_start.ps1"),
    Path("scripts/preflight_windows_mt5_shadow_autostart.ps1"),
    Path("scripts/install_windows_mt5_shadow_task.ps1"),
    Path("scripts/check_windows_mt5_shadow_runtime.ps1"),
    Path("scripts/uninstall_windows_mt5_shadow_tasks.ps1"),
)


@pytest.mark.parametrize("path", SCRIPTS)
def test_powershell_scripts_parse_when_pwsh_is_available(path: Path) -> None:
    pwsh = shutil.which("pwsh")
    if pwsh is None:
        pytest.skip("pwsh not installed on this runner")
    command = (
        "$errors=$null; "
        f"[System.Management.Automation.Language.Parser]::ParseFile('{path.as_posix()}',"
        " [ref]$null, [ref]$errors) | Out-Null; "
        "if ($errors.Count -gt 0) { $errors | ForEach-Object { Write-Error $_ }; exit 1 }"
    )
    completed = subprocess.run(
        [pwsh, "-NoProfile", "-Command", command],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr


def test_start_wrapper_is_shadow_only() -> None:
    text = Path("scripts/windows_mt5_shadow_start.ps1").read_text(encoding="utf-8")
    lower = text.lower()
    assert "mt5_shadow_supervisor.py" in text
    assert "--broker-timezone" in text
    assert "--state-dir" in text
    assert "[string]$PythonExecutable = ''" in text
    assert "if ($PythonExecutable)" in text
    assert ".venv-mt5\\Scripts\\python.exe" in text
    assert 'Write-Host "StateDir: $StateDir"' in text
    assert 'Write-Host "Python: $python"' in text
    for forbidden in ("order_send", "order_check", "live_authorized", "paper_authorized"):
        assert forbidden not in lower


def test_preflight_is_read_only_and_requires_green_heartbeat() -> None:
    text = Path("scripts/preflight_windows_mt5_shadow_autostart.ps1").read_text(
        encoding="utf-8"
    )
    lower = text.lower()
    assert "--once" in text
    assert "execution_capability -ne 'NONE'" in text
    assert "order_execution_enabled -ne $false" in text
    assert "heartbeat.status -ne 'GREEN'" in text
    assert "Register-ScheduledTask" in text
    assert "Get-Command $command" in text
    assert "register-scheduledtask -taskname" not in lower
    for forbidden in ("order_send", "order_check", "--login", "--password"):
        assert forbidden not in lower


def test_installer_registers_mt5_and_shadow_without_credentials() -> None:
    text = Path("scripts/install_windows_mt5_shadow_task.ps1").read_text(encoding="utf-8")
    lower = text.lower()
    assert "Register-ScheduledTask" in text
    assert "DAXLAB MT5 Terminal" in text
    assert "DAXLAB MT5 SHADOW" in text
    assert "terminal64" in lower
    assert "-MultipleInstances IgnoreNew" in text
    assert "-RestartCount" in text
    assert "order_execution_enabled=false" in text
    assert "[string]$StateDir = '.runtime\\mt5_shadow'" in text
    assert "[string]$PythonExecutable = ''" in text
    assert "MT5 Python executable not found" in text
    assert '-StateDir `"$StateDir`"' in text
    assert '-PythonExecutable `"$PythonExecutable`"' in text
    for forbidden in ("password", "--login", "--password", "order_send", "order_check"):
        assert forbidden not in lower


def test_runtime_check_enforces_no_order_state() -> None:
    text = Path("scripts/check_windows_mt5_shadow_runtime.ps1").read_text(encoding="utf-8")
    assert "execution_capability -ne 'NONE'" in text
    assert "order_execution_enabled -ne $false" in text
    assert "heartbeat.json" in text


def test_uninstaller_preserves_runtime_evidence() -> None:
    text = Path("scripts/uninstall_windows_mt5_shadow_tasks.ps1").read_text(encoding="utf-8")
    lower = text.lower()
    assert "Unregister-ScheduledTask" in text
    assert "runtime state and resume evidence were intentionally kept" in lower
    assert "remove-item" not in lower
