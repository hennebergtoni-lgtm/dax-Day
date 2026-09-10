from pathlib import Path
import runpy


def _module_globals():
    return runpy.run_path("scripts/mt5_windows_host_discovery.py", run_name="not_main")


def test_discovery_is_credential_free_and_no_order(tmp_path: Path):
    root = tmp_path / "repo"
    scripts = root / "scripts"
    scripts.mkdir(parents=True)
    supervisor = scripts / "mt5_shadow_supervisor.py"
    supervisor.write_text("# supervisor\n", encoding="utf-8")

    payload = _module_globals()["collect_host_discovery"](repo_root=root)
    assert payload["repo_root"] == str(root.resolve())
    assert payload["supervisor_exists"] is True
    assert payload["execution_capability"] == "NONE"
    assert payload["order_execution_enabled"] is False
    assert payload["credentials_included"] is False
    assert "login" not in payload
    assert "password" not in payload
    assert "token" not in payload


def test_discovery_reports_missing_supervisor(tmp_path: Path):
    root = tmp_path / "repo"
    root.mkdir()
    payload = _module_globals()["collect_host_discovery"](repo_root=root)
    assert payload["supervisor_exists"] is False


def test_script_has_no_mt5_initialization_or_windows_mutation():
    source = Path("scripts/mt5_windows_host_discovery.py").read_text(encoding="utf-8").lower()
    for forbidden in (
        "order_send",
        "order_check",
        "mt5.initialize",
        "mt5.login",
        "schtasks",
        "register-scheduledtask",
        "subprocess",
    ):
        assert forbidden not in source
