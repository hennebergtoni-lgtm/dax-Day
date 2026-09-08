"""Print the SHA-verified V11.2 executable surface used for replay integration."""

from __future__ import annotations

import inspect
from dataclasses import fields, is_dataclass

from daxlab.reference.recovered_engine import (
    load_exact_candidate_engine,
    load_oracle_engine,
)

NAMES = (
    "daily_context",
    "simulate_day",
    "grid",
    "cached_metrics",
    "cached_trades",
)


def _signature(value: object) -> object:
    try:
        return inspect.signature(value)
    except (TypeError, ValueError):
        return "<no-signature>"


def _string_constants(value: object) -> list[str]:
    code = getattr(value, "__code__", None)
    if code is None:
        return []
    return sorted({constant for constant in code.co_consts if isinstance(constant, str)})


def describe(label: str, engine: object) -> None:
    print(f"[{label}]")
    for name in NAMES:
        value = getattr(engine, name, None)
        if value is None:
            print(f"{name}: MISSING")
            continue
        print(f"{name}: {_signature(value)}")

    grid = list(engine.grid())
    first_param = grid[0]
    print(f"param_type: {type(first_param).__name__}")
    if is_dataclass(first_param):
        print(f"param_fields: {[field.name for field in fields(first_param)]}")
    else:
        print(f"param_repr: {first_param!r}")

    public_helpers: list[str] = []
    helper_names: list[str] = []
    for name in sorted(dir(engine)):
        if name.startswith("_"):
            continue
        lowered = name.lower()
        if not any(token in lowered for token in ("cache", "day", "session", "prepare", "build")):
            continue
        value = getattr(engine, name)
        if callable(value):
            helper_names.append(name)
            public_helpers.append(f"{name}{_signature(value)}")
    print(f"public_helpers: {public_helpers}")

    for name in ("daily_context", "simulate_day", *helper_names):
        value = getattr(engine, name, None)
        code = getattr(value, "__code__", None)
        if code is not None:
            print(f"{name}_names: {sorted(set(code.co_names))}")
            print(f"{name}_strings: {_string_constants(value)}")

    cost_scenarios = getattr(engine, "COST_SCENARIOS", None)
    print(f"COST_SCENARIOS: {cost_scenarios}")
    print(f"grid_size: {len(grid)}")


def main() -> None:
    describe("ORACLE", load_oracle_engine())
    describe("EXACT", load_exact_candidate_engine())


if __name__ == "__main__":
    main()
