"""Credential-free Windows runner for read-only DEMO evidence lookup.

Input is a strict, fingerprinted lookup request produced by the repository's
Step-2200 runtime owner. The script only initializes the already logged-in MT5
terminal, reads account/open-order/order-history/deal-history evidence, writes a
credential-free result, and shuts MT5 down. It contains no order submission,
cancellation or modification path.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping

from daxlab.adapters.file_state_store import AtomicFileStateStore
from daxlab.domain.ports import StateStorePort
from daxlab.runtime.mt5_demo_evidence_transport import (
    demo_mt5_lookup_request_from_payload,
    query_mt5_demo_evidence,
    validate_reserved_demo_mt5_lookup,
)


RESULT_ENVELOPE_SCHEMA = "DAXLAB_MT5_DEMO_LOOKUP_ENVELOPE_V1"


def execute_readonly_lookup(
    *,
    mt5: Any,
    request_payload: Mapping[str, Any],
    observed_at: datetime,
) -> dict[str, Any]:
    """Execute only the typed read-only lookup against an initialized MT5 object."""
    request = demo_mt5_lookup_request_from_payload(request_payload)
    if observed_at.tzinfo is None or observed_at.utcoffset() is None:
        raise ValueError("observed_at must be timezone-aware")
    if observed_at > request.history_to:
        raise ValueError("MT5 DEMO lookup history window expired before execution")
    result = query_mt5_demo_evidence(
        mt5=mt5,
        request=request,
        observed_at=observed_at,
    )
    body = {
        "schema_version": RESULT_ENVELOPE_SCHEMA,
        "request_fingerprint": request.fingerprint,
        "result": result.to_payload(),
        "result_fingerprint": result.fingerprint,
        "observed_at": _iso(observed_at),
        "notes": [
            "READ_ONLY",
            "NO_CREDENTIALS",
            "NO_ORDER_API",
            "NO_RESUBMIT_AUTHORITY",
            "NO_SLOT_RELEASE_AUTHORITY",
            "DEMO_EVIDENCE_LOOKUP_ONLY",
        ],
        "execution_capability": "NONE",
        "order_execution_enabled": False,
    }
    return body | {"sha256": _fingerprint(body)}


def execute_reserved_readonly_lookup(
    *, mt5: Any, store: StateStorePort, attempt_key: str,
    expected_reservation_fingerprint: str, bundle_payload: Mapping[str, Any],
    request_payload: Mapping[str, Any], observed_at: datetime,
) -> dict[str, Any]:
    """Operational boundary: current reserved QUERY preflight before SDK reads."""
    validate_reserved_demo_mt5_lookup(
        store=store, key=attempt_key,
        expected_reservation_fingerprint=expected_reservation_fingerprint,
        request_payload=request_payload, bundle_payload=bundle_payload,
        evaluated_at=observed_at,
    )
    body = execute_readonly_lookup(
        mt5=mt5, request_payload=request_payload, observed_at=observed_at,
    )
    body.pop("sha256")
    body.update(
        attempt_key=attempt_key,
        reservation_fingerprint=expected_reservation_fingerprint,
        current_windows_bundle_fingerprint=bundle_payload["sha256"],
        query_preflight_evaluated_at=_iso(observed_at),
    )
    return body | {"sha256": _fingerprint(body)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--state-dir", required=True)
    parser.add_argument("--attempt-key", required=True)
    parser.add_argument("--reservation-fingerprint", required=True)
    parser.add_argument("--bundle", required=True)
    args = parser.parse_args()

    request_path = Path(args.request)
    output_path = Path(args.output)
    if output_path.exists():
        raise RuntimeError(f"refusing to overwrite existing evidence file: {output_path}")

    raw = json.loads(request_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("lookup request file must contain one JSON object")
    state_dir = Path(args.state_dir)
    if not state_dir.is_dir():
        raise ValueError("reserved lookup state directory must already exist")
    store = AtomicFileStateStore(state_dir)
    bundle = json.loads(Path(args.bundle).read_text(encoding="utf-8"))
    validate_reserved_demo_mt5_lookup(
        store=store, key=args.attempt_key,
        expected_reservation_fingerprint=args.reservation_fingerprint,
        request_payload=raw, bundle_payload=bundle,
        evaluated_at=datetime.now(timezone.utc),
    )

    try:
        import MetaTrader5 as mt5
    except ImportError as exc:  # pragma: no cover - Windows host only
        raise RuntimeError("MetaTrader5 Python package is not installed") from exc

    if not mt5.initialize():
        code, message = mt5.last_error()
        raise RuntimeError(f"MT5 initialize failed: {code} {message}")
    try:
        observed_at = datetime.now(timezone.utc)
        result = execute_reserved_readonly_lookup(
            mt5=mt5,
            store=store, attempt_key=args.attempt_key,
            expected_reservation_fingerprint=args.reservation_fingerprint,
            bundle_payload=bundle,
            request_payload=raw,
            observed_at=observed_at,
        )
    finally:
        mt5.shutdown()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    print(f"WROTE {output_path.resolve()}")
    return 0


def _iso(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("observed_at must be timezone-aware")
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _fingerprint(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
