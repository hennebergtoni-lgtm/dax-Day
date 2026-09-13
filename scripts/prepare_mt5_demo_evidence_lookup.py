"""Prepare a strict MT5 DEMO read-only lookup request from existing evidence.

This script reuses the canonical AtomicFileStateStore and the Step-2198 query
projection. It performs no MT5 SDK calls and no broker side effects. A fresh
Windows MT5 bundle must be supplied explicitly, together with an explicit history
window and the expected reservation fingerprint.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path

from daxlab.adapters.file_state_store import AtomicFileStateStore
from daxlab.runtime.demo_transport_attempt_reservation import (
    build_reserved_demo_transport_query_request,
    load_reserved_demo_transport_attempt,
)
from daxlab.runtime.mt5_demo_evidence_transport import (
    build_demo_mt5_lookup_request,
    demo_mt5_lookup_request_to_payload,
)


@dataclass(frozen=True, slots=True)
class UtcClock:
    value: datetime

    def now(self) -> datetime:
        return self.value


def prepare_lookup_request(
    *,
    state_dir: Path,
    attempt_key: str,
    expected_reservation_fingerprint: str,
    bundle_payload: dict,
    history_from: datetime,
    history_to: datetime,
    evaluated_at: datetime,
) -> dict:
    """Build one pinned request without mutating state or contacting MT5."""
    store = AtomicFileStateStore(state_dir)
    reservation = load_reserved_demo_transport_attempt(
        store=store,
        key=attempt_key,
        expected_reservation_fingerprint=expected_reservation_fingerprint,
    )
    query_request = build_reserved_demo_transport_query_request(
        store=store,
        key=attempt_key,
        expected_reservation_fingerprint=expected_reservation_fingerprint,
        bundle_payload=bundle_payload,
        clock=UtcClock(evaluated_at),
    )
    lookup_request = build_demo_mt5_lookup_request(
        reservation=reservation,
        query_request=query_request,
        history_from=history_from,
        history_to=history_to,
    )
    return demo_mt5_lookup_request_to_payload(lookup_request)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state-dir", required=True)
    parser.add_argument("--attempt-key", required=True)
    parser.add_argument("--reservation-fingerprint", required=True)
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--history-from", required=True)
    parser.add_argument("--history-to", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    output_path = Path(args.output)
    if output_path.exists():
        raise RuntimeError(f"refusing to overwrite existing request file: {output_path}")
    bundle = json.loads(Path(args.bundle).read_text(encoding="utf-8"))
    if not isinstance(bundle, dict):
        raise ValueError("bundle file must contain one JSON object")

    evaluated_at = datetime.now(timezone.utc)
    payload = prepare_lookup_request(
        state_dir=Path(args.state_dir),
        attempt_key=args.attempt_key,
        expected_reservation_fingerprint=args.reservation_fingerprint,
        bundle_payload=bundle,
        history_from=_timestamp(args.history_from, "history_from"),
        history_to=_timestamp(args.history_to, "history_to"),
        evaluated_at=evaluated_at,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    print(f"WROTE {output_path.resolve()}")
    return 0


def _timestamp(value: str, field: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"invalid {field}") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field} must be timezone-aware")
    return parsed


if __name__ == "__main__":
    raise SystemExit(main())
