from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from daxlab.domain.execution import ExecutionIntent, OrderSide
from daxlab.domain.market import Candle, DataQualityState, InstrumentId
from daxlab.domain.ports import (
    CandleSourcePort,
    ClockPort,
    ExecutionIntentSinkPort,
    StateStorePort,
)


UTC = timezone.utc


def _candle(**overrides: object) -> Candle:
    values: dict[str, object] = {
        "instrument_id": InstrumentId("DAX40.CFD"),
        "timeframe": "5m",
        "event_time": datetime(2026, 9, 11, 8, 0, tzinfo=UTC),
        "close_time": datetime(2026, 9, 11, 8, 5, tzinfo=UTC),
        "open": 25000.0,
        "high": 25020.0,
        "low": 24990.0,
        "close": 25010.0,
        "volume": 100.0,
        "source": "fixture",
        "received_at": datetime(2026, 9, 11, 8, 5, 1, tzinfo=UTC),
        "is_closed": True,
    }
    values.update(overrides)
    return Candle(**values)  # type: ignore[arg-type]


def test_instrument_identity_is_opaque_and_broker_neutral() -> None:
    instrument_id = InstrumentId("DAX40.CFD")
    assert str(instrument_id) == "DAX40.CFD"
    with pytest.raises(ValueError, match="instrument id"):
        InstrumentId("  DAX40.CFD")


def test_candle_requires_canonical_utc_and_safe_closed_data() -> None:
    candle = _candle()
    assert candle.safe_for_decision is True

    unsafe = _candle(quality_state=DataQualityState.STALE)
    assert unsafe.safe_for_decision is False

    non_utc = timezone(timedelta(hours=2))
    with pytest.raises(ValueError, match="UTC"):
        _candle(event_time=datetime(2026, 9, 11, 10, 0, tzinfo=non_utc))


def test_candle_rejects_invalid_market_values() -> None:
    with pytest.raises(ValueError, match="high violates"):
        _candle(high=24999.0)
    with pytest.raises(ValueError, match="volume"):
        _candle(volume=-1.0)


def test_execution_intent_identity_is_deterministic_and_broker_neutral() -> None:
    kwargs = {
        "decision_id": "a" * 64,
        "provenance_fingerprint": "b" * 64,
        "created_at": datetime(2026, 9, 11, 8, 5, tzinfo=UTC),
        "instrument_id": InstrumentId("DAX40.CFD"),
        "side": OrderSide.BUY,
        "quantity": 1.0,
        "requested_price": 25010.0,
        "stop_price": 24980.0,
        "target_price": 25070.0,
    }
    first = ExecutionIntent.build(**kwargs)
    second = ExecutionIntent.build(**kwargs)

    assert first.intent_id == second.intent_id
    assert len(first.intent_id) == 64
    assert first.schema_version == "DAXLAB_EXECUTION_INTENT_V2"


def test_execution_intent_rejects_non_utc_and_invalid_quantity() -> None:
    base = {
        "decision_id": "a" * 64,
        "provenance_fingerprint": "b" * 64,
        "instrument_id": InstrumentId("DAX40.CFD"),
        "side": OrderSide.SELL,
        "quantity": 1.0,
        "requested_price": 25010.0,
        "stop_price": 25040.0,
        "target_price": 24950.0,
    }
    with pytest.raises(ValueError, match="UTC"):
        ExecutionIntent.build(created_at=datetime(2026, 9, 11, 8, 5), **base)
    with pytest.raises(ValueError, match="quantity"):
        ExecutionIntent.build(
            created_at=datetime(2026, 9, 11, 8, 5, tzinfo=UTC),
            **{**base, "quantity": 0.0},
        )


def test_ports_are_structural_boundaries_without_concrete_backends() -> None:
    class FixedClock:
        def now(self) -> datetime:
            return datetime(2026, 9, 11, 8, 5, tzinfo=UTC)

    class OneCandleSource:
        def __init__(self) -> None:
            self.remaining = _candle()

        def next_candle(self) -> Candle | None:
            candle, self.remaining = self.remaining, None
            return candle

    class MemoryStateStore:
        def __init__(self) -> None:
            self.data: dict[str, bytes] = {}

        def load(self, key: str) -> bytes | None:
            return self.data.get(key)

        def save(self, key: str, payload: bytes) -> None:
            self.data[key] = payload

    class IntentCollector:
        def __init__(self) -> None:
            self.items: list[ExecutionIntent] = []

        def accept_intent(self, intent: ExecutionIntent) -> None:
            self.items.append(intent)

    assert isinstance(FixedClock(), ClockPort)
    assert isinstance(OneCandleSource(), CandleSourcePort)
    assert isinstance(MemoryStateStore(), StateStorePort)
    assert isinstance(IntentCollector(), ExecutionIntentSinkPort)


def test_nextgen_domain_has_no_legacy_candidate_or_venue_dependencies() -> None:
    domain_root = Path(__file__).resolve().parents[1] / "src" / "daxlab" / "domain"
    source = "\n".join(
        path.read_text(encoding="utf-8").lower()
        for path in sorted(domain_root.glob("*.py"))
    )
    forbidden = (
        "metatrader5",
        "runtime.mt5",
        "legacy_dataset",
        "cand001",
        "v112_bridge",
        "google drive",
    )
    for token in forbidden:
        assert token not in source
