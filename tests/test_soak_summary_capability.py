from daxlab.runtime.shadow_soak import run_shadow_soak, soak_summary


def test_soak_summary_execution_capability_is_none() -> None:
    assert soak_summary(run_shadow_soak(()))["execution_capability"] == "NONE"
