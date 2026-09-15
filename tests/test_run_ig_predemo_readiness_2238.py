from __future__ import annotations

import importlib.util
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location(
    "ig_predemo_runner_test", SCRIPTS / "run_ig_predemo_readiness_2238.py"
)
assert SPEC and SPEC.loader
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


def _price_row(open_time: datetime, value: float) -> dict[str, object]:
    return {
        "snapshotTimeUTC": open_time.isoformat(),
        "openPrice": {"bid": value, "ask": value + 2},
        "highPrice": {"bid": value + 4, "ask": value + 6},
        "lowPrice": {"bid": value - 4, "ask": value - 2},
        "closePrice": {"bid": value + 1, "ask": value + 3},
    }


def test_inventory_bracket_hashes_identifiers_and_detects_foreign_inventory() -> None:
    positions = {"positions": [{
        "position": {"dealId": "SECRET-DEAL", "direction": "BUY", "size": 1},
        "market": {"epic": "IX.D.DAX.IFMM.IP"},
    }]}
    orders = {"workingOrders": []}
    first = runner._inventory_view(positions, orders)
    second = runner._inventory_view(positions, orders)
    assert first == second
    assert first["positions"][0]["deal_fingerprint"] != "SECRET-DEAL"
    assert "SECRET-DEAL" not in repr(first)


def test_market_v4_does_not_infer_tick_or_quantity_grid_from_digits() -> None:
    market = runner._market_view(
        {
            "instrument": {
                "epic": "IX.D.DAX.IFMM.IP",
                "type": "INDICES",
                "unit": "CONTRACTS",
                "valueOfOnePip": "1.0",
            },
            "dealingRules": {
                "minDealSize": {"value": 1, "unit": "POINTS"},
                "minNormalStopOrLimitDistance": {"value": 5, "unit": "POINTS"},
                "maxStopOrLimitDistance": {"value": 1000, "unit": "POINTS"},
            },
            "snapshot": {
                "marketStatus": "TRADEABLE",
                "bid": "20000.0",
                "ask": "20002.0",
                "decimalPlacesFactor": 1,
                "scalingFactor": 1,
                "updateTimestampUTC": 1789466400,
            },
        },
        epic="IX.D.DAX.IFMM.IP",
        observed_at=runner.datetime(2026, 9, 15, 10, 0, 1, tzinfo=runner.timezone.utc),
    )
    assert market["quantity_min"] == 1.0
    assert market["tick_size"] is None
    assert market["quantity_step"] is None and market["quantity_max"] is None
    assert market["economics_verified"] is False
    assert market["native_stop_constraints_verified"] is True


def test_windows_wrapper_is_exact_head_isolated_get_only_and_non_destructive() -> None:
    source = (SCRIPTS / "run_ig_predemo_readiness_2238.ps1").read_text(encoding="utf-8")
    owner = (SCRIPTS / "dax_windows_host_lane.psm1").read_text(encoding="utf-8")
    assert "dax_windows_host_lane.psm1" in source
    assert "Invoke-DaxHostJsonProcess" in source
    assert "clone --quiet --no-checkout --no-hardlinks" in source
    assert "checkout --quiet --detach" in source
    assert "'--runtime-root', $RuntimeRoot" in source
    assert "existing checkout remains untouched" in source
    assert "worktree add" not in source and "worktree prune" not in source
    assert "'reset'" not in source and "'stash'" not in source
    assert "'merge'" not in source and "'clean'" not in source
    assert "--force" not in source
    assert "order_send" not in source + owner and "/positions/otc" not in source + owner
    assert "DAX_STEP2238_DEPLOYMENT_OWNER_V1" in source
    assert "SUMMARY: BLOCKED / FAIL_CLOSED; error_code=" in source


def test_windows_wrapper_preflights_exact_interpreter_and_import_origins() -> None:
    source = (SCRIPTS / "run_ig_predemo_readiness_2238.ps1").read_text(encoding="utf-8")
    owner = (SCRIPTS / "dax_windows_host_lane.psm1").read_text(encoding="utf-8")
    for error_code in (
        "PYTHON_COMMAND_DISCOVERY_FAILED",
        "PYTHON_COMMAND_RESULT_NULL",
        "PYTHON_COMMAND_RESULT_MULTIPLE",
        "PYTHON_EXECUTABLE_PATH_FAILED",
        "HOST_LANE_SCRIPT_MISSING",
        "HOST_LANE_PROCESS_START_FAILED",
        "HOST_LANE_PROCESS_NO_OUTPUT",
        "HOST_LANE_PROCESS_MULTILINE_OUTPUT",
        "HOST_LANE_PROCESS_JSON_INVALID",
        "HOST_LANE_PROCESS_RESULT_INVALID",
        "HOST_LANE_PROCESS_EXIT_MISMATCH",
        "PREFLIGHT_REQUIRED_CHECK_FAILED",
        "HOST_LANE_INTERNAL_FAILURE",
    ):
        assert f"'{error_code}'" in source
    assert "-CommandType Application" in owner
    assert "-I -S" not in owner
    assert "Get-HostLaneProperty" in owner
    assert "Write-DaxHostPreflight" in owner
    assert "PYTHON_START_FAILED" not in source
    assert "PYTHON_RESULT_INVALID" not in source
    assert owner.count("2>$null") == 1


def test_python_runtime_failure_injection_is_executable_when_pwsh_exists() -> None:
    pwsh = shutil.which("pwsh")
    if pwsh is None:
        return
    completed = subprocess.run(
        [
            pwsh,
            "-NoProfile",
            "-File",
            str(ROOT / "tests/powershell/dax_windows_host_lane_failure_injection.ps1"),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "DAX Windows host lane failure injection: OK" in completed.stdout


def test_collector_brackets_inventory_and_preserves_unknown_economics(monkeypatch) -> None:
    now = datetime(2026, 9, 15, 9, 2, 59, tzinfo=timezone.utc)

    class FixedClock(datetime):
        @classmethod
        def now(cls, tz=None):
            return now.astimezone(tz)

    class Client:
        login_context = {
            "environment": "IG_DEMO",
            "currency": "EUR",
            "account_context_fingerprint": "b" * 64,
            "timezone_offset_hours": 1.0,
        }
        read_observations = ()

        def accounts(self):
            return {"accounts": [{"accountType": "CFD", "currency": "EUR"}]}

        def positions(self):
            return {"positions": []}

        def working_orders(self):
            return {"workingOrders": []}

        def market_v4(self, epic):
            return {
                "instrument": {"epic": epic, "type": "INDICES", "unit": "CONTRACTS"},
                "dealingRules": {
                    "minDealSize": {"value": 1, "unit": "POINTS"},
                    "minNormalStopOrLimitDistance": {"value": 5, "unit": "POINTS"},
                    "maxStopOrLimitDistance": {"value": 1000, "unit": "POINTS"},
                },
                "snapshot": {"marketStatus": "TRADEABLE", "bid": 100, "ask": 102},
            }

        def account_activity(self, **kwargs):
            return {"activities": [], "metadata": {"paging": {}}}

        def m5_prices(self, epic, *, max_bars):
            start = datetime(2026, 9, 15, 8, 20, tzinfo=timezone.utc)
            return {
                "prices": [_price_row(start + timedelta(minutes=5 * i), 100 + i) for i in range(9)],
                "metadata": {"pageData": {"totalPages": 1}},
            }

    monkeypatch.setattr(runner, "datetime", FixedClock)
    evidence, components = runner.collect(
        Client(), epic="IX.D.DAX.IFMM.IP", instrument_id="DAX", bars=40
    )
    assert evidence["inventory"]["stable_across_bracket"] is True
    assert evidence["inventory"]["foreign_or_manual_inventory_present"] is False
    assert evidence["inventory"]["history_scope_complete"] is True
    assert evidence["market_data"]["fresh"] is True
    assert evidence["market"]["tick_size"] is None
    assert evidence["market"]["economics_verified"] is False
    assert evidence["execution_capability"] == "NONE"
    assert evidence["order_execution_enabled"] is False
    assert set(components) == {
        "ACCOUNT.json", "INVENTORY.json", "MARKET.json", "CLOCK.json", "HISTORY_SCOPE.json"
    }


def test_publication_is_exclusive_and_manifest_hashes_summary(tmp_path) -> None:
    evidence = {
        "schema": runner.SCHEMA,
        "fingerprint": "c" * 64,
        "execution_capability": "NONE",
        "order_execution_enabled": False,
    }
    namespace = tmp_path / ".runtime" / "attempt"
    runner._publish(namespace, evidence, {}, head="d" * 40)
    manifest = json.loads((namespace / "MANIFEST.json").read_text())
    assert "SUMMARY.json" in manifest["files"]
    assert manifest["execution_capability"] == "NONE"
    try:
        runner._publish(namespace, evidence, {}, head="d" * 40)
    except FileExistsError:
        pass
    else:
        raise AssertionError("existing evidence namespace was overwritten")


def test_publication_failure_removes_only_owned_staging(tmp_path, monkeypatch) -> None:
    evidence = {
        "schema": runner.SCHEMA,
        "fingerprint": "c" * 64,
        "execution_capability": "NONE",
        "order_execution_enabled": False,
    }
    namespace = tmp_path / ".runtime" / "attempt"
    original = runner.json.dumps

    def fail_on_readiness(value, *args, **kwargs):
        if isinstance(value, dict) and value.get("schema") == runner.SCHEMA:
            raise OSError("injected publication failure")
        return original(value, *args, **kwargs)

    monkeypatch.setattr(runner.json, "dumps", fail_on_readiness)
    with pytest.raises(OSError):
        runner._publish(namespace, evidence, {}, head="d" * 40)
    assert not namespace.exists()
    assert not list(namespace.parent.glob(".attempt.partial-*"))


def test_collector_runtime_path_failure_has_fixed_code(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.setattr(sys, "argv", [
        "run_ig_predemo_readiness_2238.py",
        "--expected-head", "d" * 40,
        "--credentials-file", str(tmp_path / "credentials.env"),
        "--runtime-root", str(tmp_path / "missing"),
        "--namespace", ".runtime/attempt",
    ])
    assert runner.main() == 2
    result = json.loads(capsys.readouterr().out)
    assert result["error_code"] == "STATE_RUNTIME_ROOT_UNAVAILABLE"
    assert result["execution_capability"] == "NONE"
    assert result["order_execution_enabled"] is False


def test_collector_head_query_failure_has_fixed_code(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.setattr(sys, "argv", [
        "run_ig_predemo_readiness_2238.py",
        "--expected-head", "d" * 40,
        "--credentials-file", str(tmp_path / "credentials.env"),
        "--runtime-root", str(tmp_path),
        "--namespace", ".runtime/attempt",
    ])
    monkeypatch.setattr(runner, "_head", lambda: (_ for _ in ()).throw(OSError("secret")))
    assert runner.main() == 2
    rendered = capsys.readouterr().out
    result = json.loads(rendered)
    assert result["error_code"] == "HEAD_QUERY_FAILED"
    assert "secret" not in rendered
