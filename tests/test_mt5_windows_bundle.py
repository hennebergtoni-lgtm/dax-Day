from datetime import datetime, timedelta, timezone
import hashlib
import json

import pytest

from daxlab.runtime.mt5_windows_bundle import compact_status, parse_windows_mt5_bundle


def _seal(payload: dict) -> dict:
    value = dict(payload)
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"))
    value["sha256"] = hashlib.sha256(canonical.encode()).hexdigest()
    return value


def _bundle(*, trade_mode: str = "DISABLED", fresh: bool = True) -> dict:
    observed = datetime(2026, 9, 9, 6, 30, tzinfo=timezone.utc)
    latest = observed - timedelta(minutes=5 if fresh else 30)
    bars = []
    for offset in (10, 5, 0):
        t = latest - timedelta(minutes=offset)
        bars.append(
            {
                "open_time": t.isoformat(),
                "open": 25000.0,
                "high": 25002.0,
                "low": 24999.0,
                "close": 25001.0,
            }
        )
    payload = {
        "schema": "DAXLAB_MT5_WINDOWS_BUNDLE_V1",
        "symbol_resolution_state": "AUTO_EXACT_ALIAS_DATA_ONLY",
        "host_probe": {
            "observed_at": observed.isoformat(),
            "terminal_connected": True,
            "account_connected": True,
            "account_trade_allowed": False,
            "order_execution_enabled": False,
            "engine_loop_healthy": True,
            "clock_ok": True,
            "symbols": [
                {
                    "name": "DE40",
                    "digits": 2,
                    "point": 0.01,
                    "trade_mode": trade_mode,
                    "contract_size": 1.0,
                    "volume_min": 0.1,
                    "volume_step": 0.1,
                }
            ],
        },
        "closed_m5_feed": {
            "observed_at": observed.isoformat(),
            "requested_start_pos": 1,
            "max_age_seconds": 600.0,
            "bars": bars,
        },
        "notes": ["READ_ONLY", "BAR_0_EXCLUDED", "NO_CREDENTIALS", "NO_ORDER_API"],
    }
    return _seal(payload)


def test_data_only_de40_bundle_can_be_green() -> None:
    result = parse_windows_mt5_bundle(_bundle())
    assert result.green
    assert compact_status(result).startswith("GREEN | symbol=DE40")


def test_stale_feed_blocks() -> None:
    result = parse_windows_mt5_bundle(_bundle(fresh=False))
    assert not result.green
    assert "MARKET_DATA_STALE" in result.blockers


def test_fingerprint_tamper_is_rejected() -> None:
    payload = _bundle()
    payload["host_probe"]["terminal_connected"] = False
    with pytest.raises(ValueError, match="fingerprint mismatch"):
        parse_windows_mt5_bundle(payload)


def test_forbidden_credential_key_is_rejected_even_when_resealed() -> None:
    payload = _bundle()
    payload.pop("sha256")
    payload["host_probe"]["password"] = "never-store-this"
    payload = _seal(payload)
    with pytest.raises(ValueError, match="forbidden evidence key"):
        parse_windows_mt5_bundle(payload)


def test_bar_zero_request_is_rejected() -> None:
    payload = _bundle()
    payload.pop("sha256")
    payload["closed_m5_feed"]["requested_start_pos"] = 0
    payload = _seal(payload)
    with pytest.raises(ValueError, match="position >= 1"):
        parse_windows_mt5_bundle(payload)
