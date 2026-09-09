import json
from pathlib import Path


def test_web_reference_aggregate_remains_frozen() -> None:
    root = Path(__file__).resolve().parents[1]
    web = json.loads((root / "web/status.json").read_text())
    assert web["reference_results"]["normal_oos_trades"] == 856
    assert web["reference_results"]["normal_oos_return_r"] == -31.309210619787684
    assert web["reference_results"]["positive_wfs"] == 37
    assert web["reference_results"]["negative_wfs"] == 44
