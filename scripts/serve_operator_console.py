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
from math import isfinite
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
        "system": {k: {"state": "DISABLED" if k == "EXECUTION" else "UNKNOWN", "value": "SOURCE_UNAVAILABLE"} for k in labels},
        "blockers": ["RUNTIME_SOURCE_UNAVAILABLE_OR_INVALID", "EXECUTION_SAFETY_UNCONFIRMED"],
        "candidate": None, "timestamps": {}, "provenance": {"runtime_safety_observed": False},
        "execution_capability": "NONE", "order_execution_enabled": False,
        "shadow_authorized": True, "demo_paper_execution_authorized": False, "live_authorized": False,
    }


def build_ig_operator_projection(
    evidence: dict[str, Any], *, queried_at: datetime, instrument_id: str,
) -> dict[str, Any]:
    """Explicit V3 source on the existing view; no invented MT5 liveness.

    The configured instrument binding and original semantic fingerprint are
    validated by the canonical safety owner. GET time never refreshes evidence.
    No raw provider strings, URLs, exception text or arbitrary pointers escape.
    """
    from daxlab.domain.market import InstrumentId
    from daxlab.adapters.ig_market_data import DEFAULT_MAX_AGE
    from daxlab.runtime.bot_helper_contract import HelperSubject, observation, read_utc
    from daxlab.runtime.bot_helper import coordinate
    from daxlab.runtime.ig_predemo_safety import bind_ig_risk_session_inputs
    from daxlab.runtime.decision import stable_fingerprint

    if evidence.get("schema") != "DAXLAB_IG_PREDEMO_READINESS_V3":
        raise ValueError("IG operator requires explicit V3 source")
    binding = bind_ig_risk_session_inputs(evidence, instrument_id=InstrumentId(instrument_id))
    source_time = read_utc(evidence["collected_at_utc"])
    if (source_time.tzinfo is None or queried_at.tzinfo is None
            or source_time.utcoffset() is None or queried_at.utcoffset() is None
            or source_time > queried_at):
        raise ValueError("IG source clock invalid")
    age = (queried_at - source_time).total_seconds()
    # V3 has no verified runtime head/policy/session binding. Explicit unknowns
    # block eligibility in the same coordinator used at the runtime entrance.
    subject = HelperSubject(
        run_id=binding.source_fingerprint, provider="IG", environment="DEMO",
        account_fingerprint=binding.account_context_fingerprint,
        instrument_id=InstrumentId(instrument_id), market_contract_fingerprint=None,
        session_id=None, code_head=None, config_fingerprint=None,
    )
    events = []
    market_data = evidence.get("market_data")
    market_data = market_data if isinstance(market_data, dict) else {}
    for role, reason in (("H", "HOST_UNKNOWN"), ("D", "DEPENDENCY_MISSING"),
                         ("B", "BROKER_UNKNOWN"), ("S", "PROTECTION_UNKNOWN"),
                         ("O", "DEPENDENCY_MISSING")):
        event_time, valid_until, status, reasons = source_time, None, "UNKNOWN", (reason,)
        if role == "D" and market_data.get("status") == "PASS":
            latest = market_data.get("latest_closed_m5", {})
            threshold = market_data.get("freshness_max_age_seconds")
            if (isinstance(latest, dict) and type(threshold) in (int, float)
                    and threshold >= 0):
                try:
                    if not isfinite(threshold) or threshold != DEFAULT_MAX_AGE.total_seconds():
                        raise ValueError("invalid source freshness policy")
                    candidate_time = read_utc(latest.get("close_time"))
                    candidate_deadline = candidate_time + DEFAULT_MAX_AGE
                    if candidate_time > source_time:
                        raise ValueError("future closed bar")
                    event_time, valid_until = candidate_time, candidate_deadline
                    status, reasons = "PASS", ()
                except (ValueError, TypeError, OverflowError):
                    # One malformed derived time cannot erase the eight raw reads.
                    status, reasons = "UNKNOWN", ("DATA_INVALID",)
        events.append(observation(
            subject, role, status, source_time=event_time, observed_at=source_time,
            valid_until=valid_until, evidence_scope="REPLAY", reason_codes=reasons,
            evidence_refs=(binding.source_fingerprint,),
            dependency_event_ids=(events[2].event_id,) if role == "S" else (),
        ))
    cycle = coordinate(tuple(events), subject=subject, now=queried_at)
    cycle_view = cycle.as_dict()
    view = source_unavailable_projection()
    view.update({
        "state": "BLOCKED" if binding.blockers or cycle.blockers else "UNKNOWN",
        "source_available": True, "queried_at_utc": queried_at.isoformat(),
        "read_outcomes": [{"resource": row["resource"], "status": row["status"] if row.get("status") in {"PASS", "FAIL", "BLOCKED", "UNKNOWN"} else "UNKNOWN"}
                          for row in evidence["authenticated_read_matrix"]["resources"]],
        "blockers": list(binding.blockers) + list(cycle.blockers) + ["SOURCE_FRESHNESS_POLICY_UNKNOWN"],
        "timestamps": {"snapshot_generated_at": source_time.isoformat(),
                       "snapshot_age_seconds": age, "heartbeat_observed_at": None},
        "provenance": {"source": "IG_READINESS_V3", "snapshot_fingerprint": binding.source_fingerprint,
                       "evidence_kind": "REPLAY", "runtime_safety_observed": True},
        "health_matrix": {"web_process_alive": {"state": "GREEN", "value": "HTTP response only"},
                          "runtime": {"state": "UNKNOWN"}, "mt5": {"state": "UNKNOWN"},
                          "broker": {"state": "UNKNOWN"}},
        "freshness_matrix": {"source": "IG_READINESS_V3", "age_seconds": age,
                             "state": "UNKNOWN", "reason": "SOURCE_FRESHNESS_POLICY_UNKNOWN"},
        "risk_loss_exposure": {"state": "BLOCKED" if binding.blockers else "UNKNOWN"},
        "helper_diagnostics": {"source": "IG_READINESS_V3", "age_seconds": age,
            "reason": list(binding.blockers) + list(cycle.blockers) + ["SOURCE_FRESHNESS_POLICY_UNKNOWN"],
            "dependencies": ["IG_RISK_SESSION_INPUTS", "SOURCE_FRESHNESS_POLICY"],
            "evidence": binding.source_fingerprint, "evidence_scope": "REPLAY",
            "last_transition": None, "checks": cycle_view["checks"]},
    })
    view["helper_cycle"] = cycle_view
    view["system"]["EXECUTION"] = {"state": "DISABLED", "value": "NONE / disabled"}
    view["system"]["BOT MODE"] = {"state": "UNKNOWN", "value": "IG READ-ONLY OBSERVATION"}
    view["system"]["SNAPSHOT AGE"] = {"state": "UNKNOWN", "value": age}
    view["console_fingerprint"] = stable_fingerprint(view)
    validate_operator_console_safety(view)
    return view


class OperatorReadServer(HTTPServer):
    """Only a fixed loopback socket and the existing artifact read adapter."""

    def __init__(
        self, *, state_dir: Path, port: int = 8765, attempt_store: StateStorePort | None = None,
        attempt_key: str | None = None, reservation_fingerprint: str | None = None,
    broker_evidence_path: Path | None = None, broker_evidence_fingerprint: str | None = None,
        ig_evidence_path: Path | None = None, ig_evidence_fingerprint: str | None = None,
        ig_instrument_id: str | None = None,
    ):
        ig_values = (ig_evidence_path, ig_evidence_fingerprint, ig_instrument_id)
        if any(v is not None for v in ig_values) and any(v is None for v in ig_values):
            raise ValueError("IG source requires path, original fingerprint and instrument binding")
        if ig_evidence_path is not None and (attempt_store is not None or broker_evidence_path is not None):
            raise ValueError("IG and MT5 sources cannot be mixed")
        self.ig_evidence_path = ig_evidence_path
        self.ig_evidence_fingerprint = ig_evidence_fingerprint
        self.ig_instrument_id = ig_instrument_id
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

    def _read_projection(self) -> dict[str, Any]:
        if self.server.ig_evidence_path is not None:
            path = self.server.ig_evidence_path
            if path.stat().st_size > 4 * 1024 * 1024:
                raise ValueError("IG source exceeds read resource bound")
            evidence = read_json_object(path)
            if evidence.get("fingerprint") != self.server.ig_evidence_fingerprint:
                raise ValueError("IG original fingerprint binding mismatch")
            return build_ig_operator_projection(
                evidence, queried_at=datetime.now(timezone.utc),
                instrument_id=self.server.ig_instrument_id,
            )
        return read_local_operator_projection(
                    self.server.state_dir, queried_at=datetime.now(timezone.utc),
                    attempt_store=self.server.attempt_store, attempt_key=self.server.attempt_key,
                    reservation_fingerprint=self.server.reservation_fingerprint,
                    broker_evidence_path=self.server.broker_evidence_path,
                    broker_evidence_fingerprint=self.server.broker_evidence_fingerprint,
                )

    def do_GET(self) -> None:
        if not self._same_origin():
            self._json(403, {"state": "BLOCKED", "reason": "LOCAL_SAME_ORIGIN_ONLY"})
            return
        if self.path in {"/api/operator", "/healthz"}:
            try:
                view = self._read_projection()
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
    parser.add_argument("--ig-evidence")
    parser.add_argument("--ig-evidence-fingerprint")
    parser.add_argument("--ig-instrument-id")
    args = parser.parse_args()
    with OperatorReadServer(
        state_dir=Path(args.state_dir), port=args.port,
        attempt_store=AtomicFileStateStore(Path(args.attempt_state_dir)) if args.attempt_state_dir else None,
        attempt_key=args.attempt_key, reservation_fingerprint=args.reservation_fingerprint,
        broker_evidence_path=Path(args.broker_evidence) if args.broker_evidence else None,
        broker_evidence_fingerprint=args.broker_evidence_fingerprint,
        ig_evidence_path=Path(args.ig_evidence) if args.ig_evidence else None,
        ig_evidence_fingerprint=args.ig_evidence_fingerprint, ig_instrument_id=args.ig_instrument_id,
    ) as server:
        print("Read-only operator console: http://127.0.0.1:" + str(server.server_address[1]))
        server.serve_forever()


if __name__ == "__main__":
    main()
