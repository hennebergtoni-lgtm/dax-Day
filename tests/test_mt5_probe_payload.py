from __future__ import annotations

import pytest

from daxlab.runtime.mt5_probe_payload import parse_mt5_probe_payload


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
