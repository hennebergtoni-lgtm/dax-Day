from __future__ import annotations

import ast
from pathlib import Path

import pytest

from daxlab.adapters.file_state_store import AtomicFileStateStore
from daxlab.domain.ports import StateStorePort


def test_store_satisfies_port_and_round_trips_exact_bytes(tmp_path: Path) -> None:
    store = AtomicFileStateStore(tmp_path / "state")

    assert isinstance(store, StateStorePort)
    assert store.load("engine-state") is None

    payload = b"\x00DAX\xff\nstate\x00"
    store.save("engine-state", payload)

    assert store.load("engine-state") == payload
    assert (tmp_path / "state" / "engine-state.bin").read_bytes() == payload


def test_store_accepts_empty_payload_and_replaces_existing_state(tmp_path: Path) -> None:
    store = AtomicFileStateStore(tmp_path / "state")

    store.save("checkpoint.v1", b"first")
    store.save("checkpoint.v1", b"")
    assert store.load("checkpoint.v1") == b""

    store.save("checkpoint.v1", b"second")
    assert store.load("checkpoint.v1") == b"second"


def test_store_rejects_path_traversal_and_nonportable_keys(tmp_path: Path) -> None:
    store = AtomicFileStateStore(tmp_path / "state")

    invalid = (
        "",
        ".",
        "..",
        "../escape",
        "subdir/key",
        "subdir\\key",
        "/absolute",
        " key",
        "key ",
        "key:colon",
        "a" * 129,
    )
    for key in invalid:
        with pytest.raises(ValueError, match="portable characters"):
            store.load(key)
        with pytest.raises(ValueError, match="portable characters"):
            store.save(key, b"payload")

    with pytest.raises(TypeError, match="key must be str"):
        store.load(123)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="key must be str"):
        store.save(123, b"payload")  # type: ignore[arg-type]


def test_store_rejects_non_bytes_payload(tmp_path: Path) -> None:
    store = AtomicFileStateStore(tmp_path / "state")

    with pytest.raises(TypeError, match="payload must be bytes"):
        store.save("state", bytearray(b"x"))  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="payload must be bytes"):
        store.save("state", "text")  # type: ignore[arg-type]


def test_store_rejects_existing_non_directory_root(tmp_path: Path) -> None:
    root = tmp_path / "state"
    root.write_bytes(b"not-a-directory")

    with pytest.raises(ValueError, match="root must be a directory"):
        AtomicFileStateStore(root)


def test_failed_atomic_replace_preserves_previous_state_and_cleans_temp(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = AtomicFileStateStore(tmp_path / "state")
    store.save("checkpoint", b"known-good")

    def fail_replace(source: Path | str, target: Path | str) -> None:
        raise OSError("simulated replace failure")

    monkeypatch.setattr("daxlab.adapters.file_state_store.os.replace", fail_replace)

    with pytest.raises(OSError, match="simulated replace failure"):
        store.save("checkpoint", b"new-state")

    assert store.load("checkpoint") == b"known-good"
    leftovers = tuple((tmp_path / "state").glob(".checkpoint.bin.*.tmp"))
    assert leftovers == ()


def test_new_key_replace_failure_leaves_no_partial_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = AtomicFileStateStore(tmp_path / "state")

    def fail_replace(source: Path | str, target: Path | str) -> None:
        raise OSError("simulated replace failure")

    monkeypatch.setattr("daxlab.adapters.file_state_store.os.replace", fail_replace)

    with pytest.raises(OSError, match="simulated replace failure"):
        store.save("new-state", b"payload")

    assert store.load("new-state") is None
    assert tuple((tmp_path / "state").glob(".new-state.bin.*.tmp")) == ()


def test_adapter_is_storage_only_and_does_not_import_recovery_or_execution() -> None:
    repo = Path(__file__).resolve().parents[1]
    module = repo / "src/daxlab/adapters/file_state_store.py"
    tree = ast.parse(module.read_text(encoding="utf-8"))

    imported: set[str] = set()
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
        elif isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)

    forbidden_imports = (
        "daxlab.runtime.recovery",
        "daxlab.runtime.recovery_bundle",
        "daxlab.runtime.checkpoint",
        "daxlab.runtime.candidate",
        "daxlab.domain.execution",
        "MetaTrader5",
    )
    assert not any(
        name == prefix or name.startswith(prefix + ".")
        for name in imported
        for prefix in forbidden_imports
    )
    assert "order_send" not in names
    assert "accept_intent" not in names
