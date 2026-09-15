from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (ROOT / "scripts/export_ig_raw_truth_2233.ps1").read_text(encoding="utf-8")


def test_runner_assigns_distinct_codes_to_every_external_git_stage():
    required = {
        "REMOTE_QUERY_FAILED", "WORKTREE_STATUS_FAILED", "UNTRACKED_CODE_QUERY_FAILED",
        "LOCAL_HEAD_QUERY_FAILED", "START_HEAD_NOT_ANCESTOR", "FETCH_FAILED",
        "PUBLISHED_HEAD_QUERY_FAILED", "LOCAL_HEAD_NOT_ANCESTOR_FINAL",
        "DETACHED_CHECKOUT_FAILED", "HEAD_VERIFY_QUERY_FAILED",
    }
    assert required <= set(re.findall(r"'([A-Z][A-Z0-9_]+)'", SCRIPT))
    assert "GIT_GATE_FAILED" not in SCRIPT


def test_runner_outputs_only_allowlisted_or_prefixed_error_codes():
    assert "error_code={0}" in SCRIPT
    assert "$SafeErrorCodes -contains $candidate" in SCRIPT
    assert "$SafeErrorCodes -notcontains $innerCode" in SCRIPT
    assert "-match '^RAW_EXPORT_" not in SCRIPT
    assert "'RUNNER_UNEXPECTED_FAILURE'" in SCRIPT
    assert "Write-Host $_" not in SCRIPT
    assert "Write-Output $_" not in SCRIPT
    assert "Exception.ToString" not in SCRIPT


def test_runner_is_offline_export_only_and_preserves_originals():
    assert "scripts/export_ig_raw_truth_2233.py" in SCRIPT
    assert "original evidence retained" in SCRIPT
    assert "checkout', '--detach'" in SCRIPT
    for forbidden in ("order_send", "/positions/otc", "Remove-Item", "git reset",
                      "'reset'", "'clean'", "'merge'"):
        assert forbidden not in SCRIPT


def test_success_and_failure_have_deterministic_summary_contracts():
    assert "SUMMARY: SUCCESS; error_code=NONE" in SCRIPT
    assert "SUMMARY: BLOCKED / FAIL_CLOSED; error_code={0}" in SCRIPT
    assert "exit 0" in SCRIPT
    assert "exit 2" in SCRIPT
