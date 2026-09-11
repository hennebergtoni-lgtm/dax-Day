"""Deterministic descriptive historical replay for frozen CAND-001 semantics.

This module is measurement-only. It deliberately reuses the existing CAND-001
SHADOW orchestrator so signal/admission/lifecycle/gap/same-bar/cost semantics are
not reimplemented in a second backtester. Historical bars are replayed through
that already order-disabled coordinator; the outer evidence class remains
HISTORICAL_DESCRIPTIVE and makes no OOS or profitability claim.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import timedelta
import math
from statistics import median
from typing import Iterable
from zoneinfo import ZoneInfo

import pandas as pd

from daxlab.runtime.candidate_config import Cand001Config
from daxlab.runtime.candidate_shadow_orchestrator import (
    Cand001ShadowState,
    process_cand001_shadow_candle,
)
from daxlab.runtime.candidate_signal import SignalDirection
from daxlab.runtime.candidate_sizing import Cand001SimulationSizingPolicy
from daxlab.runtime.contracts import Candle, DataQualityState, RuntimeMode
from daxlab.runtime.decision import stable_fingerprint
from daxlab.runtime.manifests import RunManifest
from daxlab.runtime.paper_contracts import PaperFillModelConfig, Side


CAND001_HISTORICAL_REPLAY_SCHEMA = "DAXLAB_CAND001_HISTORICAL_DESCRIPTIVE_V1"
EVIDENCE_CLASS = "HISTORICAL_DESCRIPTIVE"
ECONOMIC_CLAIM = "DESCRIPTIVE_ONLY_NOT_OOS_NOT_PROFITABILITY_PROOF"


@dataclass(frozen=True, slots=True)
class Cand001HistoricalTradeRecord:
    decision_id: str
    client_order_id: str
    side: str
    opened_at: str
    closed_at: str
    requested_price: float
    stop_price: float
    target_price: float
    filled_price: float
    exit_price: float
    exit_reason: str
    planned_risk_points: float
    gross_r: float
    cost_r: float
    net_r: float
    outcome_id: str
    fill_model_fingerprint: str
    trade_fingerprint: str

    def to_payload(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class Cand001HistoricalReplayReport:
    schema_version: str
    evidence_class: str
    economic_claim: str
    candidate_id: str
    product_core_version: str
    config_fingerprint: str
    dataset_fingerprint: str
    runtime_manifest_fingerprint: str
    runtime_semantics_mode: str
    fill_model_fingerprint: str
    processed_bars: int
    processed_sessions: int
    directional_signals: int
    admitted_trades: int
    blocked_directional_signals: int
    completed_trades: int
    open_trade_at_end: bool
    long_trades: int
    short_trades: int
    wins: int
    losses: int
    flats: int
    win_rate: float | None
    gross_r: float
    cost_r: float
    net_r: float
    average_net_r: float | None
    median_net_r: float | None
    profit_factor: float | None
    max_drawdown_r: float
    block_reason_counts: tuple[tuple[str, int], ...]
    session_trade_counts: tuple[tuple[str, int], ...]
    trade_records_fingerprint: str
    report_fingerprint: str
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def __post_init__(self) -> None:
        if self.schema_version != CAND001_HISTORICAL_REPLAY_SCHEMA:
            raise ValueError("unsupported CAND-001 historical replay schema")
        if self.evidence_class != EVIDENCE_CLASS or self.economic_claim != ECONOMIC_CLAIM:
            raise ValueError("historical replay evidence classification drift")
        if self.runtime_semantics_mode != RuntimeMode.SHADOW.value:
            raise ValueError("historical replay must reuse SHADOW runtime semantics")
        if self.execution_capability != "NONE" or self.order_execution_enabled:
            raise ValueError("historical descriptive replay cannot authorize execution")

    def to_payload(self) -> dict[str, object]:
        payload = asdict(self)
        payload["block_reason_counts"] = dict(self.block_reason_counts)
        payload["session_trade_counts"] = dict(self.session_trade_counts)
        return payload


@dataclass(frozen=True, slots=True)
class Cand001HistoricalReplayEvidence:
    report: Cand001HistoricalReplayReport
    trades: tuple[Cand001HistoricalTradeRecord, ...]

    def to_payload(self) -> dict[str, object]:
        return {
            "report": self.report.to_payload(),
            "trades": [trade.to_payload() for trade in self.trades],
        }


def candles_from_legacy_session(session: pd.DataFrame) -> tuple[Candle, ...]:
    """Convert the audited Berlin-session frame into canonical CLOSED M5 candles."""
    required = {"open", "high", "low", "close"}
    missing = required - set(session.columns)
    if missing:
        raise ValueError(f"historical session missing OHLC columns: {sorted(missing)}")
    if not isinstance(session.index, pd.DatetimeIndex):
        raise ValueError("historical session index must be DatetimeIndex")
    if session.index.tz is None:
        raise ValueError("historical session index must be timezone-aware")
    if session.index.has_duplicates:
        raise ValueError("historical session timestamps must be unique")
    if not session.index.is_monotonic_increasing:
        raise ValueError("historical session timestamps must be chronological")

    candles: list[Candle] = []
    for timestamp, row in session.iterrows():
        event_time = timestamp.to_pydatetime()
        close_time = event_time + timedelta(minutes=5)
        candles.append(
            Candle(
                symbol="DE40",
                timeframe="5m",
                event_time=event_time,
                close_time=close_time,
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
                volume=None,
                source="AUDITED_RECOVERED_M5",
                received_at=close_time,
                is_closed=True,
                quality_state=DataQualityState.OK,
            )
        )
    return tuple(candles)


def run_cand001_historical_descriptive_replay(
    candles: Iterable[Candle],
    *,
    dataset_fingerprint: str,
    config: Cand001Config | None = None,
    sizing: Cand001SimulationSizingPolicy | None = None,
    fill_model: PaperFillModelConfig | None = None,
) -> Cand001HistoricalReplayEvidence:
    """Replay frozen CAND-001 semantics chronologically and return descriptive evidence."""
    if not isinstance(dataset_fingerprint, str) or len(dataset_fingerprint) != 64:
        raise ValueError("dataset_fingerprint must be a sha256-like 64-character identity")

    cfg = config or Cand001Config()
    size = sizing or Cand001SimulationSizingPolicy()
    model = fill_model or PaperFillModelConfig()
    product = cfg.product_identity()
    engine_fingerprint = stable_fingerprint(
        {
            "core_version": product.core_version,
            "product_identity": product.fingerprint(),
            "ruleset_version": cfg.ruleset_version,
            "fill_model_fingerprint": model.fingerprint,
            "historical_replay_schema": CAND001_HISTORICAL_REPLAY_SCHEMA,
        }
    )
    manifest = RunManifest.build(
        dataset_fingerprint=dataset_fingerprint,
        engine_fingerprint=engine_fingerprint,
        config={"candidate": cfg, "sizing": size},
        mode=RuntimeMode.SHADOW,
    )

    items = tuple(candles)
    _validate_candles(items, cfg)

    state = Cand001ShadowState()
    sessions: set[str] = set()
    directional_signals = 0
    admitted_trades = 0
    blocked = 0
    block_reasons: dict[str, int] = {}
    open_intents: dict[str, object] = {}
    trades: list[Cand001HistoricalTradeRecord] = []
    session_trade_counts: dict[str, int] = {}
    tz = ZoneInfo(cfg.session_timezone)

    for candle in items:
        sessions.add(candle.event_time.astimezone(tz).date().isoformat())
        result = process_cand001_shadow_candle(
            state,
            candle,
            observed_at=candle.close_time,
            run_manifest=manifest,
            config=cfg,
            sizing=size,
            fill_model=model,
        )
        state = result.state
        signal = result.pipeline_result.signal
        if signal.direction in {SignalDirection.LONG, SignalDirection.SHORT}:
            directional_signals += 1
            if result.intent_to_publish is None:
                blocked += 1
                for reason in result.pipeline_result.decision.blockers:
                    block_reasons[reason] = block_reasons.get(reason, 0) + 1

        if result.intent_to_publish is not None:
            intent = result.intent_to_publish
            admitted_trades += 1
            open_intents[intent.decision_id] = intent
            session_key = intent.created_at.astimezone(tz).date().isoformat()
            session_trade_counts[session_key] = session_trade_counts.get(session_key, 0) + 1

        if result.outcome_to_publish is not None:
            outcome = result.outcome_to_publish
            intent = open_intents.pop(outcome.decision_id, None)
            if intent is None:
                raise RuntimeError("historical outcome missing its admitted ExecutionIntent")
            trade_payload = {
                "decision_id": outcome.decision_id,
                "client_order_id": intent.client_order_id,
                "side": outcome.side.value,
                "opened_at": intent.created_at.isoformat(),
                "closed_at": outcome.closed_at.isoformat(),
                "requested_price": float(intent.requested_price),
                "stop_price": float(intent.stop_price),
                "target_price": float(intent.target_price),
                "filled_price": float(outcome.filled_price),
                "exit_price": float(outcome.exit_price),
                "exit_reason": outcome.exit_reason.value,
                "planned_risk_points": float(outcome.planned_risk_points),
                "gross_r": float(outcome.gross_r),
                "cost_r": float(outcome.cost_r),
                "net_r": float(outcome.net_r),
                "outcome_id": outcome.outcome_id,
                "fill_model_fingerprint": outcome.fill_model_fingerprint,
            }
            trades.append(
                Cand001HistoricalTradeRecord(
                    **trade_payload,
                    trade_fingerprint=stable_fingerprint(trade_payload),
                )
            )

    net_values = [trade.net_r for trade in trades]
    gross_values = [trade.gross_r for trade in trades]
    cost_values = [trade.cost_r for trade in trades]
    positive = sum(value for value in net_values if value > 0.0)
    negative_abs = abs(sum(value for value in net_values if value < 0.0))
    profit_factor = None if negative_abs == 0.0 else positive / negative_abs
    wins = sum(value > 0.0 for value in net_values)
    losses = sum(value < 0.0 for value in net_values)
    flats = sum(value == 0.0 for value in net_values)
    long_trades = sum(trade.side == Side.BUY.value for trade in trades)
    short_trades = sum(trade.side == Side.SELL.value for trade in trades)
    completed = len(trades)
    trade_fingerprint = stable_fingerprint(tuple(trade.trade_fingerprint for trade in trades))

    report_identity = {
        "schema_version": CAND001_HISTORICAL_REPLAY_SCHEMA,
        "evidence_class": EVIDENCE_CLASS,
        "economic_claim": ECONOMIC_CLAIM,
        "candidate_id": cfg.candidate_id,
        "product_core_version": product.core_version,
        "config_fingerprint": product.config_fingerprint,
        "dataset_fingerprint": dataset_fingerprint,
        "runtime_manifest_fingerprint": manifest.manifest_fingerprint,
        "runtime_semantics_mode": manifest.mode.value,
        "fill_model_fingerprint": model.fingerprint,
        "processed_bars": len(items),
        "processed_sessions": len(sessions),
        "directional_signals": directional_signals,
        "admitted_trades": admitted_trades,
        "blocked_directional_signals": blocked,
        "completed_trades": completed,
        "open_trade_at_end": state.active_trade is not None,
        "long_trades": long_trades,
        "short_trades": short_trades,
        "wins": wins,
        "losses": losses,
        "flats": flats,
        "win_rate": None if completed == 0 else wins / completed,
        "gross_r": float(sum(gross_values)),
        "cost_r": float(sum(cost_values)),
        "net_r": float(sum(net_values)),
        "average_net_r": None if completed == 0 else float(sum(net_values) / completed),
        "median_net_r": None if completed == 0 else float(median(net_values)),
        "profit_factor": None if profit_factor is None else float(profit_factor),
        "max_drawdown_r": _max_drawdown(net_values),
        "block_reason_counts": tuple(sorted(block_reasons.items())),
        "session_trade_counts": tuple(sorted(session_trade_counts.items())),
        "trade_records_fingerprint": trade_fingerprint,
        "execution_capability": "NONE",
        "order_execution_enabled": False,
    }
    report = Cand001HistoricalReplayReport(
        **report_identity,
        report_fingerprint=stable_fingerprint(report_identity),
    )
    return Cand001HistoricalReplayEvidence(report=report, trades=tuple(trades))


def _validate_candles(items: tuple[Candle, ...], config: Cand001Config) -> None:
    previous_close = None
    for candle in items:
        if candle.symbol != config.symbol or candle.timeframe != config.bar_timeframe:
            raise ValueError("historical replay candle symbol/timeframe drift")
        if not candle.safe_for_decision:
            raise ValueError("historical replay requires safe CLOSED candles")
        if candle.close_time - candle.event_time != timedelta(minutes=5):
            raise ValueError("historical replay requires exact five-minute candles")
        if previous_close is not None and candle.close_time <= previous_close:
            raise ValueError("historical replay candles must be strictly chronological")
        previous_close = candle.close_time


def _max_drawdown(values: list[float]) -> float:
    cumulative = 0.0
    peak = 0.0
    max_drawdown = 0.0
    for value in values:
        cumulative += float(value)
        peak = max(peak, cumulative)
        max_drawdown = max(max_drawdown, peak - cumulative)
    if not math.isfinite(max_drawdown):  # defensive; net-R inputs are expected finite
        raise ValueError("non-finite drawdown")
    return float(max_drawdown)
