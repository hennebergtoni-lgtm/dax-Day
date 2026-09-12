"""Deterministic historical OOS/WF measurement runner for frozen CAND-001.

Each declared OOS slice is evaluated independently with the already verified
Step-2103 descriptive replay semantics. Train days are chronology/context only:
this runner never selects, tunes or mutates CAND-001 from them. Cost stress is
applied by constructing versioned PaperFillModelConfig variants and therefore
reuses the canonical lifecycle/outcome cost semantics instead of post-hoc R math.

This is historical OOS measurement evidence only. It does not authorize PAPER or
LIVE and it does not by itself establish profitability.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

from daxlab.data.fingerprint import fingerprint_ohlc
from daxlab.data.legacy_dataset import load_audited_recovered_session
from daxlab.research.cand001_historical_replay import (
    CAND001_HISTORICAL_REPLAY_SCHEMA,
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
WINDOW_STATE_POLICY = "RESET_AT_EACH_OOS_START_NO_TRAIN_STATE"
COST_STRESS_POLICY = "MULTIPLY_SPREAD_SLIPPAGE_COMMISSION_ONLY"


@dataclass(frozen=True, slots=True)
class Cand001OosWindowCostEvidence:
    schema_version: str
    evidence_class: str
    economic_claim: str
    contract_fingerprint: str
    window_number: int
    window_fingerprint: str
    oos_start: str
    oos_end: str
    cost_model: str
    cost_multiplier: float
    oos_dataset_fingerprint: str
    fill_model_fingerprint: str
    replay_schema_version: str
    replay_report_fingerprint: str
    processed_bars: int
    processed_sessions: int
    directional_signals: int
    admitted_trades: int
    completed_trades: int
    open_trade_at_end: bool
    wins: int
    losses: int
    flats: int
    gross_r: float
    cost_r: float
    net_r: float
    profit_factor: float | None
    max_drawdown_r: float
    result_fingerprint: str
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def __post_init__(self) -> None:
        if self.schema_version != CAND001_OOS_MEASUREMENT_SCHEMA:
            raise ValueError("unsupported CAND-001 OOS measurement schema")
        if self.evidence_class != EVIDENCE_CLASS or self.economic_claim != ECONOMIC_CLAIM:
            raise ValueError("CAND-001 OOS evidence classification drift")
        if self.window_number <= 0 or self.processed_bars <= 0 or self.processed_sessions <= 0:
            raise ValueError("CAND-001 OOS evidence counts must be positive")
        for field_name, value in (
            ("contract_fingerprint", self.contract_fingerprint),
            ("window_fingerprint", self.window_fingerprint),
            ("oos_dataset_fingerprint", self.oos_dataset_fingerprint),
            ("fill_model_fingerprint", self.fill_model_fingerprint),
            ("replay_report_fingerprint", self.replay_report_fingerprint),
            ("result_fingerprint", self.result_fingerprint),
        ):
            _assert_sha256(value, field=field_name)
        if self.cost_multiplier <= 0 or not self.cost_model:
            raise ValueError("CAND-001 OOS cost identity must be positive/non-empty")
        if self.replay_schema_version != CAND001_HISTORICAL_REPLAY_SCHEMA:
            raise ValueError("CAND-001 OOS replay schema drift")
        if self.execution_capability != "NONE" or self.order_execution_enabled:
            raise ValueError("CAND-001 OOS measurement cannot authorize execution")

    def to_payload(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class Cand001OosMeasurementEvidence:
    schema_version: str
    evidence_class: str
    economic_claim: str
    contract_fingerprint: str
    dataset_fingerprint: str
    window_state_policy: str
    cost_stress_policy: str
    window_count: int
    cost_models: tuple[tuple[str, float], ...]
    results: tuple[Cand001OosWindowCostEvidence, ...]
    evidence_fingerprint: str
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def __post_init__(self) -> None:
        if self.schema_version != CAND001_OOS_MEASUREMENT_SCHEMA:
            raise ValueError("unsupported CAND-001 OOS measurement schema")
        if self.evidence_class != EVIDENCE_CLASS or self.economic_claim != ECONOMIC_CLAIM:
            raise ValueError("CAND-001 OOS aggregate classification drift")
        _assert_sha256(self.contract_fingerprint, field="contract_fingerprint")
        _assert_sha256(self.dataset_fingerprint, field="dataset_fingerprint")
        _assert_sha256(self.evidence_fingerprint, field="evidence_fingerprint")
        if self.window_state_policy != WINDOW_STATE_POLICY:
            raise ValueError("CAND-001 OOS window-state policy drift")
        if self.cost_stress_policy != COST_STRESS_POLICY:
            raise ValueError("CAND-001 OOS cost-stress policy drift")
        if self.window_count < 0:
            raise ValueError("CAND-001 OOS window_count must be non-negative")
        if len(self.results) != self.window_count * len(self.cost_models):
            raise ValueError("CAND-001 OOS result cardinality drift")
        if self.execution_capability != "NONE" or self.order_execution_enabled:
            raise ValueError("CAND-001 OOS aggregate cannot authorize execution")

    def to_payload(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "evidence_class": self.evidence_class,
            "economic_claim": self.economic_claim,
            "contract_fingerprint": self.contract_fingerprint,
            "dataset_fingerprint": self.dataset_fingerprint,
            "window_state_policy": self.window_state_policy,
            "cost_stress_policy": self.cost_stress_policy,
            "window_count": self.window_count,
            "cost_models": [list(item) for item in self.cost_models],
            "results": [item.to_payload() for item in self.results],
            "evidence_fingerprint": self.evidence_fingerprint,
            "execution_capability": self.execution_capability,
            "order_execution_enabled": self.order_execution_enabled,
        }


def run_cand001_oos_measurement(
    session: pd.DataFrame,
    *,
    contract: Cand001OosWalkForwardContract,
    config: Cand001Config | None = None,
    base_fill_model: PaperFillModelConfig | None = None,
) -> Cand001OosMeasurementEvidence:
    """Measure frozen CAND-001 independently on every declared OOS slice/cost stress."""
    cfg = config or Cand001Config()
    base_model = base_fill_model or PaperFillModelConfig()
    _validate_contract_binding(contract, cfg)
    observed_dataset_fingerprint = fingerprint_ohlc(session)
    if observed_dataset_fingerprint != contract.dataset_fingerprint:
        raise ValueError(
            "CAND-001 OOS dataset fingerprint mismatch: "
            f"contract={contract.dataset_fingerprint} observed={observed_dataset_fingerprint}"
        )
    if not isinstance(session.index, pd.DatetimeIndex) or session.index.tz is None:
        raise ValueError("CAND-001 OOS session index must be timezone-aware DatetimeIndex")
    if session.index.has_duplicates or not session.index.is_monotonic_increasing:
        raise ValueError("CAND-001 OOS session timestamps must be unique and chronological")

    local = session.index.tz_convert(ZoneInfo(cfg.session_timezone))
    local_day_strings = pd.Index(local.date).map(lambda value: value.isoformat())
    unique_days = tuple(dict.fromkeys(local_day_strings))
    windows = build_cand001_oos_windows(unique_days, contract)

    results: list[Cand001OosWindowCostEvidence] = []
    for window in windows:
        mask = (local_day_strings >= window.oos_start) & (local_day_strings <= window.oos_end)
        oos_session = session.loc[mask].copy()
        observed_days = tuple(dict.fromkeys(local_day_strings[mask]))
        if len(observed_days) != window.oos_days:
            raise RuntimeError("CAND-001 OOS window session-day cardinality drift")
        oos_fingerprint = fingerprint_ohlc(oos_session)
        candles = candles_from_legacy_session(oos_session)

        for cost_model, multiplier in contract.cost_stresses:
            stressed = _stress_fill_model(base_model, multiplier)
            replay = run_cand001_historical_descriptive_replay(
                candles,
                dataset_fingerprint=oos_fingerprint,
                config=cfg,
                fill_model=stressed,
            )
            identity = build_cand001_oos_result_identity(
                contract=contract,
                window=window,
                cost_model=cost_model,
                replay_report_fingerprint=replay.report.report_fingerprint,
            )
            results.append(
                _window_evidence(
                    contract=contract,
                    window=window,
                    identity=identity,
                    cost_model=cost_model,
                    multiplier=multiplier,
                    oos_fingerprint=oos_fingerprint,
                    replay=replay,
                )
            )

    identity_payload = {
        "schema_version": CAND001_OOS_MEASUREMENT_SCHEMA,
        "evidence_class": EVIDENCE_CLASS,
        "economic_claim": ECONOMIC_CLAIM,
        "contract_fingerprint": contract.fingerprint,
        "dataset_fingerprint": contract.dataset_fingerprint,
        "window_state_policy": WINDOW_STATE_POLICY,
        "cost_stress_policy": COST_STRESS_POLICY,
        "window_count": len(windows),
        "cost_models": contract.cost_stresses,
        "result_fingerprints": tuple(item.result_fingerprint for item in results),
        "execution_capability": "NONE",
        "order_execution_enabled": False,
    }
    return Cand001OosMeasurementEvidence(
        schema_version=CAND001_OOS_MEASUREMENT_SCHEMA,
        evidence_class=EVIDENCE_CLASS,
        economic_claim=ECONOMIC_CLAIM,
        contract_fingerprint=contract.fingerprint,
        dataset_fingerprint=contract.dataset_fingerprint,
        window_state_policy=WINDOW_STATE_POLICY,
        cost_stress_policy=COST_STRESS_POLICY,
        window_count=len(windows),
        cost_models=contract.cost_stresses,
        results=tuple(results),
        evidence_fingerprint=stable_fingerprint(identity_payload),
    )


def run_audited_recovered_m5_cand001_oos_measurement(
    directory: str | Path,
    *,
    expected_dataset_fingerprint: str,
    config: Cand001Config | None = None,
    base_fill_model: PaperFillModelConfig | None = None,
) -> Cand001OosMeasurementEvidence:
    """Load the canonical recovered dataset once and run the frozen OOS measurement."""
    _assert_sha256(expected_dataset_fingerprint, field="expected_dataset_fingerprint")
    session, dataset_report = load_audited_recovered_session(directory)
    if dataset_report.fingerprint != expected_dataset_fingerprint:
        raise ValueError(
            "audited recovered M5 fingerprint mismatch: "
            f"expected={expected_dataset_fingerprint} observed={dataset_report.fingerprint}"
        )
    contract = build_cand001_oos_contract(
        dataset_fingerprint=dataset_report.fingerprint,
        config=config,
    )
    return run_cand001_oos_measurement(
        session,
        contract=contract,
        config=config,
        base_fill_model=base_fill_model,
    )


def _validate_contract_binding(
    contract: Cand001OosWalkForwardContract,
    config: Cand001Config,
) -> None:
    identity = config.product_identity()
    if contract.candidate_id != config.candidate_id:
        raise ValueError("CAND-001 OOS candidate identity drift")
    if contract.product_core_version != identity.core_version:
        raise ValueError("CAND-001 OOS product core version drift")
    if contract.config_fingerprint != identity.config_fingerprint:
        raise ValueError("CAND-001 OOS config fingerprint drift")


def _stress_fill_model(base: PaperFillModelConfig, multiplier: float) -> PaperFillModelConfig:
    if multiplier <= 0:
        raise ValueError("CAND-001 OOS cost multiplier must be positive")
    return PaperFillModelConfig(
        spread_points=float(base.spread_points) * multiplier,
        slippage_points=float(base.slippage_points) * multiplier,
        commission_points=float(base.commission_points) * multiplier,
        latency_ms=base.latency_ms,
        same_bar_policy=base.same_bar_policy,
        gap_policy=base.gap_policy,
        partial_fill_policy=base.partial_fill_policy,
    )


def _window_evidence(
    *,
    contract: Cand001OosWalkForwardContract,
    window: Cand001OosWindow,
    identity: Cand001OosResultIdentity,
    cost_model: str,
    multiplier: float,
    oos_fingerprint: str,
    replay: Cand001HistoricalReplayEvidence,
) -> Cand001OosWindowCostEvidence:
    report = replay.report
    if report.dataset_fingerprint != oos_fingerprint:
        raise RuntimeError("CAND-001 OOS replay dataset identity drift")
    if identity.window_fingerprint != window.window_fingerprint:
        raise RuntimeError("CAND-001 OOS result/window identity drift")
    if identity.cost_model != cost_model or identity.cost_multiplier != multiplier:
        raise RuntimeError("CAND-001 OOS cost identity drift")
    return Cand001OosWindowCostEvidence(
        schema_version=CAND001_OOS_MEASUREMENT_SCHEMA,
        evidence_class=EVIDENCE_CLASS,
        economic_claim=ECONOMIC_CLAIM,
        contract_fingerprint=contract.fingerprint,
        window_number=window.number,
        window_fingerprint=window.window_fingerprint,
        oos_start=window.oos_start,
        oos_end=window.oos_end,
        cost_model=cost_model,
        cost_multiplier=multiplier,
        oos_dataset_fingerprint=oos_fingerprint,
        fill_model_fingerprint=report.fill_model_fingerprint,
        replay_schema_version=report.schema_version,
        replay_report_fingerprint=report.report_fingerprint,
        processed_bars=report.processed_bars,
        processed_sessions=report.processed_sessions,
        directional_signals=report.directional_signals,
        admitted_trades=report.admitted_trades,
        completed_trades=report.completed_trades,
        open_trade_at_end=report.open_trade_at_end,
        wins=report.wins,
        losses=report.losses,
        flats=report.flats,
        gross_r=report.gross_r,
        cost_r=report.cost_r,
        net_r=report.net_r,
        profit_factor=report.profit_factor,
        max_drawdown_r=report.max_drawdown_r,
        result_fingerprint=identity.result_fingerprint,
    )


def _assert_sha256(value: str, *, field: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"{field} must be sha256")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field} must be hexadecimal") from exc
