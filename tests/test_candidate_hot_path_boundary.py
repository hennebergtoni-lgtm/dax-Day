import ast
from pathlib import Path


HOT_PATH_MODULES = (
    "candidate_config.py",
    "candidate_signal.py",
    "candidate_trade_plan.py",
    "candidate_admission.py",
    "candidate_decision.py",
    "candidate_pipeline.py",
    "operator_snapshot.py",
)
FORBIDDEN_IMPORT_PREFIXES = (
    "pandas",
    "numpy",
    "psycopg",
    "MetaTrader5",
    "daxlab.db",
    "daxlab.runtime.mt5_",
    "daxlab.runtime.paper_contracts",
)


def imported_modules(path: Path) -> tuple[str, ...]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    values: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            values.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            values.append(node.module)
    return tuple(values)


def test_candidate_hot_path_stays_free_of_dataframe_db_mt5_and_paper_dependencies():
    runtime_dir = Path(__file__).parents[1] / "src" / "daxlab" / "runtime"

    for module_name in HOT_PATH_MODULES:
        imports = imported_modules(runtime_dir / module_name)
        forbidden = tuple(
            item
            for item in imports
            if any(item.startswith(prefix) for prefix in FORBIDDEN_IMPORT_PREFIXES)
        )
        assert forbidden == (), f"{module_name} gained forbidden hot-path imports: {forbidden}"
