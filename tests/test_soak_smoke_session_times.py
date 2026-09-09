from zoneinfo import ZoneInfo

from daxlab.runtime.shadow_soak_fixture import build_bars

BERLIN = ZoneInfo("Europe/Berlin")


def test_30_session_soak_fixture_uses_historical_berlin_session_shape() -> None:
    bars = build_bars()
    for start in range(0, len(bars), 103):
        session = bars[start : start + 103]
        assert session[0].open_time.astimezone(BERLIN).strftime("%H:%M") == "09:00"
        assert session[-1].open_time.astimezone(BERLIN).strftime("%H:%M") == "17:30"
