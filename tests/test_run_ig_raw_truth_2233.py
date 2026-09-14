"""Offline runner contract tests; no live IG session and no broker evidence."""
from datetime import datetime, timedelta, timezone
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from test_ig_demo_readonly_probe import price_row

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "raw_truth_runner_test", ROOT / "scripts/run_ig_raw_truth_2233.py",
)
assert SPEC and SPEC.loader
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)
HEAD = "a" * 40
START = datetime(2026, 9, 14, 12, 44, 47, tzinfo=timezone.utc)


class Harness:
    def __init__(self, tmp_path, monkeypatch):
        self.root = tmp_path
        self.creds = tmp_path / "external credentials with spaces.env"
        self.creds.write_text("NEVER_READ_SECRET")
        self.current = START
        self.calls = []
        self.failure = None
        self.request_offset = 0
        self.check_failure = None
        monkeypatch.setattr(runner.platform, "system", lambda: "Windows")

    def check(self, head):
        if self.check_failure:
            raise runner.diagnostic.HostTestBlocked(self.check_failure)
        assert head == HEAD
        return head

    def wait(self, target):
        self.current = target

    def execute(self, args):
        output = Path(args[args.index("--output") + 1])
        label = output.stem
        self.calls.append((label, args))
        if label == self.failure:
            return 2, "IG_AUTHENTICATION_FAILED_NO_RETRY"
        if "--compare" in args:
            index = args.index("--compare")
            payload = runner.diagnostic.compare(*(
                json.loads(Path(path).read_text()) for path in args[index + 1:index + 3]
            ))
        else:
            requested = self.current + timedelta(seconds=self.request_offset)
            boundary = requested.replace(second=0, microsecond=0)
            boundary -= timedelta(minutes=boundary.minute % 5)
            payload = runner.diagnostic.snapshot(
                [price_row(boundary - timedelta(minutes=5 * i))
                 for i in reversed(range(40))],
                head=HEAD, requested=requested, observed=requested + timedelta(seconds=1),
            )
        with output.open("x") as stream:
            json.dump(payload, stream)
        self.current += timedelta(seconds=2)
        return 0, None

    def run(self, **kwargs):
        return runner.run(
            HEAD, root=self.root, credentials_file=self.creds,
            clock=lambda: self.current, wait=self.wait, executor=self.execute,
            check=self.check, **kwargs,
        )

    def summary(self):
        return json.loads((self.root / runner.NAMESPACE / "SUMMARY.json").read_text())


@pytest.mark.parametrize("code", ["GOVERNANCE_HEAD_MISMATCH", "GOVERNANCE_TRACKED_DRIFT"])
def test_code_gate_stops_before_namespace_or_session(tmp_path, monkeypatch, code, capsys):
    h = Harness(tmp_path, monkeypatch)
    h.check_failure = code
    assert h.run() == 2
    assert h.calls == [] and not (tmp_path / runner.NAMESPACE).exists()
    assert code in capsys.readouterr().out


def test_actual_exact_head_and_tracked_drift_owner(monkeypatch):
    owner = sys.modules["ig_cand001_shadow_e2e"]
    monkeypatch.setattr(owner.subprocess, "check_output",
                        lambda argv, **kw: ("b" * 40 if argv[-1] == "HEAD" else ""))
    with pytest.raises(owner.HostTestBlocked, match="GOVERNANCE_HEAD_MISMATCH"):
        owner.check_code(HEAD)
    def output(argv, **kw):
        return HEAD if argv[-1] == "HEAD" else " M scripts/example.py"
    monkeypatch.setattr(owner.subprocess, "check_output", output)
    with pytest.raises(owner.HostTestBlocked, match="GOVERNANCE_TRACKED_DRIFT"):
        owner.check_code(HEAD)


def test_existing_namespace_preserves_all_files_no_session(tmp_path, monkeypatch):
    h = Harness(tmp_path, monkeypatch)
    directory = tmp_path / runner.NAMESPACE
    directory.mkdir(parents=True)
    (directory / "A.json").write_text("PRESERVE")
    (directory / "SUMMARY.json").write_text("PRESERVE_SUMMARY")
    assert h.run() == 2
    assert h.calls == []
    assert (directory / "A.json").read_text() == "PRESERVE"
    assert (directory / "SUMMARY.json").read_text() == "PRESERVE_SUMMARY"


@pytest.mark.parametrize("failed,called", [
    ("A", ["A"]), ("B", ["A", "B"]), ("C", ["A", "B", "C"]),
    ("AB", ["A", "B", "C", "AB"]), ("BC", ["A", "B", "C", "AB", "BC"]),
])
def test_failure_short_circuit_no_retry_summary(tmp_path, monkeypatch, failed, called, capsys):
    h = Harness(tmp_path, monkeypatch)
    h.failure = failed
    assert h.run() == 2
    assert [name for name, _ in h.calls] == called
    summary = h.summary()
    assert summary["final_state"] == "ABORTED_FAIL_CLOSED"
    assert summary["error_code"] == (
        "RAW_COMPARE_FAILED" if len(failed) == 2 else "IG_AUTHENTICATION_FAILED_NO_RETRY"
    )
    if failed in ("A", "B", "C"):
        assert all(item["status"] == "NOT_RUN" for item in summary["compare"].values())
        assert summary["raw"][failed]["exit"] == 2
        for name in ("A", "B", "C"):
            if name not in called:
                assert summary["raw"][name]["requested"] is False
                assert summary["raw"][name]["exit"] is None
    assert "NEVER_READ_SECRET" not in capsys.readouterr().out
    assert "NEVER_READ_SECRET" not in json.dumps(summary)


def test_success_full_set_local_compares_and_summary_hash(tmp_path, monkeypatch, capsys):
    h = Harness(tmp_path, monkeypatch)
    old = tmp_path / ".runtime/ig_raw_m5_truth_2233_v2"
    old.mkdir(parents=True)
    (old / "A.json").write_text("OLD_A_PRESERVED")
    assert h.run() == 0
    assert [name for name, _ in h.calls] == ["A", "B", "C", "AB", "BC"]
    summary = h.summary()
    fingerprint = summary.pop("fingerprint")
    assert fingerprint == runner.diagnostic._fingerprint(summary)
    assert summary["exact_head"] == HEAD
    assert summary["attempt_namespace"] == runner.NAMESPACE
    assert summary["final_state"] == "SUCCESS" and summary["error_code"] is None
    assert all(item["success"] and item["exit"] == 0 for item in summary["raw"].values())
    assert all(item["status"] == "SUCCESS" for item in summary["compare"].values())
    assert summary["execution_capability"] == "NONE"
    assert summary["order_execution_enabled"] is False
    assert summary["candidate_processing_performed"] is False
    assert summary["timestamp_semantics"] == "UNKNOWN"
    assert (old / "A.json").read_text() == "OLD_A_PRESERVED"
    for name, args in h.calls:
        if len(name) == 2:
            assert "--credentials-file" not in args
        else:
            assert args[args.index("--credentials-file") + 1] == str(h.creds)
    assert "FINAL STATUS: SUCCESS" in capsys.readouterr().out


def test_invalid_namespace_cannot_escape_or_print_user_text(tmp_path, monkeypatch, capsys):
    h = Harness(tmp_path, monkeypatch)
    assert h.run(namespace="../SECRET_TOKEN") == 2
    assert h.calls == []
    assert "SECRET_TOKEN" not in capsys.readouterr().out


def test_missed_window_before_invocation_stops_without_replanning(tmp_path, monkeypatch):
    h = Harness(tmp_path, monkeypatch)
    def late(target):
        h.current = target + timedelta(seconds=runner.SAMPLE_WINDOW_SECONDS)
    h.wait = late
    assert h.run() == 2
    assert h.calls == []
    assert h.summary()["error_code"] == "RAW_SAMPLING_WINDOW_MISSED"


@pytest.mark.parametrize("offset", [-1, 60])
def test_actual_request_outside_window_not_success_or_replaced(tmp_path, monkeypatch, offset):
    h = Harness(tmp_path, monkeypatch)
    h.request_offset = offset
    assert h.run() == 2
    assert [name for name, _ in h.calls] == ["A"]
    assert (tmp_path / runner.NAMESPACE / "A.json").is_file()
    assert h.summary()["error_code"] == "RAW_REQUEST_OUTSIDE_SAMPLING_WINDOW"


def test_namespace_file_injected_during_wait_not_overwritten(tmp_path, monkeypatch):
    h = Harness(tmp_path, monkeypatch)
    def inject(target):
        h.current = target
        (tmp_path / runner.NAMESPACE / "A.json").write_text("PRESERVE")
    h.wait = inject
    assert h.run() == 2
    assert h.calls == []
    assert (tmp_path / runner.NAMESPACE / "A.json").read_text() == "PRESERVE"


def test_changed_code_after_wait_blocks_no_session(tmp_path, monkeypatch):
    h = Harness(tmp_path, monkeypatch)
    def changed(target):
        h.current = target
        h.check_failure = "GOVERNANCE_TRACKED_DRIFT"
    h.wait = changed
    assert h.run() == 2
    assert h.calls == []


def test_exception_text_and_timeout_no_leak_no_retry(tmp_path, monkeypatch, capsys):
    h = Harness(tmp_path, monkeypatch)
    def failed(args):
        h.calls.append(("A", args))
        raise subprocess.TimeoutExpired("SECRET_PROVIDER_COMMAND", 120)
    h.execute = failed
    assert h.run() == 2
    assert len(h.calls) == 1
    assert h.summary()["error_code"] == "RAW_DIAGNOSTIC_TIMEOUT_NO_RETRY"
    assert "SECRET" not in capsys.readouterr().out


def test_summary_exclusive_creation_preserves_existing(tmp_path):
    (tmp_path / "SUMMARY.json").write_text("PRESERVE")
    with pytest.raises(FileExistsError):
        runner.publish_summary(tmp_path, {})
    assert (tmp_path / "SUMMARY.json").read_text() == "PRESERVE"


def test_executor_one_child_no_shell_same_interpreter_paths_spaces(monkeypatch):
    calls = []
    def child(argv, **kwargs):
        calls.append((argv, kwargs))
        return subprocess.CompletedProcess(argv, 2,
            '{"error_code":"IG_AUTHENTICATION_FAILED_NO_RETRY","secret":"SECRET"}', "SECRET")
    monkeypatch.setattr(runner.subprocess, "run", child)
    assert runner.execute(["--credentials-file", r"C:\A B\external.env"]) == (
        2, "IG_AUTHENTICATION_FAILED_NO_RETRY",
    )
    assert len(calls) == 1
    argv, kwargs = calls[0]
    assert argv[0] == sys.executable and argv[1].endswith("ig_raw_m5_timestamp_diagnostic.py")
    assert argv[-1] == r"C:\A B\external.env"
    assert kwargs["capture_output"] is True and kwargs["timeout"] == 120
    assert "shell" not in kwargs


def test_non_windows_stops(tmp_path, monkeypatch):
    h = Harness(tmp_path, monkeypatch)
    monkeypatch.setattr(runner.platform, "system", lambda: "Linux")
    assert h.run() == 2
    assert h.calls == []


@pytest.mark.parametrize("start", [START, START.replace(minute=45, second=0),
                                  START.replace(minute=46, second=0)])
def test_schedule_one_plan_next_boundary_two_periods(start):
    plan = runner.schedule(start)
    assert start < plan["A"]
    assert plan["A"].minute % 5 == 1 and plan["A"].second == 0
    assert plan["B"] - plan["A"] == plan["C"] - plan["B"] == timedelta(seconds=300)


def test_wait_bounded_chunks_checks_real_clock():
    current, ticks, sleeps = [START], [0.0], []
    def sleep(seconds):
        sleeps.append(seconds)
        current[0] += timedelta(seconds=seconds)
        ticks[0] += seconds
    target = START + timedelta(seconds=91)
    runner.wait_for(target, clock=lambda: current[0], monotonic=lambda: ticks[0], sleep=sleep)
    assert current[0] == target
    assert sleeps == [30, 30, 30, 1]


@pytest.mark.parametrize("change,code", [
    (timedelta(seconds=-1), "CLOCK_MOVED_BACKWARDS"),
    (timedelta(seconds=10), "CLOCK_DISCONTINUITY"),
])
def test_wait_clock_discontinuity_fails(change, code):
    values = iter([START, START + change])
    with pytest.raises(runner.AttemptBlocked, match=code):
        runner.wait_for(START + timedelta(minutes=1), clock=lambda: next(values),
                        monotonic=lambda: 0, sleep=lambda _: pytest.fail("No sleep"))


def test_wait_already_missed_window_fails():
    with pytest.raises(runner.AttemptBlocked, match="RAW_SAMPLING_WINDOW_MISSED"):
        runner.wait_for(START - timedelta(seconds=60), clock=lambda: START,
                        monotonic=lambda: 0, sleep=lambda _: pytest.fail("No sleep"))


def test_mutation_or_invalid_compare_artifact_is_not_accepted(tmp_path, monkeypatch):
    h = Harness(tmp_path, monkeypatch)
    actual = h.execute
    def tampered(args):
        result = actual(args)
        if "--compare" in args:
            output = Path(args[-1])
            payload = json.loads(output.read_text())
            payload["timestamp_semantics"] = "INTERVAL_START"
            output.write_text(json.dumps(payload))
        return result
    h.execute = tampered
    assert h.run() == 2
    assert [name for name, _ in h.calls] == ["A", "B", "C", "AB"]
    assert h.summary()["error_code"] == "RAW_COMPARE_EVIDENCE_MISMATCH"


def test_orchestrator_invokes_only_raw_diagnostic():
    source = (ROOT / "scripts/run_ig_raw_truth_2233.py").read_text()
    assert "ig_raw_m5_timestamp_diagnostic.py" in source
    assert "process_cand001" not in source
    assert "ig_cand001_shadow_e2e.py" not in source
    assert "/positions" not in source and "/workingorders" not in source
    assert "order_send" not in source
    assert "client.login" not in source


def test_powershell_launcher_parses_and_propagates_python_exit(tmp_path):
    pwsh = shutil.which("pwsh")
    if not pwsh:
        pytest.skip("PowerShell not installed")
    scripts = tmp_path / "checkout with spaces" / "scripts"
    scripts.mkdir(parents=True)
    launcher = scripts / "run_ig_raw_truth_2233.ps1"
    shutil.copyfile(ROOT / "scripts/run_ig_raw_truth_2233.ps1", launcher)
    (scripts / "run_ig_raw_truth_2233.py").write_text(
        "import sys\nassert sys.argv[1:] == "
        + repr(["--expected-head", HEAD, "--namespace", runner.NAMESPACE,
                "--credentials-file", r"C:\Users\Mandy\ig_demo.env"])
        + "\nsys.exit(2)\n"
    )
    result = subprocess.run(
        [pwsh, "-NoProfile", "-File", str(launcher), "-ExpectedHead", HEAD,
         "-PythonExecutable", sys.executable], capture_output=True, text=True, check=False,
    )
    assert result.returncode == 2
    assert "RAW_WINDOWS_LAUNCH_FAILED" not in result.stdout + result.stderr
