import json
from pathlib import Path
import subprocess
import sys


def test_benchmark_cli_reports_103_bar_observation_metrics():
    root = Path(__file__).parents[1]
    completed = subprocess.run(
        [
            sys.executable,
            str(root / "scripts" / "benchmark_cand001_pipeline.py"),
            "--sessions",
            "1",
            "--repeats",
            "1",
        ],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    result = json.loads(completed.stdout)

    assert result["schema_version"] == "DAX_BOT_CAND001_BENCHMARK_V1"
    assert result["candidate_id"] == "CAND-001"
    assert result["core_version"] == "DAX-BOT/1.0-alpha/CAND-001"
    assert result["bars_per_session"] == 103
    assert result["events_per_repeat"] == 103
    assert result["median_ns_per_event"] > 0
    assert result["p95_ns_per_event"] > 0
    assert result["median_events_per_second"] > 0
    assert result["performance_gate"] == "OBSERVATION_ONLY"
    assert len(result["terminal_snapshot_fingerprint"]) == 64
