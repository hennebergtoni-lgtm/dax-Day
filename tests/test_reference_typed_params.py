from dataclasses import dataclass
from types import SimpleNamespace

from daxlab.contracts import REFERENCE_COSTS
from daxlab.reference import reference_runner as rr


@dataclass(frozen=True)
class Params:
    token: int


class RecordingEngine:
    COST_SCENARIOS = tuple(model.name for model in REFERENCE_COSTS)

    def __init__(self) -> None:
        self.oos_params = []

    def grid(self):
        return [Params(index) for index in range(144)]

    def cached_metrics(self, days, params, cost_name):
        self.oos_params.append(params)
        return {
            "trades": 1,
            "return_r": 0.0,
            "pf": 1.0,
            "avg_r": 0.0,
            "max_dd_r": 0.0,
        }


def test_selected_typed_params_flow_directly_into_oos_cached_metrics(monkeypatch):
    sentinel = Params(999)
    metrics = {
        "trades": 12,
        "return_r": 0.0,
        "pf": 1.0,
        "avg_r": 0.0,
        "max_dd_r": 0.0,
    }
    candidate = rr.CandidateScore(
        variant_index=1,
        params=sentinel,
        normal=metrics,
        stress_15=metrics,
        stress_20=metrics,
        score=0.0,
        stress_ok=True,
    )
    window = SimpleNamespace(number=1, train=("train",), oos=("oos",))
    monkeypatch.setattr(rr, "select_variant", lambda engine, train, grid: candidate)
    monkeypatch.setattr(rr, "build_reference_windows", lambda days: [window])

    engine = RecordingEngine()
    rr.run_cached_reference(engine, ["ignored"])

    assert len(engine.oos_params) == len(REFERENCE_COSTS)
    assert all(params is sentinel for params in engine.oos_params)
