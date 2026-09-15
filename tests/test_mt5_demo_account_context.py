import json

import pytest

from daxlab.runtime.demo_evidence_authorization import DemoAccountMode
from daxlab.runtime.mt5_demo_account_context import (
    MT5_DEMO_ACCOUNT_CONTEXT_SCHEMA,
    normalize_mt5_account_mode,
    normalize_mt5_demo_account_context,
    parse_mt5_demo_account_context_payload,
)


DEMO = 0
CONTEST = 1
REAL = 2
LOGIN = 25115284


def _context(**overrides):
    values = {
        "raw_login": LOGIN,
        "raw_server": "Broker-Demo",
        "raw_trade_mode": DEMO,
        "trade_allowed": True,
        "resolved_symbol": "DE40",
        "demo_trade_mode": DEMO,
        "contest_trade_mode": CONTEST,
        "real_trade_mode": REAL,
    }
    values.update(overrides)
    return normalize_mt5_demo_account_context(**values)


@pytest.mark.parametrize(
    ("raw_mode", "expected"),
    [
        (DEMO, DemoAccountMode.DEMO),
        (CONTEST, DemoAccountMode.CONTEST),
        (REAL, DemoAccountMode.REAL),
        (999, DemoAccountMode.UNKNOWN),
        (None, DemoAccountMode.UNKNOWN),
        ("0", DemoAccountMode.UNKNOWN),
    ],
)
def test_account_mode_uses_exact_runtime_constants_or_unknown(raw_mode, expected):
    assert (
        normalize_mt5_account_mode(
            raw_trade_mode=raw_mode,
            demo_trade_mode=DEMO,
            contest_trade_mode=CONTEST,
            real_trade_mode=REAL,
        )
        is expected
    )


def test_missing_or_ambiguous_runtime_constants_fail_to_unknown():
    assert (
        normalize_mt5_account_mode(
            raw_trade_mode=DEMO,
            demo_trade_mode=None,
            contest_trade_mode=CONTEST,
            real_trade_mode=REAL,
        )
        is DemoAccountMode.UNKNOWN
    )
    assert (
        normalize_mt5_account_mode(
            raw_trade_mode=DEMO,
            demo_trade_mode=0,
            contest_trade_mode=0,
            real_trade_mode=2,
        )
        is DemoAccountMode.UNKNOWN
    )


def test_normalized_context_redacts_raw_login_and_preserves_safety():
    evidence = _context()
    payload = evidence.to_payload()
    encoded = json.dumps(payload, sort_keys=True)

    assert payload["schema_version"] == MT5_DEMO_ACCOUNT_CONTEXT_SCHEMA
    assert "login" not in payload
    assert "account_id" not in payload
    assert str(LOGIN) not in encoded
    assert len(payload["account_fingerprint"]) == 64
    assert payload["server"] == "Broker-Demo"
    assert payload["symbol"] == "DE40"
    assert payload["account_mode"] == "DEMO"
    assert payload["trade_allowed"] is True
    assert payload["execution_capability"] == "NONE"
    assert payload["order_execution_enabled"] is False


def test_account_fingerprint_is_stable_and_changes_with_login():
    first = _context()
    replay = _context()
    other = _context(raw_login=LOGIN + 1)

    assert first.account_fingerprint == replay.account_fingerprint
    assert first.account_fingerprint != other.account_fingerprint
    assert first.fingerprint == replay.fingerprint


def test_observed_context_feeds_step_2191_without_raw_login():
    observed = _context().to_observed_context()
    assert observed.account_id == _context().account_fingerprint
    assert observed.server == "Broker-Demo"
    assert observed.symbol == "DE40"
    assert observed.account_mode is DemoAccountMode.DEMO
    assert observed.trade_allowed is True


def test_trade_allowed_does_not_change_account_mode():
    real = _context(raw_trade_mode=REAL, trade_allowed=True)
    assert real.account_mode is DemoAccountMode.REAL
    assert real.trade_allowed is True


@pytest.mark.parametrize(
    ("overrides", "match"),
    [
        ({"raw_login": None}, "raw_login"),
        ({"raw_login": 0}, "raw_login"),
        ({"raw_server": ""}, "raw_server"),
        ({"resolved_symbol": ""}, "resolved_symbol"),
        ({"trade_allowed": 1}, "trade_allowed"),
    ],
)
def test_required_observation_inputs_fail_closed(overrides, match):
    with pytest.raises(ValueError, match=match):
        _context(**overrides)


def test_serialized_payload_roundtrip_is_strict_and_non_executable():
    evidence = _context(raw_trade_mode=CONTEST)
    parsed = parse_mt5_demo_account_context_payload(evidence.to_payload())
    assert parsed == evidence
    assert parsed.account_mode is DemoAccountMode.CONTEST
    assert parsed.execution_capability == "NONE"
    assert parsed.order_execution_enabled is False


def test_parser_rejects_unknown_fields_tampering_and_execution_inversion():
    payload = _context().to_payload()
    payload["login"] = LOGIN
    with pytest.raises(ValueError, match="unknown demo account context fields"):
        parse_mt5_demo_account_context_payload(payload)

    payload = _context().to_payload()
    payload["account_fingerprint"] = "z" * 64
    with pytest.raises(ValueError, match="hexadecimal"):
        parse_mt5_demo_account_context_payload(payload)

    payload = _context().to_payload()
    payload["order_execution_enabled"] = True
    with pytest.raises(ValueError, match="cannot grant execution"):
        parse_mt5_demo_account_context_payload(payload)
