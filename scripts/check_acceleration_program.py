"""Audit Research Factory coverage/backlog; never infer broker or execution truth."""
from __future__ import annotations

import ast
from collections import Counter
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "research/acceleration_program_v1.json"


def check(payload, root=ROOT):
    if payload["schema"] != "DAX_ACCELERATION_PROGRAM_V1":
        raise ValueError("registry schema")
    if payload["execution_capability"] != "NONE" or payload["order_execution_enabled"] is not False:
        raise ValueError("registry cannot grant execution")
    if payload["real_broker_evidence_refs"]:
        raise ValueError("real broker evidence requires a separately reviewed registry revision")
    for key, prefix, count, width in (("hypotheses", "H", 40, 2),
                                      ("failures", "F", 100, 3),
                                      ("architecture_learnings", "L", 24, 2)):
        rows = payload[key]
        expected = [prefix + str(i).zfill(width) for i in range(1, count + 1)]
        if [r["id"] for r in rows] != expected:
            raise ValueError("missing, duplicate or reordered source IDs")
        for row in rows:
            owner = row.get("owner", row.get("available_owner"))
            path = Path(owner)
            if path.is_absolute() or ".." in path.parts or not (root / path).is_file():
                raise ValueError("owner missing or unsafe")
    for source in payload["sources"]:
        if re.fullmatch(r"[0-9a-f]{64}", source["extracted_text_sha256"]) is None:
            raise ValueError("source text provenance missing")
    for row in payload["failures"]:
        if row["status"] not in {"SYNTHETIC_ONLY", "GAP", "WAITING_EXTERNAL", "LOCAL_VERIFIED"}:
            raise ValueError("synthetic scenario cannot become REAL_DEMO_VERIFIED")
        for reference in row["unit_tests"]:
            path, name = reference.split("::")
            if Path(path).is_absolute() or ".." in Path(path).parts:
                raise ValueError("unsafe test reference")
            tree = ast.parse((root / path).read_text(encoding="utf-8"))
            if name not in {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}:
                raise ValueError("test reference no longer exists")
    return {"hypotheses": dict(Counter(r["decision"] for r in payload["hypotheses"])),
            "failures": dict(Counter(r["status"] for r in payload["failures"])),
            "learnings": dict(Counter(r["decision"] for r in payload["architecture_learnings"])),
            "scope": "BACKLOG_INTEGRITY_ONLY_NOT_COVERAGE_OR_BROKER_PROOF"}


def main():
    print(json.dumps(check(json.loads(PATH.read_text(encoding="utf-8"))), sort_keys=True))


if __name__ == "__main__":
    main()
