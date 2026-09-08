from __future__ import annotations

from dataclasses import dataclass

from daxlab.research.filter_registry import ControlMode, FilterRegistry


@dataclass(frozen=True)
class RegimeSnapshot:
    volatility: str
    structure: str
    prior_day: str
    session_phase: str


@dataclass(frozen=True)
class FilterSuggestion:
    key: str
    reason: str
    action: str


def suggest_filters(snapshot: RegimeSnapshot, registry: FilterRegistry) -> tuple[FilterSuggestion, ...]:
    """Return explainable research/UI suggestions without bypassing evidence gates."""
    suggestions: list[FilterSuggestion] = []

    if snapshot.structure == "breakout_retest" and "bb001" in {x.key for x in registry.all()}:
        bb = registry.get("bb001")
        suggestions.append(
            FilterSuggestion(
                key=bb.key,
                reason="Breakout/retest structure can be annotated with causal Bollinger quality state.",
                action="observe" if bb.can_use(ControlMode.VISIBLE_ONLY) else "eligible",
            )
        )

    if snapshot.prior_day == "extended" and "prev_range_atr" in {x.key for x in registry.all()}:
        ctx = registry.get("prev_range_atr")
        suggestions.append(
            FilterSuggestion(
                key=ctx.key,
                reason="Prior-day extension is a researched context variable for retest quality.",
                action="observe" if ctx.can_use(ControlMode.VISIBLE_ONLY) else "eligible",
            )
        )

    return tuple(suggestions)
