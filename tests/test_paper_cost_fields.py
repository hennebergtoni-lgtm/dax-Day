from dataclasses import fields

from daxlab.runtime.paper_contracts import PaperTelemetry


def test_paper_telemetry_tracks_spread_slippage_and_commission() -> None:
    names = {field.name for field in fields(PaperTelemetry)}
    assert {"spread_points", "slippage_points", "commission_points"} <= names
