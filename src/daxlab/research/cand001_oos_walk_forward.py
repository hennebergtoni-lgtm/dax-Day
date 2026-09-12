"""Frozen OOS/walk-forward evaluation contract for CAND-001.

This module defines chronology and evidence identity only. It does not optimize,
select or mutate CAND-001 and it does not run broker/PAPER execution. The V1
contract deliberately reuses the project's existing deterministic walk-forward
scheduler while freezing CAND-001 before any OOS measurement.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Sequence

from daxlab.contracts import REFERENCE_COSTS, REFERENCE_WF
from daxlab.research.walk_forward import build_walk_forwards
from daxlab.runtime.candidate_config import Cand001Config
from daxlab.runtime.decision import stable_fingerprint


CAND001_OOS_WF_CONTRACT_VERSION = "CAND001_OOS_WF_CONTRACT_V1"
EVIDENCE_CLASS = "HISTORICAL_OOS_WF_EVALUATION"
ECONOMIC_CLAIM = "OOS_MEASUREMENT_NOT_PROFITABILITY_PROOF"
SELECTION_POLICY = "FROZEN_PREDECLARED_CANDIDATE_NO_TUNING"
TRAIN_ROLE = "CONTEXT_ONLY_NO_SELECTION"
OOS_ROLE = "MEASUREMENT_ONLY"


@dataclass(frozen=True, slots=True)
class Cand001OosWalkForwardContract:
    dataset_fingerprint: str
    candidate_id: str
    product_core_version: str
    config_fingerprint: str
    train_days: int
    oos_days: int
    step_days: int
    cost_stresses: tuple[tuple[str, float], ...]
    contract_version: str = CAND001_OOS_WF_CONTRACT_VERSION
    evidence_class: str = EVIDENCE_CLASS
    economic_claim: str = ECONOMIC_CLAIM
    selection_policy: str = SELECTION_POLICY
    train_role: str = TRAIN_ROLE
    oos_role: str = OOS_ROLE
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def __post_init__(self) -> None:
        if self.contract_version != CAND001_OOS_WF_CONTRACT_VERSION:
            raise ValueError("unsupported CAND-001 OOS/WF contract version")
        if len(self.dataset_fingerprint) != 64:
            raise ValueError("dataset_fingerprint must be sha256")
        try:
            int(self.dataset_fingerprint, 16)
        except ValueError as exc:
            raise ValueError("dataset_fingerprint must be hexadecimal") from exc
        if (self.train_days, self.oos_days, self.step_days) != (
            REFERENCE_WF.train_days,
            REFERENCE_WF.oos_days,
            REFERENCE_WF.step_days,
        ):
            raise ValueError("CAND-001 OOS/WF V1 chronology must remain frozen at 45/20/20")
        expected_costs = tuple((item.name, float(item.multiplier)) for item in REFERENCE_COSTS)
        if self.cost_stresses != expected_costs:
            raise ValueError("CAND-001 OOS/WF V1 cost stresses must remain frozen")
        if self.selection_policy != SELECTION_POLICY or self.train_role != TRAIN_ROLE:
            raise ValueError("CAND-001 OOS/WF V1 must prohibit train-time selection/tuning")
        if self.oos_role != OOS_ROLE:
            raise ValueError("CAND-001 OOS/WF V1 OOS role drift")
        if self.execution_capability != "NONE" or self.order_execution_enabled:
            raise ValueError("CAND-001 OOS/WF evaluation cannot authorize execution")

    @property
    def fingerprint(self) -> str:
        return stable_fingerprint(self)


@dataclass(frozen=True, slots=True)
class Cand001OosWindow:
    number: int
    train_start: str
    train_end: str
    oos_start: str
    oos_end: str
    train_days: int
    oos_days: int
    contract_fingerprint: str
    window_fingerprint: str


@dataclass(frozen=True, slots=True)
class Cand001OosResultIdentity:
    window_fingerprint: str
    cost_model: str
    cost_multiplier: float
    replay_report_fingerprint: str
    result_fingerprint: str
    evidence_class: str = EVIDENCE_CLASS
    economic_claim: str = ECONOMIC_CLAIM
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def __post_init__(self) -> None:
        for field_name, value in (
            ("window_fingerprint", self.window_fingerprint),
            ("replay_report_fingerprint", self.replay_report_fingerprint),
            ("result_fingerprint", self.result_fingerprint),
        ):
            if len(value) != 64:
                raise ValueError(f"{field_name} must be sha256")
        if self.execution_capability != "NONE" or self.order_execution_enabled:
            raise ValueError("OOS result identity cannot authorize execution")


def build_cand001_oos_contract(
    *,
    dataset_fingerprint: str,
    config: Cand001Config | None = None,
) -> Cand001OosWalkForwardContract:
    frozen = config or Cand001Config()
    identity = frozen.product_identity()
    return Cand001OosWalkForwardContract(
        dataset_fingerprint=dataset_fingerprint,
        candidate_id=frozen.candidate_id,
        product_core_version=identity.core_version,
        config_fingerprint=identity.config_fingerprint,
        train_days=REFERENCE_WF.train_days,
        oos_days=REFERENCE_WF.oos_days,
        step_days=REFERENCE_WF.step_days,
        cost_stresses=tuple((item.name, float(item.multiplier)) for item in REFERENCE_COSTS),
    )


def _normalize_day(value: date | datetime | str) -> str:
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, str):
        return date.fromisoformat(value).isoformat()
    raise TypeError("walk-forward days must be date, datetime or ISO date strings")


def build_cand001_oos_windows(
    days: Sequence[date | datetime | str],
    contract: Cand001OosWalkForwardContract,
) -> tuple[Cand001OosWindow, ...]:
    normalized = tuple(_normalize_day(value) for value in days)
    if len(set(normalized)) != len(normalized):
        raise ValueError("walk-forward days must be unique")
    if tuple(sorted(normalized)) != normalized:
        raise ValueError("walk-forward days must be strictly chronological")

    windows = build_walk_forwards(normalized, REFERENCE_WF)
    contract_fingerprint = contract.fingerprint
    result: list[Cand001OosWindow] = []
    for window in windows:
        train = tuple(str(item) for item in window.train)
        oos = tuple(str(item) for item in window.oos)
        payload = {
            "contract_fingerprint": contract_fingerprint,
            "number": window.number,
            "train_start": train[0],
            "train_end": train[-1],
            "oos_start": oos[0],
            "oos_end": oos[-1],
            "train_days": len(train),
            "oos_days": len(oos),
        }
        result.append(
            Cand001OosWindow(
                number=window.number,
                train_start=train[0],
                train_end=train[-1],
                oos_start=oos[0],
                oos_end=oos[-1],
                train_days=len(train),
                oos_days=len(oos),
                contract_fingerprint=contract_fingerprint,
                window_fingerprint=stable_fingerprint(payload),
            )
        )
    return tuple(result)


def build_cand001_oos_result_identity(
    *,
    contract: Cand001OosWalkForwardContract,
    window: Cand001OosWindow,
    cost_model: str,
    replay_report_fingerprint: str,
) -> Cand001OosResultIdentity:
    if window.contract_fingerprint != contract.fingerprint:
        raise ValueError("OOS window is not bound to supplied contract")
    costs = dict(contract.cost_stresses)
    if cost_model not in costs:
        raise ValueError("cost_model is not declared by OOS/WF contract")
    if len(replay_report_fingerprint) != 64:
        raise ValueError("replay_report_fingerprint must be sha256")
    try:
        int(replay_report_fingerprint, 16)
    except ValueError as exc:
        raise ValueError("replay_report_fingerprint must be hexadecimal") from exc

    multiplier = costs[cost_model]
    payload = {
        "contract_fingerprint": contract.fingerprint,
        "window_fingerprint": window.window_fingerprint,
        "cost_model": cost_model,
        "cost_multiplier": multiplier,
        "replay_report_fingerprint": replay_report_fingerprint,
        "evidence_class": EVIDENCE_CLASS,
    }
    return Cand001OosResultIdentity(
        window_fingerprint=window.window_fingerprint,
        cost_model=cost_model,
        cost_multiplier=multiplier,
        replay_report_fingerprint=replay_report_fingerprint,
        result_fingerprint=stable_fingerprint(payload),
    )
