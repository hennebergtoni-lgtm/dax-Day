from pathlib import Path


RUNBOOK = Path("docs/MT5_WINDOWS_SHADOW_RUNBOOK.md")


def test_runbook_preserves_no_order_boundary_and_host_sequence():
    text = RUNBOOK.read_text(encoding="utf-8")
    assert "execution_capability=NONE" in text
    assert "order_execution_enabled=false" in text
    assert "V11.2 remains frozen" in text
    assert "mt5_windows_host_discovery.py" in text
    assert "mt5_windows_probe.py" in text
    assert "mt5_timezone_diagnostic.py" in text
    assert "--once" in text
    assert "single-instance lock" in text
    assert "Reboot" in text
    assert "Forward Evidence Summary" in text


def test_runbook_forbids_timezone_guess_and_blocker_bypass():
    text = RUNBOOK.read_text(encoding="utf-8")
    assert "Do not infer verification from configuration alone" in text
    assert "Do not bypass a blocker" in text
    assert "No paper/live order authorization is implied" in text
