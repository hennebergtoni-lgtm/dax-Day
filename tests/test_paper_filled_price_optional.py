from dataclasses import fields

from daxlab.runtime.paper_contracts import PaperTelemetry


def test_paper_telemetry_tracks_requested_and_filled_price_fields() -> None:
    names = {field.name for field in fields(PaperTelemetry)}
    assert "requested_price" in names
    assert "filled_price" in names
