from datetime import datetime
import json

import pytest

from daxlab.runtime.mt5_evidence import (
    build_host_evidence,
    detect_evidence_conflict,
    read_host_evidence,
    recovery_manifest_entry,
    write_host_evidence,
)


def sample_payload() -> dict:
    return {
        "terminal_connected": True,
        "symbol": "GER40",
        "feed_fingerprint": "abc123",
        "read_only": True,
    }


def test_evidence_is_deterministic_and_manifest_safe() -> None:
    observed_at = datetime.fromisoformat("2026-09-08T22:00:00+02:00")
    first = build_host_evidence(
        observed_at=observed_at,
        kind="SYNTHETIC_READ_ONLY",
        payload=sample_payload(),
    )
    reversed_payload = dict(reversed(list(sample_payload().items())))
    second = build_host_evidence(
        observed_at=observed_at,
        kind="SYNTHETIC_READ_ONLY",
        payload=reversed_payload,
    )
    assert first.evidence_id == second.evidence_id
    assert first.payload_sha256 == second.payload_sha256
    assert recovery_manifest_entry(first)["type"] == "MT5_HOST_EVIDENCE"


def test_credentials_and_account_identifiers_are_rejected() -> None:
    observed_at = datetime.fromisoformat("2026-09-08T22:00:00+02:00")
    for key in ("password", "otp", "account_number", "api_key"):
        with pytest.raises(ValueError, match="forbidden"):
            build_host_evidence(
                observed_at=observed_at,
                kind="X",
                payload={key: "x"},
            )


def test_recovery_round_trip_and_tamper_detection(tmp_path) -> None:
    observed_at = datetime.fromisoformat("2026-09-08T22:00:00+02:00")
    evidence = build_host_evidence(
        observed_at=observed_at,
        kind="SYNTHETIC_READ_ONLY",
        payload=sample_payload(),
    )
    path = tmp_path / "mt5_host_evidence.json"
    write_host_evidence(path, evidence)
    restored = read_host_evidence(path)
    assert restored == evidence

    raw = json.loads(path.read_text())
    raw["payload"]["symbol"] = "DE40"
    path.write_text(json.dumps(raw))
    with pytest.raises(ValueError, match="hash/identity conflict"):
        read_host_evidence(path)


def test_duplicate_conflict_rules() -> None:
    observed_at = datetime.fromisoformat("2026-09-08T22:00:00+02:00")
    first = build_host_evidence(
        observed_at=observed_at,
        kind="X",
        payload=sample_payload(),
    )
    assert detect_evidence_conflict(first, first) == "DUPLICATE_IDENTICAL"

    second = build_host_evidence(
        observed_at=observed_at,
        kind="X",
        payload={**sample_payload(), "symbol": "DE40"},
    )
    assert detect_evidence_conflict(first, second) == "DISTINCT"
