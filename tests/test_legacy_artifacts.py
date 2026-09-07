from hashlib import sha256

import pytest

from daxlab.reference.legacy_artifacts import ArtifactExpectation, sha256_file, verify_artifact


def test_sha256_file_is_deterministic(tmp_path):
    path = tmp_path / "artifact.txt"
    path.write_bytes(b"dax-v11.2")

    expected = sha256(b"dax-v11.2").hexdigest()
    assert sha256_file(path) == expected
    assert sha256_file(path) == expected


def test_verify_artifact_accepts_exact_hash(tmp_path):
    path = tmp_path / "engine.ipynb"
    payload = b"proven-engine"
    path.write_bytes(payload)
    expectation = ArtifactExpectation(
        key="engine",
        filename="engine.ipynb",
        expected_sha256=sha256(payload).hexdigest(),
    )

    assert verify_artifact(path, expectation) == expectation.expected_sha256


def test_verify_artifact_rejects_hash_drift(tmp_path):
    path = tmp_path / "engine.ipynb"
    path.write_bytes(b"changed")
    expectation = ArtifactExpectation(
        key="engine",
        filename="engine.ipynb",
        expected_sha256="0" * 64,
    )

    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        verify_artifact(path, expectation)


def test_verify_artifact_rejects_wrong_filename(tmp_path):
    path = tmp_path / "wrong.ipynb"
    path.write_bytes(b"payload")
    expectation = ArtifactExpectation(key="engine", filename="engine.ipynb")

    with pytest.raises(ValueError, match="Wrong artifact"):
        verify_artifact(path, expectation)
