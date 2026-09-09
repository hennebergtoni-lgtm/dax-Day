from dataclasses import fields

from daxlab.runtime.paper_contracts import PaperTelemetry


def test_paper_telemetry_tracks_requested_accepted_and_filled_timestamps() -> None:
    names = {field.name for field in fields(PaperTelemetry)}
    assert {"requested_at", "accepted_at", "filled_at"} <= names
