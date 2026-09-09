from daxlab.runtime.shadow_soak import initial_soak_checkpoint


def test_soak_checkpoint_schema_version_is_explicit() -> None:
    assert initial_soak_checkpoint().schema_version == "DAXLAB_SHADOW_SOAK_CHECKPOINT_V2"
