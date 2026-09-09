from dataclasses import fields

from daxlab.runtime.paper_contracts import PaperTelemetry


def test_paper_telemetry_contains_lifecycle_state() -> None:
    assert "lifecycle_state" in {field.name for field in fields(PaperTelemetry)}
