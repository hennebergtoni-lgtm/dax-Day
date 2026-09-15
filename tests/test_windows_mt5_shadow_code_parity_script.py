from pathlib import Path


SCRIPT = Path("scripts/check_windows_mt5_shadow_code_parity.ps1")
LEGACY_PINNED_COMMIT = "8fe0b61a4da0b5637df372343d67b202bfbe8222"

CRITICAL_FIXED_PATHS = (
    "scripts/check_windows_mt5_shadow_code_parity.ps1",
    "scripts/check_windows_mt5_shadow_runtime.ps1",
    "scripts/install_windows_mt5_shadow_task.ps1",
    "scripts/mt5_shadow_supervisor.py",
    "scripts/mt5_windows_probe.py",
    "scripts/preflight_windows_mt5_shadow_autostart.ps1",
    "scripts/windows_mt5_shadow_start.ps1",
    "src/daxlab/runtime/atomic_json.py",
    "src/daxlab/runtime/operator_runtime_bridge.py",
    "src/daxlab/runtime/operator_snapshot.py",
    "src/daxlab/runtime/product_identity.py",
    "src/daxlab/runtime/prospective_gate.py",
    "src/daxlab/runtime/shadow_observation.py",
    "src/daxlab/runtime/shadow_resume_anchor.py",
    "src/daxlab/runtime/shadow_soak.py",
    "src/daxlab/runtime/single_instance.py",
)


def _text() -> str:
    return SCRIPT.read_text(encoding="utf-8")


def test_parity_checker_tracks_upstream_and_covers_current_candidate_mt5_surface() -> None:
    text = _text()
    assert LEGACY_PINNED_COMMIT not in text
    assert "rev-parse', '--verify', '@{upstream}" in text
    assert "HEAD PARITY | MATCH" in text
    assert "HEAD PARITY | MISMATCH" in text
    assert "ls-tree', '-r', '--name-only'" in text
    assert "(candidate_|mt5_)" in text
    assert "dynamic_candidate_mt5" in text
    for path in CRITICAL_FIXED_PATHS:
        assert path in text
    assert "MISMATCH" in text
    assert "MISSING_LOCAL" in text
    assert "EXPECTED_BLOB_UNAVAILABLE" in text
    assert "LOCAL_HASH_UNAVAILABLE" in text
    assert "exit 1" in text


def test_parity_checker_uses_git_canonical_blob_hashing_for_windows_crlf_safety() -> None:
    text = _text()
    assert "PARITY MODE | GIT_CANONICAL_BLOB / CRLF_SAFE" in text
    assert "'hash-object'" in text
    assert '"--path=$relativePath"' in text
    assert '"${ExpectedCommit}:$relativePath"' in text
    assert "LocalObjectId" in text
    assert "ExpectedObjectId" in text
    assert "Invoke-WebRequest" not in text
    assert "raw.githubusercontent.com" not in text
    assert "Get-FileHash" not in text


def test_parity_checker_has_no_execution_or_scheduler_mutation_surface() -> None:
    text = _text().lower()
    forbidden = (
        "start-scheduledtask",
        "stop-scheduledtask",
        "register-scheduledtask",
        "unregister-scheduledtask",
        "set-scheduledtask",
        "order_send",
        "ordersend",
        "trade.request",
        "execution_capability=true",
        "order_execution_enabled=true",
    )
    for token in forbidden:
        assert token not in text
    assert "read_only / no_order / no_scheduler_changes" in text
    assert "execution_capability=none" in text
    assert "order_execution_enabled=false" in text


def test_parity_checker_requires_full_lowercase_commit_sha() -> None:
    text = _text()
    assert "^[0-9a-f]{40}$" in text
