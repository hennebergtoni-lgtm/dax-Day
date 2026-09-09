"""Strict validator for credential-free evidence emitted by the Windows MT5 probe."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Mapping

from daxlab.runtime.mt5_feed_payload import ClosedM5Feed, feed_blocker, parse_closed_m5_feed
from daxlab.runtime.mt5_host_contract import Mt5HostObservation, validate_read_only_host
from daxlab.runtime.mt5_probe_payload import parse_mt5_probe_payload

_SCHEMA = "DAXLAB_MT5_WINDOWS_BUNDLE_V1"
_REQUIRED = {"schema", "symbol_resolution_state", "host_probe", "closed_m5_feed", "notes", "sha256"}
_FORBIDDEN_KEYS = {"login", "password", "token", "secret", "email", "phone", "account_id"}


@dataclass(frozen=True, slots=True)
class WindowsMt5Bundle:
    host: Mt5HostObservation
    feed: ClosedM5Feed | None
    symbol_resolution_state: str
    fingerprint: str
    blockers: tuple[str, ...]

    @property
    def green(self) -> bool:
        return not self.blockers


def _canonical_without_sha(payload: Mapping[str, Any]) -> str:
    value = dict(payload)
    value.pop("sha256", None)
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _sha256(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_without_sha(payload).encode()).hexdigest()


def _assert_no_forbidden_keys(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if str(key).lower() in _FORBIDDEN_KEYS:
                raise ValueError(f"forbidden evidence key: {key}")
            _assert_no_forbidden_keys(item)
    elif isinstance(value, list):
        for item in value:
            _assert_no_forbidden_keys(item)


def parse_windows_mt5_bundle(payload: Mapping[str, Any]) -> WindowsMt5Bundle:
    missing = _REQUIRED - payload.keys()
    unknown = payload.keys() - _REQUIRED
    if missing:
        raise ValueError(f"missing Windows MT5 bundle fields: {sorted(missing)}")
    if unknown:
        raise ValueError(f"unknown Windows MT5 bundle fields: {sorted(unknown)}")
    if payload["schema"] != _SCHEMA:
        raise ValueError("unsupported Windows MT5 bundle schema")
    _assert_no_forbidden_keys(payload)

    expected = _sha256(payload)
    if payload["sha256"] != expected:
        raise ValueError("Windows MT5 bundle fingerprint mismatch")

    state = payload["symbol_resolution_state"]
    if not isinstance(state, str) or not state:
        raise ValueError("symbol_resolution_state must be non-empty string")
    notes = payload["notes"]
    if not isinstance(notes, list) or not all(isinstance(item, str) for item in notes):
        raise ValueError("notes must be a list of strings")
    required_notes = {"READ_ONLY", "BAR_0_EXCLUDED", "NO_CREDENTIALS", "NO_ORDER_API"}
    if not required_notes.issubset(set(notes)):
        raise ValueError("Windows MT5 bundle safety notes incomplete")

    host = parse_mt5_probe_payload(payload["host_probe"])
    raw_feed = payload["closed_m5_feed"]
    feed = None if raw_feed is None else parse_closed_m5_feed(raw_feed)

    blockers: list[str] = []
    if feed is None:
        blockers.append("CLOSED_M5_FEED_MISSING")
        market_data_fresh = False
    else:
        market_data_fresh = feed.fresh and not feed.discontinuities
        blocker = feed_blocker(feed)
        if blocker:
            blockers.append(blocker)

    handshake = validate_read_only_host(
        host,
        market_data_fresh=market_data_fresh,
        allow_data_only=True,
    )
    if handshake.reason != "READ_ONLY_HEALTHY":
        blockers.append(handshake.reason)
    if state in {"AMBIGUOUS", "AMBIGUOUS_DATA_ONLY", "NOT_FOUND", "CONFIGURED_NOT_FOUND"}:
        blockers.append(f"SYMBOL_{state}")

    return WindowsMt5Bundle(
        host=host,
        feed=feed,
        symbol_resolution_state=state,
        fingerprint=expected,
        blockers=tuple(dict.fromkeys(blockers)),
    )


def compact_status(bundle: WindowsMt5Bundle) -> str:
    if bundle.green:
        symbol = bundle.host.symbols[0].name if bundle.host.symbols else "?"
        bars = len(bundle.feed.bars) if bundle.feed else 0
        return f"GREEN | symbol={symbol} | closed_m5={bars} | execution=false"
    return "BLOCKED | " + ",".join(bundle.blockers)
