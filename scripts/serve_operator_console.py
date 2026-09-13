#!/usr/bin/env python3
"""Loopback-only GET observation adapter over existing supervisor artifacts.

No database/MT5 dependency, credentials, control channel, persistence or orders.
Remote access requires a separately protected tunnel/proxy, never public binding.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
from http.server import BaseHTTPRequestHandler, HTTPServer
import base64
import json
from pathlib import Path
import re
from typing import Any

from daxlab.adapters.file_state_store import AtomicFileStateStore
from daxlab.domain.ports import StateStorePort
from daxlab.runtime.demo_transport_attempt_reservation import load_reserved_demo_transport_attempt

from daxlab.runtime.atomic_json import read_json_object
from daxlab.runtime.candidate_operator_telemetry import CredentialEvidenceError
from daxlab.runtime.candidate_operator_query import (
    CONSOLE_SCHEMA,
    build_operator_console_projection,
    validate_operator_console_safety,
)

WEB_ROOT = Path(__file__).resolve().parents[1] / "web"
_ASSETS = {
    "/": ("operator.html", "text/html; charset=utf-8"),
    "/operator.html": ("operator.html", "text/html; charset=utf-8"),
    "/operator.js": ("operator.js", "text/javascript; charset=utf-8"),
    "/operator.css": ("operator.css", "text/css; charset=utf-8"),
    "/research": ("index.html", "text/html; charset=utf-8"),
    "/status.json": ("status.json", "application/json; charset=utf-8"),
}


def read_local_operator_projection(
    state_dir: Path, *, queried_at: datetime, attempt_store: StateStorePort | None = None,
    attempt_key: str | None = None, reservation_fingerprint: str | None = None,
    broker_evidence_path: Path | None = None, broker_evidence_fingerprint: str | None = None,
) -> dict[str, Any]:
    """Read the sole existing source, with heartbeat read-before/read-after parity.

    Source files are individually atomic, not a multi-file transaction. Their
    canonical cross-bindings and stable heartbeat are checked, with no retry loop.
    """
    heartbeat_path = state_dir / "heartbeat.json"
    if heartbeat_path.exists() and heartbeat_path.stat().st_size > 4 * 1024 * 1024:
        raise ValueError("operator heartbeat exceeds read resource bound")
    before = heartbeat_path.read_bytes() if heartbeat_path.exists() else None

    def read(name: str):
        path = state_dir / name
        if not path.exists():
            return None
        # Resource bound only, never a runtime freshness/risk threshold.
        if path.stat().st_size > 4 * 1024 * 1024:
            raise ValueError("operator source exceeds read resource bound")
        return read_json_object(path)

    heartbeat = read("heartbeat.json")
    bundle = read("latest_bundle.json")
    snapshot = read("candidate_operator_snapshot.json")
    checkpoint = read("candidate_checkpoint.json")
    from daxlab.runtime.mt5_heartbeat_history import load_heartbeat_history
    history = load_heartbeat_history(state_dir / "heartbeat_history")
    reserved = load_reserved_demo_transport_attempt(
        store=attempt_store, key=attempt_key, expected_reservation_fingerprint=reservation_fingerprint,
    ) if attempt_store is not None else None
    broker_evidence = None
    if broker_evidence_path is not None:
        if broker_evidence_path.stat().st_size > 4 * 1024 * 1024:
            raise ValueError('broker evidence exceeds read resource bound')
        broker_evidence = read_json_object(broker_evidence_path)
    if heartbeat_path.exists() and heartbeat_path.stat().st_size > 4 * 1024 * 1024:
        raise ValueError("operator heartbeat exceeds read resource bound")
    after = heartbeat_path.read_bytes() if heartbeat_path.exists() else None
    if before != after:
        raise ValueError("operator source changed during read")
    view = build_operator_console_projection(
        snapshot_payload=snapshot, bundle_payload=bundle,
        heartbeat_payload=heartbeat, queried_at=queried_at,
        candidate_checkpoint_payload=checkpoint, reservation=reserved,
        expected_reservation_fingerprint=reservation_fingerprint,
        broker_evidence_payload=broker_evidence, expected_broker_evidence_fingerprint=broker_evidence_fingerprint,
        heartbeat_history=history,
    )
    view["source_available"] = all(v is not None for v in (heartbeat, bundle, snapshot))
    view["health_matrix"]["web_process_alive"] = {"state": "GREEN", "value": "this HTTP process responding only"}
    # This is a response projection, not another checkpoint/persistence digest.
    view.pop("console_fingerprint")
    from daxlab.runtime.decision import stable_fingerprint
    view["console_fingerprint"] = stable_fingerprint(view)
    return view


def source_unavailable_projection() -> dict[str, Any]:
    """Fixed bounded errors: no exception strings, filesystem paths or DSNs."""
    labels = (
        "BOT MODE", "HOST", "MT5", "FEED", "CLOCK", "ACCOUNT MODE", "SYMBOL",
        "PROTECTION", "RECONCILIATION", "SNAPSHOT AGE", "EXECUTION", "CODE", "SESSION", "INVENTORY",
    )
    return {
        "schema_version": CONSOLE_SCHEMA, "state": "UNKNOWN", "source_available": False,
        "queried_at_utc": datetime.now(timezone.utc).isoformat(),
        "system": {k: {"state": "BLOCKED" if k == "EXECUTION" else "UNKNOWN", "value": "SOURCE_UNAVAILABLE"} for k in labels},
        "blockers": ["RUNTIME_SOURCE_UNAVAILABLE_OR_INVALID", "EXECUTION_SAFETY_UNCONFIRMED"],
        "candidate": None, "timestamps": {}, "provenance": {"runtime_safety_observed": False},
        "execution_capability": "NONE", "order_execution_enabled": False,
        "shadow_authorized": True, "demo_paper_execution_authorized": False, "live_authorized": False,
    }


class OperatorReadServer(HTTPServer):
    """Only a fixed loopback socket and the existing artifact read adapter."""

    def __init__(
        self, *, state_dir: Path, port: int = 8765, attempt_store: StateStorePort | None = None,
        attempt_key: str | None = None, reservation_fingerprint: str | None = None,
    broker_evidence_path: Path | None = None, broker_evidence_fingerprint: str | None = None,
    ):
        values = (attempt_store, attempt_key, reservation_fingerprint)
        if any(v is not None for v in values) and any(v is None for v in values):
            raise ValueError("reserved console requires store/key/original fingerprint pin")
        if (broker_evidence_path is None) != (broker_evidence_fingerprint is None):
            raise ValueError("broker evidence requires source path and original fingerprint pin")
        self.broker_evidence_path = broker_evidence_path
        self.broker_evidence_fingerprint = broker_evidence_fingerprint
        self.attempt_store = attempt_store
        self.attempt_key = attempt_key
        self.reservation_fingerprint = reservation_fingerprint
        self.state_dir = Path(state_dir).resolve()
        super().__init__(("127.0.0.1", port), OperatorReadHandler)


class OperatorReadHandler(BaseHTTPRequestHandler):
    server: OperatorReadServer

    def log_message(self, format: str, *args: Any) -> None:
        # Neither request paths/headers nor provider exception text are logged.
        return

    def _same_origin(self) -> bool:
        port = self.server.server_address[1]
        allowed = {f"127.0.0.1:{port}", f"localhost:{port}"}
        host = self.headers.get("Host", "")
        if host not in allowed:
            return False
        origin = self.headers.get("Origin")
        if origin is not None and origin != f"http://{host}":
            return False
        return self.headers.get("Sec-Fetch-Site") not in {"cross-site"}

    def _send(self, status: int, body: bytes, content_type: str, *, static_html: bool = False) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store, max-age=0")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        script_hashes = []
        style_hashes = []
        if static_html:
            # Authorize ONLY the exact versioned research script/style content.
            text = body.decode("utf-8")
            for tag, hashes in (("script", script_hashes), ("style", style_hashes)):
                for inline in re.findall(rf"<{tag}[^>]*>(.*?)</{tag}>", text, re.DOTALL):
                    hashes.append("'sha256-" + base64.b64encode(sha256(inline.encode()).digest()).decode() + "'")
        csp = (
            "default-src 'self'; connect-src 'self'; script-src 'self' " + " ".join(script_hashes)
            + "; style-src 'self' " + " ".join(style_hashes)
            + "; object-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"
        )
        self.send_header("Content-Security-Policy", csp)
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status: int, value: dict[str, Any]) -> None:
        body = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
        self._send(status, body, "application/json; charset=utf-8")

    def do_GET(self) -> None:
        if not self._same_origin():
            self._json(403, {"state": "BLOCKED", "reason": "LOCAL_SAME_ORIGIN_ONLY"})
            return
        if self.path in {"/api/operator", "/healthz"}:
            try:
                view = read_local_operator_projection(
                    self.server.state_dir, queried_at=datetime.now(timezone.utc),
                    attempt_store=self.server.attempt_store, attempt_key=self.server.attempt_key,
                    reservation_fingerprint=self.server.reservation_fingerprint,
                    broker_evidence_path=self.server.broker_evidence_path,
                    broker_evidence_fingerprint=self.server.broker_evidence_fingerprint,
                )
                validate_operator_console_safety(view)
            except CredentialEvidenceError:
                view = source_unavailable_projection()
                view["blockers"].append("CREDENTIAL_FILTERING_FAILURE")
                view["alerts"] = [{"code": "CREDENTIAL_FILTERING_FAILURE", "state": "BLOCKED", "action": "OBSERVE_REVIEW_NO_REPAIR"}]
            except (OSError, ValueError, TypeError, KeyError, AttributeError, OverflowError, RecursionError):
                view = source_unavailable_projection()
            code = 200 if view["source_available"] else 503
            if self.path == "/healthz":
                self._json(code, {
                    "process_responding": True, "source_available": view["source_available"],
                    "runtime_state": view["state"], "execution_authorized": False,
                    "scope": "OBSERVATION_TRANSPORT_NOT_HOST_OR_BROKER_READINESS",
                })
            else:
                self._json(code, view)
            return
        asset = _ASSETS.get(self.path)
        if asset is None:
            self._json(404, {"state": "UNKNOWN", "reason": "READ_ROUTE_NOT_FOUND"})
            return
        filename, content_type = asset
        try:
            body = (WEB_ROOT / filename).read_bytes()
        except OSError:
            self._json(503, {"state": "UNKNOWN", "reason": "STATIC_ASSET_UNAVAILABLE"})
            return
        self._send(200, body, content_type, static_html=self.path == "/research")

    def _unsupported(self) -> None:
        self._json(405, {"state": "BLOCKED", "reason": "GET_ONLY_NO_CONTROL"})

    do_POST = _unsupported
    do_PUT = _unsupported
    do_PATCH = _unsupported
    do_DELETE = _unsupported
    do_OPTIONS = _unsupported
    do_HEAD = _unsupported


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-dir", default=".runtime/mt5_shadow")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--attempt-state-dir")
    parser.add_argument("--attempt-key")
    parser.add_argument("--reservation-fingerprint")
    parser.add_argument("--broker-evidence")
    parser.add_argument("--broker-evidence-fingerprint")
    args = parser.parse_args()
    with OperatorReadServer(
        state_dir=Path(args.state_dir), port=args.port,
        attempt_store=AtomicFileStateStore(Path(args.attempt_state_dir)) if args.attempt_state_dir else None,
        attempt_key=args.attempt_key, reservation_fingerprint=args.reservation_fingerprint,
        broker_evidence_path=Path(args.broker_evidence) if args.broker_evidence else None,
        broker_evidence_fingerprint=args.broker_evidence_fingerprint,
    ) as server:
        print("Read-only operator console: http://127.0.0.1:" + str(server.server_address[1]))
        server.serve_forever()


if __name__ == "__main__":
    main()
