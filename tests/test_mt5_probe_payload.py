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
            }
        ],
    }


def test_parse_valid_payload() -> None:
    observation = parse_mt5_probe_payload(payload())
    assert observation.order_execution_enabled is False
    assert observation.symbols[0].name == "GER40"
    assert observation.observed_at.utcoffset() is not None


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
