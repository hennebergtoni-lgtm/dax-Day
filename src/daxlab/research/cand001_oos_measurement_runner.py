"""Deterministic OOS/WF measurement runner for frozen CAND-001.

This module measures only declared OOS slices. It performs no train-time
selection, tuning, optimization or broker execution. Strategy/lifecycle/outcome
semantics are reused from the existing descriptive historical replay owner.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import date
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

from daxlab.data.legacy_dataset import load_audited_recovered_session
from daxlab.research.cand001_historical_replay import (
    Cand001HistoricalReplayEvidence,
    candles_from_legacy_session,
    run_cand001_historical_descriptive_replay,
)
from daxlab.research.cand001_oos_walk_forward import (
    ECONOMIC_CLAIM,
    EVIDENCE_CLASS,
    Cand001OosResultIdentity,
    Cand001OosWalkForwardContract,
    Cand001OosWindow,
    build_cand001_oos_contract,
    build_cand001_oos_result_identity,
    build_cand001_oos_windows,
)
from daxlab.runtime.candidate_config import Cand001Config
from daxlab.runtime.decision import stable_fingerprint
from daxlab.runtime.paper_contracts import PaperFillModelConfig


CAND001_OOS_MEASUREMENT_SCHEMA = "DAXLAB_CAND001_OOS_WF_MEASUREMENT_V1"


@dataclass(frozen=True, slots=True)
class Cand001OosMeasurement:
    window_number: int
    window_fingerprint: str
    oos_start: str
    oos_end: str
    cost_model: str
    cost_multiplier: float
    fill_model_fingerprint: str
    replay_report_fingerprint: str
    result_fingerprint: str
    processed_bars: int
    processed_sessions: int
    directional_signals: int
    admitted_trades: int
    completed_trades: int
    open_trade_at_end: bool
    gross_r: float
    cost_r: float
    net_r: float
    average_net_r: float | None
    median_net_r: float | None
    profit_factor: float | None
    max_drawdown_r: float
    trade_records_fingerprint: str
    evidence_class: str = EVIDENCE_CLASS
    economic_claim: str = ECONOMIC_CLAIM
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def __post_init__(self) -> None:
        if self.window_number <= 0:
            raise ValueError("window_number must be positive")
        for field, value in (
            ("window_fingerprint", self.window_fingerprint),
            ("fill_model_fingerprint", self.fill_model_fingerprint),
            ("replay_report_fingerprint", self.replay_report_fingerprint),
            ("result_fingerprint", self.result_fingerprint),
            ("trade_records_fingerprint", self.trade_records_fingerprint),
        ):
            _assert_sha256(value, field=field)
        if self.cost_multiplier <= 0:
            raise ValueError("cost_multiplier must be positive")
        if self.processed_bars < 0 or self.processed_sessions <= 0:
            raise ValueError("OOS measurement counts are invalid")
        if self.evidence_class != EVIDENCE_CLASS or self.economic_claim != ECONOMIC_CLAIM:
            raise ValueError("OOS measurement evidence classification drift")
        if self.execution_capability != "NONE" or self.order_execution_enabled:
            raise ValueError("OOS measurement cannot authorize execution")

    def to_payload(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class Cand001OosMeasurementBundle:
    schema_version: str
    dataset_fingerprint: str
    contract_fingerprint: str
    candidate_id: str
    config_fingerprint: str
    source_session_days: int
    window_count: int
    cost_model_count: int
    measurement_count: int
    measurements: tuple[Cand001OosMeasurement, ...]
    bundle_fingerprint: str
    evidence_class: str = EVIDENCE_CLASS
    economic_claim: str = ECONOMIC_CLAIM
    selection_policy: str = "FROZEN_PREDECLARED_CANDIDATE_NO_TUNING"
    train_role: str = "CONTEXT_ONLY_NO_SELECTION"
    oos_role: str = "MEASUREMENT_ONLY"
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def __post_init__(self) -> None:
        if self.schema_version != CAND001_OOS_MEASUREMENT_SCHEMA:
            raise ValueError("unsupported CAND-001 OOS measurement schema")
        _assert_sha256(self.dataset_fingerprint, field="dataset_fingerprint")
        _assert_sha256(self.contract_fingerprint, field="contract_fingerprint")
        _assert_sha256(self.config_fingerprint, field="config_fingerprint")
        _assert_sha256(self.bundle_fingerprint, field="bundle_fingerprint")
        if self.source_session_days <= 0 or self.window_count <= 0 or self.cost_model_count <= 0:
            raise ValueError("OOS bundle counts must be positive")
        if self.measurement_count != len(self.measurements):
            raise ValueError("measurement_count does not match measurements")
        if self.measurement_count != self.window_count * self.cost_model_count:
            raise ValueError("OOS bundle must contain every window/cost combination exactly once")
        keys = tuple((item.window_number, item.cost_model) for item in self.measurements)
        if len(set(keys)) != len(keys):
            raise ValueError("duplicate OOS window/cost measurement")
        if self.execution_capability != "NONE" or self.order_execution_enabled:
            raise ValueError("OOS measurement bundle cannot authorize execution")

    def to_payload(self) -> dict[str, object]:
        payload = asdict(self)
        payload["measurements"] = [item.to_payload() for item in self.measurements]
        return payload


def stressed_fill_model(
    base: PaperFillModelConfig,
    multiplier: float,
) -> PaperFillModelConfig:
    """Apply a declared cost stress to costs only, preserving execution policies."""
    if multiplier <= 0:
        raise ValueError("cost multiplier must be positive")
    return replace(
        base,
        spread_points=float(base.spread_points) * float(multiplier),
        slippage_points=float(base.slippage_points) * float(multiplier),
        commission_points=float(base.commission_points) * float(multiplier),
    )


def run_cand001_oos_measurements(
    session: pd.DataFrame,
    *,
    dataset_fingerprint: str,
    config: Cand001Config | None = None,
    base_fill_model: PaperFillModelConfig | None = None,
) -> Cand001OosMeasurementBundle:
    """Measure every frozen CAND-001 OOS window under every declared cost stress."""
    _assert_sha256(dataset_fingerprint, field="dataset_fingerprint")
    cfg = config or Cand001Config()
    base_model = base_fill_model or PaperFillModelConfig()
    _validate_session_surface(session, cfg)

    session_days = _ordered_session_days(session, cfg.session_timezone)
    contract = build_cand001_oos_contract(
        dataset_fingerprint=dataset_fingerprint,
        config=cfg,
    )
    windows = build_cand001_oos_windows(session_days, contract)
    if not windows:
        raise ValueError("dataset does not contain enough session days for frozen OOS/WF contract")

    measurements: list[Cand001OosMeasurement] = []
    for window in windows:
        oos_session = _slice_oos_session(session, window, cfg.session_timezone)
        oos_days = _ordered_session_days(oos_session, cfg.session_timezone)
        if len(oos_days) != window.oos_days:
            raise RuntimeError("OOS slice session-day count drift")
        candles = candles_from_legacy_session(oos_session)

        for cost_model, multiplier in contract.cost_stresses:
            fill_model = stressed_fill_model(base_model, multiplier)
            replay = run_cand001_historical_descriptive_replay(
                candles,
                dataset_fingerprint=dataset_fingerprint,
                config=cfg,
                fill_model=fill_model,
            )
            measurements.append(
                _measurement_from_replay(
                    contract=contract,
                    window=window,
                    cost_model=cost_model,
                    replay=replay,
                )
            )

    measurement_tuple = tuple(measurements)
    bundle_identity = {
        "schema_version": CAND001_OOS_MEASUREMENT_SCHEMA,
        "dataset_fingerprint": dataset_fingerprint,
        "contract_fingerprint": contract.fingerprint,
        "candidate_id": contract.candidate_id,
        "config_fingerprint": contract.config_fingerprint,
        "source_session_days": len(session_days),
        "window_count": len(windows),
        "cost_model_count": len(contract.cost_stresses),
        "measurement_result_fingerprints": tuple(
            item.result_fingerprint for item in measurement_tuple
        ),
        "evidence_class": EVIDENCE_CLASS,
        "economic_claim": ECONOMIC_CLAIM,
    }
    return Cand001OosMeasurementBundle(
        schema_version=CAND001_OOS_MEASUREMENT_SCHEMA,
        dataset_fingerprint=dataset_fingerprint,
        contract_fingerprint=contract.fingerprint,
        candidate_id=contract.candidate_id,
        config_fingerprint=contract.config_fingerprint,
        source_session_days=len(session_days),
        window_count=len(windows),
        cost_model_count=len(contract.cost_stresses),
        measurement_count=len(measurement_tuple),
        measurements=measurement_tuple,
        bundle_fingerprint=stable_fingerprint(bundle_identity),
    )


def run_audited_recovered_m5_cand001_oos_wf(
    directory: str | Path,
    *,
    expected_dataset_fingerprint: str,
    config: Cand001Config | None = None,
    base_fill_model: PaperFillModelConfig | None = None,
) -> Cand001OosMeasurementBundle:
    """Load/audit the recovered M5 surface once, then measure frozen OOS windows."""
    _assert_sha256(expected_dataset_fingerprint, field="expected_dataset_fingerprint")
    session, report = load_audited_recovered_session(directory)
    if report.fingerprint != expected_dataset_fingerprint:
        raise ValueError(
            "audited recovered M5 fingerprint mismatch: "
            f"expected={expected_dataset_fingerprint} observed={report.fingerprint}"
        )
    evidence = run_cand001_oos_measurements(
        session,
        dataset_fingerprint=report.fingerprint,
        config=config,
        base_fill_model=base_fill_model,
    )
    if evidence.source_session_days != report.session_days:
        raise RuntimeError("OOS source session-day count drift from audited dataset report")
    if evidence.window_count != 81:
        raise RuntimeError("audited 1673-day surface must produce exactly 81 frozen OOS windows")
    if evidence.measurement_count != 81 * 3:
        raise RuntimeError("audited OOS measurement must produce exactly 243 window/cost rows")
    return evidence


def _measurement_from_replay(
    *,
    contract: Cand001OosWalkForwardContract,
    window: Cand001OosWindow,
    cost_model: str,
    replay: Cand001HistoricalReplayEvidence,
) -> Cand001OosMeasurement:
    report = replay.report
    identity: Cand001OosResultIdentity = build_cand001_oos_result_identity(
        contract=contract,
        window=window,
        cost_model=cost_model,
        replay_report_fingerprint=report.report_fingerprint,
    )
    if report.evidence_class != "HISTORICAL_DESCRIPTIVE":
        raise ValueError("OOS runner requires canonical descriptive replay evidence")
    return Cand001OosMeasurement(
        window_number=window.number,
        window_fingerprint=window.window_fingerprint,
        oos_start=window.oos_start,
        oos_end=window.oos_end,
        cost_model=identity.cost_model,
        cost_multiplier=identity.cost_multiplier,
        fill_model_fingerprint=report.fill_model_fingerprint,
        replay_report_fingerprint=report.report_fingerprint,
        result_fingerprint=identity.result_fingerprint,
        processed_bars=report.processed_bars,
        processed_sessions=report.processed_sessions,
        directional_signals=report.directional_signals,
        admitted_trades=report.admitted_trades,
        completed_trades=report.completed_trades,
        open_trade_at_end=report.open_trade_at_end,
        gross_r=report.gross_r,
        cost_r=report.cost_r,
        net_r=report.net_r,
        average_net_r=report.average_net_r,
        median_net_r=report.median_net_r,
        profit_factor=report.profit_factor,
        max_drawdown_r=report.max_drawdown_r,
        trade_records_fingerprint=report.trade_records_fingerprint,
    )


def _ordered_session_days(session: pd.DataFrame, timezone_name: str) -> tuple[str, ...]:
    local_dates = session.index.tz_convert(ZoneInfo(timezone_name)).date
    ordered: list[str] = []
    previous: date | None = None
    for item in local_dates:
        if previous != item:
            ordered.append(item.isoformat())
            previous = item
    if len(set(ordered)) != len(ordered):
        raise ValueError("session days are not strictly chronological")
    return tuple(ordered)


def _slice_oos_session(
    session: pd.DataFrame,
    window: Cand001OosWindow,
    timezone_name: str,
) -> pd.DataFrame:
    local_dates = session.index.tz_convert(ZoneInfo(timezone_name)).date
    start = date.fromisoformat(window.oos_start)
    end = date.fromisoformat(window.oos_end)
    mask = [(item >= start and item <= end) for item in local_dates]
    result = session.loc[mask].copy()
    if result.empty:
        raise RuntimeError("OOS slice unexpectedly empty")
    return result


def _validate_session_surface(session: pd.DataFrame, config: Cand001Config) -> None:
    required = {"open", "high", "low", "close"}
    missing = required - set(session.columns)
    if missing:
        raise ValueError(f"OOS session missing OHLC columns: {sorted(missing)}")
    if not isinstance(session.index, pd.DatetimeIndex):
        raise ValueError("OOS session index must be DatetimeIndex")
    if session.index.tz is None:
        raise ValueError("OOS session index must be timezone-aware")
    if session.index.has_duplicates:
        raise ValueError("OOS session timestamps must be unique")
    if not session.index.is_monotonic_increasing:
        raise ValueError("OOS session timestamps must be chronological")
    ZoneInfo(config.session_timezone)


def _assert_sha256(value: str, *, field: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"{field} must be sha256")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field} must be hexadecimal") from exc
