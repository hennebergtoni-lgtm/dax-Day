from __future__ import annotations

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]

HISTORICAL_OPERATOR_MODULES = {
    "daxlab.operator.forward_monitoring_view",
    "daxlab.operator.view_models",
}
EXPECTED_PROMOTION_CONTRACT_IMPORTS = {
    "CostModel",
    "ExperimentManifest",
    "WalkForwardSpec",
}


def _tree(path: str) -> ast.AST:
    file_path = REPO_ROOT / path
    assert file_path.is_file(), f"audited compatibility surface missing: {path}"
    return ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))


def _imported_modules(tree: ast.AST) -> set[str]:
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def test_historical_operator_views_remain_isolated_from_canonical_exports() -> None:
    canonical_tree = _tree("src/daxlab/operator/__init__.py")
    imported = _imported_modules(canonical_tree)

    assert HISTORICAL_OPERATOR_MODULES.isdisjoint(imported)
    assert "daxlab.operator.read_model" in imported

    for module in HISTORICAL_OPERATOR_MODULES:
        relative = "src/" + module.replace(".", "/") + ".py"
        assert (REPO_ROOT / relative).is_file()


def test_promotion_reuses_only_the_audited_generic_contract_primitives() -> None:
    tree = _tree("src/daxlab/research/promotion.py")
    contract_imports: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "daxlab.contracts":
            contract_imports.update(alias.name for alias in node.names)

    assert contract_imports == EXPECTED_PROMOTION_CONTRACT_IMPORTS


def test_audited_compatibility_surfaces_exist_until_a_separate_retirement_step() -> None:
    audited_paths = (
        "src/daxlab/strategies/cand001/adapter.py",
        "src/daxlab/strategies/cand001/state_codec.py",
        "src/daxlab/adapters/mt5_market_data.py",
        "src/daxlab/adapters/cand001_operator.py",
        "src/daxlab/operator/forward_monitoring_view.py",
        "src/daxlab/operator/view_models.py",
        "src/daxlab/research/promotion.py",
    )

    missing = [path for path in audited_paths if not (REPO_ROOT / path).is_file()]
    assert not missing, "audited compatibility surface disappeared without retirement proof: " + ", ".join(missing)
