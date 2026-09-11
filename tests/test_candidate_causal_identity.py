from dataclasses import replace
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from daxlab.runtime.candidate_pipeline import Cand001PipelineState, process_cand001_candle
from daxlab.runtime.contracts import Candle


BERLIN = ZoneInfo("Europe/Berlin")


def _candle(received_at: datetime) -> Candle:
    event = datetime(2026, 9, 11, 9, 0, tzinfo=BERLIN)
    return Candle(
        symbol="DE40",
        timeframe="5m",
        event_time=event,
        close_time=event + timedelta(minutes=5),
        open=100.0,
        high=102.0,
        low=99.0,
        close=101.0,
        volume=None,
        source="MT5_READ_ONLY:DE40",
        received_at=received_at,
        is_closed=True,
    )


def test_transport_receipt_time_does_not_change_signal_or_decision_identity() -> None:
    early = datetime(2026, 9, 11, 9, 5, 1, tzinfo=BERLIN)
    late = early + timedelta(hours=2)
    state = Cand001PipelineState()

    first = process_cand001_candle(state, _candle(early), observed_at=early)
    second = process_cand001_candle(state, _candle(late), observed_at=late)

    assert first.signal.data_fingerprint == second.signal.data_fingerprint
    assert first.decision.decision_id == second.decision.decision_id
    assert first.operator_snapshot.snapshot_fingerprint != second.operator_snapshot.snapshot_fingerprint


def test_market_price_change_still_changes_candidate_identity() -> None:
    observed = datetime(2026, 9, 11, 9, 5, 1, tzinfo=BERLIN)
    base = _candle(observed)
    changed = replace(base, high=103.0)
    state = Cand001PipelineState()

    first = process_cand001_candle(state, base, observed_at=observed)
    second = process_cand001_candle(state, changed, observed_at=observed)

    assert first.signal.data_fingerprint != second.signal.data_fingerprint
    assert first.decision.decision_id != second.decision.decision_id
