from daxlab.runtime.shadow_soak import run_shadow_soak


def test_empty_soak_is_valid_non_executing_state() -> None:
    result = run_shadow_soak(())
    assert result.processed == 0
    assert result.blocked == 0
    assert result.duplicates_suppressed == 0
    assert result.decisions == ()
    assert result.execution_capability == "NONE"
    assert result.order_execution_enabled is False
