from dataclasses import FrozenInstanceError

import pytest

from daxlab.runtime.shadow_soak import run_shadow_soak


def test_soak_result_is_immutable() -> None:
    result = run_shadow_soak(())
    with pytest.raises(FrozenInstanceError):
        result.processed = 99
