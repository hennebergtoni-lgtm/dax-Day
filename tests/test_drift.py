from daxlab.runtime.drift import DriftState, ReferenceBand


def test_drift_can_warn_or_block_without_mutating_reference():
    band = ReferenceBand(10.0, 20.0, block_margin=0.25)
    assert band.classify(15.0) is DriftState.OK
    assert band.classify(8.0) is DriftState.WARN
    assert band.classify(30.0) is DriftState.BLOCK
    assert (band.lower, band.upper) == (10.0, 20.0)
