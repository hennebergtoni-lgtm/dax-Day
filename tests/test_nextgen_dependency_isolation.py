from __future__ import annotations

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"

PROTECTED_GLOBS = (
    "src/daxlab/domain/*.py",
    "src/daxlab/engine/*.py",
    "src/daxlab/data/catalog/*.py",
    "src/daxlab/state/*.py",
)

PROTECTED_FILES = (
    "src/daxlab/strategies/contracts.py",
    "src/daxlab/strategies/__init__.py",
    "src/daxlab/operator/read_model.py",
    "src/daxlab/operator/__init__.py",
    "src/daxlab/research/promotion.py",
    "src/daxlab/research/conformance.py",
    "src/daxlab/adapters/file_state_store.py",
)

COMPATIBILITY_RUNTIME_ALLOWLIST = {
    "src/daxlab/strategies/cand001/adapter.py": frozenset(
        {
            "daxlab.runtime.candidate_config",
            "daxlab.runtime.candidate_pipeline",
            "daxlab.runtime.candidate_signal",
            "daxlab.runtime.contracts",
            "daxlab.runtime.decision",
        }
    ),
    "src/daxlab/strategies/cand001/state_codec.py": frozenset(
        {
            "daxlab.runtime.candidate_admission",
            "daxlab.runtime.candidate_pipeline",
            "daxlab.runtime.candidate_signal",
        }
    ),
    "src/daxlab/adapters/mt5_market_data.py": frozenset(
        {
            "daxlab.runtime.mt5_feed_payload",
            "daxlab.runtime.mt5_readonly",
        }
    ),
    "src/daxlab/adapters/cand001_operator.py": frozenset(
        {
            "daxlab.runtime.candidate_operator_query",
            "daxlab.runtime.candidate_operator_telemetry",
        }
    ),
}


def _repo_relative(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def _module_parts(path: Path) -> list[str]:
    relative = path.relative_to(SRC_ROOT).with_suffix("")
    parts = list(relative.parts)
    if parts[-1] == "__init__":
        parts.pop()
    return parts


def _resolve_from_import(path: Path, node: ast.ImportFrom) -> tuple[str, ...]:
    if node.level == 0:
        if node.module is None:
            return ()
        return (node.module,)

    package_parts = _module_parts(path)
    if path.name != "__init__.py":
        package_parts = package_parts[:-1]

    climb = node.level - 1
    if climb > len(package_parts):
        return ()
    base = package_parts[: len(package_parts) - climb]

    if node.module:
        return (".".join([*base, *node.module.split(".")]),)

    return tuple(
        ".".join([*base, alias.name])
        for alias in node.names
        if alias.name != "*"
    )


def _imports(path: Path) -> tuple[str, ...]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            modules.extend(_resolve_from_import(path, node))
    return tuple(modules)


def _protected_files() -> tuple[Path, ...]:
    files: set[Path] = set()
    for pattern in PROTECTED_GLOBS:
        files.update(REPO_ROOT.glob(pattern))
    for relative in PROTECTED_FILES:
        path = REPO_ROOT / relative
        assert path.is_file(), f"protected dependency owner missing: {relative}"
        files.add(path)
    assert files, "NextGen dependency guard found no protected files"
    return tuple(sorted(files))


def _is_version_specific_legacy(module: str) -> bool:
    lowered = module.lower()
    return (
        module.startswith("daxlab.reference")
        or module in {"daxlab.detail_import", "daxlab.detail_artifact_loader"}
        or any(token in lowered for token in (".v11", ".v12", ".v112"))
    )


def _canonical_violation(module: str) -> str | None:
    if module == "MetaTrader5" or module.startswith("MetaTrader5."):
        return "direct MetaTrader5 SDK import"
    if module == "daxlab.runtime" or module.startswith("daxlab.runtime."):
        return "runtime backflow"
    if module == "daxlab.data.legacy_dataset" or module.startswith(
        "daxlab.data.legacy_dataset."
    ):
        return "legacy dataset backflow"
    if module == "daxlab.strategies.cand001" or module.startswith(
        "daxlab.strategies.cand001."
    ):
        return "CAND-001 backflow"
    if module == "daxlab.adapters" or module.startswith("daxlab.adapters."):
        return "concrete adapter backflow"
    if module.startswith("daxlab.research.") and "cand001" in module.lower():
        return "CAND-001 research backflow"
    if _is_version_specific_legacy(module):
        return "version/reference legacy backflow"
    return None


def test_protected_nextgen_owners_do_not_depend_on_legacy_runtime_or_adapters() -> None:
    violations: list[str] = []
    for path in _protected_files():
        relative = _repo_relative(path)
        for module in _imports(path):
            reason = _canonical_violation(module)
            if reason is not None:
                violations.append(f"{relative}: {module} ({reason})")
    assert not violations, "NextGen dependency isolation violated:\n" + "\n".join(violations)


def test_compatibility_edges_use_only_the_audited_runtime_import_allowlist() -> None:
    violations: list[str] = []
    for relative, allowed_runtime_modules in COMPATIBILITY_RUNTIME_ALLOWLIST.items():
        path = REPO_ROOT / relative
        assert path.is_file(), f"documented compatibility edge missing: {relative}"
        for module in _imports(path):
            if module == "MetaTrader5" or module.startswith("MetaTrader5."):
                violations.append(f"{relative}: {module} (direct MetaTrader5 SDK import)")
                continue
            if module == "daxlab.runtime" or module.startswith("daxlab.runtime."):
                if module not in allowed_runtime_modules:
                    violations.append(f"{relative}: {module} (runtime import not allowlisted)")
    assert not violations, "Compatibility dependency allowlist violated:\n" + "\n".join(
        violations
    )


def test_runtime_allowlist_has_no_implicit_package_wildcards() -> None:
    for relative, modules in COMPATIBILITY_RUNTIME_ALLOWLIST.items():
        assert modules, f"runtime allowlist must remain explicit: {relative}"
        assert all(module.startswith("daxlab.runtime.") for module in modules)
        assert "daxlab.runtime" not in modules
