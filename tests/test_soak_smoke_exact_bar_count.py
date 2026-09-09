from daxlab.runtime.shadow_soak_fixture import BARS_PER_SESSION, SESSIONS


def test_soak_smoke_constants_define_3090_closed_m5_observations() -> None:
    assert SESSIONS == 30
    assert BARS_PER_SESSION == 103
    assert SESSIONS * BARS_PER_SESSION == 3090
