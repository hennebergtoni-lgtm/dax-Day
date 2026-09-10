from pathlib import Path
import runpy


EVALUATE = runpy.run_path(
    "scripts/mt5_host_readiness.py", run_name="not_main"
)["evaluate_host_readiness"]


def _discovery():
    return {
        "platform_system": "Windows",
        "python_exe": r"C:\\Python314\\python.exe",
        "repo_root": r"C:\\dax-Day",
        "supervisor_exists": True,
        "metatrader5_importable": True,
        "execution_capability": "NONE",
        "order_execution_enabled": False,
        "credentials_included": False,
    }


def test_ready_requires_all_host_evidence_and_verified_timezone():
    result = EVALUATE(_discovery(), broker_timezone_verified=True)
    assert result["status"] == "READY"
    assert result["task_registration_allowed"] is True
    assert result["blockers"] == []
    assert result["execution_capability"] == "NONE"
    assert result["order_execution_enabled"] is False


def test_timezone_unverified_blocks_registration():
    result = EVALUATE(_discovery(), broker_timezone_verified=False)
    assert result["status"] == "BLOCKED"
    assert result["task_registration_allowed"] is False
    assert "BROKER_TIMEZONE_UNVERIFIED" in result["blockers"]


def test_missing_mt5_or_supervisor_blocks_registration():
    discovery = _discovery()
    discovery["metatrader5_importable"] = False
    discovery["supervisor_exists"] = False
    result = EVALUATE(discovery, broker_timezone_verified=True)
    assert "METATRADER5_NOT_IMPORTABLE" in result["blockers"]
    assert "SUPERVISOR_NOT_FOUND" in result["blockers"]


def test_non_windows_and_any_order_capability_block():
    discovery = _discovery()
    discovery["platform_system"] = "Linux"
    discovery["execution_capability"] = "PAPER"
    discovery["order_execution_enabled"] = True
    result = EVALUATE(discovery, broker_timezone_verified=True)
    assert result["task_registration_allowed"] is False
    assert "WINDOWS_HOST_NOT_VERIFIED" in result["blockers"]
    assert "EXECUTION_CAPABILITY_NOT_NONE" in result["blockers"]
    assert "ORDER_EXECUTION_NOT_FALSE" in result["blockers"]


def test_module_has_no_host_mutation_or_order_api():
    source = Path("scripts/mt5_host_readiness.py").read_text(encoding="utf-8").lower()
    for forbidden in (
        "order_send",
        "order_check",
        "schtasks",
        "register-scheduledtask",
        "subprocess",
        "mt5.initialize",
    ):
        assert forbidden not in source
