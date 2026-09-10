from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


SCRIPT = Path("scripts/diagnose_mt5_broker_timezone.py")


def _load_module():
    spec = importlib.util.spec_from_file_location("diagnose_mt5_broker_timezone", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _fake_probe(*, configured_symbol, bars, max_age_seconds, broker_timezone):
    del configured_symbol, bars, max_age_seconds
    delta = {
        "UTC": 7200.0,
        "Europe/Berlin": 0.25,
        "Europe/Helsinki": -3599.75,
    }.get(broker_timezone, 123.0)
    return {
        "host_probe": {
            "clock_ok": abs(delta) <= 600.0,
            "order_execution_enabled": False,
        },
        "closed_m5_feed": {
            "bars": [
                {"open_time": "2026-09-10T01:30:00+00:00"},
                {"open_time": "2026-09-10T01:35:00+00:00"},
            ]
        },
        "notes": [
            "READ_ONLY",
            "RAW_TICK_CLOCK_DELTA_SECONDS=7200.000",
            f"NORMALIZED_TICK_CLOCK_DELTA_SECONDS={delta:.3f}",
        ],
        "sha256": f"sha-{broker_timezone}",
    }


def test_diagnostic_never_auto_verifies_even_with_best_candidate(monkeypatch) -> None:
    module = _load_module()
    monkeypatch.setattr(module, "collect_probe", _fake_probe)
    payload = module.diagnose(
        symbol="DE40",
        candidates=("UTC", "Europe/Berlin", "Europe/Helsinki"),
        bars=20,
        max_age_seconds=600.0,
    )
    assert payload["decision_state"] == "HUMAN_REVIEW_REQUIRED"
    assert payload["auto_selected_timezone"] is None
    assert payload["verification_state"] == "UNVERIFIED"
    assert payload["execution_capability"] == "NONE"
    assert payload["order_execution_enabled"] is False
    berlin = next(
        item for item in payload["observations"] if item["candidate_timezone"] == "Europe/Berlin"
    )
    assert berlin["clock_ok"] is True
    assert berlin["normalized_tick_clock_delta_seconds"] == pytest.approx(0.25)


def test_requires_multiple_unique_candidates(monkeypatch) -> None:
    module = _load_module()
    monkeypatch.setattr(module, "collect_probe", _fake_probe)
    with pytest.raises(ValueError, match="at least two"):
        module.diagnose(symbol="DE40", candidates=("UTC",), bars=20, max_age_seconds=600.0)
    with pytest.raises(ValueError, match="unique"):
        module.diagnose(
            symbol="DE40",
            candidates=("UTC", "UTC"),
            bars=20,
            max_age_seconds=600.0,
        )


def test_invalid_iana_timezone_fails_before_probe(monkeypatch) -> None:
    module = _load_module()
    called = False

    def should_not_run(**kwargs):
        nonlocal called
        called = True
        return _fake_probe(**kwargs)

    monkeypatch.setattr(module, "collect_probe", should_not_run)
    with pytest.raises(Exception):
        module.diagnose(
            symbol="DE40",
            candidates=("UTC", "Not/A_Timezone"),
            bars=20,
            max_age_seconds=600.0,
        )
    assert called is False


def test_diagnostic_output_surface_is_credential_free(monkeypatch) -> None:
    module = _load_module()
    monkeypatch.setattr(module, "collect_probe", _fake_probe)
    payload = module.diagnose(
        symbol="DE40",
        candidates=("UTC", "Europe/Berlin"),
        bars=20,
        max_age_seconds=600.0,
    )
    serialized = str(payload).lower()
    for forbidden in ("password", "login", "token", "secret", "account_id"):
        assert forbidden not in serialized
    assert all(item["order_execution_enabled"] is False for item in payload["observations"])


def test_script_contains_no_order_api_or_auto_selection() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    lower = text.lower()
    for forbidden in ("order_send", "order_check", "positions_get", "history_deals_get"):
        assert forbidden not in lower
    assert '"auto_selected_timezone": None' in text
    assert '"verification_state": "UNVERIFIED"' in text
    assert '"decision_state": "HUMAN_REVIEW_REQUIRED"' in text
