from dataclasses import fields

from daxlab.runtime.paper_contracts import PaperTelemetry


def test_paper_telemetry_has_explicit_schema_version_field() -> None:
    assert "schema_version" in {field.name for field in fields(PaperTelemetry)}
