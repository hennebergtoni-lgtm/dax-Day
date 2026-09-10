from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys

import pytest


_MODULE_PATH = Path("scripts/mt5_shadow_task_spec.py")
_MODULE_NAME = "mt5_shadow_task_spec"
_SPEC = spec_from_file_location(_MODULE_NAME, _MODULE_PATH)
assert _SPEC is not None and _SPEC.loader is not None
_MODULE = module_from_spec(_SPEC)
sys.modules[_MODULE_NAME] = _MODULE
_SPEC.loader.exec_module(_MODULE)
build_windows_shadow_task_spec = _MODULE.build_windows_shadow_task_spec


def _host_layout(tmp_path: Path):
    root = tmp_path / "repo"
    scripts = root / "scripts"
    scripts.mkdir(parents=True)
    (scripts / "mt5_shadow_supervisor.py").write_text("# supervisor\n", encoding="utf-8")
    python = tmp_path / "python.exe"
    python.write_text("binary-placeholder", encoding="utf-8")
    return root, python


def test_task_spec_is_logon_bound_and_no_order(tmp_path: Path):
    root, python = _host_layout(tmp_path)
    spec = build_windows_shadow_task_spec(
        repo_root=str(root),
        python_exe=str(python),
        broker_timezone="Europe/Berlin",
    )
    payload = spec.to_payload()
    assert payload["trigger"] == "AT_LOGON"
    assert payload["run_only_when_user_logged_on"] is True
    assert payload["multiple_instances"] == "IGNORE_NEW"
    assert payload["start_when_available"] is True
    assert payload["allow_start_if_on_batteries"] is True
    assert payload["dont_stop_if_going_on_batteries"] is True
    assert payload["execution_time_limit_seconds"] == 0
    assert payload["restart_interval_minutes"] == 1
    assert payload["restart_count"] == 999
    assert payload["startup_delay_seconds"] == 60
    assert payload["execution_capability"] == "NONE"
    assert payload["order_execution_enabled"] is False
    assert payload["state_directory"].endswith(str(Path(".runtime") / "mt5_shadow"))


def test_task_spec_matches_installer_core_settings():
    installer = Path("scripts/install_windows_mt5_shadow_task.ps1").read_text(
        encoding="utf-8"
    )
    assert "-StartWhenAvailable" in installer
    assert "-AllowStartIfOnBatteries" in installer
    assert "-DontStopIfGoingOnBatteries" in installer
    assert "-MultipleInstances IgnoreNew" in installer
    assert "-RestartCount 999" in installer
    assert "-RestartInterval (New-TimeSpan -Minutes 1)" in installer
    assert "-ExecutionTimeLimit ([TimeSpan]::Zero)" in installer


def test_task_spec_requires_explicit_broker_timezone(tmp_path: Path):
    root, python = _host_layout(tmp_path)
    with pytest.raises(ValueError, match="broker_timezone"):
        build_windows_shadow_task_spec(
            repo_root=str(root), python_exe=str(python), broker_timezone="  "
        )


def test_task_spec_rejects_missing_python(tmp_path: Path):
    root, _ = _host_layout(tmp_path)
    with pytest.raises(ValueError, match="python_exe"):
        build_windows_shadow_task_spec(
            repo_root=str(root),
            python_exe=str(tmp_path / "missing.exe"),
            broker_timezone="Europe/Berlin",
        )


def test_task_spec_rejects_wrong_repo_root(tmp_path: Path):
    root = tmp_path / "repo"
    root.mkdir()
    python = tmp_path / "python.exe"
    python.write_text("binary-placeholder", encoding="utf-8")
    with pytest.raises(ValueError, match="mt5_shadow_supervisor"):
        build_windows_shadow_task_spec(
            repo_root=str(root),
            python_exe=str(python),
            broker_timezone="Europe/Berlin",
        )


def test_module_has_no_task_mutation_or_order_api():
    source = _MODULE_PATH.read_text(encoding="utf-8").lower()
    for forbidden in (
        "order_send",
        "order_check",
        "schtasks",
        "register-scheduledtask",
        "start-scheduledtask",
        "stop-scheduledtask",
        "unregister-scheduledtask",
    ):
        assert forbidden not in source
