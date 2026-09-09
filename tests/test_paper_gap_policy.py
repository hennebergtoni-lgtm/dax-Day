from daxlab.runtime.paper_contracts import GapPolicy


def test_gap_policy_is_explicit_and_single_conservative_v1_choice() -> None:
    assert {item.value for item in GapPolicy} == {"FILL_AT_FIRST_AVAILABLE"}
