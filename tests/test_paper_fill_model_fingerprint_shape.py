from daxlab.runtime.paper_contracts import PaperFillModelConfig


def test_paper_fill_model_fingerprint_is_sha256_hex() -> None:
    value = PaperFillModelConfig().fingerprint
    assert len(value) == 64
    int(value, 16)
