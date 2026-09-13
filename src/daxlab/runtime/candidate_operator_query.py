"""Pure read model for the latest CAND-001 operator telemetry snapshot.

The database/view is only a storage owner. Consumers receive a freshly validated,
credential-free envelope and a query-time bar-age observation. This module has no
DB, MT5, web-server or execution dependency.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from math import isfinite
from hashlib import sha256
from typing import Any, Mapping

from daxlab.runtime.candidate_operator_telemetry import (
    _assert_credential_free,
    operator_timestamp,
    validate_candidate_operator_snapshot,
    browser_operator_snapshot,
)

from daxlab.runtime.decision import stable_fingerprint
from daxlab.runtime.mt5_windows_bundle import parse_windows_mt5_bundle
from daxlab.runtime.mt5_shadow_supervisor import parse_supervisor_build_observation
from daxlab.runtime.operator_snapshot import parse_operator_snapshot_payload
from daxlab.runtime.candidate_config import Cand001Config
from daxlab.runtime.candidate_shadow_host_cycle import build_cand001_forward_manifest
from daxlab.runtime.candidate_shadow_checkpoint import parse_candidate_shadow_checkpoint_payload
from daxlab.runtime.demo_transport_attempt_reservation import (
    DemoTransportAttemptReservation, demo_transport_restart_status,
)

CONSOLE_SCHEMA = "DAXLAB_READONLY_OPERATOR_CONSOLE_V1"

_SCHEMA = "DAXLAB_CAND001_OPERATOR_CURRENT_V1"


@dataclass(frozen=True, slots=True)
class CandidateOperatorCurrent:
    schema_version: str
    queried_at_utc: str
    source: str
    snapshot_fingerprint: str
    snapshot_generated_at: str
    current_bar_age_seconds: float | None
    payload: dict[str, Any]
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def __post_init__(self) -> None:
        if self.schema_version != _SCHEMA:
            raise ValueError("unsupported Candidate current-view schema")
        if self.source != "cand001_operator_current":
            raise ValueError("Candidate current-view source drift")
        if self.execution_capability != "NONE" or self.order_execution_enabled is not False:
            raise ValueError("Candidate current-view cannot authorize execution")
        if self.current_bar_age_seconds is not None and (
            not isfinite(self.current_bar_age_seconds) or self.current_bar_age_seconds < 0
        ):
            raise ValueError("current_bar_age_seconds must be non-negative")

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "queried_at_utc": self.queried_at_utc,
            "source": self.source,
            "snapshot_fingerprint": self.snapshot_fingerprint,
            "snapshot_generated_at": self.snapshot_generated_at,
            "current_bar_age_seconds": self.current_bar_age_seconds,
            "payload": self.payload,
            "execution_capability": self.execution_capability,
            "order_execution_enabled": self.order_execution_enabled,
        }


def build_candidate_operator_current(
    payload: Mapping[str, Any],
    *,
    queried_at: datetime,
) -> CandidateOperatorCurrent:
    """Validate one stored snapshot and derive query-time freshness evidence."""
    if queried_at.tzinfo is None:
        raise ValueError("queried_at must be timezone-aware")
    validate_candidate_operator_snapshot(payload)

    generated_at = operator_timestamp(payload["generated_at"], "generated_at")
    if generated_at > queried_at:
        raise ValueError("stored snapshot generated_at is in the future")

    runtime = payload["runtime"]
    last_bar_close_time = runtime.get("last_bar_close_time")
    current_age: float | None = None
    if last_bar_close_time is not None:
        close_time = datetime.fromisoformat(str(last_bar_close_time))
        if close_time.tzinfo is None:
            raise ValueError("stored last_bar_close_time must be timezone-aware")
        delta = (queried_at.astimezone(timezone.utc) - close_time.astimezone(timezone.utc)).total_seconds()
        if delta < 0:
            raise ValueError("stored last_bar_close_time is in the future")
        current_age = float(delta)

    return CandidateOperatorCurrent(
        schema_version=_SCHEMA,
        queried_at_utc=queried_at.astimezone(timezone.utc).isoformat(),
        source="cand001_operator_current",
        snapshot_fingerprint=str(payload["snapshot_fingerprint"]),
        snapshot_generated_at=str(payload["generated_at"]),
        current_bar_age_seconds=current_age,
        payload=dict(payload),
    )

def build_operator_console_projection(
    *, snapshot_payload: Mapping[str, Any] | None,
    bundle_payload: Mapping[str, Any] | None,
    heartbeat_payload: Mapping[str, Any] | None,
    queried_at: datetime,
    candidate_checkpoint_payload: Mapping[str, Any] | None = None,
    reservation: DemoTransportAttemptReservation | None = None,
    expected_reservation_fingerprint: str | None = None,
    broker_evidence_payload: Mapping[str, Any] | None = None,
    expected_broker_evidence_fingerprint: str | None = None,
    heartbeat_history: tuple[Mapping[str, Any], ...] = (),
) -> dict[str, Any]:
    """Project canonical observations; NEVER evaluate readiness or grant execution.

    Feed age uses its source-bound limit. Snapshot/host age has no reviewed maximum
    here, hence UNKNOWN / UNVERIFIED_THRESHOLD. Fetch time is supplied by the UI
    separately and cannot renew any source observation.
    """
    if queried_at.tzinfo is None or queried_at.utcoffset() is None:
        raise ValueError("operator queried_at must be timezone-aware")
    now = queried_at.astimezone(timezone.utc)
    snapshot = parse_operator_snapshot_payload(snapshot_payload) if snapshot_payload is not None else None
    current = build_candidate_operator_current(snapshot.as_dict(), queried_at=now) if snapshot else None
    display_snapshot = browser_operator_snapshot(snapshot.as_dict()) if snapshot else None
    for value in (bundle_payload, heartbeat_payload):
        if value is not None:
            _assert_credential_free(value)
    bundle = parse_windows_mt5_bundle(bundle_payload) if bundle_payload is not None else None
    heartbeat_at = None
    if heartbeat_payload is not None:
        if (
            heartbeat_payload.get("schema_version") != "DAXLAB_MT5_SHADOW_HEARTBEAT_V1"
            or heartbeat_payload.get("status") not in {"GREEN", "BLOCKED", "ERROR", "STOPPED"}
            or heartbeat_payload.get("execution_capability") != "NONE"
            or heartbeat_payload.get("order_execution_enabled") is not False
        ):
            raise ValueError("operator heartbeat contract invalid")
        heartbeat_at = operator_timestamp(heartbeat_payload.get("observed_at_utc"), "heartbeat observed_at")
        _observation_age(now, heartbeat_at)
        raw_blockers = heartbeat_payload.get("blockers")
        if not isinstance(raw_blockers, list) or any(not isinstance(v, str) for v in raw_blockers):
            raise ValueError("operator heartbeat blockers invalid")
    build = None
    if heartbeat_payload is not None and "build_observation" in heartbeat_payload:
        build = parse_supervisor_build_observation(heartbeat_payload["build_observation"])
        _observation_age(now, operator_timestamp(build["observed_at"], "build observed_at"))
    blockers = list(display_snapshot["decision"]["blockers"]) if snapshot else ["CANDIDATE_SNAPSHOT_MISSING"]
    if heartbeat_payload is None:
        blockers.append("SUPERVISOR_HEARTBEAT_MISSING")
    else:
        blockers.extend(heartbeat_payload["blockers"])
        if heartbeat_payload["status"] != "GREEN" or heartbeat_payload["blockers"]:
            blockers.append("SUPERVISOR_NOT_GREEN")
    if heartbeat_payload is not None and "candidate_snapshot_fingerprint" in heartbeat_payload:
        if snapshot is None or heartbeat_payload["candidate_snapshot_fingerprint"] != snapshot.snapshot_fingerprint:
            blockers.append("HEARTBEAT_CANDIDATE_SNAPSHOT_MISMATCH")
    if bundle is None:
        blockers.append("HOST_BUNDLE_MISSING")
    else:
        blockers.extend(bundle.blockers)
        if heartbeat_payload is None or heartbeat_payload.get("bundle_sha256") != bundle.fingerprint:
            blockers.append("HEARTBEAT_BUNDLE_CYCLE_MISMATCH")
        if heartbeat_payload is not None and bundle.host.symbols and heartbeat_payload.get("symbol") != bundle.host.symbols[0].name:
            blockers.append("HEARTBEAT_SYMBOL_MISMATCH")
        _observation_age(now, bundle.host.observed_at)
    feed = bundle.feed if bundle else None
    feed_at = feed.observed_at if feed else None
    close_time = feed.bars[-1].open_time + timedelta(minutes=5) if feed else None
    feed_age = _observation_age(now, close_time) if close_time else None
    max_feed_age = bundle_payload["closed_m5_feed"]["max_age_seconds"] if feed else None
    if feed:
        _observation_age(now, feed.observed_at)
        if bundle.host.observed_at != feed.observed_at:
            blockers.append("HOST_FEED_OBSERVATION_CYCLE_MISMATCH")
        if feed_age > max_feed_age:
            blockers.append("MARKET_DATA_STALE_AT_QUERY")
        if snapshot and snapshot.last_bar_close_time != close_time:
            blockers.append("CANDIDATE_BEHIND_OR_DIFFERENT_FEED")
    ctx = bundle.demo_account_context if bundle else None
    if ctx is None:
        blockers.append("DEMO_ACCOUNT_CONTEXT_MISSING")
    elif ctx.account_mode.value != "DEMO":
        blockers.append("ACCOUNT_MODE_NOT_DEMO")
    if feed is None or not feed.broker_timezone or feed.timestamp_interpretation != "EXPLICIT_BROKER_WALL_CLOCK":
        blockers.append("EXPLICIT_BROKER_TIME_CONTEXT_MISSING")
    elif bundle_payload["host_probe"].get("broker_timezone") != feed.broker_timezone:
        blockers.append("HOST_FEED_TIMEZONE_MISMATCH")
    if ctx and bundle.host.symbols and ctx.symbol != bundle.host.symbols[0].name:
        blockers.append("ACCOUNT_SYMBOL_MISMATCH")
    # These are evidence boundaries, independent of observed strategy ALLOWED.
    blockers.extend([
        "SNAPSHOT_FRESHNESS_THRESHOLD_UNVERIFIED", "HOST_FRESHNESS_THRESHOLD_UNVERIFIED",
        "ACCOUNT_WIDE_INVENTORY_NOT_VERIFIED", "BROKER_HISTORY_COMPLETENESS_NOT_VERIFIED",
        "DEMO_PAPER_EXECUTION_NOT_AUTHORIZED",
    ])
    host = bundle.host if bundle else None
    feed_state = "UNKNOWN" if not feed else "GREEN"
    if feed and feed_age > max_feed_age:
        feed_state = "STALE"
    elif feed and (not bundle.green or any(v in blockers for v in (
        "SUPERVISOR_NOT_GREEN", "HEARTBEAT_BUNDLE_CYCLE_MISMATCH",
        "HEARTBEAT_SYMBOL_MISMATCH", "HOST_FEED_OBSERVATION_CYCLE_MISMATCH",
        "HOST_FEED_TIMEZONE_MISMATCH", "ACCOUNT_SYMBOL_MISMATCH",
    ))):
        feed_state = "BLOCKED"
    snapshot_state = "STALE" if any(v in blockers for v in (
        "CANDIDATE_BEHIND_OR_DIFFERENT_FEED", "HEARTBEAT_CANDIDATE_SNAPSHOT_MISMATCH",
    )) else "UNKNOWN"
    tiles = {
        "BOT MODE": _tile("WARN" if snapshot and heartbeat_payload else "UNKNOWN", "SHADOW observation only"),
        "HOST": _tile("BLOCKED" if host and not host.engine_loop_healthy else "UNKNOWN", "UNVERIFIED_THRESHOLD"),
        "MT5": _tile("BLOCKED" if host and not host.terminal_connected else "UNKNOWN", "connected observed" if host and host.terminal_connected else "connection unknown/down"),
        "FEED": _tile(feed_state, "CLOSED-M5" if feed else "MISSING"),
        "CLOCK": _tile("BLOCKED" if host and not host.clock_ok else "UNKNOWN", feed.broker_timezone if feed else None),
        "ACCOUNT MODE": _tile("BLOCKED" if ctx and ctx.account_mode.value != "DEMO" else "UNKNOWN", ctx.account_mode.value if ctx else None),
        "SYMBOL": _tile("UNKNOWN", host.symbols[0].name if host and host.symbols else None),
        "PROTECTION": _tile("WAITING_EXTERNAL", "no current bound verdict"),
        "RECONCILIATION": _tile("UNKNOWN", "account-wide venue evidence missing"),
        "SNAPSHOT AGE": _tile(snapshot_state, "UNVERIFIED_THRESHOLD"),
        "EXECUTION": _tile("BLOCKED", "NONE / disabled"),
    }
    projection = {
        "schema_version": CONSOLE_SCHEMA,
        "queried_at_utc": now.isoformat(),
        "state": "BLOCKED", "source": "existing_local_supervisor_artifacts",
        "system": tiles, "blockers": list(dict.fromkeys(blockers)),
        "candidate": display_snapshot,
        "timestamps": {
            "snapshot_generated_at": snapshot.generated_at.isoformat() if snapshot else None,
            "snapshot_age_seconds": _observation_age(now, snapshot.generated_at) if snapshot else None,
            "snapshot_age_threshold": "UNVERIFIED_THRESHOLD",
            "last_closed_m5_close_time": close_time.isoformat() if close_time else None,
            "current_feed_age_seconds": feed_age, "source_max_feed_age_seconds": max_feed_age,
            "snapshot_measured_bar_age_seconds": snapshot.freshness_seconds if snapshot else None,
            "candidate_current_bar_age_seconds": current.current_bar_age_seconds if current else None,
            "host_observed_at": host.observed_at.isoformat() if host else None,
            "host_age_seconds": _observation_age(now, host.observed_at) if host else None,
            "host_age_threshold": "UNVERIFIED_THRESHOLD",
            "heartbeat_observed_at": heartbeat_at.isoformat() if heartbeat_at else None,
            "feed_observed_at": feed_at.isoformat() if feed_at else None,
            "broker_tick_observed_at": None,
        },
        "host_observation": {
            "terminal_connected": host.terminal_connected if host else None,
            "account_connected": host.account_connected if host else None,
            "engine_loop_healthy": host.engine_loop_healthy if host else None,
            "clock_ok": host.clock_ok if host else None,
            "heartbeat_status": heartbeat_payload["status"] if heartbeat_payload else None,
        },
        "clock": {
            "broker_timezone": feed.broker_timezone if feed else None,
            "timestamp_interpretation": feed.timestamp_interpretation if feed else None,
            "session_review_state": "WAITING_EXTERNAL", "broker_tick_time": None,
        },
        "account_context": ctx.to_payload() if ctx else None,
        "economics": {
            "state": "UNKNOWN", "verification": "OBSERVATION_IS_NOT_REVIEWED_RISK_BINDING",
            "observed_symbol_metadata": asdict(host.symbols[0]) if host and host.symbols else None,
        },
        "risk_loss_exposure": {"state": "WAITING_EXTERNAL", "values": None},
        "session_guard": {"state": "UNKNOWN"},
        "reserved_attempt": None,
        "broker_lifecycle": {"state": "UNKNOWN", "venue_state": "UNKNOWN"},
        "reconciliation": {
            "state": "UNKNOWN", "account_inventory_complete": False,
            "history_completeness": "UNKNOWN", "targeted_lookup_is_account_inventory": False,
            "resubmit_allowed": False, "session_slot_release_allowed": False,
        },
        "recovery": {
            "state": "UNKNOWN", "candidate_observed_state": display_snapshot["runtime"]["recovery_state"] if snapshot else None,
            "candidate_reconciliation_scope": "LOCAL_SHADOW_ONLY",
            "candidate_observed_reconciliation": display_snapshot["runtime"]["reconciliation_state"] if snapshot else None,
        },
        "build_identity": {
            "state": build["state"] if build else "UNKNOWN",
            "runtime_commit": build["commit_sha"] if build else None,
            "observation": build,
        },
        "provenance": {
            "snapshot_fingerprint": snapshot.snapshot_fingerprint if snapshot else None,
            "bundle_fingerprint": bundle.fingerprint if bundle else None,
            "evidence_kind": "OBSERVATION_ONLY_NOT_EXECUTION_AUTHORIZATION",
            "candidate_display_redacted": True,
            "candidate_cycle_binding": "BOUND" if heartbeat_payload is not None and "candidate_snapshot_fingerprint" in heartbeat_payload and "HEARTBEAT_CANDIDATE_SNAPSHOT_MISMATCH" not in blockers else "LEGACY_UNBOUND_OR_MISMATCH",
        },
        "execution_capability": "NONE", "order_execution_enabled": False,
        "shadow_authorized": True, "demo_paper_execution_authorized": False, "live_authorized": False,
    }
    if candidate_checkpoint_payload is not None:
        _assert_credential_free(candidate_checkpoint_payload)
        if bundle is None or not bundle.green or feed is None or not feed.broker_timezone:
            projection["blockers"].append("CHECKPOINT_CANONICAL_HOST_CONTEXT_UNAVAILABLE")
        else:
            manifest = build_cand001_forward_manifest(bundle)
            state = parse_candidate_shadow_checkpoint_payload(candidate_checkpoint_payload, run_manifest=manifest)
            if snapshot is None or state.pipeline.signal.last_close_time != snapshot.last_bar_close_time:
                raise ValueError("Candidate checkpoint/snapshot observation mismatch")
            if snapshot.config_fingerprint != Cand001Config().product_identity().config_fingerprint:
                raise ValueError("Candidate checkpoint/snapshot config mismatch")
            projection["candidate_admission"] = {
                "state": "UNKNOWN", "scope": "PERSISTED_CAND001_SHADOW_ONLY",
                "session_date": state.pipeline.admission.session_date,
                "trades_admitted": state.pipeline.admission.trades_admitted,
                "max_trades_per_session": Cand001Config().max_trades_per_session,
                "or_high": state.pipeline.signal.or_high, "or_low": state.pipeline.signal.or_low,
                "or_slots": list(state.pipeline.signal.or_slots),
                "last_close_time": state.pipeline.signal.last_close_time.isoformat() if state.pipeline.signal.last_close_time else None,
            }
            projection["session_guard"] = projection["candidate_admission"]
            projection["recovery"].update(
                checkpoint_validation="VALID_LOCAL_SHADOW_CHECKPOINT_NOT_BROKER_RECOVERY",
                checkpoint_fingerprint=candidate_checkpoint_payload["payload_fingerprint"],
                run_manifest_fingerprint=manifest.manifest_fingerprint,
                published_intent_count=len(state.publication.published_intent_ids),
                published_outcome_count=len(state.publication.published_outcome_ids),
            )
    if (reservation is None) != (expected_reservation_fingerprint is None):
        raise ValueError("reserved projection requires exact original fingerprint pin")
    if reservation is not None:
        reservation.__post_init__()
        if reservation.fingerprint != expected_reservation_fingerprint:
            raise ValueError("reserved projection provenance pin mismatch")
        original = reservation.prepared
        protection = original.protection
        projection["reserved_attempt"] = demo_transport_restart_status(reservation)
        projection["reserved_attempt"].update(
            original_evaluated_at=reservation.evaluated_at.isoformat(),
            prepared_fingerprint=original.fingerprint,
            account_context_fingerprint=reservation.account_context_fingerprint,
            authorization_fingerprint=reservation.authorization_fingerprint,
        )
        projection["broker_lifecycle"] = {
            "local_order_state": original.broker.lifecycle.state.value,
            "lifecycle_fingerprint": original.broker.lifecycle.fingerprint,
            "venue_state": "UNKNOWN", "venue_order_id": None, "fill_evidence": None,
        }
        projection["risk_loss_exposure"].update(
            state="UNKNOWN", scope="ORIGINAL_BOUND_PROTECTION_PROVENANCE_NOT_CURRENT_READINESS",
            original_protection_status=protection.status.value,
            protection_fingerprint=protection.fingerprint,
            risk_policy_fingerprint=protection.risk_policy_fingerprint,
            sizing_evidence_fingerprint=protection.sizing_evidence_fingerprint,
            loss_admission_evidence_fingerprint=protection.loss_admission_evidence_fingerprint,
            loss_observation_checkpoint_fingerprint=protection.loss_observation_checkpoint_fingerprint,
        )
        projection["session_guard"] = {
            "state": "UNKNOWN", "scope": "ORIGINAL_NEXTGEN_POST_CONSUMPTION_GUARD",
            "session_key": original.post_guard.state.session_key,
            "trades_admitted": original.post_guard.observation.trades_admitted,
            "max_trades_per_session": original.policy.max_trades_per_session,
            "checkpoint_fingerprint": original.post_guard.checkpoint_fingerprint,
            "observed_at": original.post_guard.observed_at.isoformat(),
        }
        projection["reconciliation"].update(
            state="QUERY_REQUIRED", required_next_action="QUERY_RECONCILE_REQUIRED",
            scope="LOCAL_RESERVED_ATTEMPT_NOT_VENUE_RECONCILIATION",
        )
        projection["system"]["RECONCILIATION"] = _tile("QUERY_REQUIRED", "local reservation; venue unknown")
        projection["system"]["PROTECTION"] = _tile("UNKNOWN", "original ALLOW_EVIDENCE; no execution authority")
        projection["blockers"].append("RESERVED_ATTEMPT_VENUE_QUERY_RECONCILIATION_REQUIRED")
        if ctx != reservation.account_context:
            projection["blockers"].append("RESERVATION_CURRENT_ACCOUNT_CONTEXT_MISMATCH")
            projection["system"]["ACCOUNT MODE"] = _tile("BLOCKED", "reserved/current context mismatch")
            projection["reconciliation"]["state"] = "BLOCKED"
            projection["system"]["RECONCILIATION"] = _tile("BLOCKED", "account context mismatch")
    # Preserve every blocker identity while refusing arbitrary provider text.
    # Canonical bundle blockers are computed by existing typed owners, not raw
    # exception strings. Unknown heartbeat codes retain a digest for incidents.
    known = set(bundle.blockers) if bundle else set()
    known.update({"PROBE_OR_CYCLE_FAILED", "RESUME_OR_BUNDLE_STATE_INVALID", "CLOCK_NOT_SAFE"})
    known.update(projection["blockers"] if heartbeat_payload is None else
                 [v for v in projection["blockers"] if v not in heartbeat_payload["blockers"]])
    projection["blockers"] = [v if v in known else
                              "UNKNOWN_SOURCE_BLOCKER:" + sha256(v.encode()).hexdigest()
                              for v in projection["blockers"]]
    projection["health_dimensions"] = {
        "liveness": {"state": "GREEN" if heartbeat_payload and heartbeat_payload["status"] != "STOPPED" else "UNKNOWN",
                     "scope": "PROCESS_OBSERVED_NOT_CURRENT_FRESHNESS", "observed_at": heartbeat_at.isoformat() if heartbeat_at else None},
        "readiness": {"state": "BLOCKED", "blockers": list(projection["blockers"]), "execution_authorization": False},
        "safety": {"state": "BLOCKED", "execution_capability": "NONE", "order_execution_enabled": False},
        "broker_truth": {"state": "UNKNOWN", "history_completeness": "UNKNOWN"},
    }
    if (broker_evidence_payload is None) != (expected_broker_evidence_fingerprint is None):
        raise ValueError("broker evidence requires original envelope fingerprint pin")
    projection["broker_inventory"] = {"state": "UNKNOWN", "rows": None, "observed_at": None,
                                      "freshness_threshold": "UNVERIFIED_THRESHOLD"}
    if broker_evidence_payload is not None:
        if reservation is None:
            raise ValueError("broker lookup requires original local reservation context")
        from daxlab.runtime.mt5_demo_evidence_transport import parse_reserved_demo_lookup_envelope
        _assert_credential_free(broker_evidence_payload)
        result, inventory = parse_reserved_demo_lookup_envelope(
            broker_evidence_payload, expected_fingerprint=expected_broker_evidence_fingerprint,
            reservation=reservation,
        )
        _observation_age(now, result.observed_at)
        same_bundle = bundle is not None and broker_evidence_payload["current_windows_bundle_fingerprint"] == bundle.fingerprint
        projection["broker_lifecycle"]["observed_lookup"] = result.to_payload()
        projection["broker_lifecycle"]["observed_lookup"]["blockers"] = [
            "LOOKUP_BLOCKER:" + sha256(v.encode()).hexdigest() for v in result.blockers]
        # Reports remain broker observations; never overwrite the local lifecycle.
        if result.venue_observation is not None:
            venue = result.to_payload()["venue_observation"]
            projection["broker_lifecycle"].update(venue_state=venue["venue_state"],
                                                 venue_order_id=venue["venue_order_id"], fill_evidence=venue)
        projection["reconciliation"].update(
            state="QUERY_REQUIRED" if same_bundle else "STALE", history_completeness="UNKNOWN",
            scope="OBSERVED_LOOKUP_NOT_APPLIED_LOCAL_OR_FULL_ACCOUNT_RECONCILIATION",
            observed_at=result.observed_at.isoformat(), freshness_threshold="UNVERIFIED_THRESHOLD",
        )
        if ctx != reservation.account_context:
            projection["reconciliation"]["state"] = "BLOCKED"
        if inventory is not None:
            _observation_age(now, inventory.collection_completed_at)
            inv_state = "BLOCKED" if inventory.status == "BLOCKED" or inventory.rows or ctx != inventory.account_context else "UNKNOWN"
            if not same_bundle:
                inv_state = "STALE"
            projection["broker_inventory"] = {
                "state": inv_state, "rows": [r.to_payload() for r in inventory.rows] if inventory.status == "OBSERVED" else None,
                "observed_at": inventory.collection_completed_at.isoformat(),
                "collection_started_at": inventory.collection_started_at.isoformat(),
                "time_source": "LOCAL_OBSERVATION_CLOCK_NOT_BROKER_CLOCK", "collection_is_atomic": False,
                "open_queries_completed": inventory.status == "OBSERVED",
                "freshness_threshold": "UNVERIFIED_THRESHOLD", "account_context": inventory.account_context.to_payload(),
                "observation_fingerprint": inventory.to_payload()["observation_fingerprint"],
                "broker_reconciliation_complete": False,
            }
            projection["blockers"].extend(v if v in {"ACCOUNT_HAS_OPEN_ORDERS", "ACCOUNT_HAS_OPEN_POSITIONS"}
                                          else "INVENTORY_BLOCKER:" + sha256(v.encode()).hexdigest()
                                          for v in inventory.blockers)
            if inventory.rows:
                projection["blockers"].append("UNEXPECTED_BROKER_INVENTORY_REVIEW_REQUIRED")
        if not same_bundle:
            projection["blockers"].append("BROKER_EVIDENCE_CURRENT_BUNDLE_MISMATCH")
        projection["provenance"]["broker_evidence_fingerprint"] = expected_broker_evidence_fingerprint
        projection["system"]["RECONCILIATION"] = _tile(projection["reconciliation"]["state"], "observed report; local state unchanged")
        projection["health_dimensions"]["readiness"]["blockers"] = list(projection["blockers"])
    projection["system"]["CODE"] = _tile("UNKNOWN", projection["build_identity"]["runtime_commit"])
    projection["system"]["SESSION"] = _tile("WAITING_EXTERNAL", "timezone/session review required")
    projection["system"]["INVENTORY"] = _tile(projection["broker_inventory"]["state"], "broker-observed; no repair authority")
    projection["health_matrix"] = {
        "runtime_backend_alive": _tile("GREEN", "canonical read completed at queried_at; not Candidate liveness"),
        "candidate_loop_alive": _tile(snapshot_state, "snapshot observation; freshness threshold unverified"),
        "mt5_connected": tiles["MT5"], "feed_fresh": tiles["FEED"],
        "closed_m5_fresh": tiles["FEED"], "broker_clock_observed": _tile("UNKNOWN", "no broker tick clock evidence"),
        "account_context_valid": tiles["ACCOUNT MODE"], "inventory_observed": tiles["INVENTORY"],
        "reconciliation_current": tiles["RECONCILIATION"], "protection_current": tiles["PROTECTION"],
        "telemetry_fresh": tiles["SNAPSHOT AGE"],
    }
    projection["freshness_matrix"] = {
        "operator_snapshot": {"observed_at": projection["timestamps"]["snapshot_generated_at"], "state": snapshot_state,
                              "threshold": "UNVERIFIED_THRESHOLD"},
        "closed_m5": {"observed_at": projection["timestamps"]["last_closed_m5_close_time"], "state": feed_state,
                      "threshold_seconds": max_feed_age, "threshold_owner": "SOURCE_CLOSED_M5_FEED"},
        "mt5_host": {"observed_at": projection["timestamps"]["host_observed_at"], "state": tiles["HOST"]["state"],
                     "threshold": "UNVERIFIED_THRESHOLD"},
        "broker_clock": {"observed_at": None, "state": "UNKNOWN", "threshold": "UNVERIFIED_THRESHOLD"},
        "inventory": {"observed_at": projection["broker_inventory"]["observed_at"], "state": tiles["INVENTORY"]["state"],
                      "threshold": "UNVERIFIED_THRESHOLD"},
        "reconciliation": {"observed_at": projection["reconciliation"].get("observed_at"), "state": tiles["RECONCILIATION"]["state"],
                           "threshold": "UNVERIFIED_THRESHOLD"},
        "economics": {"observed_at": projection["timestamps"]["host_observed_at"], "state": "UNKNOWN",
                      "threshold": "UNVERIFIED_THRESHOLD", "scope": "SYMBOL_METADATA_OBSERVATION_NOT_REVIEWED_BINDING"},
    }
    gates = {name: "WAITING_EXTERNAL" for name in (
        "exact_pr_head", "exact_runtime_build", "windows_host", "mt5_connection", "broker_clock",
        "timezone_session", "demo_account", "server", "symbol", "inventory", "broker_economics",
        "fixed_cash_risk_review", "loss_exposure_policy_review", "loss_observation_provenance", "protection",
    )}
    gates.update(feed="VERIFIED" if feed_state == "GREEN" else "BLOCKED" if feed_state in {"STALE", "BLOCKED"} else "UNKNOWN",
                 closed_m5="VERIFIED" if feed_state == "GREEN" else "BLOCKED" if feed_state in {"STALE", "BLOCKED"} else "UNKNOWN",
                 session_guard="UNKNOWN", reservation="BLOCKED" if reservation else "UNKNOWN",
                 reconciliation="BLOCKED" if reservation else "UNKNOWN", telemetry="BLOCKED" if snapshot_state == "STALE" else "UNKNOWN",
                 unexpected_broker_inventory="BLOCKED" if projection["broker_inventory"].get("rows") else "UNKNOWN",
                 execution_disabled="VERIFIED", first_demo_authorization="USER_AUTH")
    for gate, tile in (("windows_host", "HOST"), ("mt5_connection", "MT5"), ("demo_account", "ACCOUNT MODE"), ("broker_clock", "CLOCK"), ("inventory", "INVENTORY")):
        if tiles[tile]["state"] in {"BLOCKED", "STALE"}:
            gates[gate] = "BLOCKED"
    projection["monday_pre_demo"] = {"state": "BLOCKED", "gates": gates,
                                     "scope": "OBSERVATION_CHECKLIST_NOT_READINESS_VERDICT_OR_ORDER_AUTHORIZATION",
                                     "external_step": 2206, "host_lane": 2122}
    projection["alerts"] = [{"code": code, "state": "BLOCKED", "action": "OBSERVE_REVIEW_NO_REPAIR"}
                            for code in projection["blockers"]]
    timeline = []

    def event(stage: str, observed: datetime, fingerprint: str, scope: str, detail: Any):
        future_local = observed > now and scope.startswith("ORIGINAL_")
        if future_local:
            projection["blockers"].append("LOCAL_CHECKPOINT_TIME_AFTER_CURRENT_OBSERVATION")
        else:
            _observation_age(now, observed)
        row = {"stage": stage, "observed_at": observed.isoformat(), "source_fingerprint": fingerprint,
               "scope": scope, "detail": detail, "independent_transition_time": "UNKNOWN",
               "state": "BLOCKED" if future_local else "UNKNOWN"}
        row["event_id"] = stable_fingerprint(row)
        timeline.append(row)

    if feed:
        event("MARKET_OBSERVATION", feed.observed_at, bundle.fingerprint, "OBSERVED_CLOSED_M5", close_time.isoformat())
    if snapshot:
        for stage, section in (("SIGNAL", "signal"), ("ADMISSION", "admission"), ("DECISION", "decision")):
            event(stage, snapshot.generated_at, snapshot.snapshot_fingerprint,
                  "CURRENT_SNAPSHOT_GENERATED_AT_NOT_INDEPENDENT_TRANSITION_TIME", display_snapshot[section])
    if reservation:
        event("PREPARED", reservation.prepared.post_guard.observed_at, reservation.prepared.fingerprint,
              "ORIGINAL_POST_GUARD_OBSERVATION_NOT_PREPARED_CREATION_TIME_OR_VENUE_FACT", {"state": "REQUESTED"})
        event("RESERVATION", reservation.evaluated_at, reservation.fingerprint,
              "ORIGINAL_DURABLE_LOCAL_ATTEMPT_NOT_SUBMISSION_ACK", {"venue_state": "UNKNOWN"})
    if broker_evidence_payload is not None:
        event("QUERY_RECONCILIATION_OBSERVATION", result.observed_at, expected_broker_evidence_fingerprint,
              "BROKER_LOOKUP_NOT_APPLIED_RECONCILIATION", {"status": result.status.value})
    for hb in heartbeat_history:
        _assert_credential_free(hb)
        if (hb.get("execution_capability") != "NONE" or hb.get("order_execution_enabled") is not False
                or hb.get("status") not in {"GREEN", "BLOCKED", "ERROR", "STOPPED"}):
            raise ValueError("incident heartbeat safety/status contract invalid")
        event("SUPERVISOR_OBSERVATION", operator_timestamp(hb.get("observed_at_utc"), "incident heartbeat time"),
              stable_fingerprint(hb), "EXISTING_BOUNDED_HEARTBEAT_ARCHIVE_NOT_EXECUTION_JOURNAL",
              {"status": hb["status"], "blocker_count": len(hb.get("blockers", []))})
    unique_events = {row["event_id"]: row for row in timeline}
    projection["incident_timeline"] = {
        "events": sorted(unique_events.values(), key=lambda row: (row["observed_at"], row["stage"], row["event_id"])),
        "history_completeness": "UNKNOWN", "replay_scope": "DISPLAY_ONLY_NO_STATE_REPLAY",
        "missing_transition_times": "UNKNOWN_NOT_INFERRED_FROM_BROWSER_OR_BAR_TIME",
    }
    projection["blockers"] = list(dict.fromkeys(projection["blockers"]))
    projection["health_dimensions"]["readiness"]["blockers"] = list(projection["blockers"])
    _assert_credential_free(projection)
    projection["console_fingerprint"] = stable_fingerprint(projection)
    return projection


def _observation_age(now: datetime, observed: datetime) -> float:
    if observed.tzinfo is None or observed.utcoffset() is None:
        raise ValueError("operator observation must be timezone-aware")
    age = (now - observed).total_seconds()
    if age < 0:
        raise ValueError("operator observation is in the future")
    return age


def _tile(state: str, value: Any) -> dict[str, Any]:
    return {"state": state, "value": value}


def validate_operator_console_safety(value: Mapping[str, Any]) -> None:
    """Independent response guard: a read model can never enable execution."""
    if (value.get("schema_version") != CONSOLE_SCHEMA
            or value.get("execution_capability") != "NONE"
            or value.get("order_execution_enabled") is not False
            or value.get("shadow_authorized") is not True
            or value.get("demo_paper_execution_authorized") is not False
            or value.get("live_authorized") is not False
            or value.get("system", {}).get("EXECUTION", {}).get("state") not in {"BLOCKED", "DISABLED"}):
        raise ValueError("operator execution display contradicts disabled safety contract")
    _assert_credential_free(value)
