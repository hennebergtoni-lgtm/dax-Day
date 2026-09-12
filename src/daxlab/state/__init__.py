"""State, checkpoint and recovery contracts for DAX-BOT NextGen."""

from daxlab.state.codecs import StrategyStateCodec
from daxlab.state.loss_exposure import (
    LOSS_EXPOSURE_OBSERVATION_CHECKPOINT_SCHEMA,
    LossExposureCheckpointCompatibilityError,
    LossExposureObservationCheckpoint,
    assert_loss_exposure_checkpoint_compatible,
    build_loss_exposure_observation_checkpoint,
    load_loss_exposure_checkpoint,
    loss_exposure_checkpoint_from_bytes,
    loss_exposure_checkpoint_to_bytes,
    save_loss_exposure_checkpoint,
)
from daxlab.state.replay_checkpoint import (
    CHECKPOINT_SCHEMA,
    CheckpointCompatibilityError,
    ProductCheckpointV1,
    assert_checkpoint_compatible,
    build_product_checkpoint,
    checkpoint_from_bytes,
    checkpoint_to_bytes,
    load_checkpoint,
    save_checkpoint,
)

__all__ = [
    "CHECKPOINT_SCHEMA",
    "LOSS_EXPOSURE_OBSERVATION_CHECKPOINT_SCHEMA",
    "CheckpointCompatibilityError",
    "LossExposureCheckpointCompatibilityError",
    "LossExposureObservationCheckpoint",
    "ProductCheckpointV1",
    "StrategyStateCodec",
    "assert_checkpoint_compatible",
    "assert_loss_exposure_checkpoint_compatible",
    "build_loss_exposure_observation_checkpoint",
    "build_product_checkpoint",
    "checkpoint_from_bytes",
    "checkpoint_to_bytes",
    "load_checkpoint",
    "load_loss_exposure_checkpoint",
    "loss_exposure_checkpoint_from_bytes",
    "loss_exposure_checkpoint_to_bytes",
    "save_checkpoint",
    "save_loss_exposure_checkpoint",
]
