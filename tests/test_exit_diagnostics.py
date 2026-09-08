import pytest

from daxlab.research.exit_diagnostics import describe_exit


def test_exit_diagnostics_capture_ratio() -> None:
    state = describe_exit(realized_r=1.0, mfe_r=2.0, mae_r=-0.5)
    assert state.capture_ratio == 0.5
    assert state.adverse_to_realized_ratio == 0.5


def test_exit_diagnostics_reject_invalid_signs() -> None:
    with pytest.raises(ValueError, match="mfe_r"):
        describe_exit(realized_r=1.0, mfe_r=-0.1, mae_r=-0.5)
    with pytest.raises(ValueError, match="mae_r"):
        describe_exit(realized_r=1.0, mfe_r=1.0, mae_r=0.2)
