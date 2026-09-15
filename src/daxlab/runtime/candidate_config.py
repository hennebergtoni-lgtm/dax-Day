"""Typed, immutable rule contract for the first DAX-BOT 1.x alpha candidate.

CAND-001 is intentionally small and observable. It is not a profitability claim.
The confirmed-breakout close semantic is adapted from causal research evidence;
the concrete candidate selections (DE40, OR15, OR-opposite stop, 1.5R, one trade
per session) are explicit NEW_1X_SELECTION choices rather than inherited V11.2
behavior.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from daxlab.runtime.product_identity import BotProductIdentity


CANDIDATE_ID = "CAND-001"
PRODUCT_VERSION = "1.0-alpha"
RULESET_VERSION = "CAND_001_RULESET_V1"
BREAKOUT_SEMANTIC_PROVENANCE = "REUSE_ELIGIBLE_RESEARCH_SEMANTIC"
SELECTION_PROVENANCE = "NEW_1X_SELECTION"


class RegimePolicy(StrEnum):
    OBSERVE_ONLY = "OBSERVE_ONLY"


class StructureRule(StrEnum):
    OPENING_RANGE = "OPENING_RANGE"


class EntryRule(StrEnum):
    CONFIRMED_BREAKOUT_CLOSE = "CONFIRMED_BREAKOUT_CLOSE"


class DirectionPolicy(StrEnum):
    BOTH = "BOTH"


class StopRule(StrEnum):
    OR_OPPOSITE = "OR_OPPOSITE"


class TargetRule(StrEnum):
    FIXED_R_MULTIPLE = "FIXED_R_MULTIPLE"


@dataclass(frozen=True, slots=True)
class Cand001Config:
    """Frozen strategy-relevant configuration snapshot for CAND-001."""

    candidate_id: str = CANDIDATE_ID
    ruleset_version: str = RULESET_VERSION
    symbol: str = "DE40"
    bar_timeframe: str = "5m"
    session_timezone: str = "Europe/Berlin"
    session_start: str = "09:00"
    session_end: str = "17:30"
    or_minutes: int = 15
    regime_policy: RegimePolicy = RegimePolicy.OBSERVE_ONLY
    structure_rule: StructureRule = StructureRule.OPENING_RANGE
    entry_rule: EntryRule = EntryRule.CONFIRMED_BREAKOUT_CLOSE
    direction_policy: DirectionPolicy = DirectionPolicy.BOTH
    stop_rule: StopRule = StopRule.OR_OPPOSITE
    target_rule: TargetRule = TargetRule.FIXED_R_MULTIPLE
    reward_risk: float = 1.5
    max_trades_per_session: int = 1

    def __post_init__(self) -> None:
        fixed_values = {
            "candidate_id": (self.candidate_id, CANDIDATE_ID),
            "ruleset_version": (self.ruleset_version, RULESET_VERSION),
            "symbol": (self.symbol, "DE40"),
            "bar_timeframe": (self.bar_timeframe, "5m"),
            "session_timezone": (self.session_timezone, "Europe/Berlin"),
            "session_start": (self.session_start, "09:00"),
            "session_end": (self.session_end, "17:30"),
            "or_minutes": (self.or_minutes, 15),
            "reward_risk": (self.reward_risk, 1.5),
            "max_trades_per_session": (self.max_trades_per_session, 1),
        }
        for field_name, (observed, expected) in fixed_values.items():
            if observed != expected:
                raise ValueError(f"{field_name} must be fixed at {expected!r} for CAND-001")

        enum_fields = {
            "regime_policy": (self.regime_policy, RegimePolicy, RegimePolicy.OBSERVE_ONLY),
            "structure_rule": (self.structure_rule, StructureRule, StructureRule.OPENING_RANGE),
            "entry_rule": (self.entry_rule, EntryRule, EntryRule.CONFIRMED_BREAKOUT_CLOSE),
            "direction_policy": (self.direction_policy, DirectionPolicy, DirectionPolicy.BOTH),
            "stop_rule": (self.stop_rule, StopRule, StopRule.OR_OPPOSITE),
            "target_rule": (self.target_rule, TargetRule, TargetRule.FIXED_R_MULTIPLE),
        }
        for field_name, (observed, enum_type, expected) in enum_fields.items():
            if not isinstance(observed, enum_type) or observed is not expected:
                raise ValueError(f"{field_name} must be fixed at {expected.value!r} for CAND-001")

    def product_identity(self) -> BotProductIdentity:
        return BotProductIdentity.build(
            product_version=PRODUCT_VERSION,
            candidate_id=self.candidate_id,
            config=self,
        )
