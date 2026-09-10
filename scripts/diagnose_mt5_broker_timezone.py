#!/usr/bin/env python3
"""Read-only MT5 broker-timezone diagnostic; never auto-verifies a timezone.

The script reuses the existing credential-free `collect_probe()` function for a
small explicit set of IANA timezone candidates. It compares normalized tick clock
deltas and closed-M5 timestamps, but deliberately returns
`HUMAN_REVIEW_REQUIRED` instead of selecting or authorizing any timezone.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from mt5_windows_probe import collect_probe

_FORBIDDEN_KEYS = {"login", "password", "token", "secret", "email", "phone", "account_id"}


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


def diagnose(
    *,
    symbol: str,
    candidates: tuple[str, ...],
    bars: int,
    max_age_seconds: float,
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
        probe = collect_probe(
            configured_symbol=symbol,
            bars=bars,
            max_age_seconds=max_age_seconds,
            broker_timezone=candidate,
        )
        notes = list(probe.get("notes") or [])
        feed = probe.get("closed_m5_feed") or {}
        host = probe.get("host_probe") or {}
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
                "probe_sha256": probe.get("sha256"),
                "order_execution_enabled": False,
            }
        )

    payload: dict[str, Any] = {
        "schema": "DAXLAB_MT5_BROKER_TIMEZONE_DIAGNOSTIC_V1",
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="DE40")
    parser.add_argument("--candidate", action="append", dest="candidates", required=True)
    parser.add_argument("--bars", type=int, default=20)
    parser.add_argument("--max-age-seconds", type=float, default=600.0)
    parser.add_argument("--output", default="mt5_broker_timezone_diagnostic.json")
    args = parser.parse_args()

    payload = diagnose(
        symbol=args.symbol,
        candidates=tuple(args.candidates),
        bars=args.bars,
        max_age_seconds=args.max_age_seconds,
    )
    path = Path(args.output)
    if path.exists():
        raise RuntimeError(f"refusing to overwrite existing evidence file: {path}")
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    print(f"WROTE {path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
