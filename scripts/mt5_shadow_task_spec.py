#!/usr/bin/env python3
"""Build a credential-free Windows Task Scheduler specification for MT5 SHADOW.

This module does not register, start, stop, or delete Windows tasks. It only
validates host paths/configuration and emits a deterministic task specification
that mirrors the existing PowerShell installer contract for later host-side
verification after the broker timezone is VERIFIED.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "DAXLAB_MT5_WINDOWS_TASK_SPEC_V1"
TASK_NAME = "DAXLAB MT5 SHADOW"


@dataclass(frozen=True)
class WindowsShadowTaskSpec:
    schema_version: str
    task_name: str
    trigger: str
    run_only_when_user_logged_on: bool
    multiple_instances: str
    start_when_available: bool
    allow_start_if_on_batteries: bool
    dont_stop_if_going_on_batteries: bool
    execution_time_limit_seconds: int
    restart_interval_minutes: int
    restart_count: int
    startup_delay_seconds: int
    python_exe: str
    supervisor_script: str
    working_directory: str
    state_directory: str
    broker_timezone: str
    execution_capability: str
    order_execution_enabled: bool

    def to_payload(self) -> dict[str, Any]:
        return asdict(self)


def _existing_file(path: str, label: str) -> Path:
    value = Path(path).expanduser().resolve()
    if not value.is_file():
        raise ValueError(f"{label} must be an existing file")
    return value


def _existing_dir(path: str, label: str) -> Path:
    value = Path(path).expanduser().resolve()
    if not value.is_dir():
        raise ValueError(f"{label} must be an existing directory")
    return value


def build_windows_shadow_task_spec(
    *,
    repo_root: str,
    python_exe: str,
    broker_timezone: str,
    state_directory: str | None = None,
) -> WindowsShadowTaskSpec:
    """Return a fail-closed task spec without performing any Windows mutation."""
    root = _existing_dir(repo_root, "repo_root")
    python = _existing_file(python_exe, "python_exe")
    supervisor = root / "scripts" / "mt5_shadow_supervisor.py"
    if not supervisor.is_file():
        raise ValueError("repo_root does not contain scripts/mt5_shadow_supervisor.py")

    timezone = broker_timezone.strip()
    if not timezone:
        raise ValueError("broker_timezone must be explicitly supplied")

    state = (
        Path(state_directory).expanduser().resolve()
        if state_directory is not None
        else root / ".runtime" / "mt5_shadow"
    )

    return WindowsShadowTaskSpec(
        schema_version=SCHEMA_VERSION,
        task_name=TASK_NAME,
        trigger="AT_LOGON",
        run_only_when_user_logged_on=True,
        multiple_instances="IGNORE_NEW",
        start_when_available=True,
        allow_start_if_on_batteries=True,
        dont_stop_if_going_on_batteries=True,
        execution_time_limit_seconds=0,
        restart_interval_minutes=5,
        restart_count=3,
        startup_delay_seconds=0,
        python_exe=str(python),
        supervisor_script=str(supervisor.resolve()),
        working_directory=str(root),
        state_directory=str(state),
        broker_timezone=timezone,
        execution_capability="NONE",
        order_execution_enabled=False,
    )
