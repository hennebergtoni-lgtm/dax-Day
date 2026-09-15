"""BOOST001 bounded-sleeve simulation; research only, never order sizing."""

from __future__ import annotations

import random
from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True, slots=True)
class SleeveConfig:
    initial_capital: float = 200.0
    risk_fraction: float = 0.05
    max_eur_risk: float = 20.0
    ruin_floor: float = 1.0

    def __post_init__(self) -> None:
        _validate_r_values([self.initial_capital, self.risk_fraction, self.max_eur_risk, self.ruin_floor])
        if self.initial_capital <= 0:
            raise ValueError("initial_capital must be positive")
        if not 0 < self.risk_fraction <= 1:
            raise ValueError("risk_fraction must be in (0, 1]")
        if self.max_eur_risk <= 0:
            raise ValueError("max_eur_risk must be positive")
        if self.ruin_floor < 0 or self.ruin_floor >= self.initial_capital:
            raise ValueError("ruin_floor must be >= 0 and below initial capital")


@dataclass(frozen=True, slots=True)
class SleeveStep:
    index: int
    starting_capital: float
    euro_risk: float
    r_result: float
    pnl: float
    ending_capital: float


@dataclass(frozen=True, slots=True)
class SleeveResult:
    initial_capital: float
    final_capital: float
    max_drawdown_fraction: float
    ruined: bool
    steps: tuple[SleeveStep, ...]


def _validate_r_values(r_values: list[float]) -> None:
    try:
        valid = all(type(value) in (int, float) and isfinite(float(value)) for value in r_values)
    except OverflowError:
        valid = False
    if not valid:
        raise ValueError("R outcomes must be finite")


def simulate_sleeve(r_values: list[float], config: SleeveConfig) -> SleeveResult:
    """Apply fixed-fraction/capped risk; losses can never trigger a risk increase."""
    _validate_r_values(r_values)
    capital = float(config.initial_capital)
    peak = capital
    max_drawdown_fraction = 0.0
    steps: list[SleeveStep] = []
    ruined = False

    for index, raw_r in enumerate(r_values):
        if capital <= config.ruin_floor:
            ruined = True
            break
        starting = capital
        euro_risk = min(starting * config.risk_fraction, config.max_eur_risk)
        r_result = float(raw_r)
        pnl = euro_risk * r_result
        capital = max(0.0, starting + pnl)
        peak = max(peak, capital)
        drawdown = 0.0 if peak == 0 else (peak - capital) / peak
        max_drawdown_fraction = max(max_drawdown_fraction, drawdown)
        steps.append(
            SleeveStep(
                index=index,
                starting_capital=starting,
                euro_risk=euro_risk,
                r_result=r_result,
                pnl=pnl,
                ending_capital=capital,
            )
        )
        if capital <= config.ruin_floor:
            ruined = True
            break

    return SleeveResult(
        initial_capital=config.initial_capital,
        final_capital=capital,
        max_drawdown_fraction=max_drawdown_fraction,
        ruined=ruined,
        steps=tuple(steps),
    )


def bootstrap_ruin_probability(
    observed_r: list[float],
    config: SleeveConfig,
    *,
    paths: int = 1000,
    trades_per_path: int | None = None,
    seed: int = 0,
) -> float:
    """Seeded bootstrap estimate for research comparison, never a live guarantee."""
    _validate_r_values(observed_r)
    if not observed_r:
        raise ValueError("observed_r must not be empty")
    _positive_integer(paths, "paths")
    path_length = trades_per_path if trades_per_path is not None else len(observed_r)
    _positive_integer(path_length, "trades_per_path")

    rng = random.Random(seed)
    ruined = 0
    for _ in range(paths):
        path = [rng.choice(observed_r) for _ in range(path_length)]
        ruined += simulate_sleeve(path, config).ruined
    return ruined / paths


@dataclass(frozen=True, slots=True)
class FixedCashResearchConfig:
    """Explicit cash/floor/horizon model; never a runtime admission/sizing policy."""

    initial_capital: float
    cash_risk: float
    capital_floor: float
    horizon_trades: int

    def __post_init__(self):
        _validate_r_values([self.initial_capital, self.cash_risk, self.capital_floor])
        if self.initial_capital <= 0 or self.cash_risk <= 0:
            raise ValueError("capital and cash risk must be positive")
        if not 0 <= self.capital_floor < self.initial_capital:
            raise ValueError("floor must be non-negative below capital")
        _positive_integer(self.horizon_trades, "horizon")


def _positive_integer(value, name):
    if type(value) is not int or value <= 0:
        raise ValueError(name + " must be a positive integer")


def resample_indices(size, *, horizon, mode, block_length, labels, rng):
    """Preserve local sequence within blocks, with explicit terminal truncation.

    REGIME_RUN samples homogeneous chronological runs; it does not preserve regime
    transition probabilities. SESSION/CLUSTER labels identify contiguous units,
    never arbitrary ex-post merging. Trade horizon may censor the final unit.
    """
    for value, name in ((size, "size"), (horizon, "horizon"), (block_length, "block length")):
        _positive_integer(value, name)
    if mode not in {"IID", "CIRCULAR_BLOCK", "SESSION_BLOCK", "CLUSTER_BLOCK", "REGIME_RUN"}:
        raise ValueError("unsupported resampling")
    if block_length > size or horizon > 1_000_000:
        raise ValueError("block length or horizon exceeds research bounds")
    units = []
    if mode in {"SESSION_BLOCK", "CLUSTER_BLOCK", "REGIME_RUN"}:
        if labels is None or len(labels) != size or any(
            not isinstance(label, str) or not label for label in labels
        ):
            raise ValueError("resampling requires aligned explicit labels")
        current = []
        prior = None
        seen = set()
        for index, label in enumerate(labels):
            if label != prior:
                if mode != "REGIME_RUN" and label in seen:
                    raise ValueError("session/cluster label reappears after another unit")
                if current:
                    units.append(current)
                current = []
                seen.add(label)
            current.append(index)
            prior = label
        units.append(current)
    selected = []
    censored = False
    while len(selected) < horizon:
        if mode == "IID":
            unit = [rng.randrange(size)]
        elif mode == "CIRCULAR_BLOCK":
            start = rng.randrange(size)
            unit = [(start + i) % size for i in range(block_length)]
        else:
            unit = rng.choice(units)
        remaining = horizon - len(selected)
        censored = len(unit) > remaining
        selected.extend(unit[:remaining])
    return tuple(selected), censored


def simulate_fixed_cash(r_values, config):
    """Trade-boundary cash model, no margin/equity/intrabar/unseen-shock guarantee."""
    _validate_r_values(r_values)
    if len(r_values) != config.horizon_trades:
        raise ValueError("exact declared trade horizon required")
    capital = peak = float(config.initial_capital)
    max_drawdown = 0.0
    floor_hit = False
    risks = []
    for value in r_values:
        if capital <= config.capital_floor:
            floor_hit = True
            break
        risk = min(config.cash_risk, capital - config.capital_floor)
        risks.append(risk)
        capital += risk * value
        if not isfinite(capital):
            raise ValueError("cash simulation overflow")
        peak = max(peak, capital)
        max_drawdown = max(max_drawdown, peak - capital)
        if capital <= config.capital_floor:
            floor_hit = True
            break
    return {"final_capital": capital, "floor_hit": floor_hit,
            "max_cash_drawdown": max_drawdown, "cash_risks": tuple(risks),
            "trades_observed": len(risks), "scope": "TRADE_BOUNDARY_RESEARCH_NOT_ACCOUNT_EQUITY"}


def fixed_cash_tail_research(gross_r, cost_r, config, *, source_sha256,
                             paths=1000, seed=0, mode="IID", block_length=1, labels=None):
    """Normal/1.5x/2x cost sensitivity with identical sampled paths across stresses.

    Inputs must contain explicit gross-R and cost-R under one pinned ledger/spec.
    Never derive costs from aggregate net-R or manufacture quote/gap slippage.
    """
    from dataclasses import asdict
    import hashlib
    import json
    import re
    from daxlab.research.failure_analysis import empirical_distribution

    _validate_r_values(gross_r)
    _validate_r_values(cost_r)
    if not gross_r or len(gross_r) != len(cost_r) or any(value < 0 for value in cost_r):
        raise ValueError("aligned non-empty gross/cost ledger required")
    if re.fullmatch(r"[0-9a-f]{64}", source_sha256) is None:
        raise ValueError("pinned source SHA256 required")
    _positive_integer(paths, "paths")
    if paths * config.horizon_trades > 1_000_000:
        raise ValueError("research work budget exceeded")
    if type(seed) is not int:
        raise ValueError("integer deterministic seed required")
    rng = random.Random(seed)
    outcomes = {factor: [] for factor in (1.0, 1.5, 2.0)}
    censored = 0
    for _ in range(paths):
        indices, cut = resample_indices(len(gross_r), horizon=config.horizon_trades,
                                        mode=mode, block_length=block_length, labels=labels, rng=rng)
        censored += cut
        for factor, results in outcomes.items():
            values = [gross_r[i] - factor * cost_r[i] for i in indices]
            results.append(simulate_fixed_cash(values, config))
    identity = {"source_sha256": source_sha256, "gross_r": gross_r, "cost_r": cost_r,
                "config": asdict(config), "mode": mode, "block_length": block_length,
                "labels": labels, "paths": paths, "seed": seed}
    digest = hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(",", ":"),
                                      allow_nan=False).encode()).hexdigest()
    return {"schema": "DAX_FIXED_CASH_TAIL_RESEARCH_V1", "identity_sha256": digest,
            "source_sha256": source_sha256, "source_verification": "CALLER_PIN_NOT_INDEPENDENT_LEDGER_VALIDATION",
            "assumptions": identity,
            "mode": mode, "terminal_unit_censored_paths": censored,
            "regime_transition_probabilities_preserved": False,
            "inference": "CONDITIONAL_EMPIRICAL_RESAMPLING_NOT_FUTURE_SURVIVAL_GUARANTEE",
            "account_equity_margin_cashflow_intrabar": "NOT_MODELED",
            "execution_capability": "NONE", "order_execution_enabled": False,
            "cost_stresses": {
                str(factor): {
                    "floor_hit_rate": sum(r["floor_hit"] for r in results) / paths,
                    "final_capital": empirical_distribution([r["final_capital"] for r in results]) | {
                        "worst_observed": min(r["final_capital"] for r in results),
                        "worst_direction": "LOWER_CAPITAL",
                        "quantile_direction": "UPPER_QUANTILES_ARE_HIGHER_CAPITAL_NOT_LOSS_TAIL",
                    },
                    "max_cash_drawdown": empirical_distribution([r["max_cash_drawdown"] for r in results]),
                } for factor, results in outcomes.items()}}
