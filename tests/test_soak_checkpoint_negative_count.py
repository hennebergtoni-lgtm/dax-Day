from dataclasses import replace

import pytest

from daxlab.runtime.shadow_soak import initial_soak_checkpoint, verify_soak_checkpoint


def test_checkpoint_rejects_negative_processed_count() -> None:
    checkpoint = initial_soak_checkpoint()
    with pytest.raises(ValueError, match="processed_count"):
        verify_soak_checkpoint(replace(checkpoint, processed_count=-1))
