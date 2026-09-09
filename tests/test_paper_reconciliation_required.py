from dataclasses import fields

from daxlab.runtime.paper_contracts import PaperTelemetry


def test_paper_telemetry_requires_reconciliation_state_field() -> None:
    names = {field.name for field in fields(PaperTelemetry)}
    assert "reconciliation_state" in names
    assert "health_state" in names
    assert "feed_age_seconds" in names
    assert "client_order_id" in names
