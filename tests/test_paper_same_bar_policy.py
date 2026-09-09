from daxlab.runtime.paper_contracts import SameBarPolicy


def test_same_bar_policy_is_explicit_and_conservative() -> None:
    assert {item.value for item in SameBarPolicy} == {"CONSERVATIVE_STOP_FIRST"}
