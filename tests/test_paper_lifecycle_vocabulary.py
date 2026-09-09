from daxlab.runtime.paper_contracts import PaperLifecycleState


def test_paper_lifecycle_vocabulary_is_exact_and_versioned_by_contract() -> None:
    assert {state.value for state in PaperLifecycleState} == {
        "ACK",
        "REJECT",
        "PARTIAL",
        "FILLED",
        "CANCELLED",
    }
