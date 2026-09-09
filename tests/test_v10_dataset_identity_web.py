import json
from pathlib import Path


def test_v10_web_retains_hash_verified_session_identity() -> None:
    root = Path(__file__).resolve().parents[1]
    dataset = json.loads((root / "web/status.json").read_text())["dataset"]
    assert dataset["identity_state"] == "HASH_VERIFIED"
    assert dataset["session_rows"] == 172319
    assert dataset["session_days"] == 1673
    assert dataset["session_sha256"] == (
        "e51bba6cb2befe5e7eb0376318e43b096a3e2ecaae3f556019862975c60286a2"
    )
