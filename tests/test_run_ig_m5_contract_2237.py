from __future__ import annotations

from datetime import datetime, timedelta, timezone
import importlib.util
import json
from pathlib import Path

import pytest


_PATH = Path(__file__).resolve().parents[1] / "scripts" / "run_ig_m5_contract_2237.py"
_SPEC = importlib.util.spec_from_file_location("ig_m5_contract_2237_runner_test", _PATH)
assert _SPEC and _SPEC.loader
runner = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(runner)

HEAD = "a" * 40
CLOSE = datetime(2026, 9, 14, 15, 30, tzinfo=timezone.utc)
NAMESPACE = ".runtime/ig_m5_contract_2237_interval_start_v2_attempt_99"


def test_resume_target_is_next_true_close_plus_sampling_offset() -> None:
    assert runner.resume_target(CLOSE) == CLOSE + timedelta(minutes=5, seconds=5)


def test_runner_uses_one_session_and_preserves_fresh_resume_operator(
    tmp_path, monkeypatch,
) -> None:
    calls: list[str] = []

    class Client:
        execution_capability = "NONE"
        order_execution_enabled = False

        def __init__(self, *, credentials):
            calls.append("construct")

        def login(self):
            calls.append("login")

        def logout(self):
            calls.append("logout")

    monkeypatch.setattr(runner.platform, "system", lambda: "Windows")
    monkeypatch.setattr(runner.candidate, "check_code", lambda head: head)
    monkeypatch.setattr(
        runner.candidate,
        "require_verified_live_provider_contract",
        lambda: None,
    )
    monkeypatch.setattr(runner.candidate, "validate_evidence", lambda *args, **kwargs: None)
    monkeypatch.setattr(runner.probe, "_credentials_from_file", lambda path: object())

    cycles = []

    def cycle(client, *, head, prior, clock):
        calls.append("cycle")
        recovery = "FRESH_START" if prior is None else "RESUME_ANCHOR_RECONCILED"
        close = CLOSE if prior is None else CLOSE + timedelta(minutes=5)
        payload = {
            "recovery_state": recovery,
            "latest_finalized_m5": {"close_time": close.isoformat()},
            "fingerprint": recovery,
            "operator_snapshot": {"mode": "SHADOW"},
            "operator_projection": {"mode": "SHADOW"},
            "execution_capability": "NONE",
            "order_execution_enabled": False,
        }
        cycles.append(payload)
        return payload

    monkeypatch.setattr(runner, "_cycle", cycle)
    waits = []
    code, summary = runner.run(
        HEAD,
        namespace=NAMESPACE,
        credentials_file=tmp_path / "external.env",
        root=tmp_path,
        clock=lambda: CLOSE,
        wait=waits.append,
        client_factory=Client,
    )

    assert code == 0
    assert summary["status"] == "SUCCESS"
    assert calls == ["construct", "login", "cycle", "cycle", "logout"]
    assert waits == [CLOSE + timedelta(minutes=5, seconds=5)]
    directory = tmp_path / NAMESPACE
    assert json.loads((directory / "FRESH_START.json").read_text())["recovery_state"] == "FRESH_START"
    assert json.loads((directory / "RESUME.json").read_text())["recovery_state"] == (
        "RESUME_ANCHOR_RECONCILED"
    )
    assert (directory / "OPERATOR.json").is_file()
    assert (directory / "SUMMARY.json").is_file()


def test_runner_existing_namespace_fails_before_credentials_or_session(
    tmp_path, monkeypatch,
) -> None:
    (tmp_path / NAMESPACE).mkdir(parents=True)
    monkeypatch.setattr(runner.platform, "system", lambda: "Windows")
    monkeypatch.setattr(runner.candidate, "check_code", lambda head: head)
    monkeypatch.setattr(
        runner.candidate,
        "require_verified_live_provider_contract",
        lambda: None,
    )
    monkeypatch.setattr(
        runner.probe,
        "_credentials_from_file",
        lambda path: pytest.fail("credentials read"),
    )
    code, summary = runner.run(HEAD, namespace=NAMESPACE, root=tmp_path)
    assert code == 2
    assert summary["error_code"] == "STATE_NAMESPACE_EXISTS"


def test_powershell_wrapper_has_one_runner_and_no_dealing_route() -> None:
    source = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "run_ig_m5_contract_2237.ps1"
    ).read_text(encoding="utf-8")
    assert source.count("run_ig_m5_contract_2237.py") == 1
    assert "order_send" not in source
    assert "/positions/otc" not in source
    assert "SUMMARY: BLOCKED / FAIL_CLOSED; error_code=" in source
