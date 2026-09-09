from daxlab.runtime.shadow_soak import run_shadow_soak, soak_summary


def test_soak_execution_flag_is_false_in_result_and_summary() -> None:
    result = run_shadow_soak(())
    assert result.order_execution_enabled is False
    assert soak_summary(result)["order_execution_enabled"] is False
