from pathlib import Path

import pytest

from scripts.mt5_shadow_task_spec import build_windows_shadow_task_spec


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
    assert payload["restart_interval_minutes"] == 5
    assert payload["restart_count"] == 3
    assert payload["startup_delay_seconds"] == 60
    assert payload["execution_capability"] == "NONE"
    assert payload["order_execution_enabled"] is False
    assert payload["state_directory"].endswith(str(Path(".runtime") / "mt5_shadow"))


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
    source = Path("scripts/mt5_shadow_task_spec.py").read_text(encoding="utf-8").lower()
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
