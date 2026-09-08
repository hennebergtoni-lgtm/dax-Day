"""Print the SHA-verified V11.2 executable surface used for replay integration."""
from __future__ import annotations

import inspect

from daxlab.reference.recovered_engine import load_exact_candidate_engine, load_oracle_engine


NAMES = (
    "daily_context",
    "simulate_day",
    "grid",
    "cached_metrics",
    "cached_trades",
)


def describe(label: str, engine: object) -> None:
    print(f"[{label}]")
    for name in NAMES:
        value = getattr(engine, name, None)
        if value is None:
            print(f"{name}: MISSING")
            continue
        try:
            signature = inspect.signature(value)
        except (TypeError, ValueError):
            signature = "<no-signature>"
        print(f"{name}: {signature}")
    cost_scenarios = getattr(engine, "COST_SCENARIOS", None)
    print(f"COST_SCENARIOS: {cost_scenarios}")
    print(f"grid_size: {len(list(engine.grid()))}")


def main() -> None:
    describe("ORACLE", load_oracle_engine())
    describe("EXACT", load_exact_candidate_engine())


if __name__ == "__main__":
    main()
