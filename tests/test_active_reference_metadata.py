from daxlab.reference.v11_2 import V11_2, assert_reference_invariants


def test_active_reference_metadata_cannot_fall_back_to_legacy() -> None:
    assert_reference_invariants()
    assert V11_2.oos_trades == 856
    assert V11_2.oos_return_r == -31.309210619787684
    assert V11_2.positive_wfs == 37
    assert V11_2.negative_wfs == 44
    assert V11_2.legacy_oos_trades == 1384
    assert V11_2.legacy_oos_return_r == -68.10950257808015
    assert V11_2.oos_trades != V11_2.legacy_oos_trades
