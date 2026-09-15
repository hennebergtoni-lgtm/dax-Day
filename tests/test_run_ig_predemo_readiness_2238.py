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


def _assert_authenticated_matrix(payload: dict[str, object]) -> None:
    assert payload["login_success"] is True
    assert payload["readiness_matrix_row_count"] == 8
    rows = payload["readiness_matrix"]
    assert isinstance(rows, list) and len(rows) == 8
    assert [row["resource"] for row in rows] == [
        resource for resource, _ in runner.READ_RESOURCE_CONTRACTS
    ]


class MatrixClient:
    def __init__(
        self,
        *,
        raise_resource: str | None = None,
        invalid_resource: str | None = None,
        lose_auth_resource: str | None = None,
    ) -> None:
        self.raise_resource = raise_resource
        self.invalid_resource = invalid_resource
        self.lose_auth_resource = lose_auth_resource
        self.calls: list[str] = []
        self._authenticated = True
        self.login_calls = 0
        self.logout_calls = 0
        self._login_context = {
            "environment": "IG_DEMO",
            "currency": "EUR",
            "account_context_fingerprint": "b" * 64,
            "timezone_offset_hours": 1.0,
        }

    @property
    def login_context(self):
        return self._login_context

    @property
    def authenticated(self) -> bool:
        return self._authenticated

    def login(self):
        self.login_calls += 1
        self._authenticated = True

    def logout(self):
        self.logout_calls += 1
        self._authenticated = False

    def _result(self, resource: str, endpoint: str, payload: dict[str, object]):
        self.calls.append(resource)
        if resource == self.lose_auth_resource:
            self._authenticated = False
        if resource == self.raise_resource:
            raise OSError("credential-and-account-secret")
        if resource == self.invalid_resource:
            return {"unsafe": "credential-and-account-secret"}
        now = datetime(2026, 9, 15, 9, 2, 59, tzinfo=timezone.utc)
        return runner.IgReadinessRead(
            resource=resource,
            endpoint_family=endpoint,
            status="PASS",
            reason_code="NONE",
            response_shape_status="VALID",
            request_started_at=now,
            response_observed_at=now,
            http_status_class="HTTP_2XX",
            provider_error_code=None,
            request_id_fingerprint=None,
            server_date_utc=now,
            payload=payload,
        )

    def readiness_accounts(self):
        return self._result("ACCOUNTS", "ACCOUNTS_V1", {"accounts": []})

    def readiness_positions(self, resource):
        return self._result(resource, "POSITIONS_V2", {"positions": []})

    def readiness_working_orders(self, resource):
        return self._result(resource, "WORKING_ORDERS_V2", {"workingOrders": []})

    def readiness_market_v4(self, epic):
        return self._result(
            "MARKET_V4",
            "MARKET_V4",
            {
                "instrument": {"epic": epic, "type": "INDICES", "unit": "CONTRACTS"},
                "dealingRules": {
                    "minDealSize": {"value": 1, "unit": "POINTS"},
                    "minNormalStopOrLimitDistance": {"value": 5, "unit": "POINTS"},
                    "maxStopOrLimitDistance": {"value": 1000, "unit": "POINTS"},
                },
                "snapshot": {"marketStatus": "TRADEABLE", "bid": 100, "ask": 102},
            },
        )

    def readiness_account_activity(self, **kwargs):
        return self._result(
            "ACTIVITY_HISTORY",
            "ACTIVITY_HISTORY_V3",
            {"activities": [], "metadata": {"paging": {}}},
        )

    def readiness_m5_prices(self, epic, *, max_bars):
        start = datetime(2026, 9, 15, 8, 20, tzinfo=timezone.utc)
        return self._result(
            "M5_PRICES",
            "PRICES_V3",
            {
                "prices": [
                    _price_row(start + timedelta(minutes=5 * index), 100 + index)
                    for index in range(9)
                ],
                "metadata": {"pageData": {"totalPages": 1}},
            },
        )


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
    assert "dax_windows_python_runtime_probe.py" in owner
    assert "Invoke-DaxHostJsonProcess" in source
    assert "Write-IgReadinessMatrix" in source
    assert "request_started_at_utc" in source and "response_observed_at_utc" in source
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
    assert "MaterializedPath = $materializedPath" in source
    assert "[System.IO.File]::Delete([string]$ownerContext.MaterializedPath)" in source
    assert source.index("[System.IO.File]::Delete([string]$ownerContext.MaterializedPath)") < source.index(
        "Test-RunnerOwnedDeployment -TemporaryRoot $temporaryRoot", source.index("} finally {")
    )
    assert "SUMMARY: BLOCKED / FAIL_CLOSED; error_code=" in source
    assert source.index("COLLECTOR PRECHECK:") < source.index("AUTH READ-ONLY START:")


def test_windows_wrapper_preflights_exact_interpreter_and_import_origins() -> None:
    source = (SCRIPTS / "run_ig_predemo_readiness_2238.ps1").read_text(encoding="utf-8")
    owner = (SCRIPTS / "dax_windows_host_lane.psm1").read_text(encoding="utf-8")
    for error_code in (
        "PYTHON_COMMAND_DISCOVERY_FAILED",
        "PYTHON_COMMAND_RESULT_NULL",
        "PYTHON_RUNTIME_AMBIGUOUS",
        "PYTHON_RUNTIME_NO_VALID_CANDIDATE",
        "PYTHON_RUNTIME_PROBE_MISSING",
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
    assert "PYTHON_CANDIDATE_STORE_ALIAS_REJECTED" in owner
    assert "identity_fingerprint" in owner
    assert "-I -S" not in owner
    assert "Get-HostLaneProperty" in owner
    assert "Write-DaxHostPreflight" in owner
    assert "PYTHON_START_FAILED" not in source
    assert "PYTHON_RESULT_INVALID" not in source
    # Candidate probes and the final payload both suppress raw stderr.
    assert owner.count("2>$null") == 2
    for error_code in runner.ERROR_CODES:
        assert f"'{error_code}'" in source
    assert "HostLaneProcessExitContract" in owner
    assert "FailurePhase" in source
    assert "payload_failure_phase=" in source
    assert "process_exit_contract=" in source
    assert "$errorCode = if ($primaryErrorCode)" in source


def test_windows_runtime_owner_has_classified_preimport_contract() -> None:
    source = (SCRIPTS / "run_ig_predemo_readiness_2238.ps1").read_text(encoding="utf-8")
    owner = (SCRIPTS / "dax_windows_host_lane.psm1").read_text(encoding="ascii")
    workflow = (ROOT / ".github/workflows/windows-host-lane-ci.yml").read_text(
        encoding="utf-8"
    )
    import_test = (
        ROOT / "tests/powershell/dax_windows_module_import_contract.ps1"
    ).read_text(encoding="ascii")

    for error_code in (
        "MODULE_FILE_MISSING",
        "MODULE_PARSE_FAILED",
        "MODULE_VERSION_INCOMPATIBLE",
        "MODULE_IMPORT_EXCEPTION",
        "MODULE_EXPORT_CONTRACT_FAILED",
    ):
        assert f"'{error_code}'" in source
    assert "HOST_RUNTIME_OWNER_IMPORT_FAILED" not in source
    assert "function Import-DaxHostRuntimeOwner" in source
    assert source.index("Parser]::ParseFile") < source.index(
        "Import-Module -Name $materializedPath"
    )
    assert source.index("Import-Module -Name $materializedPath") < source.index(
        "Get-Command -Name $registeredName"
    )
    assert source.index("Import-DaxHostRuntimeOwner") < source.index("Resolve-DaxHostPython")
    assert "path=HASH_VERIFIED_RUNNER_OWNED_COPY" in source
    assert "dependencies=NONE" in source
    assert "MODULE_DIAGNOSTIC:" in source
    assert "module_file_sha256" in source
    assert "path_fingerprint" in source
    assert "fully_qualified_error_id" in source
    assert "language_mode" in source and "execution_policy" in source
    assert "security_marker" in source
    assert "RUNNER_OWNED_HASH_VERIFIED_MODULE_COPY" in source
    assert "UNIQUE_PER_RUN" in source
    assert "Import-Module -Name $materializedPath -Global -Prefix $prefix" in source
    assert "Remove-Module -ModuleInfo $ownerContext.Module" in source
    assert "MODULE_INITIALIZATION_OR_COMMAND_REGISTRATION" in source
    assert "MODULE_MATERIALIZATION" in source
    assert "LANGUAGE_MODE" in source
    assert "EXPORT_DISCOVERY_OR_COMMAND_REGISTRATION" in source
    import_boundary = source[
        source.index("function Import-DaxHostRuntimeOwner"):
        source.index("function Invoke-Closeout")
    ]
    assert "Write-Host $_" not in import_boundary
    assert "Write-Output $_" not in import_boundary
    assert owner.startswith("#requires -Version 5.1\n")
    assert max(owner.encode("ascii")) < 128

    assert "shell: powershell" in workflow
    assert "Windows PowerShell 5.1 exact module import contract" in workflow
    assert "tests/powershell/dax_windows_module_import_contract.ps1" in workflow
    assert "PowerShell 7 compatibility" in workflow
    for contract in (
        "ParseFile",
        "Import-Module -Name $fullPath",
        "ExportedFunctions.Keys",
        "unicode-",
        "host lane lf.psm1",
        "host lane crlf.psm1",
        "bounded-long-path-segment",
    ):
        assert contract in import_test


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
        def result(self, resource, payload, endpoint):
            return runner.IgReadinessRead(
                resource=resource,
                endpoint_family=endpoint,
                status="PASS",
                reason_code="NONE",
                response_shape_status="VALID",
                request_started_at=now,
                response_observed_at=now,
                http_status_class="HTTP_2XX",
                provider_error_code=None,
                request_id_fingerprint=None,
                server_date_utc=now,
                payload=payload,
            )

        def readiness_accounts(self):
            return self.result("ACCOUNTS", {"accounts": [{"accountType": "CFD", "currency": "EUR"}]}, "ACCOUNTS_V1")

        def readiness_positions(self, resource):
            return self.result(resource, {"positions": []}, "POSITIONS_V2")

        def readiness_working_orders(self, resource):
            return self.result(resource, {"workingOrders": []}, "WORKING_ORDERS_V2")

        def readiness_market_v4(self, epic):
            return self.result("MARKET_V4", {
                "instrument": {"epic": epic, "type": "INDICES", "unit": "CONTRACTS"},
                "dealingRules": {
                    "minDealSize": {"value": 1, "unit": "POINTS"},
                    "minNormalStopOrLimitDistance": {"value": 5, "unit": "POINTS"},
                    "maxStopOrLimitDistance": {"value": 1000, "unit": "POINTS"},
                },
                "snapshot": {"marketStatus": "TRADEABLE", "bid": 100, "ask": 102},
            }, "MARKET_V4")

        def readiness_account_activity(self, **kwargs):
            return self.result("ACTIVITY_HISTORY", {"activities": [], "metadata": {"paging": {}}}, "ACTIVITY_HISTORY_V3")

        def readiness_m5_prices(self, epic, *, max_bars):
            start = datetime(2026, 9, 15, 8, 20, tzinfo=timezone.utc)
            return self.result("M5_PRICES", {
                "prices": [_price_row(start + timedelta(minutes=5 * i), 100 + i) for i in range(9)],
                "metadata": {"pageData": {"totalPages": 1}},
            }, "PRICES_V3")

    monkeypatch.setattr(runner, "datetime", FixedClock)
    evidence, components = runner.collect(
        Client(), epic="IX.D.DAX.IFMM.IP", instrument_id="DAX", bars=40
    )
    assert evidence["inventory"]["stable_across_bracket"] is True
    assert evidence["inventory"]["foreign_or_manual_inventory_present"] is False
    assert evidence["history_scope"]["scope_complete"] is True
    assert evidence["market_data"]["fresh"] is True
    assert evidence["market"]["tick_size"] is None
    assert evidence["market"]["economics_verified"] is False
    assert evidence["execution_capability"] == "NONE"
    assert evidence["order_execution_enabled"] is False
    assert evidence["authenticated_read_matrix"]["counts"]["PASS"] == 8
    assert set(components) == {"READ_MATRIX.json", "ACCOUNT.json", "INVENTORY.json",
                               "MARKET.json", "CLOCK.json", "HISTORY_SCOPE.json"}


@pytest.mark.parametrize(
    "failed_resource", [resource for resource, _ in runner.READ_RESOURCE_CONTRACTS]
)
def test_outer_guard_keeps_all_eight_rows_for_every_resource_exception(
    failed_resource: str,
) -> None:
    client = MatrixClient(raise_resource=failed_resource)
    raw_rows = runner._initial_readiness_rows()
    evidence, _ = runner.collect(
        client,
        epic="IX.D.DAX.IFMM.IP",
        instrument_id="DAX",
        bars=40,
        raw_rows=raw_rows,
    )
    matrix = evidence["authenticated_read_matrix"]
    assert matrix["row_count"] == 8
    assert len(matrix["resources"]) == 8
    failed = next(row for row in matrix["resources"] if row["resource"] == failed_resource)
    assert failed["status"] == "UNKNOWN"
    assert failed["reason_code"] == f"IG_READ_{failed_resource}_UNCLASSIFIED"
    assert len(client.calls) == 8
    assert "credential-and-account-secret" not in json.dumps(evidence)


@pytest.mark.parametrize(
    "invalid_resource", [resource for resource, _ in runner.READ_RESOURCE_CONTRACTS]
)
def test_outer_guard_normalizes_every_invalid_resource_result(
    invalid_resource: str,
) -> None:
    client = MatrixClient(invalid_resource=invalid_resource)
    evidence, _ = runner.collect(
        client, epic="IX.D.DAX.IFMM.IP", instrument_id="DAX", bars=40
    )
    matrix = evidence["authenticated_read_matrix"]
    row = next(item for item in matrix["resources"] if item["resource"] == invalid_resource)
    assert matrix["row_count"] == 8
    assert row["status"] == "UNKNOWN"
    assert row["reason_code"] == f"IG_READ_{invalid_resource}_UNCLASSIFIED"
    assert len(client.calls) == 8
    assert "credential-and-account-secret" not in json.dumps(evidence)


def test_definitive_auth_loss_blocks_remaining_rows_without_erasing_matrix() -> None:
    client = MatrixClient(lose_auth_resource="MARKET_V4")
    evidence, _ = runner.collect(
        client, epic="IX.D.DAX.IFMM.IP", instrument_id="DAX", bars=40
    )
    matrix = evidence["authenticated_read_matrix"]
    assert matrix["row_count"] == 8
    assert client.calls == ["ACCOUNTS", "POSITIONS_A", "WORKING_ORDERS_A", "MARKET_V4"]
    assert [row["status"] for row in matrix["resources"][4:]] == [
        "BLOCKED", "BLOCKED", "BLOCKED", "BLOCKED"
    ]
    assert {row["reason_code"] for row in matrix["resources"][4:]} == {
        "IG_READ_AUTH_PRECONDITION_BLOCKED"
    }


def test_unreadable_auth_health_is_not_misclassified_as_definitive_loss() -> None:
    class Client(MatrixClient):
        @property
        def authenticated(self):
            raise RuntimeError("credential-and-account-secret")

    client = Client()
    evidence, _ = runner.collect(
        client, epic="IX.D.DAX.IFMM.IP", instrument_id="DAX", bars=40
    )
    assert evidence["authenticated_read_matrix"]["row_count"] == 8
    assert len(client.calls) == 8


@pytest.mark.parametrize(
    ("stage", "target"),
    (
        ("MATRIX_CONSTRUCTION", "_matrix_from_rows"),
        ("INVENTORY", "_inventory_view"),
        ("MARKET_ECONOMICS", "_market_view"),
        ("M5", "_closed_candles"),
        ("CLOCK", "_clock_projection"),
        ("DEPENDENT_CONCLUSIONS", "_dependent_projection"),
        ("COMPONENT_CONSTRUCTION", "_build_components"),
    ),
)
def test_each_derived_processing_exception_preserves_raw_eight_row_matrix(
    monkeypatch, stage: str, target: str
) -> None:
    def fail(*args, **kwargs):
        raise RuntimeError("credential-and-account-secret")

    monkeypatch.setattr(runner, target, fail)
    evidence, _ = runner.collect(
        MatrixClient(), epic="IX.D.DAX.IFMM.IP", instrument_id="DAX", bars=40
    )
    assert evidence["authenticated_read_matrix"]["row_count"] == 8
    assert evidence["authenticated_read_matrix"]["counts"]["PASS"] == 8
    assert evidence["derived_processing"][stage]["status"] == "BLOCKED"
    assert evidence["derived_processing_complete"] is False
    assert "credential-and-account-secret" not in json.dumps(evidence)


def test_login_context_projection_exception_preserves_raw_eight_row_matrix() -> None:
    class Client(MatrixClient):
        @property
        def login_context(self):
            raise RuntimeError("credential-and-account-secret")

    evidence, _ = runner.collect(
        Client(), epic="IX.D.DAX.IFMM.IP", instrument_id="DAX", bars=40
    )
    assert evidence["authenticated_read_matrix"]["row_count"] == 8
    assert evidence["authenticated_read_matrix"]["counts"]["PASS"] == 8
    assert evidence["derived_processing"]["LOGIN_CONTEXT"]["status"] == "BLOCKED"


def test_history_projection_exception_preserves_raw_eight_row_matrix() -> None:
    class Client(MatrixClient):
        def readiness_account_activity(self, **kwargs):
            return self._result(
                "ACTIVITY_HISTORY",
                "ACTIVITY_HISTORY_V3",
                {"activities": "wrong-type", "metadata": {"paging": {}}},
            )

    evidence, _ = runner.collect(
        Client(), epic="IX.D.DAX.IFMM.IP", instrument_id="DAX", bars=40
    )
    assert evidence["authenticated_read_matrix"]["row_count"] == 8
    assert evidence["authenticated_read_matrix"]["counts"]["PASS"] == 8
    assert evidence["derived_processing"]["HISTORY"]["status"] == "BLOCKED"


@pytest.mark.parametrize(
    ("target", "expected_phase", "expected_code"),
    (
        ("_finalize_evidence", "EVIDENCE", "EVIDENCE_INVALID"),
        ("_publish", "PUBLISH", "EVIDENCE_PUBLICATION_FAILED"),
    ),
)
def test_post_read_failure_always_emits_raw_eight_row_matrix(
    tmp_path, monkeypatch, capsys, target: str, expected_phase: str, expected_code: str
) -> None:
    client = MatrixClient()
    monkeypatch.setattr(sys, "argv", [
        "run_ig_predemo_readiness_2238.py",
        "--expected-head", "d" * 40,
        "--credentials-file", str(tmp_path / "credentials.env"),
        "--runtime-root", str(tmp_path),
        "--namespace", ".runtime/attempt",
    ])
    monkeypatch.setattr(runner, "_head", lambda: "d" * 40)
    monkeypatch.setattr(runner, "_credentials_from_file", lambda _: object())
    monkeypatch.setattr(runner, "IgDemoReadOnlyClient", lambda _: client)

    def fail(*args, **kwargs):
        raise OSError("credential-and-account-secret")

    monkeypatch.setattr(runner, target, fail)
    assert runner.main() == 2
    rendered = capsys.readouterr().out
    result = json.loads(rendered)
    assert result["failure_phase"] == expected_phase
    assert result["error_code"] == expected_code
    _assert_authenticated_matrix(result)
    assert result["readiness_matrix_counts"]["PASS"] == 8
    assert client.login_calls == 1 and client.logout_calls == 1
    assert "credential-and-account-secret" not in rendered


def test_matrix_builder_failure_after_login_still_emits_exactly_eight_rows(
    tmp_path, monkeypatch, capsys
) -> None:
    client = MatrixClient()
    monkeypatch.setattr(sys, "argv", [
        "run_ig_predemo_readiness_2238.py",
        "--expected-head", "d" * 40,
        "--credentials-file", str(tmp_path / "credentials.env"),
        "--runtime-root", str(tmp_path),
        "--namespace", ".runtime/attempt",
    ])
    monkeypatch.setattr(runner, "_head", lambda: "d" * 40)
    monkeypatch.setattr(runner, "_credentials_from_file", lambda _: object())
    monkeypatch.setattr(runner, "IgDemoReadOnlyClient", lambda _: client)
    monkeypatch.setattr(
        runner,
        "_matrix_from_rows",
        lambda *_: (_ for _ in ()).throw(RuntimeError("credential-and-account-secret")),
    )
    assert runner.main() == 2
    rendered = capsys.readouterr().out
    result = json.loads(rendered)
    _assert_authenticated_matrix(result)
    assert result["readiness_matrix_counts"]["PASS"] == 8
    assert "credential-and-account-secret" not in rendered


def test_emergency_matrix_drops_corrupt_row_instead_of_leaking_it() -> None:
    rows = runner._initial_readiness_rows()
    rows[0]["provider_error_code"] = "credential-and-account-secret"
    matrix = runner._emergency_matrix(rows)
    assert matrix["row_count"] == 8
    assert matrix["resources"][0]["status"] == "UNKNOWN"
    assert matrix["resources"][0]["provider_error_code"] is None
    assert "credential-and-account-secret" not in json.dumps(matrix)


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
    assert b"\r\n" not in (namespace / "SUMMARY.json").read_bytes()
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


def _git_head(path: Path) -> str:
    return subprocess.run(
        ["git", "-C", str(path), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def test_collector_head_is_bound_to_script_repo_from_different_git_cwd(
    tmp_path, monkeypatch
) -> None:
    other = tmp_path / "other-checkout"
    other.mkdir()
    subprocess.run(["git", "init", "--quiet", str(other)], check=True)
    subprocess.run(["git", "-C", str(other), "config", "user.name", "Test"], check=True)
    subprocess.run(
        ["git", "-C", str(other), "config", "user.email", "test@example.invalid"],
        check=True,
    )
    (other / "marker.txt").write_text("other\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(other), "add", "marker.txt"], check=True)
    subprocess.run(["git", "-C", str(other), "commit", "--quiet", "-m", "other"], check=True)
    other_head = _git_head(other)
    exact_clone_head = _git_head(ROOT)
    assert other_head != exact_clone_head
    monkeypatch.chdir(other)
    assert runner._head() == exact_clone_head


def test_collector_head_is_bound_to_script_repo_from_non_git_cwd(
    tmp_path, monkeypatch
) -> None:
    non_git = tmp_path / "not-a-checkout"
    non_git.mkdir()
    exact_clone_head = _git_head(ROOT)
    monkeypatch.chdir(non_git)
    assert runner._head() == exact_clone_head


def test_pre_auth_precheck_validates_local_contract_without_constructing_client(
    tmp_path, monkeypatch, capsys
) -> None:
    exact_clone_head = runner._head()
    monkeypatch.setattr(sys, "argv", [
        "run_ig_predemo_readiness_2238.py",
        "--expected-head", exact_clone_head,
        "--credentials-file", str(tmp_path / "credentials.env"),
        "--runtime-root", str(tmp_path),
        "--namespace", ".runtime/attempt",
        "--pre-auth-precheck",
    ])
    monkeypatch.setattr(runner, "_credentials_from_file", lambda _: object())
    monkeypatch.setattr(
        runner,
        "IgDemoReadOnlyClient",
        lambda _: (_ for _ in ()).throw(AssertionError("client must not be constructed")),
    )
    assert runner.main() == 0
    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 1
    result = json.loads(lines[0])
    assert result["pre_auth_precheck"] == "PASS"
    assert result["exact_head"] == exact_clone_head
    assert result["execution_capability"] == "NONE"
    assert result["order_execution_enabled"] is False


def test_authenticated_read_failure_emits_one_structured_line_and_exit_two(
    tmp_path, monkeypatch, capsys
) -> None:
    class Client:
        logout_calls = 0

        def login(self):
            return None

        def logout(self):
            self.logout_calls += 1

    client = Client()
    monkeypatch.setattr(sys, "argv", [
        "run_ig_predemo_readiness_2238.py",
        "--expected-head", "d" * 40,
        "--credentials-file", str(tmp_path / "credentials.env"),
        "--runtime-root", str(tmp_path),
        "--namespace", ".runtime/attempt",
    ])
    monkeypatch.setattr(runner, "_head", lambda: "d" * 40)
    monkeypatch.setattr(runner, "_credentials_from_file", lambda _: object())
    monkeypatch.setattr(runner, "IgDemoReadOnlyClient", lambda _: client)
    monkeypatch.setattr(
        runner, "collect", lambda *_, **__: (_ for _ in ()).throw(OSError("secret"))
    )
    assert runner.main() == 2
    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 1
    result = json.loads(lines[0])
    assert result["cleanup_error_code"] == "NONE"
    assert result["error_code"] == "IG_SESSION_READ_FAILED_NO_RETRY"
    assert result["execution_capability"] == "NONE"
    assert result["failure_phase"] == "READ"
    assert result["order_execution_enabled"] is False
    assert result["status"] == "BLOCKED"
    _assert_authenticated_matrix(result)
    assert client.logout_calls == 1
    assert "secret" not in lines[0]


def test_read_failure_preserves_primary_code_when_logout_cleanup_fails(
    tmp_path, monkeypatch, capsys
) -> None:
    class Client:
        logout_calls = 0

        def login(self):
            return None

        def logout(self):
            self.logout_calls += 1
            raise OSError("secret cleanup")

    client = Client()
    monkeypatch.setattr(sys, "argv", [
        "run_ig_predemo_readiness_2238.py",
        "--expected-head", "d" * 40,
        "--credentials-file", str(tmp_path / "credentials.env"),
        "--runtime-root", str(tmp_path),
        "--namespace", ".runtime/attempt",
    ])
    monkeypatch.setattr(runner, "_head", lambda: "d" * 40)
    monkeypatch.setattr(runner, "_credentials_from_file", lambda _: object())
    monkeypatch.setattr(runner, "IgDemoReadOnlyClient", lambda _: client)
    monkeypatch.setattr(
        runner, "collect", lambda *_, **__: (_ for _ in ()).throw(OSError("secret read"))
    )
    assert runner.main() == 2
    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 1
    result = json.loads(lines[0])
    assert result["error_code"] == "IG_SESSION_READ_FAILED_NO_RETRY"
    assert result["cleanup_error_code"] == "IG_SESSION_CLEANUP_FAILED"
    assert result["failure_phase"] == "READ"
    _assert_authenticated_matrix(result)
    assert client.logout_calls == 1
    assert "secret" not in lines[0]


def test_logout_failure_after_successful_collection_is_structured_cleanup_failure(
    tmp_path, monkeypatch, capsys
) -> None:
    class Client(MatrixClient):
        def logout(self):
            self.logout_calls += 1
            raise OSError("secret logout")

    client = Client()
    monkeypatch.setattr(sys, "argv", [
        "run_ig_predemo_readiness_2238.py",
        "--expected-head", "d" * 40,
        "--credentials-file", str(tmp_path / "credentials.env"),
        "--runtime-root", str(tmp_path),
        "--namespace", ".runtime/attempt",
    ])
    monkeypatch.setattr(runner, "_head", lambda: "d" * 40)
    monkeypatch.setattr(runner, "_credentials_from_file", lambda _: object())
    monkeypatch.setattr(runner, "IgDemoReadOnlyClient", lambda _: client)
    assert runner.main() == 2
    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 1
    result = json.loads(lines[0])
    assert result["error_code"] == "IG_SESSION_CLEANUP_FAILED"
    assert result["cleanup_error_code"] == "IG_SESSION_CLEANUP_FAILED"
    assert result["failure_phase"] == "CLEANUP"
    _assert_authenticated_matrix(result)
    assert client.logout_calls == 1
    assert "secret" not in lines[0]


def test_incomplete_read_matrix_is_published_after_one_cleanup(
    tmp_path, monkeypatch, capsys
) -> None:
    class Client:
        logout_calls = 0
        def login(self):
            return None
        def logout(self):
            self.logout_calls += 1

    client = Client()
    raw_rows = [
        runner._fallback_read(resource, endpoint, status="PASS", reason_code="NONE").safe_view()
        for resource, endpoint in runner.READ_RESOURCE_CONTRACTS
    ]
    raw_rows[3] = runner._fallback_read(
        "MARKET_V4",
        "MARKET_V4",
        status="FAIL",
        reason_code="IG_READ_MARKET_V4_HTTP_FAILED",
    ).safe_view()
    matrix = runner._matrix_from_rows(raw_rows)
    evidence = {
        "schema": runner.SCHEMA, "account": {}, "inventory": {}, "market": {},
        "clock": {}, "history_scope": {}, "authenticated_read_matrix": matrix,
        "dependent_conclusions": {"economics": "BLOCKED"},
        "derived_processing_complete": True,
        "execution_capability": "NONE", "order_execution_enabled": False,
    }
    monkeypatch.setattr(sys, "argv", [
        "run_ig_predemo_readiness_2238.py", "--expected-head", "d" * 40,
        "--credentials-file", str(tmp_path / "credentials.env"),
        "--runtime-root", str(tmp_path), "--namespace", ".runtime/attempt",
    ])
    monkeypatch.setattr(runner, "_head", lambda: "d" * 40)
    monkeypatch.setattr(runner, "_credentials_from_file", lambda _: object())
    monkeypatch.setattr(runner, "IgDemoReadOnlyClient", lambda _: client)
    def collect(*args, raw_rows, **kwargs):
        raw_rows[:] = matrix["resources"]
        return evidence, {}

    monkeypatch.setattr(runner, "collect", collect)
    assert runner.main() == 2
    result = json.loads(capsys.readouterr().out)
    assert result["error_code"] == "IG_READINESS_MATRIX_INCOMPLETE"
    assert result["readiness_matrix_counts"]["PASS"] == 7
    _assert_authenticated_matrix(result)
    assert result["cleanup_error_code"] == "NONE"
    assert client.logout_calls == 1
    published = json.loads((tmp_path / ".runtime/attempt/READ_MATRIX.json").read_text())
    assert published["authenticated_read_matrix"] == matrix
    summary = json.loads((tmp_path / ".runtime/attempt/SUMMARY.json").read_text())
    assert summary["status"] == "BLOCKED"
    assert summary["error_code"] == "IG_READINESS_MATRIX_INCOMPLETE"
