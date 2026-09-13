"""Read-only normalization of redacted MT5 account context for DEMO evidence.

This module is dependency-free and deliberately contains no MetaTrader5 import,
connection owner, credential handling or order API. It converts values already
observed by the existing Windows MT5 probe into redacted evidence that can feed
the separate Step-2191 demo-evidence authorization contract.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any

from daxlab.runtime.demo_evidence_authorization import (
    DemoAccountMode,
    DemoEvidenceObservedContext,
)


MT5_DEMO_ACCOUNT_CONTEXT_SCHEMA = "DAXLAB_MT5_DEMO_ACCOUNT_CONTEXT_V1"
_ACCOUNT_ID_NAMESPACE = "DAXLAB:MT5:ACCOUNT_ID:V1"


@dataclass(frozen=True, slots=True)
class Mt5DemoAccountContextEvidence:
    schema_version: str
    account_fingerprint: str
    server: str
    symbol: str
    account_mode: DemoAccountMode
    trade_allowed: bool
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def __post_init__(self) -> None:
        if self.schema_version != MT5_DEMO_ACCOUNT_CONTEXT_SCHEMA:
            raise ValueError("MT5 demo account context schema mismatch")
        _sha(self.account_fingerprint, "account_fingerprint")
        _nonempty(self.server, "server")
        _nonempty(self.symbol, "symbol")
        if not isinstance(self.account_mode, DemoAccountMode):
            raise ValueError("account_mode must be DemoAccountMode")
        if type(self.trade_allowed) is not bool:
            raise ValueError("trade_allowed must be bool")
        if self.execution_capability != "NONE" or self.order_execution_enabled:
            raise ValueError("MT5 demo account context cannot grant execution")

    @property
    def fingerprint(self) -> str:
        return _fingerprint(self.to_payload())

    def to_payload(self) -> dict[str, Any]:
        """Return credential-free serialized evidence; raw login is never present."""
        return {
            "schema_version": self.schema_version,
            "account_fingerprint": self.account_fingerprint,
            "server": self.server,
            "symbol": self.symbol,
            "account_mode": self.account_mode.value,
            "trade_allowed": self.trade_allowed,
            "execution_capability": self.execution_capability,
            "order_execution_enabled": self.order_execution_enabled,
        }

    def to_observed_context(self) -> DemoEvidenceObservedContext:
        """Adapt redacted probe evidence into the Step-2191 authorization input."""
        return DemoEvidenceObservedContext(
            account_id=self.account_fingerprint,
            server=self.server,
            symbol=self.symbol,
            account_mode=self.account_mode,
            trade_allowed=self.trade_allowed,
        )


def normalize_mt5_demo_account_context(
    *,
    raw_login: Any,
    raw_server: Any,
    raw_trade_mode: Any,
    trade_allowed: Any,
    resolved_symbol: Any,
    demo_trade_mode: Any,
    contest_trade_mode: Any,
    real_trade_mode: Any,
) -> Mt5DemoAccountContextEvidence:
    """Normalize an already-observed MT5 account object into redacted evidence.

    Runtime constants are supplied by the existing MT5 probe instead of importing
    MetaTrader5 here. Missing, malformed or ambiguous trade-mode constants map to
    UNKNOWN; they never default to DEMO.
    """

    if type(raw_login) is not int or raw_login <= 0:
        raise ValueError("raw_login must be a positive integer")
    server = _required_text(raw_server, "raw_server")
    symbol = _required_text(resolved_symbol, "resolved_symbol")
    if type(trade_allowed) is not bool:
        raise ValueError("trade_allowed must be bool")

    account_mode = normalize_mt5_account_mode(
        raw_trade_mode=raw_trade_mode,
        demo_trade_mode=demo_trade_mode,
        contest_trade_mode=contest_trade_mode,
        real_trade_mode=real_trade_mode,
    )
    account_fingerprint = sha256(
        f"{_ACCOUNT_ID_NAMESPACE}:{raw_login}".encode("utf-8")
    ).hexdigest()

    return Mt5DemoAccountContextEvidence(
        schema_version=MT5_DEMO_ACCOUNT_CONTEXT_SCHEMA,
        account_fingerprint=account_fingerprint,
        server=server,
        symbol=symbol,
        account_mode=account_mode,
        trade_allowed=trade_allowed,
    )


def normalize_mt5_account_mode(
    *,
    raw_trade_mode: Any,
    demo_trade_mode: Any,
    contest_trade_mode: Any,
    real_trade_mode: Any,
) -> DemoAccountMode:
    """Map exact MT5 runtime constants; malformed/ambiguous input fails to UNKNOWN."""

    values = (demo_trade_mode, contest_trade_mode, real_trade_mode)
    if any(type(value) is not int for value in values):
        return DemoAccountMode.UNKNOWN
    if len(set(values)) != 3:
        return DemoAccountMode.UNKNOWN
    if type(raw_trade_mode) is not int:
        return DemoAccountMode.UNKNOWN

    mapping = {
        demo_trade_mode: DemoAccountMode.DEMO,
        contest_trade_mode: DemoAccountMode.CONTEST,
        real_trade_mode: DemoAccountMode.REAL,
    }
    return mapping.get(raw_trade_mode, DemoAccountMode.UNKNOWN)


def parse_mt5_demo_account_context_payload(
    payload: Any,
) -> Mt5DemoAccountContextEvidence:
    """Strictly parse the redacted account-context object from serialized evidence."""

    if not isinstance(payload, dict):
        raise ValueError("demo_account_context must be an object")
    required = {
        "schema_version",
        "account_fingerprint",
        "server",
        "symbol",
        "account_mode",
        "trade_allowed",
        "execution_capability",
        "order_execution_enabled",
    }
    missing = required - payload.keys()
    unknown = payload.keys() - required
    if missing:
        raise ValueError(f"missing demo account context fields: {sorted(missing)}")
    if unknown:
        raise ValueError(f"unknown demo account context fields: {sorted(unknown)}")

    try:
        mode = DemoAccountMode(payload["account_mode"])
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid demo account context account_mode") from exc

    return Mt5DemoAccountContextEvidence(
        schema_version=payload["schema_version"],
        account_fingerprint=payload["account_fingerprint"],
        server=payload["server"],
        symbol=payload["symbol"],
        account_mode=mode,
        trade_allowed=payload["trade_allowed"],
        execution_capability=payload["execution_capability"],
        order_execution_enabled=payload["order_execution_enabled"],
    )


def _required_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def _nonempty(value: str, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be non-empty")


def _sha(value: str, field: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"{field} must be a 64-character SHA-256 hex string")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field} must be hexadecimal") from exc


def _fingerprint(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()
