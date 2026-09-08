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
    if any(not isfinite(float(value)) for value in r_values):
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
    if paths <= 0:
        raise ValueError("paths must be positive")
    path_length = trades_per_path if trades_per_path is not None else len(observed_r)
    if path_length <= 0:
        raise ValueError("trades_per_path must be positive")

    rng = random.Random(seed)
    ruined = 0
    for _ in range(paths):
        path = [rng.choice(observed_r) for _ in range(path_length)]
        ruined += simulate_sleeve(path, config).ruined
    return ruined / paths
