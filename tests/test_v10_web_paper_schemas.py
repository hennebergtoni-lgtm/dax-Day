import json
from pathlib import Path


def test_web_paper_preparation_schema_names_match_contracts() -> None:
    root = Path(__file__).resolve().parents[1]
    paper = json.loads((root / "web/status.json").read_text())["paper_preparation"]
    assert paper["execution_intent_schema"] == "DAXLAB_EXECUTION_INTENT_V1"
    assert paper["fill_model_schema"] == "DAXLAB_PAPER_FILL_MODEL_V1"
    assert paper["telemetry_schema"] == "DAXLAB_PAPER_TELEMETRY_V1"
