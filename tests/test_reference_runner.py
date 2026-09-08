from dataclasses import dataclass

import pandas as pd

from daxlab.reference.reference_runner import (
    aggregate_reference,
    build_reference_windows,
    select_variant,
)


@dataclass(frozen=True)
class P:
    name: str


class FakeEngine:
    COST_SCENARIOS = {"normal": {}, "stress_1.5x": {}, "stress_2x": {}}

    @staticmethod
    def metrics(_):
        return {"trades": 0, "avg_r": 0.0, "pf": 0.0, "max_dd_r": 0.0, "return_r": 0.0}

    def cached_metrics(self, days, params, cost):
        base = {
            "a": {"trades": 20, "avg_r": 0.05, "pf": 1.10, "max_dd_r": -2.0, "return_r": 1.0},
            "b": {"trades": 20, "avg_r": 0.04, "pf": 1.20, "max_dd_r": -1.0, "return_r": 1.0},
        }[params.name].copy()
        if cost == "stress_1.5x":
            base.update({"pf": 1.05, "avg_r": 0.01})
        if cost == "stress_2x":
            if params.name == "a":
                base.update({"pf": 0.96, "avg_r": -0.01})
            else:
                base.update({"pf": 0.90, "avg_r": -0.03})
        return base


def test_reference_windows_are_fixed_rolling_45_20_20():
    days = list(range(1673))
    windows = build_reference_windows(days)
    assert len(windows) == 81
    assert windows[0].train == tuple(range(45))
    assert windows[0].oos == tuple(range(45, 65))
    assert windows[1].train == tuple(range(20, 65))
    assert windows[1].oos == tuple(range(65, 85))
    assert len(windows[-1].train) == 45
    assert len(windows[-1].oos) == 20


def test_selection_prefers_stress_eligible_pool():
    engine = FakeEngine()
    pick = select_variant(engine, tuple(range(45)), [P("a"), P("b")])
    assert pick.params == P("a")
    assert pick.stress_ok is True


def test_aggregate_counts_positive_negative_flat():
    frame = pd.DataFrame(
        [
            {"cost": "normal", "trades": 2, "return_r": 1.0},
            {"cost": "normal", "trades": 3, "return_r": -2.0},
            {"cost": "normal", "trades": 0, "return_r": 0.0},
            {"cost": "stress_1.5x", "trades": 5, "return_r": -1.0},
            {"cost": "stress_2x", "trades": 5, "return_r": -2.0},
        ]
    )
    out = aggregate_reference(frame)
    normal = out["costs"]["normal"]
    assert normal == {
        "oos_trades": 5,
        "oos_return_r": -1.0,
        "positive_wfs": 1,
        "negative_wfs": 1,
        "flat_wfs": 1,
    }
