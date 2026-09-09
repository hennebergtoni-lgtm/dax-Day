from pathlib import Path


def test_main_ci_retains_neon_migration_integrity_and_restore_gates() -> None:
    root = Path(__file__).resolve().parents[1]
    workflow = (root / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    for label in (
        "Neon connection gate",
        "Apply research database migrations",
        "Neon integrity gate",
        "Isolated database restore drill",
        "Isolated detail import drill",
    ):
        assert label in workflow
