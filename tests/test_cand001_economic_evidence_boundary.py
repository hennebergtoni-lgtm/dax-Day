from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "docs" / "CAND001_ECONOMIC_EVIDENCE_AUDIT_V1.md"
CLOSEOUT = ROOT / "docs" / "DAX_BOT_1_0_CLOSEOUT_FINAL.md"


def test_cand001_economic_status_is_explicitly_unverified() -> None:
    text = AUDIT.read_text(encoding="utf-8")
    assert "CAND-001 profitability is `UNVERIFIED`" in text
    assert "CAND-001 robustness is `UNVERIFIED`" in text
    assert "no REF-V11.2 or V12 research metric may be relabeled" in text


def test_cand001_full_sample_measurement_cannot_be_called_oos_edge_proof() -> None:
    text = AUDIT.read_text(encoding="utf-8")
    assert "DESCRIPTIVE / IN-SAMPLE MEASUREMENT" in text
    assert "must not be called an independent edge proof" in text
    assert "No full-sample result, however attractive, may bypass OOS/WF" in text


def test_alpha_closeout_remains_non_profitability_claim() -> None:
    text = CLOSEOUT.read_text(encoding="utf-8")
    assert "NO PROFITABILITY OR EXECUTION CLAIM" in text
    assert "does not claim profitability" in text
    assert "not a profitability milestone" in text.lower()


def test_minimum_harness_requires_existing_cand001_semantics_and_fingerprints() -> None:
    text = AUDIT.read_text(encoding="utf-8")
    assert "Reuse the exact CAND-001 runtime semantics/config identity" in text
    assert "Reuse Candidate admission, virtual lifecycle" in text
    assert "dataset, product/candidate/config, core/ruleset and cost-model fingerprints" in text
    assert "do not create a second strategy interpretation" in text
