"""Historical sequential SHADOW replay over already-closed M5 bars.

Historical replay is research evidence only. It is not broker/MT5 evidence and
has no order capability. Bars are accepted chronologically; exact duplicate
closed bars are idempotently suppressed. Each emitted observation sees only the
prefix ending at that closed bar, never a future bar.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from hashlib import sha256
import json
from typing import Any, Iterable

from daxlab.runtime.mt5_readonly import Mt5Bar
from daxlab.runtime.shadow_observation import (
    ShadowDecision,
    ShadowObservationInput,
    V112_ENGINE_SHA256,
    V112_EXPERIMENT_ID,
    build_shadow_decision,
)
from daxlab.runtime.shadow_soak import bar_fingerprint

_SCHEMA = "DAXLAB_HISTORICAL_SEQUENTIAL_REPLAY_V1"
_EVIDENCE_STATE = "HISTORICAL_REPLAY_ONLY_NOT_BROKER_EVIDENCE"
VERIFIED_DATASET_ID = "dax_m5_2014_2019_audited_v1"
VERIFIED_DATASET_SHA256 = "e51bba6cb2befe5e7eb0376318e43b096a3e2ecaae3f556019862975c60286a2"


@dataclass(frozen=True, slots=True)
class HistoricalReplayBinding:
    dataset_id: str = VERIFIED_DATASET_ID
    dataset_sha256: str = VERIFIED_DATASET_SHA256
    reference_experiment_id: str = V112_EXPERIMENT_ID
    reference_engine_sha256: str = V112_ENGINE_SHA256

    def __post_init__(self) -> None:
        if self.dataset_id != VERIFIED_DATASET_ID:
            raise ValueError("historical replay dataset ID mismatch")
        if self.dataset_sha256 != VERIFIED_DATASET_SHA256:
            raise ValueError("historical replay dataset fingerprint mismatch")
        if self.reference_experiment_id != V112_EXPERIMENT_ID:
            raise ValueError("historical replay V11.2 experiment mismatch")
        if self.reference_engine_sha256 != V112_ENGINE_SHA256:
            raise ValueError("historical replay V11.2 engine fingerprint mismatch")


@dataclass(frozen=True, slots=True)
class HistoricalDecisionLog:
    sequence: int
    bar_open_time: str
    bar_fingerprint: str
    visible_bar_count: int
    strategy_decision_state: str
    action: str
    reason_codes: tuple[str, ...]
    shadow_decision_id: str
    log_id: str


@dataclass(frozen=True, slots=True)
class HistoricalReplayRecord:
    sequence: int
    bar_open_time: str
    bar_fingerprint: str
    visible_bar_count: int
    decision: ShadowDecision
    decision_log: HistoricalDecisionLog


@dataclass(frozen=True, slots=True)
class HistoricalReplayResult:
    schema_version: str
    evidence_state: str
    symbol: str
    timeframe_minutes: int
    records: tuple[HistoricalReplayRecord, ...]
    replay_fingerprint: str
    dataset_id: str
    dataset_sha256: str
    reference_experiment_id: str
    reference_engine_sha256: str
    duplicates_suppressed: int = 0
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False


def run_historical_sequential_replay(
    bars: Iterable[Mt5Bar],
    *,
    symbol: str = "DAX",
    timeframe_minutes: int = 5,
    binding: HistoricalReplayBinding | None = None,
) -> HistoricalReplayResult:
    """Feed closed M5 bars one-by-one with duplicate idempotency."""
    if not symbol.strip():
        raise ValueError("symbol must be non-empty")
    if timeframe_minutes != 5:
        raise ValueError("historical sequential replay currently requires M5")
    active_binding = binding or HistoricalReplayBinding()
    HistoricalReplayBinding(
        dataset_id=active_binding.dataset_id,
        dataset_sha256=active_binding.dataset_sha256,
        reference_experiment_id=active_binding.reference_experiment_id,
        reference_engine_sha256=active_binding.reference_engine_sha256,
    )

    records: list[HistoricalReplayRecord] = []
    seen_fingerprints: set[str] = set()
    seen_time_identity: dict[str, str] = {}
    previous_unique_time = None
    duplicates = 0
    minimum_delta = timedelta(minutes=timeframe_minutes)

    for bar in tuple(bars):
        _validate_bar(bar)
        fingerprint = bar_fingerprint(bar)
        time_key = bar.open_time.isoformat()
        existing_identity = seen_time_identity.get(time_key)
        if existing_identity is not None and existing_identity != fingerprint:
            raise ValueError("historical replay duplicate timestamp has conflicting OHLC")
        if fingerprint in seen_fingerprints:
            duplicates += 1
            continue
        if previous_unique_time is not None:
            if bar.open_time <= previous_unique_time:
                raise ValueError("historical replay bars must be strictly chronological")
            if bar.open_time - previous_unique_time < minimum_delta:
                raise ValueError("historical replay bars overlap M5 chronology")

        sequence = len(records)
        visible_bar_count = sequence + 1
        observed_at = bar.open_time + timedelta(minutes=timeframe_minutes, seconds=1)
        decision = build_shadow_decision(
            ShadowObservationInput(
                observed_at=observed_at,
                symbol=symbol,
                closed_bar_fingerprint=fingerprint,
                host_read_only_healthy=True,
                feed_fresh=True,
                clock_ok=True,
                single_instance_lock_held=True,
                reference_experiment_id=active_binding.reference_experiment_id,
                reference_engine_sha256=active_binding.reference_engine_sha256,
            )
        )
        if decision.action != "NO_ORDER":
            raise RuntimeError("historical replay emitted order-capable action")
        decision_log = _decision_log(
            sequence=sequence,
            bar=bar,
            bar_identity=fingerprint,
            visible_bar_count=visible_bar_count,
            decision=decision,
        )
        records.append(
            HistoricalReplayRecord(
                sequence=sequence,
                bar_open_time=bar.open_time.isoformat(),
                bar_fingerprint=fingerprint,
                visible_bar_count=visible_bar_count,
                decision=decision,
                decision_log=decision_log,
            )
        )
        seen_fingerprints.add(fingerprint)
        seen_time_identity[time_key] = fingerprint
        previous_unique_time = bar.open_time

    replay_fingerprint = _hash(
        {
            "schema_version": _SCHEMA,
            "symbol": symbol,
            "timeframe_minutes": timeframe_minutes,
            "bar_fingerprints": [record.bar_fingerprint for record in records],
            "decision_ids": [record.decision.decision_id for record in records],
            "decision_log_ids": [record.decision_log.log_id for record in records],
            "dataset_id": active_binding.dataset_id,
            "dataset_sha256": active_binding.dataset_sha256,
            "reference_experiment_id": active_binding.reference_experiment_id,
            "reference_engine_sha256": active_binding.reference_engine_sha256,
        }
    )
    return HistoricalReplayResult(
        schema_version=_SCHEMA,
        evidence_state=_EVIDENCE_STATE,
        symbol=symbol,
        timeframe_minutes=timeframe_minutes,
        records=tuple(records),
        replay_fingerprint=replay_fingerprint,
        dataset_id=active_binding.dataset_id,
        dataset_sha256=active_binding.dataset_sha256,
        reference_experiment_id=active_binding.reference_experiment_id,
        reference_engine_sha256=active_binding.reference_engine_sha256,
        duplicates_suppressed=duplicates,
    )


def _decision_log(
    *,
    sequence: int,
    bar: Mt5Bar,
    bar_identity: str,
    visible_bar_count: int,
    decision: ShadowDecision,
) -> HistoricalDecisionLog:
    state = "NO_STRATEGY_DECISION"
    reasons = tuple(decision.reason_codes) + ("HISTORICAL_REPLAY_OBSERVATION_ONLY",)
    payload = {
        "sequence": sequence,
        "bar_open_time": bar.open_time.isoformat(),
        "bar_fingerprint": bar_identity,
        "visible_bar_count": visible_bar_count,
        "strategy_decision_state": state,
        "action": decision.action,
        "reason_codes": list(reasons),
        "shadow_decision_id": decision.decision_id,
    }
    return HistoricalDecisionLog(
        sequence=sequence,
        bar_open_time=bar.open_time.isoformat(),
        bar_fingerprint=bar_identity,
        visible_bar_count=visible_bar_count,
        strategy_decision_state=state,
        action=decision.action,
        reason_codes=reasons,
        shadow_decision_id=decision.decision_id,
        log_id=_hash(payload),
    )


def _validate_bar(bar: Mt5Bar) -> None:
    if bar.open_time.tzinfo is None:
        raise ValueError("historical replay timestamps must be timezone-aware")
    if bar.high < max(bar.open, bar.close) or bar.low > min(bar.open, bar.close):
        raise ValueError("historical replay OHLC envelope invalid")
    if bar.high < bar.low:
        raise ValueError("historical replay high below low")


def _hash(value: dict[str, Any]) -> str:
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return sha256(canonical.encode("utf-8")).hexdigest()
