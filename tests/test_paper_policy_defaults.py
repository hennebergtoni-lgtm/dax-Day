from daxlab.runtime.paper_contracts import (
    GapPolicy,
    PaperFillModelConfig,
    PartialFillPolicy,
    SameBarPolicy,
)


def test_paper_policy_defaults_are_explicit_and_conservative() -> None:
    model = PaperFillModelConfig()
    assert model.same_bar_policy is SameBarPolicy.CONSERVATIVE_STOP_FIRST
    assert model.gap_policy is GapPolicy.FILL_AT_FIRST_AVAILABLE
    assert model.partial_fill_policy is PartialFillPolicy.DISABLED
