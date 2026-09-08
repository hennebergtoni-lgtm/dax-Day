"""Offline preflight for reconstructing the DAX Research Lab from versioned state."""
from __future__ import annotations

from pathlib import Path

EXPECTED_MIGRATIONS = (
    "0001_research_core.sql",
    "0002_reference_provenance.sql",
    "0003_active_reference_registry.sql",
    "0004_detail_evidence_registry.sql",
)
EXPECTED_FILES = (
    "data/manifests/dax_m5_2014_2019_audited.json",
    "research/V112_REFERENCE_V1/reference_result.json",
    "src/daxlab/runtime/checkpoint.py",
    "src/daxlab/runtime/manifests.py",
    "src/daxlab/runtime/recovery_bundle.py",
    "scripts/check_db_integrity.py",
    "docs/RECOVERY_AND_RECONSTRUCTION_CONTRACT_V1.md",
)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    missing = [path for path in EXPECTED_FILES if not (root / path).is_file()]
    migration_dir = root / "db" / "migrations"
    observed_migrations = tuple(sorted(path.name for path in migration_dir.glob("*.sql")))
    if observed_migrations != EXPECTED_MIGRATIONS:
        raise SystemExit(
            "recovery preflight failed: migration chain drift | "
            f"expected={EXPECTED_MIGRATIONS} observed={observed_migrations}"
        )
    if missing:
        raise SystemExit(f"recovery preflight failed: missing canonical files {missing}")
    print(
        "Recovery preflight OK | canonical_files="
        f"{len(EXPECTED_FILES)} | migrations={len(EXPECTED_MIGRATIONS)}"
    )


if __name__ == "__main__":
    main()
