import pytest

from daxlab.research.v12_evidence_gate import (
    OhlcEvidenceIdentity,
    TradeEvidenceIdentity,
    REPRODUCED_TRADE_PROVENANCE,
    REPRODUCED_TRADES_SHA256,
    VERIFIED_DATASET_SHA256,
    verify_ohlc_evidence,
    verify_reproduced_trade_evidence,
)


def test_verified_ohlc_identity_passes() -> None:
    verify_ohlc_evidence(OhlcEvidenceIdentity(172_319, 1_673, VERIFIED_DATASET_SHA256))


def test_ohlc_identity_fails_closed_on_any_drift() -> None:
    with pytest.raises(ValueError, match="row-count"):
        verify_ohlc_evidence(OhlcEvidenceIdentity(172_318, 1_673, VERIFIED_DATASET_SHA256))
    with pytest.raises(ValueError, match="session-day"):
        verify_ohlc_evidence(OhlcEvidenceIdentity(172_319, 1_672, VERIFIED_DATASET_SHA256))
    with pytest.raises(ValueError, match="fingerprint"):
        verify_ohlc_evidence(OhlcEvidenceIdentity(172_319, 1_673, "0" * 64))


def test_verified_reproduced_trade_identity_passes() -> None:
    verify_reproduced_trade_evidence(
        TradeEvidenceIdentity(856, REPRODUCED_TRADES_SHA256, REPRODUCED_TRADE_PROVENANCE)
    )


def test_trade_identity_fails_closed_on_any_drift() -> None:
    with pytest.raises(ValueError, match="row-count"):
        verify_reproduced_trade_evidence(
            TradeEvidenceIdentity(855, REPRODUCED_TRADES_SHA256, REPRODUCED_TRADE_PROVENANCE)
        )
    with pytest.raises(ValueError, match="fingerprint"):
        verify_reproduced_trade_evidence(
            TradeEvidenceIdentity(856, "0" * 64, REPRODUCED_TRADE_PROVENANCE)
        )
    with pytest.raises(ValueError, match="provenance"):
        verify_reproduced_trade_evidence(
            TradeEvidenceIdentity(856, REPRODUCED_TRADES_SHA256, "LEGACY_EVIDENCE_ONLY")
        )
