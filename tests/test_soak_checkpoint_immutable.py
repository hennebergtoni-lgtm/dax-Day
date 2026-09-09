from dataclasses import FrozenInstanceError

import pytest

from daxlab.runtime.shadow_soak import initial_soak_checkpoint


def test_soak_checkpoint_is_immutable() -> None:
    checkpoint = initial_soak_checkpoint()
    with pytest.raises(FrozenInstanceError):
        checkpoint.processed_count = 1
