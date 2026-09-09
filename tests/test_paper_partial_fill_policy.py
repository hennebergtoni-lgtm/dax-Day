from daxlab.runtime.paper_contracts import PartialFillPolicy


def test_partial_fill_policy_is_explicit_and_bounded() -> None:
    assert {item.value for item in PartialFillPolicy} == {"DISABLED", "PRO_RATA"}
