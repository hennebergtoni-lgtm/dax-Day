import json
from pathlib import Path


def test_v10_web_retains_engine_and_oracle_hashes() -> None:
    root = Path(__file__).resolve().parents[1]
    engine = json.loads((root / "web/status.json").read_text())["engine"]
    assert engine["exact_candidate_sha256"] == (
        "b3d62e0cad72420d36ade523857d024d4a334298be51a8313069e36614bda888"
    )
    assert engine["oracle_sha256"] == (
        "62adde1ccd630d01e9500b20c0efa88a0a8bd277e74c1a2c932ec6fc6efd3a0f"
    )
    assert engine["variants"] == 144
