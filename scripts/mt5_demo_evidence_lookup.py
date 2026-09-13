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

from daxlab.runtime.mt5_demo_evidence_transport import (
    demo_mt5_lookup_request_from_payload,
    query_mt5_demo_evidence,
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    request_path = Path(args.request)
    output_path = Path(args.output)
    if output_path.exists():
        raise RuntimeError(f"refusing to overwrite existing evidence file: {output_path}")

    raw = json.loads(request_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("lookup request file must contain one JSON object")

    try:
        import MetaTrader5 as mt5
    except ImportError as exc:  # pragma: no cover - Windows host only
        raise RuntimeError("MetaTrader5 Python package is not installed") from exc

    if not mt5.initialize():
        code, message = mt5.last_error()
        raise RuntimeError(f"MT5 initialize failed: {code} {message}")
    try:
        observed_at = datetime.now(timezone.utc)
        result = execute_readonly_lookup(
            mt5=mt5,
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
