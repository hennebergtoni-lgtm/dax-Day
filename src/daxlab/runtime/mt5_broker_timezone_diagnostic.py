"""Fail-closed helpers for read-only MT5 broker-timezone diagnostics.

This module compares observations produced by an injected probe callable. It never
selects, verifies, or authorizes a broker timezone and has no MT5/order dependency.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Callable
from zoneinfo import ZoneInfo

_FORBIDDEN_KEYS = {"login", "password", "token", "secret", "email", "phone", "account_id"}

ProbeCallable = Callable[..., dict[str, Any]]


def _note_value(notes: list[str], prefix: str) -> float | None:
    marker = f"{prefix}="
    for note in notes:
        if note.startswith(marker):
            return float(note[len(marker) :])
    return None


def _assert_credential_free(payload: Any) -> None:
    if isinstance(payload, dict):
        for key, value in payload.items():
            if str(key).lower() in _FORBIDDEN_KEYS:
                raise RuntimeError(f"forbidden diagnostic output key: {key}")
            _assert_credential_free(value)
    elif isinstance(payload, list):
        for value in payload:
            _assert_credential_free(value)


def _fingerprint(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def diagnose_broker_timezone(
    *,
    probe: ProbeCallable,
    symbol: str,
    candidates: tuple[str, ...],
    bars: int,
    max_age_seconds: float,
    observed_at: datetime | None = None,
) -> dict[str, Any]:
    if not symbol.strip():
        raise ValueError("symbol must be non-empty")
    if len(candidates) < 2:
        raise ValueError("at least two timezone candidates are required")
    if len(set(candidates)) != len(candidates):
        raise ValueError("timezone candidates must be unique")
    for candidate in candidates:
        ZoneInfo(candidate)

    observations: list[dict[str, Any]] = []
    for candidate in candidates:
        probe_payload = probe(
            configured_symbol=symbol,
            bars=bars,
            max_age_seconds=max_age_seconds,
            broker_timezone=candidate,
        )
        _assert_credential_free(probe_payload)
        notes = list(probe_payload.get("notes") or [])
        feed = probe_payload.get("closed_m5_feed") or {}
        host = probe_payload.get("host_probe") or {}
        bars_payload = feed.get("bars") or []
        observations.append(
            {
                "candidate_timezone": candidate,
                "clock_ok": bool(host.get("clock_ok")),
                "raw_tick_clock_delta_seconds": _note_value(
                    notes, "RAW_TICK_CLOCK_DELTA_SECONDS"
                ),
                "normalized_tick_clock_delta_seconds": _note_value(
                    notes, "NORMALIZED_TICK_CLOCK_DELTA_SECONDS"
                ),
                "closed_m5_count": len(bars_payload),
                "first_closed_m5_open_time": (
                    bars_payload[0].get("open_time") if bars_payload else None
                ),
                "last_closed_m5_open_time": (
                    bars_payload[-1].get("open_time") if bars_payload else None
                ),
                "probe_sha256": probe_payload.get("sha256"),
                "order_execution_enabled": False,
            }
        )

    now = observed_at or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("observed_at must be timezone-aware")
    payload: dict[str, Any] = {
        "schema": "DAXLAB_MT5_BROKER_TIMEZONE_DIAGNOSTIC_V1",
        "observed_at_utc": now.astimezone(timezone.utc).isoformat(),
        "symbol": symbol,
        "decision_state": "HUMAN_REVIEW_REQUIRED",
        "auto_selected_timezone": None,
        "verification_state": "UNVERIFIED",
        "observations": observations,
        "execution_capability": "NONE",
        "order_execution_enabled": False,
        "notes": [
            "READ_ONLY",
            "DIAGNOSTIC_ONLY",
            "NO_AUTO_TIMEZONE_SELECTION",
            "NO_CREDENTIALS",
            "NO_ORDER_API",
        ],
    }
    _assert_credential_free(payload)
    payload["sha256"] = _fingerprint(payload)
    return payload
