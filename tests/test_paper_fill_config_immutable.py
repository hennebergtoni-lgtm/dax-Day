from dataclasses import FrozenInstanceError

import pytest

from daxlab.runtime.paper_contracts import PaperFillModelConfig


def test_paper_fill_model_config_is_immutable() -> None:
    model = PaperFillModelConfig()
    with pytest.raises(FrozenInstanceError):
        model.slippage_points = 9.0
