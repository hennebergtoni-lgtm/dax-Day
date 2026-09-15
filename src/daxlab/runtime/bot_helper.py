"""Bounded pure composition of existing owners, with a real SHADOW entrance veto.

No broker I/O, persistence, policy calculation or background worker lives here.
The existing runtime owns its state. Broker-read gaps in a readiness matrix
reach the safety entrance as a veto while host and data truth stay independent.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from daxlab.runtime.bot_helper_contract import (
    HelperEvent, HelperSubject, ROLES, digest, observation, read_utc, utc,
)
from daxlab.runtime.broker_execution_protection import evaluate_independent_pretrade_controls
from daxlab.runtime.candidate_config import Cand001Config
from daxlab.runtime.candidate_shadow_orchestrator import (
    Cand001ShadowState, Cand001ShadowStepResult, process_cand001_shadow_candle,
)
from daxlab.runtime.contracts import Candle, DataQualityState
from daxlab.runtime.quality import classify_session_sequence, source_agrees
from daxlab.runtime.time import to_berlin

STICKY = frozenset({"UNRESOLVED_STATE", "QUERY_REQUIRED",
                    "PTC_UNKNOWN_RESERVATION_QUERY_REQUIRED", "PTC_EMERGENCY_AUTHORITY_LATCHED"})


@dataclass(frozen=True, slots=True)
class HelperCheck:
    role: str
    status: str
    reason_codes: tuple[str, ...]
    source_time: str | None = None
    observed_at: str | None = None
    valid_until: str | None = None
    evidence_refs: tuple[str, ...] = ()
    dependency_event_ids: tuple[str, ...] = ()
    last_transition: str | None = None

    def as_dict(self) -> dict:
        return {"role": self.role, "status": self.status,
                "reason_codes": list(self.reason_codes), "source_time": self.source_time,
                "observed_at": self.observed_at, "valid_until": self.valid_until,
                "evidence_refs": list(self.evidence_refs),
                "dependency_event_ids": list(self.dependency_event_ids),
                "last_transition": self.last_transition}


@dataclass(frozen=True, slots=True)
class HelperCycle:
    subject: HelperSubject
    generated_at: str
    checks: tuple[HelperCheck, ...]
    blockers: tuple[str, ...]
    shadow_blockers: tuple[str, ...]
    event_refs: tuple[str, ...]
    evidence_scopes: tuple[str, ...]

    @property
    def shadow_allowed(self) -> bool:
        return not self.shadow_blockers

    def as_dict(self) -> dict:
        return {"schema": "DAXLAB_BOT_HELPER_CYCLE_V1", "subject": self.subject.as_dict(),
                "generated_at": self.generated_at, "checks": [c.as_dict() for c in self.checks],
                "blockers": list(self.blockers), "shadow_blockers": list(self.shadow_blockers),
                "shadow_allowed": self.shadow_allowed, "event_refs": list(self.event_refs),
                "evidence_scopes": list(self.evidence_scopes), "execution_status": "DISABLED",
                "execution_capability": "NONE", "order_execution_enabled": False}


def coordinate(events, *, subject: HelperSubject, now: datetime, previous=()) -> HelperCycle:
    """Fixed five-row reducer. Failures retain independent observations and causes."""
    if type(subject) is not HelperSubject:
        raise ValueError("HELPER_INVALID_SUBJECT")
    subject.__post_init__()
    current_time = read_utc(utc(now))
    global_reasons: set[str] = set()
    per_role = {role: set() for role in ROLES}
    by_role: dict[str, list[HelperEvent]] = {role: [] for role in ROLES}
    if not isinstance(events, (tuple, list)) or not isinstance(previous, (tuple, list)):
        events, previous = (), ()
        global_reasons.add("HELPER_FAILED")
    if len(events) > 256 or len(previous) > 256:
        # Bounded emergency output contains all expected roles, no silent green.
        events, previous = (), ()
        global_reasons.add("EVENT_OVERFLOW")
    if any(value is None for value in (subject.code_head, subject.config_fingerprint,
                                       subject.market_contract_fingerprint, subject.session_id)):
        global_reasons.add("IDENTITY_MISMATCH")
    seen: dict[str, HelperEvent] = {}
    validated: set[int] = set()
    previous_roles: dict[str, list[HelperEvent]] = {role: [] for role in ROLES}
    for event in (*previous, *events):
        if type(event) is not HelperEvent:
            global_reasons.add("HELPER_FAILED")
            continue
        # Revalidate frozen instances too; unsafe in-process construction isn't trusted.
        try:
            event.__post_init__()
            event.subject.__post_init__()
        except Exception:
            global_reasons.add("HELPER_FAILED")
            continue
        role = event.source_role
        if event.subject != subject:
            global_reasons.add("IDENTITY_MISMATCH")
            continue
        validated.add(id(event))
        existing = seen.get(event.event_id)
        if existing is not None and existing.payload_hash != event.payload_hash:
            per_role[role].add("CONTRADICTION")
        else:
            seen[event.event_id] = event
    for event in previous:
        if id(event) in validated:
            previous_roles[event.source_role].append(event)
            per_role[event.source_role].update(STICKY.intersection(event.reason_codes))
            if read_utc(event.observed_at) > current_time:
                global_reasons.add("CLOCK_ROLLBACK")
    delivered: set[str] = set()
    current_last: dict[str, HelperEvent] = {}
    for event in events:
        if id(event) not in validated:
            continue
        role = event.source_role
        if event.event_id in delivered:
            continue
        delivered.add(event.event_id)
        preceding = current_last.get(role)
        if preceding is not None and (
                event.source_sequence < preceding.source_sequence
                or read_utc(event.source_time) < read_utc(preceding.source_time)):
            per_role[role].add("SOURCE_ORDER")
        current_last[role] = event
        by_role[role].append(event)
        reasons = per_role[role]
        reasons.update(event.reason_codes)
        if event.status != "PASS" and not event.reason_codes:
            reasons.add("HELPER_FAILED")
        if read_utc(event.source_time) > current_time or read_utc(event.observed_at) > current_time:
            reasons.add("SOURCE_FUTURE")
        if event.valid_until is None:
            reasons.add("FRESHNESS_UNKNOWN")
        elif current_time > read_utc(event.valid_until):
            reasons.add("SOURCE_STALE")
        for prior in previous_roles[role]:
            if prior.producer_epoch != event.producer_epoch:
                reasons.add("PRODUCER_EPOCH_CHANGED")
            if (read_utc(prior.source_time) > read_utc(event.source_time)
                    or prior.source_sequence > event.source_sequence):
                reasons.add("SOURCE_ORDER")
    scopes = {e.evidence_scope for es in by_role.values() for e in es}
    if scopes.intersection({"SYNTHETIC", "REPLAY"}) and len(scopes) > 1:
        global_reasons.add("IDENTITY_MISMATCH")

    dependency_cache: dict[tuple[str, int], set[str]] = {}

    def dependencies(event: HelperEvent, path: tuple[str, ...] = ()) -> set[str]:
        if event.event_id in path:
            return {"DEPENDENCY_CYCLE"}
        if len(path) >= 8:
            return {"ROUTING_DEPTH"}
        cache_key = (event.event_id, len(path))
        if cache_key in dependency_cache:
            return dependency_cache[cache_key]
        result: set[str] = set()
        for ref in event.dependency_event_ids:
            target = seen.get(ref)
            if target is None:
                result.add("DEPENDENCY_MISSING")
            else:
                result.update(per_role[target.source_role])
                if target.valid_until is None:
                    result.add("FRESHNESS_UNKNOWN")
                elif current_time > read_utc(target.valid_until):
                    result.add("SOURCE_STALE")
                if read_utc(target.source_time) > current_time or read_utc(target.observed_at) > current_time:
                    result.add("SOURCE_FUTURE")
                if target.status != "PASS":
                    result.update(target.reason_codes or ("HELPER_FAILED",))
                result.update(dependencies(target, (*path, event.event_id)))
        dependency_cache[cache_key] = result
        return result

    for es in by_role.values():
        for event in es:
            per_role[event.source_role].update(dependencies(event))
    checks = []
    shadow_reasons = set(global_reasons)
    all_reasons = set(global_reasons)
    for role in ROLES:
        es = by_role[role]
        reasons = per_role[role] | global_reasons
        if not es:
            reasons.add("DEPENDENCY_MISSING")
        if role in {"H", "D"} or (role in {"S", "O"} and es) or reasons.intersection(STICKY):
            shadow_reasons.update(reasons)
        all_reasons.update(reasons)
        latest = max(es, key=lambda e: (e.source_time, e.source_sequence, e.event_id)) if es else None
        prior_latest = max(previous_roles[role], key=lambda e: (e.source_time, e.source_sequence), default=None)
        transition = latest.source_time if latest and prior_latest and (
            latest.status != prior_latest.status or latest.reason_codes != prior_latest.reason_codes
        ) else None
        checks.append(HelperCheck(
            role, "BLOCKED" if reasons and es else "UNKNOWN" if not es else "PASS",
            tuple(sorted(reasons)), latest.source_time if latest else None,
            latest.observed_at if latest else None, latest.valid_until if latest else None,
            tuple(sorted({ref for e in es for ref in e.evidence_refs})),
            tuple(sorted({ref for e in es for ref in e.dependency_event_ids})),
            transition,
        ))
    return HelperCycle(subject, utc(now), tuple(checks), tuple(sorted(all_reasons)),
                       tuple(sorted(shadow_reasons)), tuple(sorted(delivered)), tuple(sorted(scopes)))


@dataclass(frozen=True, slots=True)
class HelperShadowResult:
    state: Cand001ShadowState
    shadow_result: Cand001ShadowStepResult | None
    cycle: HelperCycle


def run_helper_shadow_candle(state, candle, *, observed_at, run_manifest, subject,
                             events, previous_candle=None, ptc_inputs=None,
                             max_receive_delay=timedelta(minutes=2),
                             evidence_scope="SYNTHETIC", previous_events=(),
                             config=None, sizing=None, fill_model=None, expected_subject=None):
    """Veto before *any* Candidate/session/intent mutation; return original state on block.

    max_receive_delay is the existing data-quality owner policy, explicitly supplied
    by live adapters using their current contract. No broker TTL or risk is inferred.
    """
    now = read_utc(utc(observed_at))
    cfg = config or Cand001Config()
    findings = list(events) if isinstance(events, (tuple, list)) else [None]
    data_reasons = set()
    source_time = now
    evidence_refs = ()
    valid_delay = max_receive_delay if isinstance(max_receive_delay, timedelta) and max_receive_delay >= timedelta(0) else None
    try:
        if type(candle) is not Candle or type(state) is not Cand001ShadowState:
            raise ValueError
        candle.__post_init__()
        if (type(candle.is_closed) is not bool or
                (candle.volume is not None and type(candle.volume) not in (int, float)) or
                any(type(v) not in (int, float) for v in
                    (candle.open, candle.high, candle.low, candle.close))):
            raise ValueError
        if not isinstance(max_receive_delay, timedelta) or max_receive_delay < timedelta(0):
            raise ValueError
        if (candle.symbol != cfg.symbol or candle.timeframe != cfg.bar_timeframe
                or subject.config_fingerprint != run_manifest.config_fingerprint
                or subject.session_id != to_berlin(candle.event_time).date().isoformat()
                or subject.run_id != run_manifest.manifest_fingerprint):
            data_reasons.add("IDENTITY_MISMATCH")
        if expected_subject is not None:
            if subject != expected_subject:
                data_reasons.add("IDENTITY_MISMATCH")
        elif subject.provider != "SYNTHETIC" or subject.instrument_id.value != cfg.symbol:
            # Real adapters must supply their explicit canonical binding. Never alias
            # an opaque IG epic/instrument to DE40 based on spelling.
            data_reasons.add("IDENTITY_MISMATCH")
        source_time = candle.close_time
        quality = classify_session_sequence(previous_candle, candle, timedelta(minutes=5),
                                            max_receive_delay=max_receive_delay)
        if quality is not DataQualityState.OK:
            data_reasons.add("DATA_" + quality.value)
        if now < candle.close_time or now < candle.received_at:
            data_reasons.add("DATA_CLOCK_SKEW")
        if now - candle.close_time > max_receive_delay:
            data_reasons.add("DATA_STALE")
        if candle.close_time - candle.event_time != timedelta(minutes=5):
            data_reasons.add("DATA_INVALID")
        anchor = state.pipeline.signal.last_close_time
        if anchor is not None and candle.close_time <= anchor:
            data_reasons.add("DATA_DUPLICATE" if candle.close_time == anchor else "DATA_OUT_OF_ORDER")
        if (previous_candle is not None and candle.event_time == previous_candle.event_time
                and source_agrees(previous_candle, candle) is not DataQualityState.OK):
            data_reasons.add("DATA_REVISION")
        evidence_refs = (digest({"event_time": utc(candle.event_time), "close_time": utc(candle.close_time),
                                 "ohlc": [candle.open, candle.high, candle.low, candle.close],
                                 "source_hash": digest(candle.source)}),)
    except Exception:
        data_reasons.add("DATA_INVALID")
        source_time = now
    # A future source is preserved by its safe reason, not a fabricated future envelope.
    safe_source = min(source_time, now)
    findings.append(observation(subject, "D", "BLOCKED" if data_reasons else "PASS",
                               source_time=safe_source, observed_at=now,
                               valid_until=safe_source + valid_delay if valid_delay is not None else None,
                               evidence_scope=evidence_scope,
                               reason_codes=tuple(sorted(data_reasons)), evidence_refs=evidence_refs,
                               evidence_schema="CLOSED_CANDLE_V1"))
    if ptc_inputs is not None:
        try:
            if type(ptc_inputs) is not dict or set(ptc_inputs) != {"policy", "observation", "protection"}:
                raise ValueError
            ptc = evaluate_independent_pretrade_controls(**ptc_inputs)
            reasons = tuple(ptc["blockers"])
            if (subject.account_fingerprint != ptc_inputs["policy"]["account_identity_sha256"]
                    or subject.instrument_identity_fingerprint != ptc_inputs["policy"]["instrument_identity_sha256"]
                    or subject.risk_policy_fingerprint != ptc["policy_fingerprint"]):
                reasons += ("IDENTITY_MISMATCH",)
            refs = (ptc["fingerprint"],)
        except Exception:
            reasons, refs = ("PROTECTION_UNKNOWN",), ()
        findings.append(observation(subject, "S", "BLOCKED" if reasons else "PASS",
                                   source_time=now, observed_at=now, valid_until=now,
                                   evidence_scope=evidence_scope, reason_codes=reasons,
                                   evidence_refs=refs, evidence_schema="DAX_INDEPENDENT_PTC_DIAGNOSTIC_V1"))
    cycle = coordinate(findings, subject=subject, now=now, previous=previous_events)
    if not cycle.shadow_allowed:
        return HelperShadowResult(state, None, cycle)
    # This is the existing sole state owner, not a second strategy or state machine.
    result = process_cand001_shadow_candle(
        state, candle, observed_at=observed_at, run_manifest=run_manifest,
        config=cfg, sizing=sizing, fill_model=fill_model,
        helper_events=tuple(findings), helper_subject=subject,
        helper_max_receive_delay=max_receive_delay,
        helper_instrument_id=subject.instrument_id if expected_subject is not None else None,
    )
    return HelperShadowResult(result.state, result, cycle)


def runtime_data_reasons(state, candle, *, observed_at, subject, config,
                         window=None, max_receive_delay=timedelta(minutes=2),
                         instrument_id=None) -> tuple[str, ...]:
    """Entrance recheck of actual candles, including the existing bounded catchup.

    A full source window permits historical initialization only while its latest
    source close is fresh. It is not receipt-time relabelling: original candles
    are unchanged and historical decisions remain REPLAY/HISTORICAL_CATCHUP.
    """
    reasons: set[str] = set()
    try:
        if type(candle) is not Candle or type(state) is not Cand001ShadowState:
            raise ValueError
        if not isinstance(max_receive_delay, timedelta) or max_receive_delay < timedelta(0):
            raise ValueError
        if window is None:
            candles = (candle,)
        elif type(window) is tuple and 1 <= len(window) <= 256 and candle in window:
            candles = window
        else:
            raise ValueError
        now = read_utc(utc(observed_at))
        bound_instrument = instrument_id.value if instrument_id is not None else config.symbol
        if (subject.instrument_id.value != bound_instrument
                or subject.session_id != to_berlin(candle.event_time).date().isoformat()
                or (subject.provider not in {"SYNTHETIC", "REPLAY"} and instrument_id is None)):
            reasons.add("IDENTITY_MISMATCH")
        previous = None
        latest = candles[-1]
        # Historical source allowance belongs to this explicit bounded window only.
        history_span = latest.close_time - candles[0].close_time
        for item in candles:
            if type(item) is not Candle:
                raise ValueError
            item.__post_init__()
            if (type(item.is_closed) is not bool or type(item.quality_state) is not DataQualityState
                    or (item.volume is not None and type(item.volume) not in (int, float))
                    or any(type(v) not in (int, float) for v in
                           (item.open, item.high, item.low, item.close))):
                raise ValueError
            if item.symbol != config.symbol or item.timeframe != config.bar_timeframe:
                reasons.add("IDENTITY_MISMATCH")
            if item.source != candle.source or item.close_time - item.event_time != timedelta(minutes=5):
                reasons.add("DATA_INVALID")
            quality = classify_session_sequence(previous, item, timedelta(minutes=5),
                                                max_receive_delay=max_receive_delay + history_span)
            if quality is not DataQualityState.OK:
                reasons.add("DATA_" + quality.value)
            if item.close_time > now or item.received_at > now:
                reasons.add("DATA_CLOCK_SKEW")
            previous = item
        if now - latest.close_time > max_receive_delay:
            reasons.add("DATA_STALE")
        anchor = state.pipeline.signal.last_close_time
        if anchor is not None:
            if candle.close_time <= anchor:
                reasons.add("DATA_DUPLICATE" if candle.close_time == anchor else "DATA_OUT_OF_ORDER")
            elif (to_berlin(candle.event_time).date() == to_berlin(anchor).date()
                  and candle.close_time - anchor > timedelta(minutes=5)):
                reasons.add("DATA_GAP")
    except Exception:
        reasons.add("DATA_INVALID")
    return tuple(sorted(reasons))


def run_ig_readiness_shadow(state, evidence, *, subject, observed_at, run_manifest,
                            instrument_id, epic, previous_candle=None,
                            evidence_scope="REPLAY") -> HelperShadowResult:
    """Actual V3 producer -> existing risk binding -> guarded Candidate entrance.

    The configured adapter explicitly binds its opaque instrument/epic to CAND-001.
    No symbol spelling heuristic, second connection, invented economics or PTC
    limits. Missing broker economics remain diagnostics, not a SHADOW ban. A
    missing/invalid actual price still blocks before Candidate admission.
    """
    from daxlab.adapters.ig_market_data import (
        PROVIDER_TIMESTAMP_SEMANTICS, canonical_ig_m5_contract, ig_m5_interval,
    )
    from daxlab.runtime.decision import stable_fingerprint
    from daxlab.runtime.ig_predemo_safety import (
        IG_DERIVATION_STAGES,
        bind_ig_risk_session_inputs,
    )

    now = read_utc(utc(observed_at))
    cfg = Cand001Config()
    findings = []
    candle = None
    delay = timedelta(0)
    try:
        if evidence.get("schema") != "DAXLAB_IG_PREDEMO_READINESS_V3":
            raise ValueError
        binding = bind_ig_risk_session_inputs(evidence, instrument_id=instrument_id)
        if (subject.provider != "IG" or subject.environment != "DEMO"
                or subject.instrument_id != instrument_id
                or evidence["market"].get("epic") != epic
                or subject.market_contract_fingerprint != stable_fingerprint(canonical_ig_m5_contract())
                or subject.account_fingerprint != binding.account_context_fingerprint):
            raise ValueError
        market_data = evidence["market_data"]
        if (market_data.get("timestamp_semantics") != PROVIDER_TIMESTAMP_SEMANTICS
                or market_data.get("freshness_basis") != "TRUE_CLOSE_TIME"):
            raise ValueError
        from math import isfinite
        age_limit = market_data["freshness_max_age_seconds"]
        if type(age_limit) not in (int, float) or not isfinite(age_limit) or age_limit < 0:
            raise ValueError
        # Source max-age must be the existing IG adapter policy, not a payload knob.
        from daxlab.adapters.ig_market_data import DEFAULT_MAX_AGE
        if age_limit != DEFAULT_MAX_AGE.total_seconds():
            raise ValueError
        delay = DEFAULT_MAX_AGE
        row = market_data["latest_closed_m5"]
        if market_data["status"] != "PASS" or row["source"] != f"IG_READ_ONLY:{epic}:MID_BID_ASK":
            raise ValueError
        source_time = read_utc(row["close_time"])
        event_time = read_utc(row["event_time"])
        source_interval = ig_m5_interval({"snapshotTimeUTC": row["snapshot_time_utc"]})
        if source_interval != (event_time, source_time):
            raise ValueError
        reads = evidence["authenticated_read_matrix"]["resources"]
        price_read = next(r for r in reads if r["resource"] == "M5_PRICES")
        if price_read["status"] != "PASS" or source_time > read_utc(price_read["request_started_at_utc"]):
            raise ValueError
        received = read_utc(price_read["response_observed_at_utc"])
        candle = Candle(
            symbol=cfg.symbol, timeframe=cfg.bar_timeframe,
            event_time=event_time, close_time=source_time,
            open=row["open"], high=row["high"], low=row["low"], close=row["close"],
            volume=row["volume"], source=row["source"], received_at=received, is_closed=True,
        )
        findings.append(observation(subject, "H", "PASS", source_time=received,
                                    observed_at=received, valid_until=source_time + delay,
                                    evidence_scope=evidence_scope, evidence_refs=(binding.source_fingerprint,),
                                    evidence_schema="DAXLAB_IG_PREDEMO_READINESS_V3"))
        read_blocked = any(row.get("status") != "PASS" for row in reads)
        derived = evidence.get("derived_processing")
        derived_blocked = (
            evidence.get("derived_processing_complete") is not True
            or not isinstance(derived, dict)
            or any(
                not isinstance(derived.get(stage), dict)
                or derived[stage].get("status") != "PASS"
                for stage in IG_DERIVATION_STAGES
            )
        )
        findings.append(observation(subject, "B", "BLOCKED" if read_blocked else "PASS",
                                    source_time=received, observed_at=received,
                                    valid_until=received,
                                    evidence_scope=evidence_scope,
                                    reason_codes=("BROKER_READ_FAILED",)
                                    if read_blocked else (),
                                    evidence_refs=(binding.source_fingerprint,),
                                    evidence_schema="DAXLAB_IG_PREDEMO_READINESS_V3"))
        findings.append(observation(
            subject, "S",
            "BLOCKED" if read_blocked or derived_blocked else "PASS",
            source_time=received, observed_at=received, valid_until=source_time + delay,
            evidence_scope=evidence_scope,
            reason_codes=("READINESS_BLOCKED",)
            if read_blocked or derived_blocked else (),
            evidence_refs=(binding.source_fingerprint,),
            evidence_schema="DAXLAB_IG_PREDEMO_READINESS_V3",
        ))
        findings.append(observation(
            subject, "O", "PASS", source_time=received, observed_at=received,
            valid_until=source_time + delay, evidence_scope=evidence_scope,
            evidence_refs=(binding.source_fingerprint,),
            evidence_schema="DAXLAB_IG_PREDEMO_READINESS_V3",
        ))
    except Exception:
        findings.append(observation(subject, "H", "BLOCKED", source_time=now,
                                    observed_at=now, valid_until=now, evidence_scope=evidence_scope,
                                    reason_codes=("IDENTITY_MISMATCH",)))
    return run_helper_shadow_candle(
        state, candle, observed_at=now, run_manifest=run_manifest, subject=subject,
        events=tuple(findings), previous_candle=previous_candle, max_receive_delay=delay,
        evidence_scope=evidence_scope, expected_subject=subject,
    )
