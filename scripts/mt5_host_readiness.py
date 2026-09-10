#!/usr/bin/env python3
"""Fail-closed evaluator for Windows MT5 SHADOW host readiness evidence."""
from __future__ import annotations

from typing import Any, Mapping


SCHEMA_VERSION = "DAXLAB_MT5_HOST_READINESS_V1"


def evaluate_host_readiness(
    discovery: Mapping[str, Any],
    *,
    broker_timezone_verified: bool,
) -> dict[str, Any]:
    blockers: list[str] = []
    if discovery.get("execution_capability") != "NONE":
        blockers.append("EXECUTION_CAPABILITY_NOT_NONE")
    if discovery.get("order_execution_enabled") is not False:
        blockers.append("ORDER_EXECUTION_NOT_FALSE")
    if discovery.get("credentials_included") is not False:
        blockers.append("CREDENTIAL_CONTRACT_FAILED")
    if discovery.get("platform_system") != "Windows":
        blockers.append("WINDOWS_HOST_NOT_VERIFIED")
    if discovery.get("supervisor_exists") is not True:
        blockers.append("SUPERVISOR_NOT_FOUND")
    if discovery.get("metatrader5_importable") is not True:
        blockers.append("METATRADER5_NOT_IMPORTABLE")
    if not str(discovery.get("python_exe", "")).strip():
        blockers.append("PYTHON_EXE_NOT_FOUND")
    if not str(discovery.get("repo_root", "")).strip():
        blockers.append("REPO_ROOT_NOT_FOUND")
    if broker_timezone_verified is not True:
        blockers.append("BROKER_TIMEZONE_UNVERIFIED")

    ready = not blockers
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "READY" if ready else "BLOCKED",
        "blockers": blockers,
        "task_registration_allowed": ready,
        "execution_capability": "NONE",
        "order_execution_enabled": False,
    }
