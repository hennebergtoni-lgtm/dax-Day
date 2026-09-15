from __future__ import annotations

import pytest

from daxlab.runtime.demo_evidence_authorization import DemoAccountMode
from daxlab.runtime.mt5_probe_payload import (
    parse_mt5_demo_account_context,
    parse_mt5_probe_payload,
)


def payload() -> dict:
    return {
        "observed_at": "2026-09-08T21:00:00+02:00",
        "terminal_connected": True,
        "account_connected": True,
        "account_trade_allowed": True,
        "order_execution_enabled": False,
        "engine_loop_healthy": True,
        "clock_ok": True,
        "symbols": [
            {
                "name": "GER40",
                "digits": 1,
                "point": 0.1,
                "trade_mode": "FULL",
                "contract_size": 1.0,
                "volume_min": 0.01,
                "volume_step": 0.01,
                "volume_max": 100.0,
                "volume_limit": 0.0,
                "tick_size": 0.1,
                "tick_value": 0.1,
                "tick_value_profit": 0.1,
                "tick_value_loss": 0.1,
                "currency_profit": "EUR",
                "currency_margin": "EUR",
                "margin_initial": 0.0,
                "margin_maintenance": 0.0,
            }
        ],
    }


def demo_account_context() -> dict:
    return {
        "schema_version": "DAXLAB_MT5_DEMO_ACCOUNT_CONTEXT_V1",
        "account_fingerprint": "a" * 64,
        "server": "Broker-Demo",
        "symbol": "GER40",
        "account_mode": "DEMO",
        "trade_allowed": True,
        "execution_capability": "NONE",
        "order_execution_enabled": False,
    }


def test_parse_valid_payload() -> None:
    observation = parse_mt5_probe_payload(payload())
    assert observation.order_execution_enabled is False
    symbol = observation.symbols[0]
    assert symbol.name == "GER40"
    assert symbol.volume_min == 0.01
    assert symbol.volume_step == 0.01
    assert symbol.volume_max == 100.0
    assert symbol.volume_limit == 0.0
    assert symbol.tick_size == 0.1
    assert symbol.tick_value == 0.1
    assert symbol.tick_value_profit == 0.1
    assert symbol.tick_value_loss == 0.1
    assert symbol.currency_profit == "EUR"
    assert symbol.currency_margin == "EUR"
    assert symbol.margin_initial == 0.0
    assert symbol.margin_maintenance == 0.0
    assert observation.observed_at.utcoffset() is not None


def test_legacy_shadow_payload_remains_valid_but_has_no_demo_context() -> None:
    item = payload()
    parse_mt5_probe_payload(item)
    assert parse_mt5_demo_account_context(item) is None


def test_optional_redacted_demo_context_is_strict_and_adapts_to_step_2191() -> None:
    item = payload()
    item["demo_account_context"] = demo_account_context()

    parse_mt5_probe_payload(item)
    observed = parse_mt5_demo_account_context(item)
    assert observed is not None
    assert observed.account_id == "a" * 64
    assert observed.server == "Broker-Demo"
    assert observed.symbol == "GER40"
    assert observed.account_mode is DemoAccountMode.DEMO
    assert observed.trade_allowed is True


def test_malformed_optional_demo_context_fails_closed() -> None:
    item = payload()
    item["demo_account_context"] = demo_account_context()
    item["demo_account_context"]["order_execution_enabled"] = True
    with pytest.raises(ValueError, match="cannot grant execution"):
        parse_mt5_probe_payload(item)

    item = payload()
    item["demo_account_context"] = demo_account_context()
    item["demo_account_context"]["login"] = 123456
    with pytest.raises(ValueError, match="unknown demo account context fields"):
        parse_mt5_probe_payload(item)


def test_zero_tick_and_margin_economics_are_observation_not_readiness() -> None:
    item = payload()
    symbol = item["symbols"][0]
    symbol["tick_value"] = 0.0
    symbol["tick_value_profit"] = 0.0
    symbol["tick_value_loss"] = 0.0
    observation = parse_mt5_probe_payload(item)
    parsed = observation.symbols[0]
    assert parsed.tick_value == 0.0
    assert parsed.tick_value_profit == 0.0
    assert parsed.tick_value_loss == 0.0
    assert parsed.margin_initial == 0.0


def test_rejects_unknown_top_level_field() -> None:
    item = payload()
    item["password"] = "must-never-cross-boundary"
    with pytest.raises(ValueError, match="unknown MT5 probe fields"):
        parse_mt5_probe_payload(item)


def test_rejects_missing_execution_guard() -> None:
    item = payload()
    del item["order_execution_enabled"]
    with pytest.raises(ValueError, match="missing MT5 probe fields"):
        parse_mt5_probe_payload(item)


def test_rejects_naive_timestamp() -> None:
    item = payload()
    item["observed_at"] = "2026-09-08T21:00:00"
    with pytest.raises(ValueError, match="timezone-aware"):
        parse_mt5_probe_payload(item)


def test_rejects_non_boolean_guard() -> None:
    item = payload()
    item["order_execution_enabled"] = 0
    with pytest.raises(ValueError, match="must be boolean"):
        parse_mt5_probe_payload(item)


def test_rejects_invalid_symbol_metadata() -> None:
    item = payload()
    item["symbols"][0]["point"] = 0
    with pytest.raises(ValueError, match="point must be positive"):
        parse_mt5_probe_payload(item)


def test_rejects_negative_observed_broker_economics() -> None:
    item = payload()
    item["symbols"][0]["tick_value_loss"] = -0.1
    with pytest.raises(ValueError, match="tick_value_loss must be non-negative"):
        parse_mt5_probe_payload(item)


def test_rejects_empty_broker_currency() -> None:
    item = payload()
    item["symbols"][0]["currency_profit"] = ""
    with pytest.raises(ValueError, match="currency_profit must be non-empty"):
        parse_mt5_probe_payload(item)
