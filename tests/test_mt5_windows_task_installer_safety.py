from pathlib import Path


INSTALLER = Path("scripts/install_windows_mt5_shadow_task.ps1")
STARTER = Path("scripts/windows_mt5_shadow_start.ps1")


def test_installer_requires_explicit_broker_timezone_and_interactive_logon():
    source = INSTALLER.read_text(encoding="utf-8")
    assert "[Parameter(Mandatory = $true)]" in source
    assert "[string]$BrokerTimezone" in source
    assert "-LogonType Interactive" in source
    assert "-RunLevel Limited" in source
    assert "-MultipleInstances IgnoreNew" in source


def test_installer_does_not_embed_credentials_or_order_api():
    source = INSTALLER.read_text(encoding="utf-8").lower()
    for forbidden in (
        "order_send",
        "order_check",
        "--login",
        "--password",
        "account_password",
        "metatrader5.initialize",
    ):
        assert forbidden not in source
    assert "execution_capability=none" in source
    assert "order_execution_enabled=false" in source


def test_start_wrapper_uses_dedicated_venv_and_no_order_mode():
    source = STARTER.read_text(encoding="utf-8")
    assert ".venv-mt5\\Scripts\\python.exe" in source
    assert "mt5_shadow_supervisor.py" in source
    assert "--broker-timezone $BrokerTimezone" in source
    assert "Execution: NONE / NO_ORDER" in source


def test_installer_never_claims_timezone_verification():
    source = INSTALLER.read_text(encoding="utf-8").lower()
    assert "broker_timezone_verified=true" not in source
    assert "timezone verified" not in source
