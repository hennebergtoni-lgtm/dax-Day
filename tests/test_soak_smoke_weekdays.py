from zoneinfo import ZoneInfo

from scripts.shadow_soak_smoke import build_bars

BERLIN = ZoneInfo("Europe/Berlin")


def test_30_session_soak_fixture_contains_weekdays_only() -> None:
    bars = build_bars()
    session_starts = bars[::103]
    assert len(session_starts) == 30
    assert all(bar.open_time.astimezone(BERLIN).weekday() < 5 for bar in session_starts)
