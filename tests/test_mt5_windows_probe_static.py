from pathlib import Path


PROBE = Path("scripts/mt5_windows_probe.py")
BOOTSTRAP = Path("scripts/windows_mt5_bootstrap.ps1")


def test_probe_excludes_bar_zero_and_has_no_order_api() -> None:
    text = PROBE.read_text(encoding="utf-8")
    assert "closed_rates_start_pos(1)" in text
    assert "copy_rates_from_pos" in text
    assert "order_send" not in text
    assert "order_check" not in text
    assert "login(" not in text


def test_probe_marks_execution_disabled() -> None:
    text = PROBE.read_text(encoding="utf-8")
    assert '"order_execution_enabled": False' in text
    assert '"BAR_0_EXCLUDED"' in text
    assert '"NO_CREDENTIALS"' in text


def test_bootstrap_does_not_accept_credentials() -> None:
    text = BOOTSTRAP.read_text(encoding="utf-8").lower()
    assert "password" in text  # explicit warning is expected
    assert "--password" not in text
    assert "--login" not in text
    assert "order_send" not in text
