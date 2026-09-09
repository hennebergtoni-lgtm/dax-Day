import pytest

from daxlab.runtime.shadow_soak import run_shadow_soak


def test_soak_rejects_empty_symbol() -> None:
    with pytest.raises(ValueError, match="symbol"):
        run_shadow_soak((), symbol="   ")
